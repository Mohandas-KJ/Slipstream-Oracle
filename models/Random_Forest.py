"""
Slipstream Oracle — Random Forest Model
========================================
Input  : outputs/oracle_v2.csv
Output : outputs/random_forest_predictions.csv
         models/random_forest.pkl
"""

import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# ============================================================
# CONFIG
# ============================================================

INPUT_CSV   = Path("outputs/oracle_v2.csv")
OUTPUT_CSV  = Path("outputs/random_forest_predictions.csv")
MODEL_PATH  = Path("models/random_forest.pkl")

FEATURES = [
    "QualiPosition",
    "GridPosition",
    "AvgFinishLast3",
    "AvgFinishLast5",
    "AvgGridLast3",
    "AvgGridLast5",
    "AvgPointsLast3",
    "AvgPointsLast5",
]

TARGET       = "TargetFinish"
TEST_SIZE    = 0.20
RANDOM_STATE = 42

# ============================================================
# 1. LOAD
# ============================================================

def load_data(path: Path) -> pd.DataFrame:
    """Load oracle_v2 CSV and return a clean DataFrame."""
    df = pd.read_csv(path)

    # Convert features and target to numeric; non-numeric values (R, W, D …) → NaN
    for col in FEATURES + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)
    dropped = before - len(df)

    print(f"  Loaded   : {before} rows from '{path}'")
    if dropped:
        print(f"  Dropped  : {dropped} rows with NaN in features / target")
    print(f"  Remaining: {len(df)} rows\n")

    return df

# ============================================================
# 2. SPLIT
# ============================================================

def split(df: pd.DataFrame):
    """Return X_train, X_test, y_train, y_test."""
    X = df[FEATURES]
    y = df[TARGET]
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)

# ============================================================
# 3. TRAIN
# ============================================================

def train(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Fit and return a RandomForestRegressor."""
    model = RandomForestRegressor(
        n_estimators=200,       # 200 trees — good balance of accuracy vs speed
        max_depth=None,         # let trees grow fully; forest handles overfitting
        min_samples_leaf=2,     # avoids single-row leaves
        random_state=RANDOM_STATE,
        n_jobs=-1,              # use all CPU cores
    )
    model.fit(X_train, y_train)
    return model

# ============================================================
# 4. EVALUATE
# ============================================================

def evaluate(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Predict on test set and return metrics dict."""
    y_pred = model.predict(X_test)

    metrics = {
        "mae":  round(mean_absolute_error(y_test, y_pred), 4),
        "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
        "r2":   round(r2_score(y_test, y_pred), 4),
        "y_pred": y_pred,
    }
    return metrics

# ============================================================
# 5. FEATURE IMPORTANCE
# ============================================================

def feature_importance_table(model: RandomForestRegressor) -> pd.DataFrame:
    """Return a DataFrame of features sorted by importance descending."""
    fi = pd.DataFrame({
        "Feature":    FEATURES,
        "Importance": model.feature_importances_,
    }).sort_values("Importance", ascending=False).reset_index(drop=True)

    fi["Importance"] = fi["Importance"].round(4)
    fi.index += 1           # rank starts at 1
    return fi

# ============================================================
# 6. SAVE
# ============================================================

def save_predictions(df: pd.DataFrame, X_test: pd.DataFrame, y_test: pd.Series, y_pred: np.ndarray) -> None:
    """Save test-set predictions alongside metadata columns."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    meta_cols = ["Year", "RoundNumber", "Race", "Driver", "Team"]
    available = [c for c in meta_cols if c in df.columns]

    result = df.loc[X_test.index, available].copy()
    result["ActualFinish"]    = y_test.values
    result["PredictedFinish"] = y_pred.round(2)
    result["Error"]           = (result["PredictedFinish"] - result["ActualFinish"]).round(2)

    result.to_csv(OUTPUT_CSV, index=False)
    print(f"  Predictions saved → {OUTPUT_CSV}")


def save_model(model: RandomForestRegressor) -> None:
    """Pickle the trained model."""
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"  Model saved       → {MODEL_PATH}")

# ============================================================
# 7. SUMMARY PRINTER
# ============================================================

def print_summary(
    X_train: pd.DataFrame,
    X_test:  pd.DataFrame,
    metrics: dict,
    fi:      pd.DataFrame,
) -> None:

    W = 44      # table width

    def rule(char="─"): print("  " + char * W)
    def row(label, value): print(f"  │  {label:<20}{str(value):>20}  │")

    print()
    print("  ╔" + "═" * W + "╗")
    print("  ║" + " SLIPSTREAM ORACLE — RANDOM FOREST ".center(W) + "║")
    print("  ╠" + "═" * W + "╣")
    row("Training samples",  len(X_train))
    row("Testing  samples",  len(X_test))
    rule()
    row("MAE",  metrics["mae"])
    row("RMSE", metrics["rmse"])
    row("R²",   metrics["r2"])
    print("  ╠" + "═" * W + "╣")
    print("  ║" + " FEATURE IMPORTANCE ".center(W) + "║")
    print("  ╠" + "═" * W + "╣")
    print(f"  │  {'#':<4}{'Feature':<22}{'Importance':>14}  │")
    rule()
    for rank, r in fi.iterrows():
        bar = "█" * int(r["Importance"] * 80)      # visual bar scaled to width
        print(f"  │  {rank:<4}{r['Feature']:<22}{r['Importance']:>14.4f}  │")
        print(f"  │      {bar:<38}  │")
    print("  ╚" + "═" * W + "╝")
    print()

# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("\n── Loading data ─────────────────────────────────────")
    df = load_data(INPUT_CSV)

    print("── Splitting (80 / 20) ──────────────────────────────")
    X_train, X_test, y_train, y_test = split(df)
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}\n")

    print("── Training RandomForestRegressor ───────────────────")
    model = train(X_train, y_train)
    print("  Done.\n")

    print("── Evaluating ───────────────────────────────────────")
    metrics = evaluate(model, X_test, y_test)

    fi = feature_importance_table(model)

    print("── Saving ───────────────────────────────────────────")
    save_predictions(df, X_test, y_test, metrics["y_pred"])
    save_model(model)

    print_summary(X_train, X_test, metrics, fi)


if __name__ == "__main__":
    main()