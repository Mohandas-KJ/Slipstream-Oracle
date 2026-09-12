"""
Slipstream Oracle — Post Qualifying Update
==========================================
Hybrid data architecture:

    FastF1  →  QualiPosition   (pure qualifying result, ~45 min after session)
    Manual  →  GridPosition    (final grid after FIA penalty decisions, Sat morning)

WHY HYBRID:
  FastF1 Q session GridPosition is always empty before the race happens.
  FastF1 R session GridPosition is only populated after the race finishes.
  FIA publishes the official Starting Grid document (PDF/web) on Saturday
  morning before the race — that is the only reliable source for final grid
  positions including all penalties.

WORKFLOW:
  1. Run this script ~45 min after qualifying ends
     → QualiPosition auto-fetched from FastF1
  2. Check FIA Starting Grid Saturday morning (fia.com or F1 app)
  3. If any grid penalties exist, enter them when prompted
  4. Script writes updated Prediction.csv ready for race_predictor.py
"""

import fastf1
import pandas as pd
import numpy as np
import Generals.streamlib as stlib
from sliplog import logs

fastf1.Cache.enable_cache("cache")

# ============================================================
# CONFIG
# ============================================================

YEAR      = 2026
ROUND     = stlib.get_current_gp_no()
EVENT     = stlib.get_eventname(ROUND)
CSV_PATH  = f"outputs/{YEAR}_{EVENT}/Prediction.csv"

# ============================================================
# STEP 1 — FastF1: fetch QualiPosition
# ============================================================

# spl-cl: fetch_quali_positions — pulls Q session Position from FastF1.
# spl-cl: This is the ONLY reliable thing FastF1 gives us before the race.
# spl-cl: GridPosition in Q results is always empty (confirmed empirically).
def fetch_quali_positions(year: int, round_number: int) -> pd.DataFrame:
    """
    Returns DataFrame with columns: Driver, QualiPosition
    Source: FastF1 qualifying session results → Position column
    Available: ~45 min after qualifying chequered flag
    """
    print(f"  Fetching FastF1 qualifying session (Year={year}, Round={round_number}) ...")
    q = fastf1.get_session(year, round_number, "Q")

    # spl-cl: bare q.load() — no arguments. Passing ANY kwarg (laps=False etc.)
    # spl-cl: causes results to come back all NaN. Confirmed empirically.
    q.load()

    if q.results.empty:
        raise ValueError("FastF1 returned empty qualifying results. Session may not be available yet.")

    df = q.results[["Abbreviation", "Position", "Q1", "Q2", "Q3"]].copy()
    df.columns = ["Driver", "QualiPosition", "Q1", "Q2", "Q3"]
    df["QualiPosition"] = pd.to_numeric(df["QualiPosition"], errors="coerce")
    df = df.sort_values("QualiPosition").reset_index(drop=True)

    # spl-cl: display full FastF1 quali table so user can verify before penalty prompt
    print(f"\n  ── FastF1 Qualifying Results ───────────────────────────")
    print(f"  {'P':<4} {'Driver':<8} {'Q1':>10} {'Q2':>10} {'Q3':>10}")
    print("  " + "─" * 46)
    for _, row in df.iterrows():
        q1 = str(row["Q1"])[:10] if pd.notna(row["Q1"]) else "    —"
        q2 = str(row["Q2"])[:10] if pd.notna(row["Q2"]) else "    —"
        q3 = str(row["Q3"])[:10] if pd.notna(row["Q3"]) else "    —"
        print(f"  {int(row['QualiPosition']) if pd.notna(row['QualiPosition']) else '?':<4} {row['Driver']:<8} {q1:>10} {q2:>10} {q3:>10}")
    print()
    print(f"  ✓  {df['QualiPosition'].notna().sum()} drivers fetched. Verify above before continuing.")
    print()
    input("  Press ENTER to continue → ")

    return df[["Driver", "QualiPosition"]]


# ============================================================
# STEP 2 — Manual: collect GridPosition from FIA starting grid
# ============================================================

