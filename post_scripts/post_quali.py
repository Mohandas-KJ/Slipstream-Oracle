# Imports
import pandas as pd

# Read the dataset
df = pd.read_csv("outputs/austria_2026_predict.csv")

# Function to add
def add_grid(data,drivers,position):

    user = pd.DataFrame({"Driver": drivers,
            "Position": position})
    
    df1 = data.copy()
   
    for d in user["Driver"]:
        pos = user.loc[user["Driver"] == d, "Position"].iloc[0]

        df1.loc[df1["Driver"] == d, "QualiPosition"] = pos
        df1.loc[df1["Driver"] == d, "GridPosition"] = pos

    df1 = df1.sort_values(by="GridPosition",ascending=True).reset_index(drop=True)
    
    df1.to_csv("outputs/austria.csv",index=False)
    print("CSV Exported Successfully!")

# Example: VER RUS HAM ...
d = input("Enter Drivers (GRID): ")
pos = [i for i in range(1,len(d)+1)]

add_grid(df,d,pos)