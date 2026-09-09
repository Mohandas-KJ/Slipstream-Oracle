# Imports
import pandas as pd
import fastf1
import Generals.streamlib as stlib
from sliplog import logs

fastf1.Cache.enable_cache("cache")  # spl-cl: reuse cache from data_collector

# Read the prediction dataset for current GP
df = pd.read_csv(f"outputs/2026_{stlib.get_eventname(stlib.get_current_gp_no())}/Prediction.csv")

# ============================================================
# spl-cl: fetch_quali_grid — pulls QualiPosition and GridPosition
# spl-cl: separately from FastF1 so grid penalties are correctly
# spl-cl: reflected. Old code set both to the same value which
# spl-cl: contradicted how the model was trained (Belgian GP etc.)
# spl-cl: QualiPosition = where driver qualified (pure pace)
# spl-cl: GridPosition  = actual grid slot after penalties applied
# ============================================================
def fetch_quali_grid(year: int, round_number: int) -> pd.DataFrame:
    """
    Fetch QualiPosition and GridPosition for every driver from FastF1.
    Returns a DataFrame with columns: Driver, QualiPosition, GridPosition.

    QualiPosition — from the qualifying session results (Q result position)
    GridPosition  — from the race session results (GridPosition column),
                    which reflects any grid penalties applied after quali.

    Available roughly 45-60 min after quali session ends on FastF1.
    """

    print(f"  Fetching qualifying session  (Year={year}, Round={round_number}) ...")
    q_session = fastf1.get_session(year, round_number, "Q")
    q_session.load(laps=False, telemetry=False, weather=False, messages=False)

    quali_df = q_session.results[["Abbreviation", "Position"]].copy()
    quali_df.columns = ["Driver", "QualiPosition"]
    quali_df["QualiPosition"] = pd.to_numeric(quali_df["QualiPosition"], errors="coerce")
    print(f"  Qualifying positions fetched : {len(quali_df)} drivers")

    # spl-cl: GridPosition comes from the Race session results, NOT quali.
    # spl-cl: FastF1 populates race results GridPosition after grid drops are applied.
    # spl-cl: This is available after qualifying + any steward decisions (usually Sat evening).
    print(f"  Fetching race session grid   (Year={year}, Round={round_number}) ...")
    r_session = fastf1.get_session(year, round_number, "R")
    r_session.load(laps=False, telemetry=False, weather=False, messages=False)

    race_df = r_session.results[["Abbreviation", "GridPosition"]].copy()
    race_df.columns = ["Driver", "GridPosition"]
    race_df["GridPosition"] = pd.to_numeric(race_df["GridPosition"], errors="coerce")
    print(f"  Grid positions fetched       : {len(race_df)} drivers")

    merged = quali_df.merge(race_df, on="Driver", how="outer")
    return merged
# spl-cl: end fetch_quali_grid


# spl-cl: add_grid — updates Prediction.csv with real QualiPosition and GridPosition
def add_grid(data: pd.DataFrame, grid_data: pd.DataFrame) -> pd.DataFrame:
    """
    Update QualiPosition and GridPosition columns in prediction DataFrame
    using real FastF1 data. Drivers not found in FastF1 (e.g. reserve drivers
    added manually) retain their existing values.
    """
    df1 = data.copy()

    for _, row in grid_data.iterrows():
        d = row["Driver"]
        mask = df1["Driver"] == d

        if not mask.any():
            print(f"  ⚠  {d} in FastF1 results but not in Prediction.csv — skipping")
            continue

        # spl-cl: set separately — these will differ when grid penalties exist
        if not pd.isna(row["QualiPosition"]):
            df1.loc[mask, "QualiPosition"] = row["QualiPosition"]
        if not pd.isna(row["GridPosition"]):
            df1.loc[mask, "GridPosition"] = row["GridPosition"]

    # spl-cl: sort by GridPosition (actual race start order, not quali order)
    df1 = df1.sort_values("GridPosition", ascending=True).reset_index(drop=True)
    return df1
# spl-cl: end add_grid


# ============================================================
# MAIN
# ============================================================

year        = 2026
round_no    = stlib.get_current_gp_no()
event_name  = stlib.get_eventname(round_no)
out_path    = f"outputs/{year}_{event_name}/Prediction.csv"

print(f"\n── Post-Quali Update : {event_name} (Round {round_no}) ──")

# spl-cl: try FastF1 first; fall back to manual entry if session not yet available
try:
    grid_data = fetch_quali_grid(year, round_no)

    # spl-cl: show the diff so user can spot penalties visually
    print(f"\n  {'Driver':<8} {'Quali':>6} {'Grid':>6} {'Penalty?':>10}")
    print("  " + "─" * 34)
    for _, r in grid_data.sort_values("GridPosition").iterrows():
        q = r["QualiPosition"]; g = r["GridPosition"]
        penalty = f"  ▲ {int(g-q):+d}" if not pd.isna(q) and not pd.isna(g) and q != g else ""
        print(f"  {r['Driver']:<8} {str(q):>6} {str(g):>6}{penalty}")

    df_updated = add_grid(df, grid_data)
    df_updated.to_csv(out_path, index=False)
    print(f"\n  ✓  Prediction.csv updated → {out_path}")
    logs.write(f"Post-quali update complete: {event_name} R{round_no} (FastF1)")

except Exception as e:
    # spl-cl: FastF1 fallback — session not available yet, use manual entry
    # spl-cl: This happens if quali just ended and data isn't on the API yet (~45 min delay)
    print(f"\n  ⚠  FastF1 fetch failed: {e}")
    print(f"  Falling back to manual entry.")
    print(f"  (Re-run in ~45 min after quali ends for automatic fetch)\n")

    d   = input("Enter Drivers in GRID order (space-separated): ").split()
    pos = list(range(1, len(d) + 1))

    # spl-cl: manual fallback still separates quali from grid
    print("Any grid penalties? Enter as 'DRIVER GRIDPOS' one per line. Empty to finish:")
    penalties = {}
    while True:
        entry = input("  Penalty > ").strip().upper()
        if not entry:
            break
        parts = entry.split()
        if len(parts) == 2:
            penalties[parts[0]] = int(parts[1])

    grid_data_manual = pd.DataFrame({"Driver": d, "QualiPosition": pos})
    grid_data_manual["GridPosition"] = grid_data_manual.apply(
        lambda r: penalties.get(r["Driver"], r["QualiPosition"]), axis=1
    )
    df_updated = add_grid(df, grid_data_manual)
    df_updated.to_csv(out_path, index=False)
    print(f"\n  ✓  Prediction.csv updated → {out_path}")
    logs.write(f"Post-quali update complete: {event_name} R{round_no} (manual fallback)")