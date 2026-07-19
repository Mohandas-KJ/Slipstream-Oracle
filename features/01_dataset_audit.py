import sys,os
from pathlib import Path
from sliplog import logs

import fastf1
import pandas as pd

# ============================================================
# CONFIG  (must match data_collector.py)
# ============================================================

YEARS     = [2022, 2023, 2024, 2025, 2026]
DATA_DIR  = Path("data")
CACHE_DIR = "cache"

# Files expected per GP and minimum row count to be "valid"
EXPECTED_FILES = {
    "Q": {
        "qualifying_results.csv": 1,   # at least 1 driver row
    },
    "R": {
        "race_results.csv": 1,
        "race_laps.csv":    1,
    },
}

# ============================================================
# HELPERS
# ============================================================

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg):   print(f"  {RED}✗{RESET}  {msg}")
def head(msg):  print(f"\n{BOLD}{CYAN}{msg}{RESET}")


def check_csv(path: Path, min_rows: int) -> str:
    """
    Returns:
        'ok'      – file exists and has enough rows
        'empty'   – file exists but only has headers (0 data rows)
        'missing' – file does not exist
    """
    if not path.exists():
        return "missing"
    try:
        df = pd.read_csv(path)
        if len(df) < min_rows:
            return "empty"
        return "ok"
    except Exception:
        return "empty"   # unreadable / corrupt → treat as empty


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    fastf1.Cache.enable_cache(CACHE_DIR)

    issues: list[str] = []   # collects every problem for the final summary

    total_gps      = 0
    total_files    = 0
    ok_files       = 0
    missing_files  = 0
    empty_files    = 0

    for year in YEARS:

        head(f"  {year}  {'─'*50}")

        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
        except Exception as exc:
            warn(f"Could not load schedule for {year}: {exc}")
            issues.append(f"[{year}] Schedule unavailable: {exc}")
            continue

        for _, event in schedule.iterrows():

            gp_name = (
                str(event["EventName"])
                .replace("/", "-")
                .replace(" ", "_")
            )
            gp_folder = DATA_DIR / str(year) / gp_name
            total_gps += 1

            gp_ok    = True
            gp_lines = []

            for session_id, files in EXPECTED_FILES.items():
                for filename, min_rows in files.items():
                    total_files += 1
                    path   = gp_folder / filename
                    status = check_csv(path, min_rows)

                    if status == "ok":
                        ok_files += 1
                        gp_lines.append(("ok", f"{session_id} / {filename}"))
                    elif status == "empty":
                        empty_files += 1
                        gp_ok = False
                        gp_lines.append(("empty", f"{session_id} / {filename}  ← headers only / no data"))
                        issues.append(f"[{year}] {gp_name}  →  {session_id}/{filename}  (empty)")
                    else:  # missing
                        missing_files += 1
                        gp_ok = False
                        gp_lines.append(("missing", f"{session_id} / {filename}  ← FILE MISSING"))
                        issues.append(f"[{year}] {gp_name}  →  {session_id}/{filename}  (missing)")

            # Print GP block only if there are problems (keeps output clean)
            if not gp_ok:
                print(f"\n  {BOLD}{gp_name}{RESET}")
                for status, line in gp_lines:
                    if status == "ok":
                        ok(line)
                    elif status == "empty":
                        warn(line)
                    else:
                        err(line)

    # ============================================================
    # SUMMARY
    # ============================================================

    print(f"\n{'═'*60}")
    print(f"{BOLD}  SUMMARY{RESET}")
    print(f"{'═'*60}")
    print(f"  GPs checked   : {total_gps}")
    print(f"  Files checked : {total_files}")
    print(f"  {GREEN}✓ OK          : {ok_files}{RESET}")
    print(f"  {YELLOW}⚠ Empty       : {empty_files}{RESET}")
    print(f"  {RED}✗ Missing     : {missing_files}{RESET}")

    if not issues:
        print(f"\n  {GREEN}{BOLD}All data is complete. Nothing to re-download.{RESET}")
    else:
        print(f"\n  {BOLD}Issues to fix ({len(issues)} total):{RESET}")
        for issue in issues:
            print(f"    {RED}•{RESET} {issue}")
        print(f"\n  {YELLOW}Tip: Re-run data_collector.py — it will skip files that are OK{RESET}")
        print(f"  {YELLOW}     and only re-fetch the ones listed above.{RESET}")   

    logs.write("Run Data Audit")

    print()
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()