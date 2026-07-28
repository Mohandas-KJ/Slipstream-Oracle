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

def run_training_prediction():
    print("\nModel Ready to Run....\n")
    
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