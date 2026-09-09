# Import
import pandas as pd
from pathlib import Path
from sliplog import logs
import numpy as np
import fastf1
import sys

# Path
DATA_DIR = Path("data")
Q_RESULT = "qualifying_results.csv"
R_RESULT = "race_results.csv"
R_LAPS = "race_laps.csv"

#Config
YEAR = [2022,2023,2024,2025,2026]

# spl-cl: TEAM_CANONICAL — maps every historical team name variant to one
# spl-cl: canonical current name. Without this the encoder sees AlphaTauri,
# spl-cl: RB and Racing Bulls as 3 different teams, breaking TSU's career
# spl-cl: history lookup and confusing the model's Team feature.
#
# spl-cl: Lineage confirmed from oracle_v1 data:
# spl-cl:   AlphaTauri (2022-23) → RB (2024) → Racing Bulls (2025-26)
# spl-cl:   Alfa Romeo (2022-23) → Kick Sauber (2024-25) → Audi (2026)
TEAM_CANONICAL = {
    # Faenza team lineage
    "AlphaTauri":  "Racing Bulls",
    "RB":          "Racing Bulls",
    "Racing Bulls": "Racing Bulls",
    # Hinwil team lineage
    "Alfa Romeo":  "Audi",
    "Kick Sauber": "Audi",
    "Audi":        "Audi",
    # Stable teams — listed explicitly for completeness
    "Red Bull Racing": "Red Bull Racing",
    "Mercedes":        "Mercedes",
    "Ferrari":         "Ferrari",
    "McLaren":         "McLaren",
    "Alpine":          "Alpine",
    "Aston Martin":    "Aston Martin",
    "Williams":        "Williams",
    "Haas F1 Team":    "Haas F1 Team",
    "Cadillac":        "Cadillac",
}

def normalise_team(name: str) -> str:
    # spl-cl: returns canonical name; falls back to original if not in map
    return TEAM_CANONICAL.get(str(name).strip(), str(name).strip())

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

    event["Session5DateUtc"] = pd.to_datetime(event["Session5DateUtc"],utc=True)

    # Keep only completed events
    event = event[
        event["Session5DateUtc"] < pd.Timestamp.now(tz="UTC")
    ]

    fin_list = (
        event["EventName"]
        .str.replace(" ", "_")
        .tolist()
    )

    return fin_list

def get_drivers_GP(year):
   
    
    year_path = DATA_DIR / str(year)

    if not year_path.exists():
        raise FileNotFoundError(f"No data found for year {year} at {year_path}")

    drivers = set()

    for gp_folder in sorted(year_path.iterdir()):
        if not gp_folder.is_dir():
            continue

        # race_laps has every driver per lap — most complete source
        laps_csv    = gp_folder / "race_laps.csv"
        results_csv = gp_folder / "race_results.csv"

        if laps_csv.exists():
            df = pd.read_csv(laps_csv, usecols=["Driver"])
            drivers.update(df["Driver"].dropna().unique().tolist())

        elif results_csv.exists():
            df = pd.read_csv(results_csv, usecols=["Abbreviation"])
            drivers.update(df["Abbreviation"].dropna().unique().tolist())

    if not drivers:
        raise ValueError(f"No driver data found in any GP folder for {year}")

    return sorted(drivers)

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
                raw_team = quali_res[quali_res["Abbreviation"] == driv]["TeamName"].iloc[0]
                df["Team"].append(normalise_team(raw_team))  # spl-cl: normalise here
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
logs.write("Generated Training dataset: Updated files oracle_v1.csv and pickle file")