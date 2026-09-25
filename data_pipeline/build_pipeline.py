from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://books.toscrape.com/"
CATEGORIES = [
    ("Travel", "catalogue/category/books/travel_2/index.html"),
    ("Mystery", "catalogue/category/books/mystery_3/index.html"),
    ("Historical Fiction", "catalogue/category/books/historical-fiction_4/index.html"),
    ("Science Fiction", "catalogue/category/books/science-fiction_1/index.html"),
]
GBP_TO_INR_RATE = 105.50
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "books.db"
RAW_DATA_PATH = BASE_DIR / "books_raw.csv"
QUERY_OUTPUT_PATH = BASE_DIR / "sql_results.md"
QUERY_SQL_PATH = BASE_DIR / "queries.sql"


def scrape_category(category_name: str, category_url: str) -> list[dict]:
    url = BASE_URL + category_url
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    books = []

    for article in soup.select("article.product_pod"):
        try:
            title = article.h3.a["title"]
            price_text = article.select_one("p.price_color").get_text(strip=True)
            price_match = re.search(r"\d+\.\d+", price_text)
            if price_match is None:
                price_gbp = np.nan
            else:
                price_gbp = float(price_match.group(0))

            rating_tag = article.select_one("p.star-rating")
            rating_class = rating_tag.get("class", ["star-rating", "Zero"])[-1]
            rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
            rating = rating_map.get(rating_class, np.nan)

            availability_text = article.select_one("p.instock.availability").get_text(" ", strip=True)
            in_stock = "in stock" in availability_text.lower()

            books.append(
                {
                    "title": title,
                    "price_gbp": price_gbp,
                    "rating": rating,
                    "in_stock": in_stock,
                    "category": category_name,
                }
            )
        except Exception:
            continue

    return books


def build_dataframe() -> pd.DataFrame:
    rows: list[dict] = []
    for category_name, category_url in CATEGORIES:
        rows.extend(scrape_category(category_name, category_url))

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No books were scraped.")

    df = df.dropna(subset=["title", "category"]).copy()
    df["price_gbp"] = pd.to_numeric(df["price_gbp"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["in_stock"] = df["in_stock"].fillna(False).astype(bool)

    if df["price_gbp"].isna().any():
        median_price = df["price_gbp"].median()
        df["price_gbp"] = df["price_gbp"].fillna(median_price)
    if df["rating"].isna().any():
        median_rating = df["rating"].median()
        df["rating"] = df["rating"].fillna(median_rating)

    df["price_gbp"] = df["price_gbp"].astype(float)
    df["rating"] = df["rating"].astype(int)
    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR_RATE).round(2)
    df = df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]]
    df.to_csv(RAW_DATA_PATH, index=False)
    return df


def create_database(df: pd.DataFrame) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("DROP TABLE IF EXISTS books")
    conn.execute("DROP TABLE IF EXISTS categories")
    conn.execute(
        """
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price_gbp REAL,
            price_inr REAL,
            rating INTEGER,
            in_stock INTEGER,
            category_id INTEGER,
            FOREIGN KEY(category_id) REFERENCES categories(category_id)
        )
        """
    )

    category_df = pd.DataFrame({"category_name": sorted(df["category"].drop_duplicates().tolist())})
    category_df.to_sql("categories", conn, if_exists="append", index=False)

    categories = pd.read_sql_query("SELECT category_id, category_name FROM categories", conn)
    category_map = dict(zip(categories["category_name"], categories["category_id"]))

    books_df = df.copy()
    books_df["category_id"] = books_df["category"].map(category_map)
    books_rows = books_df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category_id"]].copy()
    books_rows["in_stock"] = books_rows["in_stock"].astype(int)
    books_rows.columns = ["title", "price_gbp", "price_inr", "rating", "in_stock", "category_id"]
    books_rows.to_sql("books", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    return df


def build_queries() -> list[dict]:
    query_sql = [
        {
            "name": "select_where_order_limit",
            "sql": "SELECT title, price_inr FROM books WHERE in_stock = 1 ORDER BY price_inr DESC LIMIT 10;",
        },
        {
            "name": "distinct_categories",
            "sql": "SELECT DISTINCT category_name FROM categories ORDER BY category_name;",
        },
        {
            "name": "price_between",
            "sql": "SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 20 AND 40 ORDER BY price_gbp;",
        },
        {
            "name": "in_clause",
            "sql": "SELECT title, rating FROM books WHERE category_id IN (SELECT category_id FROM categories WHERE category_name IN ('Travel', 'Mystery')) ORDER BY rating DESC LIMIT 10;",
        },
        {
            "name": "join_highest_rated",
            "sql": "SELECT c.category_name, b.title, b.rating, b.price_inr FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY b.rating DESC, c.category_name LIMIT 10;",
        },
    ]

    with QUERY_SQL_PATH.open("w", encoding="utf-8") as fh:
        for item in query_sql:
            fh.write(f"-- {item['name']}\n{item['sql']}\n\n")

    return query_sql


def execute_queries() -> dict[str, pd.DataFrame]:
    conn = sqlite3.connect(DB_PATH)
    results: dict[str, pd.DataFrame] = {}
    for query in build_queries():
        df = pd.read_sql_query(query["sql"], conn)
        results[query["name"]] = df
        print(f"\nQuery: {query['name']}\n{query['sql']}\n")
        print(df.head(10).to_string(index=False))
    conn.close()
    return results


def validate_join_equivalence() -> None:
    conn = sqlite3.connect(DB_PATH)
    sql_join = pd.read_sql_query(
        "SELECT c.category_name, b.title, b.rating, b.price_inr FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY b.rating DESC, c.category_name LIMIT 10;",
        conn,
    )
    conn.close()

    books = pd.read_csv(RAW_DATA_PATH)
    categories = pd.DataFrame({
        "category_id": [1, 2, 3, 4],
        "category_name": ["Historical Fiction", "Mystery", "Science Fiction", "Travel"],
    })
    books_with_id = books.copy()
    books_with_id["category_id"] = books_with_id["category"].map({
        "Historical Fiction": 1,
        "Mystery": 2,
        "Science Fiction": 3,
        "Travel": 4,
    })
    merge_join = books_with_id[["title", "rating", "price_inr", "category_id"]].merge(
        categories,
        on="category_id",
        how="inner",
    )[["category_name", "title", "rating", "price_inr"]].sort_values(["rating", "category_name"], ascending=[False, True]).head(10).reset_index(drop=True)

    print("\nPandas merge result (equivalent to SQL join):")
    print(merge_join.to_string(index=False))
    print("\nSQL join result:")
    print(sql_join.to_string(index=False))

    print("\nJoin outputs equivalent:", sql_join.reset_index(drop=True).equals(merge_join.rename(columns={"category_name": "category_name", "title": "title", "rating": "rating", "price_inr": "price_inr"}).reset_index(drop=True)) )


def write_summary(results: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# SQL Query Results",
        "",
        "The project-defined conversion rate is `1 GBP = 105.50 INR`.",
        "",
    ]
    for name, frame in results.items():
        lines.append(f"## {name}")
        lines.append(frame.head(10).to_markdown(index=False))
        lines.append("")

    QUERY_OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = build_dataframe()
    print(f"Scraped {len(df)} books across {df['category'].nunique()} categories.")
    create_database(df)
    results = execute_queries()
    write_summary(results)
    validate_join_equivalence()


if __name__ == "__main__":
    main()
