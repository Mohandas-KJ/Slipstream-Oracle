# Import
import pandas as pd
from pathlib import Path
import numpy as np
import fastf1
import sys

# Path
DATA_DIR = Path("data")
Q_RESULT = "qualifying_results.csv"
R_RESULT = "race_results.csv"
R_LAPS = "race_laps.csv"

# CONFIG
YEAR = [2022,2023,2024,2025,2026]

df = {"Year": [],
      "Race": [],
      "Driver": [],
      "Team": [],
      "QualiPosition": [],
      "GridPosition": [],
      "TargetFinish": [],
      "Points": []}

events = {}
drivers = {}

def get_event_list(year):

    fastf1.Cache.enable_cache("cache")

    event = fastf1.get_event_schedule(
        year,
        include_testing=False
    )

    # Keep only completed events
    event = event[
        event["EventDate"] < pd.Timestamp.now()
    ]

    fin_list = (
        event["EventName"]
        .str.replace(" ", "_")
        .tolist()
    )

    return fin_list

def get_drivers_GP(year):

    const_path = DATA_DIR / str(year) / "Australian_Grand_Prix" / "race_laps.csv"

    df = pd.read_csv(const_path)

    return df["Driver"].unique().tolist()

for y in YEAR:
    events[y] = get_event_list(y)
    drivers[y] =  get_drivers_GP(y)

for dt in YEAR:
    for eve in events[dt]:
        quali_res = pd.read_csv(DATA_DIR / str(dt) / eve / Q_RESULT)
        race_res = pd.read_csv(DATA_DIR / str(dt) / eve / R_RESULT)

        for driv in drivers[dt]:
            df["Year"].append(dt)
            df["Race"].append(eve)
            df["Driver"].append(driv)

            if driv in quali_res["Abbreviation"].values and driv in race_res["Abbreviation"].values:
                df["Team"].append(quali_res[quali_res["Abbreviation"] == driv]["TeamName"].iloc[0])
                df["QualiPosition"].append(quali_res[quali_res["Abbreviation"] == driv]["Position"].iloc[0])
                df["GridPosition"].append(race_res[race_res["Abbreviation"] == driv]["GridPosition"].iloc[0])
                df["TargetFinish"].append(race_res[race_res["Abbreviation"] == driv]["ClassifiedPosition"].iloc[0])
                df["Points"].append(race_res[race_res["Abbreviation"] == driv]["Points"].iloc[0])
            else:
                df["Team"].append(np.nan)
                df["QualiPosition"].append(np.nan)
                df["GridPosition"].append(np.nan)
                df["TargetFinish"].append(np.nan)
                df["Points"].append(np.nan)

dataframe = pd.DataFrame(df)
dataframe.to_csv("outputs/oracle_v1.csv")
print("CSV Exported Successfully!")
dataframe.to_pickle("outputs/oracle_v1_pickle.pkl")
print("Pickle File Generated!")