# spl-cl: collect_grid_positions — prompts user to enter the FIA official
# spl-cl: starting grid order. FastF1 cannot give this before the race.
# spl-cl: Source: fia.com → Documents → Starting Grid (published Sat morning)
# spl-cl: or F1 app → Race Hub → Starting Grid tab.
def collect_grid_positions(quali_df: pd.DataFrame) -> pd.DataFrame:
    """
    Two-step grid collection:
      A) Default: assume GridPosition = QualiPosition (no penalties)
      B) User enters any penalty changes on top

    Returns quali_df with GridPosition column added.
    """
    grid_df = quali_df.copy()

    # spl-cl: start with GridPosition = QualiPosition as default
    grid_df["GridPosition"] = grid_df["QualiPosition"]

    print()
    print("  ── FIA Starting Grid ──────────────────────────────────")
    print("  Source: fia.com → Documents → Starting Grid")
    print("          OR  F1 app → Race Hub → Starting Grid")
    print()

    # spl-cl: ask if any grid penalties exist — skip entire block if clean grid
    has_penalties = input("  Any grid penalties or changes from quali order? [y/n]: ").strip().lower()

    if has_penalties == "y":
        print()
        print("  Enter each penalty as:  DRIVER  FINAL_GRID_POSITION")
        print("  Example:  NOR 13   (NOR drops from P3 to P13)")
        print("  Empty line to finish.")
        print()

        penalties = {}
        while True:
            entry = input("  Penalty > ").strip().upper()
            if not entry:
                break
            parts = entry.split()
            if len(parts) != 2:
                print("  ⚠  Format: DRIVER POSITION  (e.g. NOR 13)")
                continue
            driver, pos = parts[0], parts[1]
            if not pos.isdigit():
                print("  ⚠  Position must be a number")
                continue
            penalties[driver] = int(pos)
            print(f"  ✓  {driver} → Grid P{pos}")

        # spl-cl: apply penalties to GridPosition column
        for driver, final_pos in penalties.items():
            mask = grid_df["Driver"] == driver
            if mask.any():
                grid_df.loc[mask, "GridPosition"] = final_pos
            else:
                print(f"  ⚠  {driver} not found in qualifying results — skipping")

    return grid_df


# ============================================================
# STEP 3 — Update Prediction.csv
# ============================================================

def update_prediction_csv(csv_path: str, grid_df: pd.DataFrame) -> pd.DataFrame:
    """
    Write QualiPosition and GridPosition into Prediction.csv.
    Sort by GridPosition (actual race start order).
    """
    df = pd.read_csv(csv_path)

    for _, row in grid_df.iterrows():
        driver = row["Driver"]
        mask   = df["Driver"] == driver

        if not mask.any():
            print(f"  ⚠  {driver} in FastF1 results but not in Prediction.csv — skipping")
            continue

        df.loc[mask, "QualiPosition"] = row["QualiPosition"]
        df.loc[mask, "GridPosition"]  = row["GridPosition"]

    # spl-cl: sort by final grid position — this is race start order
    df = df.sort_values("GridPosition", ascending=True).reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    return df


# ============================================================
# DISPLAY
# ============================================================

def print_grid(df: pd.DataFrame) -> None:
    """Print the final grid with penalty flags for visual verification."""

    print()
    print(f"  ╔{'═'*52}╗")
    print(f"  ║{'STARTING GRID  —  ' + EVENT.replace('_',' ').upper():^52}║")
    print(f"  ╠{'═'*52}╣")
    print(f"  │  {'P':<4} {'Driver':<8} {'Team':<22} {'Quali':>5} {'Grid':>5}  │")
    print(f"  ├{'─'*52}┤")

    for _, row in df.sort_values("GridPosition").iterrows():
        q = row["QualiPosition"]; g = row["GridPosition"]
        try:
            penalty_flag = f" ▼{int(g-q):+d}" if int(g) != int(q) else "     "
        except:
            penalty_flag = "     "
        print(
            f"  │  {int(g) if not pd.isna(g) else '?':<4}"
            f" {row['Driver']:<8}"
            f" {str(row.get('Team','')):<22}"
            f" {str(int(q)) if not pd.isna(q) else 'NaN':>5}"
            f" {str(int(g)) if not pd.isna(g) else 'NaN':>5}"
            f"  {penalty_flag}│"
        )

    print(f"  ╚{'═'*52}╝")
    print()


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"\n── Post-Quali Update : {EVENT}  (Round {ROUND}) ──────")
    print()
    print("  HYBRID ARCHITECTURE:")
    print("  FastF1  →  QualiPosition  (auto)")
    print("  FIA     →  GridPosition   (manual — from FIA starting grid doc)")
    print()

    # spl-cl: Step 1 — FastF1 quali fetch with graceful fallback
    try:
        quali_df = fetch_quali_positions(YEAR, ROUND)

    except Exception as e:
        # spl-cl: FastF1 not ready yet (~45 min after quali ends)
        print(f"  ⚠  FastF1 unavailable: {e}")
        print(f"  Falling back to manual quali order entry.")
        print(f"  Re-run in ~45 min for automatic fetch.\n")

        d = input("  Enter drivers in QUALI order (space-separated): ").split()
        quali_df = pd.DataFrame({
            "Driver":       d,
            "QualiPosition": list(range(1, len(d) + 1))
        })

    # spl-cl: Step 2 — manual FIA grid (penalties on top of quali)
    print()
    grid_df = collect_grid_positions(quali_df)

    # spl-cl: Step 3 — update and save Prediction.csv
    print()
    print("  Updating Prediction.csv ...")
    df_updated = update_prediction_csv(CSV_PATH, grid_df)

    print_grid(df_updated)

    print(f"  ✓  Saved → {CSV_PATH}")
    print(f"  Next: run race_predictor.py on race day\n")

    logs.write(f"Post-quali complete: {EVENT} R{ROUND} — hybrid FastF1 + FIA grid")


if __name__ == "__main__":
    main()