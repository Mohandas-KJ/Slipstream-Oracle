import os
import sys
import time
from pathlib import Path

import fastf1

# ============================================================
# CONFIG
# ============================================================

YEARS     = [2022, 2023, 2024, 2025, 2026]
DATA_DIR  = Path("data")
CACHE_DIR = "cache"

# Delay between API calls (seconds).
# 500 calls/h  →  1 call per 7.2 s  →  use 8 s to stay safely under.
# Raise to 10-12 if you still hit 429/500 errors.
API_DELAY = 8

# ============================================================
# HELPERS
# ============================================================

def log(msg: str, tag: str = "INFO") -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{tag:5s}] {msg}", flush=True)


def already_done(gp_folder: Path, session_id: str) -> bool:
    """Return True if all expected output files already exist on disk."""
    if session_id == "Q":
        return (gp_folder / "qualifying_results.csv").exists()
    if session_id == "R":
        return (
            (gp_folder / "race_results.csv").exists()
            and (gp_folder / "race_laps.csv").exists()
        )
    return False


def fetch_session(
    year:       int,
    round_num:  int,
    gp_name:    str,
    session_id: str,
    gp_folder:  Path,
) -> bool:
    """Download one session and write CSVs. Returns True on success."""

    label = f"{year} {gp_name} [{session_id}]"

    # ── RESUME: skip if already on disk ─────────────────────
    if already_done(gp_folder, session_id):
        log(f"SKIP  {label}  (already downloaded)", tag="SKIP")
        return True

    try:
        session = fastf1.get_session(year, round_num, session_id)

        if session_id == "Q":
            session.load(laps=False, telemetry=False, weather=False, messages=False)
            session.results.to_csv(gp_folder / "qualifying_results.csv", index=False)

        elif session_id == "R":
            session.load(telemetry=False, weather=False, messages=False)
            session.results.to_csv(gp_folder / "race_results.csv", index=False)
            session.laps.to_csv(gp_folder / "race_laps.csv",       index=False)

        log(f"OK    {label}", tag="OK")
        return True

    except Exception as exc:
        log(f"FAIL  {label}  →  {exc}", tag="FAIL")
        return False

# ============================================================
# MAIN  (single-threaded, rate-limited, resumable)
# ============================================================

def main() -> None:

    fastf1.Cache.enable_cache(CACHE_DIR)

    log(f"Output dir : {DATA_DIR.resolve()}")
    log(f"API delay  : {API_DELAY}s between calls  (~{3600 // API_DELAY} calls/h)")
    log("Tip: re-run anytime — already-downloaded sessions are skipped.")
    print()

    total = ok = skipped = failed = 0
    t_start = time.time()

    for year in YEARS:

        log(f"{'='*55}")
        log(f"Year: {year}")
        log(f"{'='*55}")

        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
        except Exception as exc:
            log(f"Could not load schedule for {year}: {exc}", tag="WARN")
            continue

        for _, event in schedule.iterrows():

            gp_name = (
                str(event["EventName"])
                .replace("/", "-")
                .replace(" ", "_")
            )
            round_num = int(event["RoundNumber"])
            gp_folder = DATA_DIR / str(year) / gp_name
            gp_folder.mkdir(parents=True, exist_ok=True)

            for session_id in ("Q", "R"):

                total += 1

                # Skip check (no API call needed)
                if already_done(gp_folder, session_id):
                    log(
                        f"SKIP  {year} {gp_name} [{session_id}]  (already downloaded)",
                        tag="SKIP",
                    )
                    skipped += 1
                    ok += 1
                    continue

                # Fetch (with rate-limit delay)
                success = fetch_session(year, round_num, gp_name, session_id, gp_folder)

                if success:
                    ok += 1
                else:
                    failed += 1

                # Rate-limit pause — only after an actual API call
                remaining = total - ok - failed + skipped  # rough sessions left
                log(
                    f"  → waiting {API_DELAY}s  "
                    f"[done {ok}/{total}  |  failed {failed}  |  left ~{total - ok - failed + skipped}]"
                )
                time.sleep(API_DELAY)

    # ── summary ─────────────────────────────────────────────
    elapsed = time.time() - t_start
    mins, secs = divmod(int(elapsed), 60)
    print()
    log(f"Finished in {mins}m {secs}s")
    log(f"✓ {ok} succeeded  (of which {skipped} skipped/already done)")
    log(f"✗ {failed} failed")
    log(f"Total: {total} sessions")

    if failed:
        log("Re-run the script to retry failed sessions — successes won't be re-downloaded.", tag="TIP")


if __name__ == "__main__":
    main()