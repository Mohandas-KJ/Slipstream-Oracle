"""
Slipstream Oracle — Austria 2026 GP Prediction Dataset Builder
==============================================================
Reads oracle_v1.csv, computes rolling averages (last 3 & last 5 races)
from the 7 completed 2026 rounds, and writes a ready-to-predict CSV
for the Austrian Grand Prix (Round 8).

QualiPosition and GridPosition are left NaN — fill them in once
qualifying results are known, then run predict_austria.py.

Usage
-----
    python build_austria_dataset.py
"""

import numpy as np
import pandas as pd
import json

# ============================================================
# CONFIG
# ============================================================

V1_CSV      = "outputs/oracle_v1.csv"
OUTPUT_CSV  = "outputs/austria_2026_predict.csv"
COMPLETED_TAB = "catalog/2026/completed.json" # Hardcoded Year for now
ROUND_MAP = "catalog/2026/Schedule.csv"

YEAR        = 2026

CATALOG_COMP = f"catalog/{YEAR}/completed.json"

# Read Schedule
R_Schedule = pd.read_csv(ROUND_MAP)


with open(COMPLETED_TAB) as f:
    ROUND_MAP_2026 = json.load(f)

"""
# Map every completed 2026 race → round number
ROUND_MAP_2026 = {
    "Australian_Grand_Prix": 1,
    "Chinese_Grand_Prix":    2,
    "Japanese_Grand_Prix":   3,
    "Miami_Grand_Prix":      4,
    "Canadian_Grand_Prix":   5,
    "Monaco_Grand_Prix":     6,
    "Barcelona_Grand_Prix":  7,
}
"""
ROUND       = ROUND_MAP_2026[max(ROUND_MAP_2026,key=ROUND_MAP_2026.get)] + 1
RACE_NAME   = R_Schedule[R_Schedule["RoundNumber"] == ROUND]["EventName"].iloc[0]


# ── 2 extra drivers for Austria (reserve / new entries) ─────
# Fill in their real team once confirmed.
# QualiPosition / GridPosition will be filled before prediction.
EXTRA_DRIVERS = [
    # {"Driver": "XXX", "Team": "Some Team"},
    # {"Driver": "YYY", "Team": "Some Team"},
]

# ============================================================
# HELPERS
# ============================================================

def rolling_avgs(series: pd.Series, n: int) -> float:
    """Mean of last N numeric values; NaN if no data."""
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return np.nan
    return round(vals.tail(n).mean(), 2)

# ============================================================
# BUILD
# ============================================================

def build_austria_dataset() -> pd.DataFrame:

    # ── load v1 and tag round numbers ───────────────────────
    df = pd.read_csv(V1_CSV)
    df_2026 = df[df["Year"] == YEAR].copy()
    df_2026["Round"] = df_2026["Race"].map(ROUND_MAP_2026)
    df_2026 = df_2026.sort_values("Round").reset_index(drop=True)

    # latest team per driver (in case they changed mid-season)
    team_map = df_2026.groupby("Driver")["Team"].last().to_dict()
    drivers  = sorted(df_2026["Driver"].unique())

    print(f"  Base drivers (from v1 2026) : {len(drivers)}")
    print(f"  Extra drivers (Austria only): {len(EXTRA_DRIVERS)}")

    rows = []

    # ── regular drivers ─────────────────────────────────────
    for d in drivers:
        dr = df_2026[df_2026["Driver"] == d].sort_values("Round")

        rows.append({
            "Year":            YEAR,
            "RoundNumber":     ROUND,
            "Race":            RACE_NAME,
            "Driver":          d,
            "Team":            team_map[d],
            # Fill these in once qualifying is done
            "QualiPosition":   np.nan,
            "GridPosition":    np.nan,
            # Rolling averages — computed from all 7 prior races
            "AvgFinishLast3":  rolling_avgs(dr["TargetFinish"], 3),
            "AvgFinishLast5":  rolling_avgs(dr["TargetFinish"], 5),
            "AvgGridLast3":    rolling_avgs(dr["GridPosition"],  3),
            "AvgGridLast5":    rolling_avgs(dr["GridPosition"],  5),
            "AvgPointsLast3":  rolling_avgs(dr["Points"],        3),
            "AvgPointsLast5":  rolling_avgs(dr["Points"],        5),
            # Target is unknown — model will predict this
            "TargetFinish":    np.nan,
        })

    # ── extra / reserve drivers ─────────────────────────────
    for extra in EXTRA_DRIVERS:
        rows.append({
            "Year":            YEAR,
            "RoundNumber":     ROUND,
            "Race":            RACE_NAME,
            "Driver":          extra["Driver"],
            "Team":            extra["Team"],
            "QualiPosition":   np.nan,
            "GridPosition":    np.nan,
            # No history → all NaN; model will use NaN (fill or impute before predict)
            "AvgFinishLast3":  np.nan,
            "AvgFinishLast5":  np.nan,
            "AvgGridLast3":    np.nan,
            "AvgGridLast5":    np.nan,
            "AvgPointsLast3":  np.nan,
            "AvgPointsLast5":  np.nan,
            "TargetFinish":    np.nan,
        })

    df_out = pd.DataFrame(rows)

    df_out.to_csv(OUTPUT_CSV, index=False)

    # ── print preview ────────────────────────────────────────
    print(f"\n  {'Driver':<8} {'Team':<18} {'AvgF3':>6} {'AvgF5':>6} {'AvgG3':>6} {'AvgG5':>6} {'AvgP3':>6} {'AvgP5':>6}")
    print("  " + "─" * 72)
    for _, r in df_out.iterrows():
        print(
            f"  {r['Driver']:<8} {r['Team']:<18}"
            f" {r['AvgFinishLast3']:>6}"
            f" {r['AvgFinishLast5']:>6}"
            f" {r['AvgGridLast3']:>6}"
            f" {r['AvgGridLast5']:>6}"
            f" {r['AvgPointsLast3']:>6}"
            f" {r['AvgPointsLast5']:>6}"
        )
    print()
    print(f"  ✓  {len(df_out)} drivers  →  {OUTPUT_CSV}")
    print()
    print("  Next step:")
    print("    1. Fill in QualiPosition + GridPosition once qualifying is done")
    print("    2. Add any extra/reserve drivers to EXTRA_DRIVERS in this script")

    return df_out


if __name__ == "__main__":
    print("\n── Building Austria 2026 Prediction Dataset ─────────")
    build_austria_dataset()