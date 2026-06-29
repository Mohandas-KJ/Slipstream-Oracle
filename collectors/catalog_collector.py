"""
This File is used to collect and store the Complete Round Map 
and other Schedule related Files
1. It gets an year from the user and creates a DIR
2. Gets the RoundNumber and EventName from fastf1 API
3. Saves it as .csv file
4. Consists of a json file to track the GP status
"""

# Imports
import fastf1,os
import pandas as pd
from pathlib import Path

CORE_PATH = "catalog"

def create_dir(year):

    #make complete path
    path_dir = Path(CORE_PATH) / str(2026)
    
    if not path_dir.exists():
        print("Catalog Folder not found! Creating......")
        path_dir.mkdir(parents=True)
        print("Catalog Folder Created!")
    else:
        print("Catalog Folder Exits!")
