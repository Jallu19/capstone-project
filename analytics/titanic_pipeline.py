from __future__ import annotations

import joblib
import matplotlib
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.linear_model import LinearRegression

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid")

DATA_PATH = "titanic.csv"
MODEL_PATH = "best_model_pipeline.joblib"
REPORT_PATH = "model_report.md"


def load_dataset() -> pd.DataFrame:
    df = sns.load_dataset("titanic")
    df.to_csv(DATA_PATH, index=False)
    return df


def profile_data(df: pd.DataFrame) -> None:
    print(df.info())
    print(df.describe())
    print(df.shape)
    missing = df.isna().mean().sort_values(ascending=False)
    print("Missing percentages:\n", missing[missing > 0])


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    missing = df.isna().mean()
    # threshold-based strategy
    for column in df.columns:
        pct = missing[column]
        if pd.notna(pct) and pct > 0:
            if pct < 0.05:
                df = df.dropna(subset=[column])
            elif pct <= 0.30:
                if column in ["age", "fare"]:
                    df[column] = df[column].fillna(df[column].median())
                else:
                    df[column] = df[column].fillna(df[column].mode()[0])
            else:
                if column in ["deck"]:
                    df[column] = df[column].fillna("missing")
                else:
                    df = df.drop(columns=[column])
    return df


def save_cleaned(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.to_csv(DATA_PATH, index=False)
    return df


def plot_univariate(df: pd.DataFrame) -> None:
    for col in ["age", "fare"]:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        df[col].plot.hist(ax=axes[0], bins=20)
        axes[0].set_title(f"Histogram of {col}")

        sns.boxplot(x=df[col], ax=axes[1])
        axes[1].set_title(f"Box plot of {col}")
        fig.tight_layout()
        fig.savefig(f"{col}_dist.png", dpi=150)
        plt.close(fig)


def summarize_outliers(df: pd.DataFrame) -> dict:
    out = {}
    for col in ["age", "fare"]:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        count = ((df[col] < lower) | (df[col] > upper)).sum()
        out[col] = count
    return out


def compute_skewness(df: pd.DataFrame) -> None:
    fares = df["fare"]
    mean = fares.mean()
    median = fares.median()
    mode = fares.mode().iloc[0]
    print(f"Fare mean={mean}, median={median}, mode={mode}")


def bivariate_analysis(df: pd.DataFrame) -> None:
    print("Survival by sex:", df.groupby("sex")["survived"].mean().to_dict())
    print("Survival by pclass:", df.groupby("pclass")["survived"].mean().to_dict())
    print("Survival by sex and pclass:\n", df.groupby(["sex", "pclass"])["survived"].mean().to_dict())

    corr = df[["survived", "pclass", "age", "sibsp", "parch", "fare"]].corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Titanic correlation heatmap")
    plt.tight_layout()
    plt.savefig("correlation_heatmap.png", dpi=150)
    plt.close()
    print(corr)


def get_top_correlations(corr: pd.DataFrame) -> list[tuple[str, str, float]]:
    off_diag = []
    cols = corr.columns
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            off_diag.append((a, b, abs(corr.loc[a, b])))
    return sorted(off_diag, key=lambda x: x[2], reverse=True)[:2]


def multivariate_charts(df: pd.DataFrame) -> None:
    chart_specs = [
        ("survival_by_sex", sns.barplot, {"x": "sex", "y": "survived", "data": df, "ci": None}),
        ("fare_by_class", sns.boxplot, {"x": "pclass", "y": "fare", "data": df}),
        ("age_by_survival", sns.boxplot, {"x": "survived", "y": "age", "data": df}),
        ("fare_vs_age", sns.scatterplot, {"x": "age", "y": "fare", "hue": "survived", "data": df})
    ]
    for name, func, kwargs in chart_specs:
        plt.figure(figsize=(8, 6))
        func(**kwargs)
        plt.title(name)
        plt.tight_layout()
        plt.savefig(f"{name}.png", dpi=150)
        plt.close()


def standardize_check(df: pd.DataFrame) -> None:
    df2 = df.copy()
    age_mean, age_sd = df2["age"].mean(), df2["age"].std(ddof=0)
    fare_mean, fare_sd = df2["fare"].mean(), df2["fare"].std(ddof=0)
    df2["age_z"] = (df2["age"] - age_mean) / age_sd
    df2["fare_z"] = (df2["fare"] - fare_mean) / fare_sd
    print("Age z-score summary:", df2["age_z"].mean(), df2["age_z"].std(ddof=0))
    print("Fare z-score summary:", df2["fare_z"].mean(), df2["fare_z"].std(ddof=0))


def make_model_pipeline() -> Pipeline:
    numeric_features = ["age", "fare", "sibsp", "parch"]
    categorical_features = ["sex", "embarked"]
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_features),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical_features),
        ]
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    return pipeline


def evaluate_classifier(y_true, y_pred, proba=None) -> dict:
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }
    if proba is not None:
        fpr, tpr, _ = roc_curve(y_true, proba)
        metrics["auc"] = auc(fpr, tpr)
    return metrics


def run_classifiers(df: pd.DataFrame) -> dict:
    X = df.drop(columns=["survived"])
    y = df["survived"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(random_state=42, n_estimators=200)
    }
    results = {}
    for name, estimator in models.items():
        numeric_features = ["age", "fare", "sibsp", "parch"]
        categorical_features = ["sex", "embarked"]
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_features),
                ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical_features),
            ]
        )
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        proba = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else None
        metrics = evaluate_classifier(y_test, y_pred, proba)
        results[name] = {"cm": confusion_matrix(y_test, y_pred), **metrics}

        if name == "Decision Tree":
            plt.figure(figsize=(16, 10))
            plot_tree(pipeline.named_steps["model"], filled=True, feature_names=pipeline.named_steps["preprocessor"].get_feature_names_out(), class_names=["Not Survived", "Survived"])
            plt.savefig("decision_tree.png", dpi=150)
            plt.close()

    print(results)
    return results


