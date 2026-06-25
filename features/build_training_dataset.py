# Import
import pandas as pd
from pathlib import Path
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

    event = fastf1.get_event_schedule(year,include_testing=False)
    fin_list = event.EventName.to_list()
    for i in fin_list:
        fin_list[fin_list.index(i)] = str(i).replace(" ","_")

    return fin_list

def get_drivers_GP(year):

    const_path = DATA_DIR / str(year) / "Australian_Grand_Prix" / "race_laps.csv"

    df = pd.read_csv(const_path)

    return df["Driver"].unique().tolist()

for y in YEAR:
    events[y] = get_event_list(y)
    drivers[y] =  get_drivers_GP(y)

print(drivers)

for dt in YEAR:
    for eve in events[dt]:
        quali_res = DATA_DIR / str(dt) / eve / Q_RESULT
        race_res = DATA_DIR / str(dt) / eve / R_RESULT





