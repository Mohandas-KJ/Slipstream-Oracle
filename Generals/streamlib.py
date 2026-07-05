import pandas as pd 
import json

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Get EvenNumber
def get_eventname(evnt_no):
    # Read CSV
    df = pd.read_csv(f"{PROJECT_ROOT}/catalog/2026/Schedule.csv")

    # Return name
    return df.loc[df["RoundNumber"] == evnt_no, "EventName"].iloc[0]

def get_current_gp_no():

    # json location
    with open("catalog/2026/completed.json") as js:
        file = json.load(js)
    
    # Get Number
    Round_NO = file[max(file,key=file.get)] + 1

    return Round_NO