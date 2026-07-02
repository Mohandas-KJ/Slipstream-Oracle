"""
This Script is used to evaluate post Race Scenario
1. It takes the predicted dataset and Driver Actual position after race
2. Calculates and fills in the error column for each Driver
3. Displays the average Error
"""

# Imports
import pandas as pd
from pathlib import Path
import json

# CONFIG
COMPLETED_TAB = "catalog/2026/completed.json" # Hardcoded Year for now
ROUND_MAP = "catalog/2026/Schedule.csv"

def read_prediction(location):
    df = pd.read_csv(location)
    return df

def get_post_position_calc_error(data,drivers,pos,loc):
    
    temp_df = pd.DataFrame({"Driver": drivers,
                            "Position": pos})
    
    df1 = data.copy()
    
    for d in temp_df["Driver"]:
        pos = temp_df.loc[temp_df["Driver"] == d, "Position"].iloc[0]

        df1.loc[df1["Driver"] == d, "TargetFinish"] = pos
    
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


if __name__ == "__main__":
    
    LOCATION = input("Prediction File (Relative): ")
    df = read_prediction(LOCATION)
    print("Prediction File Loaded!\n")

    Driver = input("Enter Drivers (Rank): ").split()
    pos = [i for i in range(1,len(Driver)+1)]
    file = get_post_position_calc_error(df,Driver,pos,LOCATION)

    error = calculate_error(file)
    print(f"The Average Error: {error}\n")

    print(f"{df["EventName"].unique().iloc[0]} is marked as completed!")
    mark_round_complete()

    print("\nScript Execution Complete!")


    