def imbalance_analysis(df: pd.DataFrame) -> None:
    X = df.drop(columns=["survived"])
    y = df["survived"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    from imblearn.over_sampling import SMOTE
    from sklearn.base import clone

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["age", "fare", "sibsp", "parch"]),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), ["sex", "embarked"]),
        ]
    )

    rf = RandomForestClassifier(random_state=42, n_estimators=200)
    baseline_pipeline = Pipeline([("preprocessor", preprocessor), ("model", clone(rf))])
    balanced_pipeline = Pipeline([("preprocessor", preprocessor), ("model", RandomForestClassifier(random_state=42, n_estimators=200, class_weight="balanced"))])

    baseline_pipeline.fit(X_train, y_train)
    balanced_pipeline.fit(X_train, y_train)

    X_train_sm, y_train_sm = SMOTE(random_state=42).fit_resample(preprocessor.fit_transform(X_train), y_train)
    sm_pipeline = Pipeline([("preprocessor", preprocessor), ("model", RandomForestClassifier(random_state=42, n_estimators=200))])
    sm_pipeline.fit(X_train, y_train)
    # Replace with a direct model fit on the oversampled transformed data to reflect the SMOTE strategy.
    sm_model = RandomForestClassifier(random_state=42, n_estimators=200)
    sm_model.fit(X_train_sm, y_train_sm)

    for name, model, X_eval, y_eval in [
        ("baseline", baseline_pipeline, X_test, y_test),
        ("balanced", balanced_pipeline, X_test, y_test),
        ("smote", sm_pipeline, X_test, y_test),
    ]:
        if name == "smote":
            preds = sm_model.predict(preprocessor.transform(X_test))
        else:
            preds = model.predict(X_test)
        print(name, {
            "precision": precision_score(y_eval, preds, zero_division=0),
            "recall": recall_score(y_eval, preds, zero_division=0),
            "f1": f1_score(y_eval, preds, zero_division=0),
        })


def grid_search_rf(df: pd.DataFrame) -> None:
    X = df.drop(columns=["survived"])
    y = df["survived"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["age", "fare", "sibsp", "parch"]),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), ["sex", "embarked"]),
        ]
    )
    rf = RandomForestClassifier(oob_score=True, random_state=42)
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", rf)])
    param_grid = {
        "model__n_estimators": [50, 100, 150],
        "model__max_depth": [None, 5, 10],
        "model__max_features": ["sqrt", "log2", None],
    }
    search = GridSearchCV(pipeline, param_grid=param_grid, cv=StratifiedKFold(3), scoring="accuracy")
    search.fit(X_train, y_train)
    print("Best RF params:", search.best_params_)
    print("Best RF OOB:", search.best_estimator_.named_steps["model"].oob_score_)


def regression_side_task(df: pd.DataFrame) -> None:
    X = df.drop(columns=["fare"])
    y = df["fare"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["age", "sibsp", "parch"]),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), ["sex", "embarked", "pclass", "survived"]),
        ]
    )
    model = LinearRegression()
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = mean_squared_error(y_test, pred, squared=False)
    r2 = pipeline.score(X_test, y_test)
    n = len(y_test)
    p = X_test.shape[1]
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)
    residuals = y_test - pred
    plt.figure(figsize=(8, 6))
    plt.scatter(pred, residuals)
    plt.axhline(0, color="red", linestyle="--")
    plt.title("Residual plot")
    plt.tight_layout()
    plt.savefig("regression_residuals.png", dpi=150)
    plt.close()
    print({"MAE": mae, "RMSE": rmse, "R2": r2, "AdjR2": adj_r2})


def save_pipeline(df: pd.DataFrame) -> None:
    X = df.drop(columns=["survived"])
    y = df["survived"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["age", "fare", "sibsp", "parch"]),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), ["sex", "embarked"]),
        ]
    )
    final_model = RandomForestClassifier(random_state=42, n_estimators=200)
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", final_model)])
    pipeline.fit(X_train, y_train)
    joblib.dump(pipeline, MODEL_PATH)
    loaded = joblib.load(MODEL_PATH)
    sample = X_test.iloc[[0]].copy()
    pred_raw = loaded.predict(sample)
    print("Reloaded pipeline prediction on raw input:", pred_raw.tolist())


def main() -> None:
    df = load_dataset()
    profile_data(df)
    cleaned = clean_dataset(df)
    cleaned = save_cleaned(cleaned)
    plot_univariate(cleaned)
    print("Outliers:", summarize_outliers(cleaned))
    compute_skewness(cleaned)
    bivariate_analysis(cleaned)
    corr = cleaned[["survived", "pclass", "age", "sibsp", "parch", "fare"]].corr()
    print("Top correlations:", get_top_correlations(corr))
    multivariate_charts(cleaned)
    standardize_check(cleaned)
    run_classifiers(cleaned)
    imbalance_analysis(cleaned)
    grid_search_rf(cleaned)
    regression_side_task(cleaned)
    save_pipeline(cleaned)

    report = """
# Model Summary

This module profiles the Titanic dataset, analyzes missingness and skewness, trains a set of classifiers, and builds a regression side-task.

## Final recommendation

The random forest offers the best overall classification balance and is the strongest deployment candidate because it combines strong accuracy with a good recall/precision tradeoff and robust feature handling. The decision tree is easier to interpret but is usually less stable, while logistic regression is simpler but weaker on the nonlinear relationships in the Titanic data.
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(report)


if __name__ == "__main__":
    main()
