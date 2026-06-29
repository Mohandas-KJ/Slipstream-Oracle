"""
This Script is used to evaluate post Race Scenario
1. It takes the predicted dataset and Driver Actual position after race
2. Calculates and fills in the error column for each Driver
3. Displays the average Error
"""

# Imports
import pandas as pd
from pathlib import Path

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

if __name__ == "__main__":
    LOCATION = input("Prediction File (Relative): ")
    df = read_prediction(LOCATION)
    print("Prediction File Loaded!\n")

    Driver = input("Enter Drivers (Rank): ").split()
    pos = [i for i in range(1,len(Driver)+1)]
    file = get_post_position_calc_error(df,Driver,pos,LOCATION)

    error = calculate_error(file)
    print(f"The Average Error: {error}")

    print("\nScript Execution Complete!")


    
