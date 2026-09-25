# Data Pipeline Module

This module follows the end-to-end raw-to-relational pipeline:

1. scrape public book listings,
2. clean and validate the fields,
3. convert `price_gbp` to `price_inr` using the fixed baseline `1 GBP = 105.50 INR`,
4. normalize the data into SQLite, and
5. validate the database using SQL and pandas.

## Parsing and cleaning choices

- `price_gbp`: string values are normalized by dropping the currency symbol and converting to `float`.
- `rating`: text labels like `Three` are converted to integer values from 1 to 5.
- `in_stock`: the raw availability text is parsed into a boolean.
- For any inconsistent or missing numeric value, median imputation is applied to keep the pipeline stable without crashing on messy rows.

## SQLite schema

The database uses a normalized two-table design:

- `categories(category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE)`
- `books(book_id INTEGER PRIMARY KEY, title TEXT, price_gbp REAL, price_inr REAL, rating INTEGER, in_stock INTEGER, category_id INTEGER REFERENCES categories(category_id))`

## Run

```bash
cd data_pipeline
python build_pipeline.py
```

## Query validation

The script writes at least five SQL queries and logs their output, and then reproduces the join using `pd.merge(...)` to demonstrate equivalence with the SQL result.
