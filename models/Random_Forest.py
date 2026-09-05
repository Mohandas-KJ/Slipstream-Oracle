"""
Slipstream Oracle — Random Forest Model
========================================
Input  : outputs/oracle_v2.csv
Output : outputs/random_forest_predictions.csv
         models/random_forest.pkl

Encoding strategy
-----------------
Team, Race, Driver  → LabelEncoder  (low cardinality categoricals)
Year, RoundNumber   → used as-is    (already ordinal integers)
All numeric columns → used as-is
"""

import pickle
from pathlib import Path
from sliplog import logs

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# ============================================================
# CONFIG
# ============================================================

INPUT_CSV   = Path("outputs/oracle_v2.csv")
OUTPUT_CSV  = Path("outputs/random_forest_predictions.csv")
MODEL_PATH  = Path("models/random_forest.pkl")

# Columns to label-encode
CATEGORICAL = ["Race", "Team", "Driver"]

# All features fed to the model (categoricals will be encoded in-place)
FEATURES = [
    "Year",
    "RoundNumber",
    "Race",           # encoded
    "Driver",         # encoded
    "Team",           # encoded
    "QualiPosition",
    "GridPosition",
    "AvgFinishLast3",
    "AvgFinishLast5",
    "AvgGridLast3",
    "AvgGridLast5",
    "AvgPointsLast3",
    "AvgPointsLast5",
    "PositionsGainedLastRace",
    "FinishStdLast5"
]

TARGET       = "TargetFinish"
TEST_SIZE    = 0.20
RANDOM_STATE = 42

# ============================================================
# 1. LOAD & ENCODE
# ============================================================

def load_and_encode(path: Path) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    """
    Load oracle_v2 CSV, label-encode categoricals, cast target to numeric.
    Returns the processed DataFrame and a dict of fitted encoders
    (needed later to decode predictions or encode new inference data).
    """
    df = pd.read_csv(path)

    # ── encode categoricals ──────────────────────────────────
    encoders: dict[str, LabelEncoder] = {}
    for col in CATEGORICAL:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"  Encoded  : {col:<10} → {len(le.classes_)} classes")

    # ── target: DNF/DNS/W codes → NaN ───────────────────────
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")

    # ── drop rows missing in features or target ──────────────
    before = len(df)
    df = df.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)
    dropped = before - len(df)

    print(f"\n  Loaded   : {before} rows from '{path}'")
    if dropped:
        print(f"  Dropped  : {dropped} rows  (NaN in features / non-numeric target)")
    print(f"  Remaining: {len(df)} rows\n")

    return df, encoders

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
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model

# ============================================================
# 4. EVALUATE
# ============================================================

def evaluate(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Predict on test set and return metrics + predictions."""
    y_pred = model.predict(X_test)
    return {
        "mae":    round(mean_absolute_error(y_test, y_pred), 4),
        "rmse":   round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
        "r2":     round(r2_score(y_test, y_pred), 4),
        "y_pred": y_pred,
    }

# ============================================================
# 5. FEATURE IMPORTANCE
# ============================================================

def feature_importance_table(model: RandomForestRegressor) -> pd.DataFrame:
    """Return features sorted by importance descending."""
    fi = pd.DataFrame({
        "Feature":    FEATURES,
        "Importance": model.feature_importances_,
    }).sort_values("Importance", ascending=False).reset_index(drop=True)
    fi["Importance"] = fi["Importance"].round(4)
    fi.index += 1
    return fi

# ============================================================
# 6. SAVE
# ============================================================

def save_predictions(
    df:     pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    y_pred: np.ndarray,
    encoders: dict[str, LabelEncoder],
) -> None:
    """Save test-set predictions. Decode label-encoded columns back to strings."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    result = df.loc[X_test.index, ["Year", "RoundNumber"] + CATEGORICAL].copy()

    # decode back to readable strings
    for col, le in encoders.items():
        result[col] = le.inverse_transform(result[col].astype(int))

    result["ActualFinish"]    = y_test.values
    result["PredictedFinish"] = y_pred.round(2)
    result["Error"]           = (result["PredictedFinish"] - result["ActualFinish"]).round(2)

    result.to_csv(OUTPUT_CSV, index=False)
    print(f"  Predictions saved → {OUTPUT_CSV}")


def save_model(model: RandomForestRegressor, encoders: dict[str, LabelEncoder]) -> None:
    """Pickle model + encoders together so inference is self-contained."""
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    bundle = {"model": model, "encoders": encoders, "features": FEATURES}
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"  Model saved       → {MODEL_PATH}")

# ============================================================
# 7. SUMMARY PRINTER
# ============================================================

def print_summary(X_train, X_test, metrics, fi) -> None:

    W = 48

    def rule():  print("  ├" + "─" * W + "┤")
    def row(label, value): print(f"  │  {label:<22}{str(value):>22}  │")

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
    print(f"  │  {'#':<4}{'Feature':<24}{'Importance':>18}  │")
    rule()
    max_imp = fi["Importance"].max()
    for rank, r in fi.iterrows():
        bar_len = int((r["Importance"] / max_imp) * 28) if max_imp > 0 else 0
        bar = "█" * bar_len
        tag = " ★" if r["Importance"] == max_imp else ("  " if r["Importance"] > 0.01 else " ·")
        print(f"  │  {rank:<4}{r['Feature']:<18}{tag}  {r['Importance']:>6.4f}  {bar:<28}│")
    print("  ╚" + "═" * W + "╝")
    print()

# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("\n── Loading & Encoding ───────────────────────────────")
    df, encoders = load_and_encode(INPUT_CSV)

    print("── Splitting 80 / 20 ────────────────────────────────")
    X_train, X_test, y_train, y_test = split(df)
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}\n")

    print("── Training RandomForestRegressor ───────────────────")
    model = train(X_train, y_train)
    print("  Done.\n")

    print("── Evaluating ───────────────────────────────────────")
    metrics = evaluate(model, X_test, y_test)
    fi = feature_importance_table(model)

    print("── Saving ───────────────────────────────────────────")
    save_predictions(df, X_test, y_test, metrics["y_pred"], encoders)
    save_model(model, encoders)

    print_summary(X_train, X_test, metrics, fi)
    logs.write("Trained Random Forest model on new datas")
    


if __name__ == "__main__":
    main()