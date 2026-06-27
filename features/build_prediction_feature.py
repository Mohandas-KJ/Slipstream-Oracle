"""
Build prediction features for the NEXT race.

Example:
Latest race completed = Spain 2026
Next race             = Austria 2026

Output:
predictions/austria_2026_features.csv
"""

from pathlib import Path
import pandas as pd


INPUT = Path("outputs/oracle_v2.csv")
OUTPUT = Path("predictions/austria_2026_features.csv")


FEATURES = [
    "QualiPosition",
    "GridPosition",
    "AvgFinishLast3",
    "AvgFinishLast5",
    "AvgGridLast3",
    "AvgGridLast5",
    "AvgGridLast3",
    "AvgGridLast5",
    "AvgPointsLast3",
    "AvgPointsLast5",
]


def main():

    df = pd.read_csv(INPUT)

    # --------------------------------------------------
    # Find the latest completed race
    # --------------------------------------------------

    latest_year = df["Year"].max()

    latest_round = (
        df[df["Year"] == latest_year]["RoundNumber"]
        .max()
    )

    latest = df[
        (df["Year"] == latest_year) &
        (df["RoundNumber"] == latest_round)
    ].copy()

    # --------------------------------------------------
    # Keep only information available BEFORE next race
    # --------------------------------------------------

    prediction = latest[
        [
            "Driver",
            "Team",
            *FEATURES
        ]
    ].copy()

    # remove duplicates if any
    prediction = prediction.drop_duplicates(
        subset="Driver"
    )

    prediction = prediction.sort_values(
        "Driver"
    ).reset_index(drop=True)

    OUTPUT.parent.mkdir(exist_ok=True)

    prediction.to_csv(
        OUTPUT,
        index=False
    )

    print()

    print("=" * 60)
    print("SLIPSTREAM ORACLE")
    print("=" * 60)

    print(
        f"Latest completed race : {latest_year} Round {latest_round}"
    )

    print(
        f"Drivers               : {len(prediction)}"
    )

    print()

    print(prediction)

    print()

    print(
        f"Saved to:\n{OUTPUT}"
    )


if __name__ == "__main__":
    main()