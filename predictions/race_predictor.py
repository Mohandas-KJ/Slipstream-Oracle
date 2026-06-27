import joblib
import pandas as pd

model = joblib.load("models/random_forest.pkl")

df = pd.read_csv(
    "predictions/austria_2026_features.csv"
)

FEATURES = [
    "QualiPosition",
    "GridPosition",
    "AvgFinishLast3",
    "AvgFinishLast5",
    "AvgGridLast3",
    "AvgGridLast5",
    "AvgPointsLast3",
    "AvgPointsLast5",
]

df["PredictedFinish"] = model.predict(df[FEATURES]).round(2)

df = df.sort_values("PredictedFinish").reset_index(drop=True)

df["PredictedPosition"] = range(
    1,
    len(df) + 1
)

print(df[[
    "PredictedPosition",
    "Driver",
    "PredictedFinish"
]])