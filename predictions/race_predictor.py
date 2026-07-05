"""
Slipstream Oracle — Austria 2026 GP Predictor
==============================================
Loads austria_2026_predict.csv (built by build_austria_dataset.py),
encodes it using the saved LabelEncoders from the pkl,
and predicts TargetFinish for every driver.

Run AFTER filling in QualiPosition & GridPosition.

Usage
-----
    python predict_austria.py
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from Generals import streamlib

# ============================================================
# CONFIG
# ============================================================

INPUT_CSV  = "outputs/austria.csv"
OUTPUT_CSV = Path("predictions/2026")
MODEL_PKL  = "models/random_forest.pkl"

def create_dir():
    """
    1. Check the dir exists
    2. If not create a new one
    """

    # Save Path
    Save_Path = OUTPUT_CSV / streamlib.get_eventname()

# ============================================================
# LOAD
# ============================================================

def load_bundle(pkl_path: str) -> tuple:
    with open(pkl_path, "rb") as f:
        bundle = pickle.load(f)
    return bundle["model"], bundle["encoders"], bundle["features"]


def load_input(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)

# ============================================================
# ENCODE
# ============================================================

def encode(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    """
    Label-encode categorical columns using the fitted encoders from training.
    Unknown labels (new drivers/teams/races not seen during training) are
    handled gracefully — they get -1 and a warning instead of crashing.
    """
    df = df.copy()

    for col, le in encoders.items():
        known = set(le.classes_)
        unseen = set(df[col].astype(str).unique()) - known

        if unseen:
            print(f"  ⚠  Unseen {col} values: {unseen}")
            print(f"     These rows will be encoded as -1 (unknown).")
            # map known → encoded int, unknown → -1
            df[col] = df[col].astype(str).apply(
                lambda x: le.transform([x])[0] if x in known else -1
            )
        else:
            df[col] = le.transform(df[col].astype(str))

    return df

# ============================================================
# PREDICT
# ============================================================

def predict(df_raw: pd.DataFrame, model, encoders: dict, features: list) -> pd.DataFrame:

    df = encode(df_raw, encoders)

    # Rows that have NaN in features can't be predicted
    X = df[features]
    missing_mask = X.isnull().any(axis=1)

    if missing_mask.any():
        print(f"\n  ⚠  {missing_mask.sum()} rows have NaN features and will be skipped:")
        print(f"     {df_raw.loc[missing_mask, 'Driver'].tolist()}")
        print(f"     → Fill QualiPosition & GridPosition before running.\n")

    X_valid = X[~missing_mask]

    result = df_raw.copy()
    result["PredictedFinish"] = np.nan

    if X_valid.empty:
        print("  ✗  No rows with complete features — nothing to predict.")
        print("     Fill QualiPosition & GridPosition in the CSV first.\n")
        return result

    preds = model.predict(X_valid).round(2)
    result.loc[~missing_mask, "PredictedFinish"] = preds

    # Sort by predicted finish ascending
    result = result.sort_values("PredictedFinish").reset_index(drop=True)
    result.index += 1   # rank from 1

    return result

# ============================================================
# PRINT + SAVE
# ============================================================

def print_podium(result: pd.DataFrame) -> None:

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║        AUSTRIA 2026 — PREDICTED RACE RESULTS        ║")
    print("  ╠══════════════════════════════════════════════════════╣")
    print(f"  │  {'P':<4} {'Driver':<8} {'Team':<20} {'Predicted':>10}  │")
    print("  ├──────────────────────────────────────────────────────┤")

    for pos, row in result.iterrows():
        if pd.isna(row["PredictedFinish"]):
            continue
        medal = medals.get(pos, "  ")
        print(
            f"  │  {str(pos)+'.':<4} {row['Driver']:<8}"
            f" {row['Team']:<20} {row['PredictedFinish']:>8.2f}  {medal}  │"
        )

    print("  ╚══════════════════════════════════════════════════════╝")
    print()


def save(result: pd.DataFrame) -> None:
    result.to_csv(OUTPUT_CSV, index_label="PredictedPosition")
    print(f"  ✓  Saved → {OUTPUT_CSV}")


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("\n── Loading model & encoders ──────────────────────────")
    model, encoders, features = load_bundle(MODEL_PKL)
    print(f"  Features : {features}")

    print("\n── Loading Austria dataset ───────────────────────────")
    df_raw = load_input(INPUT_CSV)
    print(f"  Drivers  : {len(df_raw)}")

    quali_filled = df_raw["QualiPosition"].notna().sum()
    grid_filled  = df_raw["GridPosition"].notna().sum()
    print(f"  QualiPosition filled : {quali_filled}/{len(df_raw)}")
    print(f"  GridPosition  filled : {grid_filled}/{len(df_raw)}")

    print("\n── Predicting ────────────────────────────────────────")
    result = predict(df_raw, model, encoders, features)

    print_podium(result)

    print("── Saving ────────────────────────────────────────────")
    save(result)


if __name__ == "__main__":
    main()