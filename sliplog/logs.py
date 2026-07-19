# Imports
from datetime import datetime

# Code for Logging
def write(txt):
    with open("Logs/Sliplog.log","a",encoding="utf-8") as logf:
        logf.write(f"[{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}] - {txt}\n")