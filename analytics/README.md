# Analytics Module

This module follows one coherent story: load Titanic once, save an offline fallback CSV, clean it defensively, profile it, and then move into a modeling pipeline.

## EDA and cleaning notes

- Missing-value thresholds are applied per column using the rule: under 5% -> drop rows; 5% to 30% -> impute; above 30% -> decide whether to drop or encode as a separate category.
- The saved dataset is `analytics/titanic.csv` and is the offline fallback for grading.
- The modeling stage uses a train-only preprocessing pipeline so the test fold never leaks information.

## Required outputs

The notebook/script reports:

- df.info(), df.describe(), and df.shape
- percentage missingness table
- age and fare histograms and box plots with IQR-based outlier counts
- survival-rate breakdowns by sex, passenger class, and sex + class
- correlation matrix heatmap on the six specified columns
- at least four multivariate charts with written interpretation
- standardization sanity check for age and fare
- model comparison table and final deployment recommendation

## Run

```bash
cd analytics
python titanic_pipeline.py
```
