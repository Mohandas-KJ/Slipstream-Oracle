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

import os  # spl-cl: needed to read SLIP_DRIVER_CHANGES env var from main.py
import numpy as np
import pandas as pd
import json
from pathlib import Path
from sliplog import logs

# ============================================================
# CONFIG
# ============================================================

V1_CSV      = "outputs/oracle_v1.csv"
OUTPUT_CSV  = Path("outputs")
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

Save_Path = OUTPUT_CSV / f"{YEAR}_{R_Schedule[R_Schedule['RoundNumber'] == ROUND]['EventName'].iloc[0]}"

if not Save_Path.exists():
    print("Directory not Found")
    Save_Path.mkdir(parents=True,exist_ok=True)
    print("Directory created!")


# ── 2 extra drivers for Austria (reserve / new entries) ─────
# Fill in their real team once confirmed.
# QualiPosition / GridPosition will be filled before prediction.
EXTRA_DRIVERS = [
    {"Driver": "LAW", "Team": "Red Bull Racing"},
    {"Driver": "TSU", "Team": "Racing Bulls"},
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

def rolling_std(series: pd.Series, n: int) -> float:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return 0
    return round(vals.tail(n).std(), 2)

def poslast(df: pd.DataFrame) -> float:

    last = df.tail(1)
    
    if last.empty:
        return 0

    grid = pd.to_numeric(last["GridPosition"].iloc[0],errors="coerce")
    finish = pd.to_numeric(last["TargetFinish"].iloc[0],errors="coerce")

    if pd.isna(grid) or pd.isna(finish):
        return 0

    return round(grid - finish,2)

# spl-cl: handle_driver_changes — processes runtime lineup changes passed via env var
# spl-cl: reads full oracle_v1 for career history so reserve drivers get real avgs not NaN
def handle_driver_changes(df_all: pd.DataFrame, rows: list, changes: dict) -> list:
    """
    Apply driver lineup changes to the rows list in-place.

    Args:
        df_all   : full oracle_v1 dataframe (all years) for career history lookup
        rows     : list of row dicts already built for base drivers
        changes  : {"add": [{"Driver":..,"Team":..}], "remove": ["CODE",..]}

    Returns:
        Updated rows list with removals applied and additions appended.
    """

    # spl-cl: REMOVE — drop rows for absent/replaced drivers
    remove_set = set(changes.get("remove", []))
    if remove_set:
        before = len(rows)
        rows = [r for r in rows if r["Driver"] not in remove_set]
        print(f"  ✗  Removed {before - len(rows)} driver(s): {remove_set}")

    # spl-cl: ADD — build proper feature rows for incoming drivers using career history
    for entry in changes.get("add", []):
        code = entry["Driver"]
        team = entry["Team"]

        # spl-cl: check if driver already exists in rows (duplicate guard)
        if any(r["Driver"] == code for r in rows):
            # spl-cl: driver already present (e.g. LAW in 2026 base) — just update team
            for r in rows:
                if r["Driver"] == code:
                    r["Team"] = team
                    print(f"  ↻  {code} already in lineup — team updated to '{team}'")
            continue

        # spl-cl: search career history across ALL years in oracle_v1
        career = df_all[df_all["Driver"] == code].copy()

        if career.empty:
            print(f"  ⚠  {code}: no career history found in oracle_v1 — avgs will be NaN")
            avg_f3 = avg_f5 = avg_g3 = avg_g5 = avg_p3 = avg_p5 = std_f5 = pos_gained = np.nan
        else:
            # spl-cl: sort by year so tail() gives most recent N races correctly
            career = career.sort_values(["Year"]).reset_index(drop=True)
            avg_f3 = rolling_avgs(career["TargetFinish"], 3)
            avg_f5 = rolling_avgs(career["TargetFinish"], 5)
            avg_g3 = rolling_avgs(career["GridPosition"],  3)
            avg_g5 = rolling_avgs(career["GridPosition"],  5)
            avg_p3 = rolling_avgs(career["Points"],        3)
            avg_p5 = rolling_avgs(career["Points"],        5)
            std_f5 = rolling_std(career["TargetFinish"], 5)
            pos_gained = poslast(career)
            print(f"  ★  {code}: history found ({len(career)} rows across {sorted(career['Year'].unique())})")
            print(f"       AvgF3={avg_f3}  AvgF5={avg_f5}  AvgG3={avg_g3}  AvgG5={avg_g5}")

        rows.append({
            "Year":           YEAR,
            "RoundNumber":    ROUND,
            "Race":           RACE_NAME,
            "Driver":         code,
            "Team":           team,
            "QualiPosition":  np.nan,
            "GridPosition":   np.nan,
            "AvgFinishLast3": avg_f3,
            "AvgFinishLast5": avg_f5,
            "AvgGridLast3":   avg_g3,
            "AvgGridLast5":   avg_g5,
            "AvgPointsLast3": avg_p3,
            "AvgPointsLast5": avg_p5,
            "PositionsGainedLastRace":  pos_gained,
            "FinishStdLast5": std_f5,
            "TargetFinish":   np.nan,
        })

    return rows
# spl-cl: end handle_driver_changes

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
            "PositionsGainedLastRace":  poslast(dr),
            "FinishStdLast5": rolling_std(dr["TargetFinish"],5),
            # Target is unknown — model will predict this
            "TargetFinish":    np.nan,
        })

    # ── extra / reserve drivers (static list defined at top) ─
    # spl-cl: EXTRA_DRIVERS handled via handle_driver_changes below — keeping block for
    # spl-cl: backward compat when script is run standalone without main.py env injection
    static_changes = {"add": EXTRA_DRIVERS, "remove": []}
    rows = handle_driver_changes(df, rows, static_changes)

    # spl-cl: runtime driver changes — injected by main.py via SLIP_DRIVER_CHANGES env var
    # spl-cl: overrides/extends the static EXTRA_DRIVERS list above
    _env_changes = os.environ.get("SLIP_DRIVER_CHANGES")
    if _env_changes:
        try:
            runtime_changes = json.loads(_env_changes)
            if runtime_changes.get("add") or runtime_changes.get("remove"):
                print("\n  Applying runtime driver changes from main.py...")
                rows = handle_driver_changes(df, rows, runtime_changes)
        except json.JSONDecodeError:
            print("  ⚠  Could not parse SLIP_DRIVER_CHANGES env var — skipping runtime changes")
    # spl-cl: end runtime driver changes block

    df_out = pd.DataFrame(rows)

    df_out.to_csv(Save_Path / "Prediction.csv", index=False)

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
    print(f"  ✓  {len(df_out)} drivers  →  {Save_Path}")
    print()
    print("  Next step:")
    print("    1. Fill in QualiPosition + GridPosition once qualifying is done")
    print("    2. Add any extra/reserve drivers to EXTRA_DRIVERS in this script")

    return df_out


if __name__ == "__main__":
    print("\n── Building Austria 2026 Prediction Dataset ─────────")
    build_austria_dataset()
    logs.write("Generated Training Dataset")