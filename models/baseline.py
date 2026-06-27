# Imports 
import pandas as pd

# Import Data
df = pd.read_csv("outputs/oracle_v2.csv")

def baseline_1(data):

    new_df = data[["Year","RoundNumber","Race","Driver","Team"]]
    new_df["Predicted"] = data["AvgFinishLast3"]
    new_df["Actual"] = data["TargetFinish"]
    new_df["Actual"] = pd.to_numeric(new_df["Actual"], errors="coerce")
    new_df["Error"] = abs(new_df["Predicted"] - new_df["Actual"])

    return new_df

new_data = baseline_1(df)
new_data.to_csv("outputs/baseline_prediction.csv",index=False)