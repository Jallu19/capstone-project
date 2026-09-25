# Zepto Capstone Project

This single repository contains three connected modules:

1. Data pipeline in `data_pipeline/` for scraping, cleaning, conversion, and SQLite loading.
2. Analytics pipeline in `analytics/` for profiling, EDA, and predictive modeling on the Titanic dataset.
3. Support assistant in `support_assistant/` for a grounded policy Q&A service built on ChromaDB and LangGraph.

## Setup

Use the consolidated requirements file at the repository root:

```bash
python -m pip install -r requirements.txt
```

## Run each module

### Data pipeline

```bash
cd data_pipeline
python build_pipeline.py
```

### Analytics pipeline

```bash
cd analytics
python titanic_pipeline.py
```

### Support assistant

```bash
cd support_assistant
python main.py
```

Then send a request to the API:

```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"query":"What is Zepto's delivery policy?"}'
```

## Design summary

### Data pipeline

The pipeline scrapes book listings from `books.toscrape.com`, cleans the fields, converts `price_gbp` to `price_inr` using the required fixed rate `1 GBP = 105.50 INR`, stores the normalized data in SQLite, and validates the results with SQL and pandas queries.

### Analytics pipeline

The analytics flow uses a single load of the Titanic dataset, saves an offline fallback CSV, applies threshold-based missing-value handling, explores the distributions and correlations, then trains a full sklearn modeling pipeline with train-only preprocessing and a saved end-to-end artifact.

### Support assistant

The support assistant stores Zepto policy text in ChromaDB, embeds the corpus with `all-MiniLM-L6-v2`, retrieves the most relevant chunks for an input question, and routes through LangGraph with a deterministic offline mock mode by default. This ensures the service works without API keys or bell-curve network dependence.

## File structure

```text
capstone-project/
├── README.md
├── requirements.txt
├── data_pipeline/
│   ├── README.md
│   ├── build_pipeline.py
│   ├── books_raw.csv
│   ├── books.db
│   ├── queries.sql
│   └── sql_results.md
├── analytics/
│   ├── README.md
│   ├── titanic_pipeline.py
│   ├── titanic.csv
│   ├── best_model_pipeline.joblib
│   └── model_report.md
├── support_assistant/
│   ├── README.md
│   ├── main.py
│   ├── Dockerfile
│   ├── docs/
│   └── chroma_store/
├── sample_data/
├── final_Capstone_project.ipynb
└── .git/
```
