import os
from pathlib import Path

import fastf1
import pandas as pd

# =========================
# CONFIG
# =========================

YEARS = [2022, 2023, 2024, 2025, 2026]

DATA_DIR = Path("data")

# Enable FastF1 cache
fastf1.Cache.enable_cache("cache")

# =========================
# COLLECT
# =========================

for year in YEARS:

    print(f"\n{'='*60}")
    print(f"Collecting {year}")
    print(f"{'='*60}")

    try:
        schedule = fastf1.get_event_schedule(year)

    except Exception as e:
        print(f"Failed to load schedule for {year}: {e}")
        continue

    for _, event in schedule.iterrows():

        gp_name = (
            str(event["EventName"])
            .replace("/", "-")
            .replace(" ", "_")
        )

        gp_folder = DATA_DIR / str(year) / gp_name
        gp_folder.mkdir(parents=True, exist_ok=True)

        print(f"\n{year} - {gp_name}")

        # ======================================
        # QUALIFYING
        # ======================================

        try:

            q_session = fastf1.get_session(
                year,
                event["RoundNumber"],
                "Q"
            )

            q_session.load()

            q_session.results.to_csv(
                gp_folder / "qualifying_results.csv",
                index=False
            )

            print("Qualifying Done")

        except Exception as e:

            print(f"Qualifying Error: {e}")

        # ======================================
        # RACE
        # ======================================

        try:

            race_session = fastf1.get_session(
                year,
                event["RoundNumber"],
                "R"
            )

            race_session.load()

            race_session.results.to_csv(
                gp_folder / "race_results.csv",
                index=False
            )

            race_session.laps.to_csv(
                gp_folder / "race_laps.csv",
                index=False
            )

            print("Race Done")

        except Exception as e:

            print(f"Race Error: {e}")

print("\nData collection complete!")