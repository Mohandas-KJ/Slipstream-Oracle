# Imports
from datetime import datetime
from Generals import streamlib

# Code for Logging
def write(txt):
    cur_gp = streamlib.get_current_gp_no()
    with open("Logs/Sliplog.log","a",encoding="utf-8") as logf:
        logf.write(f"[{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}][{cur_gp} - {streamlib.get_eventname(cur_gp)}] - {txt}\n")