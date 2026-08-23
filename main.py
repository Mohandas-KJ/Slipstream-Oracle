"""
Main File!
Executes all files in 2 Phases
PHASES:
1. Prediction Phase
2. Post Race and Evaluation phase

FLOW:
1. Define Needed Folders
2. Check Whether they exist
3. Display the Current GP Name and Round Number
4. Ask whether to continue further
5. If no, reconfigure
6. If yes, proceed further
"""

# Imports
import subprocess,sys
from Generals import streamlib
from pathlib import Path

collectors = Path("collectors")
features = Path("features")
models = Path("models")
post_scripts = Path("post_scripts")
predictions = Path("predictions")

def banner():
    print("""
 ████ █     ███ ████   ████ █████ ████  █████  ███  █   █     ███  ████   ███   ███  █     █████ 
█     █      █  █   █ █       █   █   █ █     █   █ ██ ██    █   █ █   █ █   █ █     █     █     
 ███  █      █  ████   ███    █   ████  ████  █████ █ █ █    █   █ ████  █████ █     █     ████  
    █ █      █  █         █   █   █  █  █     █   █ █   █    █   █ █  █  █   █ █     █     █     
████  █████ ███ █     ████    █   █   █ █████ █   █ █   █     ███  █   █ █   █  ███  █████ █████    v1.0
""")

def validate_folders() -> bool:
    if collectors.exists() and features.exists() and models.exists() and post_scripts.exists() and predictions.exists():
        print(
            "\nScripts Loaded:\n\ncollectors/\n"
            + "\n".join(f"├── {a.name}" for a in collectors.glob("*.py"))
            + "\n"
        )

        print("features/\n"
            + "\n".join(f"├── {a.name}" for a in features.glob("*.py"))
            + "\n"
        )

        print("models/\n"
            + "\n".join(f"├── {a.name}" for a in models.glob("*.py"))
            + "\n"
        )

        print("post_scripts/\n"
            + "\n".join(f"├── {a.name}" for a in post_scripts.glob("*.py"))
            + "\n"
        )

        print("predictions/\n"
            + "\n".join(f"├── {a.name}" for a in predictions.glob("*.py"))
            + "\n"
        )

        return True

    return False

def display_event() -> bool:
    eve_no = streamlib.get_current_gp_no()
    print(f"CURRENT EVENT DETAILS:\nRound Number: {eve_no}\nRound Name: {streamlib.get_eventname(eve_no)}\n")

    if input("Want to Proceed to next Phase? [y/n]: ").lower() == "y":
        return True

    return False

# spl-cl: collect_driver_changes — interactive prompt for lineup changes before dataset build
def collect_driver_changes() -> dict:
    """
    Ask the user if there are any driver lineup changes for this GP.
    Returns a dict:
        {
            "add":    [{"Driver": "TSU", "Team": "Racing Bulls"}, ...],
            "remove": ["HAD", ...]
        }
    If no changes, returns {"add": [], "remove": []}.
    """
    changes = {"add": [], "remove": []}

    print("\n── Driver Lineup Changes ─────────────────────────────")
    # spl-cl: ask once upfront — skip entire block if no changes
    if input("Any driver changes for this GP? [y/n]: ").strip().lower() != "y":
        print("  No changes. Continuing with default lineup.\n")
        return changes

    # spl-cl: collect drivers to REMOVE (injured / absent / replaced)
    print("\nDrivers to REMOVE from this GP (e.g. HAD, BEA)")
    print("Enter codes one per line. Empty line to finish:")
    while True:
        code = input("  Remove > ").strip().upper()
        if not code:
            break
        changes["remove"].append(code)
        print(f"  ✗  {code} marked for removal")

    # spl-cl: collect drivers to ADD (reserve / replacement entries)
    print("\nDrivers to ADD for this GP (reserve / replacement)")
    print("Enter code and team. Empty driver code to finish:")
    while True:
        code = input("  Driver code > ").strip().upper()
        if not code:
            break
        team = input(f"  Team for {code} > ").strip()
        changes["add"].append({"Driver": code, "Team": team})
        print(f"  ★  {code} ({team}) marked for addition")

    # spl-cl: confirm summary before proceeding
    print(f"\n  Summary → Remove: {changes['remove']}  |  Add: {[d['Driver'] for d in changes['add']]}")
    return changes
# spl-cl: end collect_driver_changes


def run_training_prediction():
    print("\nModel Ready to Run....\n")

    # spl-cl: collect lineup changes here — passed via env to 04_build_prediction_feature.py
    import json, os
    driver_changes = collect_driver_changes()
    # spl-cl: serialize changes to env var so subprocess can read without a temp file
    os.environ["SLIP_DRIVER_CHANGES"] = json.dumps(driver_changes)

    subprocess.run([sys.executable, features / "02_build_training_dataset.py"],check=True)
    print()
    subprocess.run([sys.executable, features / "03_building_feature.py"],check=True)
    print()
    subprocess.run([sys.executable, features / "04_build_prediction_feature.py"],check=True)
    
    print("\nRunning Model Training.....\n")
    
    subprocess.run([sys.executable, models / "Random_Forest.py"],check=True)
    
    print("\nRunning Post Quali scenario....")

    if input("Grid Data available? [y/n]").lower() == "y":
        subprocess.run([sys.executable, post_scripts / "post_quali.py"],check=True)
        print("\nLoading Prediction Model!\n")
        subprocess.run([sys.executable, predictions / "race_predictor.py"],check=True)

def run_validation():
    print("\nRunning Validation Phase.....\n")
    subprocess.run([sys.executable, post_scripts / "post_race.py"],check=True)
    print()
    print("Validation Completed!")

def choice_chooser():
    print("\nChoose One:\n1. Slipstream Prediction\n2. Slipstream Validation (post-race)\n")

    usr = int(input("$ "))

    if usr == 1:
        print("\nPrediction Phase Selected")
        return 1
    elif usr == 2:
        print("\nValidation Phase Selected")
        return 2
    else:
        print("Invalid Option!")
        exit(-1)

def main():
    banner()

    if validate_folders():
        print("\nValidation Successful!\n")

    if display_event():
        if choice_chooser() == 1:
            run_training_prediction()
        else:
            run_validation()
    else:
        print("Operation Cancelled by user.....\nShutdown Complete!")

if __name__ == "__main__":
    main()