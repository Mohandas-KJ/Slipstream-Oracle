import fastf1
import pandas as pd

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

def extract_feature_35(year):

    new_df = {"Year": [],
              "RoundNumber": [],
              "Race": [],
              "Driver": [],
              "Team": [],
              "QualiPosition": [],
              "GridPosition": [],
              "AvgFinishLast3": [],
              "AvgFinishLast5": [],
              "AvgGridLast3": [],
              "AvgGridLast5": [],
              "AvgPointsLast3": [],
              "AvgPointsLast5": [],
              "TargetFinish": []}

    df = pd.read_csv("outputs/oracle_v1.csv")
    df = add_round_number(df).drop(columns=["Unnamed: 0"]).sort_values(by=["Year","Round"],ascending=True).reset_index(drop=True)

    target_data = df[df["Year"] == year]

    rounds = target_data["Round"].unique()
    drivers = target_data["Driver"].unique()

    last3 = target_data["Round"].unique()[::-1][:3].tolist()
    last5 = target_data["Round"].unique()[::-1][:5].tolist()

    for r in rounds:
        for d in drivers:

            new_df["Year"].append(year)
            new_df["RoundNumber"].append(r)
            new_df["Race"].append(target_data[target_data["Round"] == r]["Race"].iloc[0])

            new_df["Driver"].append(d)
            new_df["Team"].append(target_data[target_data["Driver"] == d]["Team"].iloc[0])
            new_df["QualiPosition"].append(target_data[(target_data["Round"] == r) & (target_data["Driver"] == d)]["QualiPosition"].iloc[0])
            new_df["GridPosition"].append(target_data[(target_data["Round"] == r) & (target_data["Driver"] == d)]["GridPosition"].iloc[0])
            new_df["AvgFinishLast3"].append(pd.to_numeric(target_data[(target_data["Round"].isin(last3)) &(target_data["Driver"] == d)]["TargetFinish"],errors="coerce").mean().round(2))
            new_df["AvgFinishLast5"].append(pd.to_numeric(target_data[(target_data["Round"].isin(last5)) &(target_data["Driver"] == d)]["TargetFinish"],errors="coerce").mean().round(2))
            new_df["AvgGridLast3"].append(pd.to_numeric(target_data[(target_data["Round"].isin(last3)) &(target_data["Driver"] == d)]["GridPosition"],errors="coerce").mean().round(2))
            new_df["AvgGridLast5"].append(pd.to_numeric(target_data[(target_data["Round"].isin(last5)) &(target_data["Driver"] == d)]["GridPosition"],errors="coerce").mean().round(2))
            new_df["AvgPointsLast3"].append(pd.to_numeric(target_data[(target_data["Round"].isin(last3)) &(target_data["Driver"] == d)]["Points"],errors="coerce").mean().round(2))
            new_df["AvgPointsLast5"].append(pd.to_numeric(target_data[(target_data["Round"].isin(last5)) &(target_data["Driver"] == d)]["Points"],errors="coerce").mean().round(2))
            new_df["TargetFinish"].append(target_data[(target_data["Round"].isin(last3)) &(target_data["Driver"] == d)]["TargetFinish"].iloc[0])

    
    df = pd.DataFrame(new_df)
    df.to_csv("outputs/oracle_v2.csv",index=False)

extract_feature_35(2026)

    

