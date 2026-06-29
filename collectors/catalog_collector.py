"""
This File is used to collect and store the Complete Round Map 
and other Schedule related Files
1. It gets an year from the user and creates a DIR
2. Gets the RoundNumber and EventName from fastf1 API
3. Saves it as .csv file
4. Consists of a json file to track the GP status
"""

# Imports
import fastf1,os
import pandas as pd
from pathlib import Path

CORE_PATH = "catalog"
CACHE = "cache/"

def create_dir(year):

    #make complete path
    path_dir = Path(CORE_PATH) / str(2026)
    
    if not path_dir.exists():
        print("Catalog Folder not found! Creating......")
        path_dir.mkdir(parents=True)
        print("Catalog Folder Created!")
    else:
        print("Catalog Folder Exits!")

def get_schedule(year):

    # Data Frame
    dft = {}

    # Create Directory
    create_dir(year)

    # Enable Caching
    fastf1.Cache.enable_cache(CACHE)

    # Load Session and Get Schedule
    session = fastf1.get_event_schedule(2026,include_testing=False)

    # Get Rounds and Events
    rounds = session["RoundNumber"].tolist()
    events_ses = session["EventName"].tolist()
    events = []

    for e in events_ses:
        t = str(e).replace(" ","_")
        events.append(t)

    dft["RoundNumber"] = rounds
    dft["EventName"] = events

    path_dir = Path(CORE_PATH) / str(2026)

    df = pd.DataFrame(dft)
    df.to_csv(path_dir / "Schedule.csv",index=False)
    print("Schedule File Svaed!")
    

print("Schedule Collector")
year = int(input("Enter Year: "))
get_schedule(2026)