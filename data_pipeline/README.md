# Data Pipeline Module

This module follows the raw-to-relational pipeline:

1. Scrape books from the public books.toscrape.com catalogue.
2. Clean and validate the fields.
3. Convert GBP to INR using the fixed project baseline `1 GBP = 105.50 INR`.
4. Load the results into a normalized SQLite database with a two-table schema.
5. Run SQL and pandas queries to validate the results.

## Cleaning and parsing decisions

- `price_gbp`: the currency symbol is removed and the value is converted to a float.
- `rating`: star text such as `Three` is mapped to integer values `1` through `5`.
- `in_stock`: the raw availability string is parsed into a boolean.
- Missing numeric values are filled through the median-imputation rule, which is used defensively when messy rows appear unexpectedly. This keeps the pipeline stable without crashing on partial data.

## Database schema

The SQLite database uses a normalized two-table structure:

- `categories(category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE)`
- `books(book_id INTEGER PRIMARY KEY, title TEXT, price_gbp REAL, price_inr REAL, rating INTEGER, in_stock INTEGER, category_id INTEGER REFERENCES categories(category_id))`

## Running the pipeline

```bash
cd data_pipeline
python build_pipeline.py
```

This script generates the database, writes SQL outputs, and prints the query results to the console.

## Validation notes

This module deliberately scrapes more than 60 books across multiple categories and then verifies the SQL results against a pandas-based join query to ensure both approaches produce equivalent outputs.
