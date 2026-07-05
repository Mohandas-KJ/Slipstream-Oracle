import pandas as pd 

# Get EvenNumber
def get_eventname(evnt_no):
    # Read CSV
    df = pd.read_csv("catalog/Schedule.csv")

    # Return name
    return df[df["RoundNumber" == evnt_no, "EventName"]].iloc[0]