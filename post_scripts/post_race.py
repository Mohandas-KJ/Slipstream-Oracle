"""
This Script is used to evaluate post Race Scenario
1. It takes the predicted dataset and Driver Actual position after race
2. Calculates and fills in the error column for each Driver
3. Displays the average Error
"""

# Imports
import pandas as pd
from pathlib import Path
import json,fastf1
from Generals import streamlib
from sliplog import logs

# CONFIG
COMPLETED_TAB = "catalog/2026/completed.json" # Hardcoded Year for now
ROUND_MAP = "catalog/2026/Schedule.csv"
DATA_DIR = Path("data/2026")

def read_prediction(location):
    df = pd.read_csv(location)
    return df

def get_latest():
    with open(COMPLETED_TAB) as f:
        completed = json.load(f)
    
    return completed[max(completed,key=completed.get)]

def get_race_result(round_no):

    fastf1.Cache.enable_cache("cache")

    session = fastf1.get_session(2026,streamlib.get_eventname(round_no),"R")
    session.load()

    return session.results[["Abbreviation", "ClassifiedPosition"]].rename(
    columns={"Abbreviation": "Driver", "ClassifiedPosition": "Position"}
    ).reset_index(drop=True)

def get_post_position_calc_error(pos_df,data,loc):
    
    df1 = data.copy()
    
    for d in pos_df["Driver"]:
        pos = pos_df.loc[pos_df["Driver"] == d, "Position"].iloc[0]

        df1.loc[df1["Driver"] == d, "TargetFinish"] = pos

    df1["RaceStatus"] = df1["TargetFinish"]

    df1["TargetFinish"] = pd.to_numeric(df1["TargetFinish"],errors="coerce")
    df1["Error"] = abs(df1["TargetFinish"] - df1["PredictedFinish"])

    dir_save = Path(loc).parent
    
    df1.to_csv(f"{dir_save}/Final_Data.csv",index=False)
    print("Final File Generated Successfully!")
    return f"{dir_save}/Final_Data.csv"

def calculate_error(loc):

    df = pd.read_csv(loc)

    return df["Error"].mean()

def mark_round_complete():
    """
    1. This Function maps the current round as completed
    2. It reads the json
    3. Gets the Highest RoundNumber's Key -> EventName
    4. Increment the RoundNumber and access the Schedule
    5. Write the key and It's RoundNumber to json
    """

    # Open the json file
    with open(COMPLETED_TAB) as f:
        Completed_RM = json.load(f)
    
    # Select Highest Key
    current_event_no = Completed_RM[max(Completed_RM,key=Completed_RM.get)] + 1

    # Import the Scedule 
    round_mp = pd.read_csv(ROUND_MAP)
    
    # Get the EventName and RoundNumber and write it to json
    Completed_RM[round_mp[round_mp["RoundNumber"] == current_event_no]["EventName"].iloc[0]] = current_event_no

    # Write it Safely
    with open(COMPLETED_TAB,"w") as fl:
        json.dump(Completed_RM,fl,indent=4)

def get_post_event_data(round_no):
    """
    1. This function downloads the post race data and save it to data
    2. Get the event name with Round Number
    3. Build Path
    4. Load qualifying results and export
    5. Load Race Results and export
    6. Load Race Laps and export
    """

    # Get the event
    round_sc = pd.read_csv(ROUND_MAP)
    Round_name = round_sc[round_sc["RoundNumber"] == round_no]["EventName"].iloc[0] # We use this for Path

    # Path Building
    Target_path = DATA_DIR / Round_name

    # Load F1
    fastf1.Cache.enable_cache("cache")
    # Load session
    events = ["Q","R"]
    for e in events:
        session = fastf1.get_session(2026,str(Round_name).replace("_"," "),e)
        session.load()

        if e.__eq__("Q"):
            Q_Results = session.results
            Q_Results.to_csv(Target_path / "qualifying_results.csv",index=False)
            print("Qualifying Results saved!")
        else:
            R_Laps = session.laps
            R_Results = session.results
            
            # Export
            R_Laps.to_csv(Target_path / "race_laps.csv",index=False)
            print("Race Lap Results saved!")
            R_Results.to_csv(Target_path / "race_results.csv",index=False)
            print("Race Results Saved!")

        
if __name__ == "__main__":

    
    LOCATION = input("Prediction File (Relative): ")
    df = read_prediction(LOCATION)
    print("Prediction File Loaded!\n")

    print("Loading Race data....")
    file = get_post_position_calc_error(get_race_result(streamlib.get_current_gp_no()),df,LOCATION)

    error = calculate_error(file)
    print(f"The Average Error: {error}\n")
    logs.write("Performed post race routines: Calculated Errors")

    print(f"{df["Race"].unique()[0]} is marked as completed!")
    mark_round_complete()

    get_post_event_data(get_latest())

    print("\nScript Execution Complete!")