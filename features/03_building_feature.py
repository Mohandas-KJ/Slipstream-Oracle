import fastf1
import pandas as pd
from sliplog import logs

fastf1.Cache.enable_cache("cache")

_schedule_cache: dict[int, dict[str, int]] = {}

def _get_round_map(year: int) -> dict[str, int]:
    if year not in _schedule_cache:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        _schedule_cache[year] = {
            str(e["EventName"]).replace("/", "-").replace(" ", "_"): int(e["RoundNumber"])
            for _, e in schedule.iterrows()
        }
    return _schedule_cache[year]


def add_round_number(df: pd.DataFrame) -> pd.DataFrame:
    def lookup(row):
        rmap = _get_round_map(int(row["Year"]))
        return rmap.get(str(row["Race"]))

    df = df.copy()
    df.insert(0, "Round", df.apply(lookup, axis=1))
    df["Round"] = pd.to_numeric(df["Round"], errors="coerce").astype("Int64")
    return df

import pandas as pd


def extract_feature_35(year: int, df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Build oracle_v2 style feature rows for a given year.

    For each (round, driver), the rolling averages (last 3 and last 5 races)
    are computed from the races STRICTLY BEFORE the current round.
    If there aren't enough races in the current year, it walks back into
    the previous year (from the last round backwards) to fill the window.

    Parameters
    ----------
    year     : the season year to generate features for
    df_all   : the full oracle_v1 dataframe (all years), with a 'Round' column
               (add it via add_round_number() before calling this function)

    Returns
    -------
    DataFrame in oracle_v2 format.
    """

    # ── sort entire history once ─────────────────────────────────────────────
    df_all = df_all.copy()
    df_all["TargetFinish_num"] = pd.to_numeric(df_all["TargetFinish"], errors="coerce")
    df_all["GridPosition_num"] = pd.to_numeric(df_all["GridPosition"],  errors="coerce")
    df_all["Points_num"]       = pd.to_numeric(df_all["Points"],        errors="coerce")

    # canonical sort key: (Year, Round)
    df_all = df_all.sort_values(["Year", "Round"]).reset_index(drop=True)

    # ── target year slice ────────────────────────────────────────────────────
    target = df_all[df_all["Year"] == year]
    rounds  = sorted(target["Round"].unique())

    # ── history = everything BEFORE this year (for cross-season look-back) ──
    history_prev = df_all[df_all["Year"] < year]

    rows = []

    for r in rounds:

        race_name = target[target["Round"] == r]["Race"].iloc[0]
        drivers   = target[target["Round"] == r]["Driver"].unique()

        # races in the CURRENT year that come BEFORE round r
        prev_rounds_this_year = [x for x in rounds if x < r]

        for d in drivers:

            cur = target[(target["Round"] == r) & (target["Driver"] == d)]
            if cur.empty:
                continue

            # ── build the driver's ordered history up to (not including) round r ──
            # current year races before r
            dr_this = df_all[
                (df_all["Year"] == year) &
                (df_all["Round"].isin(prev_rounds_this_year)) &
                (df_all["Driver"] == d)
            ].sort_values(["Year", "Round"])

            # how many more do we need to fill a window of 5?
            need = 5 - len(dr_this)

            if need > 0:
                # pull from previous years, most recent first
                dr_prev = history_prev[history_prev["Driver"] == d] \
                    .sort_values(["Year", "Round"]) \
                    .tail(need)
                dr_history = pd.concat([dr_prev, dr_this], ignore_index=True)
            else:
                dr_history = dr_this

            # last N rows  (already sorted oldest→newest, so tail gives most recent N)
            last3 = dr_history.tail(3)
            last5 = dr_history.tail(5)
            last = dr_history.tail(1)

            def avg(series): return round(series.mean(), 2) if len(series) else float("nan")

            if last.empty:
                positions_gained = np.nan
            else:
                grid = last["GridPosition_num"].iloc[0]
                finish = last["TargetFinish_num"].iloc[0]
                            
                if pd.isna(grid) or pd.isna(finish):
                    positions_gained = np.nan
                else:
                    positions_gained = round(grid - finish, 2)

            rows.append({
                "Year":            year,
                "RoundNumber":     r,
                "Race":            race_name,
                "Driver":          d,
                "Team":            cur["Team"].iloc[0],
                "QualiPosition":   cur["QualiPosition"].iloc[0],
                "GridPosition":    cur["GridPosition"].iloc[0],
                "AvgFinishLast3":  avg(last3["TargetFinish_num"]),
                "AvgFinishLast5":  avg(last5["TargetFinish_num"]),
                "AvgGridLast3":    avg(last3["GridPosition_num"]),
                "AvgGridLast5":    avg(last5["GridPosition_num"]),
                "AvgPointsLast3":  avg(last3["Points_num"]),
                "AvgPointsLast5":  avg(last5["Points_num"]),
                "PositionsGainedLastRace":  positions_gained,
                "FinishStdLast5": round(np.std(last5["TargetFinish_num"]), 2),
                "TargetFinish":    cur["TargetFinish"].iloc[0],
            })

    return pd.DataFrame(rows)


# ── usage ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    df_v1 = pd.read_csv("outputs/oracle_v1.csv")
    df_v1 = add_round_number(df_v1)

    # drop the unnamed index column if present
    df_v1 = df_v1.loc[:, ~df_v1.columns.str.startswith("Unnamed")]

    result = extract_feature_35(2026, df_v1)
    result.to_csv("outputs/oracle_v2.csv", index=False)
    print(result.head(10).to_string())
    print(f"\nDone. Shape: {result.shape}")
    logs.write("Generated Feature Dataset: oracle_v2.csv")

    

