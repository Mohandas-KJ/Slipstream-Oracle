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
from sklearn.model_selection import cross_val_score  # spl-cl: kept for future use
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
RANDOM_STATE = 42
# spl-cl: ROLLING SPLIT — no fixed test year.
# spl-cl: train = everything except the latest round in the dataset
# spl-cl: test  = latest round only (the most recently completed race)
# spl-cl: This mirrors real deployment exactly: you always train on all
# spl-cl: completed races and the next one is what you predict.
# spl-cl: When oracle_v2 spans 2022-2026, the model trains on 4+ years
# spl-cl: of history and tests on Round 13 (Monza) — truly unseen.

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
    # spl-cl: rolling split — finds the latest (Year, RoundNumber) in the dataset
    # spl-cl: and uses it as test. Everything before = train.
    # spl-cl: Works correctly whether oracle_v2 has 1 year or 5 years of data.
    # spl-cl: Example with full data: train=2022R1→2026R12, test=2026R13 (Monza)
    # spl-cl: No hardcoding needed — updates automatically every race weekend.

    latest_year  = int(df["Year"].max())
    latest_round = int(df[df["Year"] == latest_year]["RoundNumber"].max())

    test_mask  = (df["Year"] == latest_year) & (df["RoundNumber"] == latest_round)
    train_mask = ~test_mask

    train = df[train_mask]
    test  = df[test_mask]

    test_race = test["Race"].iloc[0] if not test.empty else "?"

    print(f"  Latest round detected : Year {latest_year}  Round {latest_round}  ({test_race})")
    print(f"  Train : {len(train)} rows  (everything before R{latest_round})")
    print(f"  Test  : {len(test)} rows   (R{latest_round} — held out as unseen)\n")

    return train[FEATURES], test[FEATURES], train[TARGET], test[TARGET]

# ============================================================
# 3. TRAIN
# ============================================================

def train(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Fit and return a RandomForestRegressor."""
    # spl-cl: min_samples_leaf scales with data size — hardcoded 2 was tuned for
    # spl-cl: 165 rows. With ~1466 train rows it creates overfit micro-leaves.
    # spl-cl: 1% of training rows is the standard rule of thumb for RF leaf size.
    min_leaf = max(2, len(X_train) // 100)  # spl-cl: ~1% of train rows, min 2
    print(f"  min_samples_leaf : {min_leaf}  (1% of {len(X_train)} train rows)")

    model = RandomForestRegressor(
        n_estimators=300,        # spl-cl: 200→300: more trees = more stable with larger data
        max_depth=None,
        min_samples_leaf=min_leaf,  # spl-cl: dynamic, was hardcoded 2
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
    row("Train (all prev rounds)", len(X_train))
    row("Test  (latest round)",    len(X_test))
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