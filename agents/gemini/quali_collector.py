"""
Slipstream Oracle — Realtime Qualifying & Starting Grid Collector (Gemini Agent)
================================================================================
Communicates with Google AI Studio's latest Gemini Flash model to retrieve:
1. Currently ongoing Formula 1 Grand Prix, Round Number, and Qualifying Status.
2. User verification/approval of event details.
3. Official Qualifying results (QualiPosition) and Final Starting Grid with FIA
   penalties applied (GridPosition).
4. A follow-up verification prompt to confirm all penalty cascades and return a
   finalized pandas DataFrame matching the required reference structure:
       Attributes: ["QualiPosition", "GridPosition"] (along with Driver & Team)

Note: This module ONLY returns the DataFrame in-memory. It does NOT save or write
any CSV files to disk, keeping it decoupled and ready for integration into main.py.
"""

import os
import re
import json
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Base paths
AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent.parent
ENV_FILE = AGENT_DIR / ".env"

DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


# ==============================================================================
# CONFIG & ENVIRONMENT LOADER
# ==============================================================================

def load_gemini_config() -> Tuple[str, str]:
    """
    Loads GEMINI_API_KEY and GEMINI_MODEL from agents/gemini/.env or environment.
    Returns:
        (api_key, model_name)
    Raises:
        ValueError if GEMINI_API_KEY is missing or empty.
    """
    env_vars: Dict[str, str] = {}

    # Read from agents/gemini/.env if it exists
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    env_vars[k] = v

    # Fallback to os.environ or root .env
    api_key = (
        env_vars.get("GEMINI_API_KEY")
        or env_vars.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    )

    model = (
        env_vars.get("GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or DEFAULT_MODEL
    )

    if not api_key:
        raise ValueError(
            "\n[Slipstream Oracle — Gemini Agent] Missing API Key!\n"
            f"Please insert your Google AI Studio API key into '{ENV_FILE}':\n"
            "    GEMINI_API_KEY=your_actual_key_here\n"
            "You can generate a free key at: https://aistudio.google.com/\n"
        )

    return api_key, model


# ==============================================================================
# GOOGLE AI STUDIO API CLIENT
# ==============================================================================

def call_gemini_api(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    use_grounding: bool = True,
    system_instruction: Optional[str] = None
) -> str:
    """
    Sends a prompt to Google AI Studio's Gemini Flash model via REST API.
    Supports Google Search grounding for realtime F1 session data and
    automatically retries candidate models if needed.
    """
    # Build candidate model list with specified model first
    candidate_models = [model] + [m for m in FALLBACK_MODELS if m != model]

    last_error = None

    for candidate in candidate_models:
        url = GEMINI_API_URL.format(model=candidate) + f"?key={api_key}"
        headers = {"Content-Type": "application/json"}

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Attempt first with Google Search grounding tool for realtime data
        if use_grounding:
            payload["tools"] = [{"googleSearch": {}}]

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)

            # If search grounding fails (e.g. 400 Bad Request on certain model/tier), retry without tools
            if resp.status_code == 400 and use_grounding:
                payload.pop("tools", None)
                resp = requests.post(url, headers=headers, json=payload, timeout=45)

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    text_parts = [p.get("text", "") for p in parts if "text" in p]
                    full_text = "".join(text_parts).strip()
                    if full_text:
                        return full_text
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text}"
                # If model not found (404), continue to next candidate model
                if resp.status_code == 404:
                    continue

        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(
        f"[Slipstream Oracle — Gemini Agent] Failed to communicate with Google AI Studio: {last_error}"
    )


def extract_json_payload(response_text: str) -> Any:
    """
    Extracts and parses JSON object or array from model response text,
    handling markdown codeblocks or plain text gracefully.
    """
    text = response_text.strip()

    # 1. Direct JSON parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Extract from ```json ... ``` or ``` ... ```
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except Exception:
            pass

    # 3. Extract bracketed array [...]
    match_arr = re.search(r"(\[[\s\S]*\])", text)
    if match_arr:
        try:
            return json.loads(match_arr.group(1).strip())
        except Exception:
            pass

    # 4. Extract bracketed object {...}
    match_obj = re.search(r"(\{[\s\S]*\})", text)
    if match_obj:
        try:
            return json.loads(match_obj.group(1).strip())
        except Exception:
            pass

    raise ValueError(
        f"Unable to parse structured JSON from Gemini response:\n{response_text[:300]}..."
    )


# ==============================================================================
# PHASE 1: RETRIEVE ONGOING GP, ROUND NUMBER, AND QUALI STATUS
# ==============================================================================

def get_current_gp_status(api_key: str, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """
    Prompts the Gemini Flash model to identify the currently ongoing or latest
    Formula 1 Grand Prix, its Round Number, and whether Qualifying has concluded.
    """
    # Context helper from catalog if available
    calendar_hint = ""
    try:
        schedule_file = PROJECT_ROOT / "catalog" / "2026" / "Schedule.csv"
        completed_file = PROJECT_ROOT / "catalog" / "2026" / "completed.json"
        if schedule_file.exists() and completed_file.exists():
            with open(completed_file, "r") as cf:
                completed = json.load(cf)
            next_round = max(completed.values()) + 1
            sched_df = pd.read_csv(schedule_file)
            event_row = sched_df[sched_df["RoundNumber"] == next_round]
            if not event_row.empty:
                calendar_hint = f"(Project Calendar Context: Round {next_round} is scheduled as {event_row['EventName'].iloc[0]})"
    except Exception:
        pass

    prompt = f"""
You are the Formula 1 Realtime Data Agent for Slipstream Oracle.
Search the latest official Formula 1 calendar, live race control telemetry, and official session news {calendar_hint}.

Determine:
1. The currently ongoing or most recent Formula 1 Grand Prix name.
2. The official FIA Round Number for this Grand Prix in the season.
3. The Qualifying session status: whether Qualifying is finished, currently in progress, or scheduled/not started.
4. A brief 1-2 sentence description of circuit location and session date.

Return ONLY a valid JSON object matching this schema:
```json
{{
  "gp_name": "Official Grand Prix Name",
  "round_number": 18,
  "quali_status": "Finished",
  "is_finished": true,
  "details": "Qualifying concluded at Circuit of the Americas. Starting grid finalized."
}}
```
"""

    system_instruction = (
        "You are an expert Formula 1 telemetry analyst. "
        "Retrieve live, accurate, real-time Grand Prix and session status data. "
        "Always respond in valid structured JSON."
    )

    response = call_gemini_api(
        prompt=prompt,
        api_key=api_key,
        model=model,
        use_grounding=True,
        system_instruction=system_instruction
    )

    data = extract_json_payload(response)
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    return {
        "gp_name": data.get("gp_name", "Unknown Grand Prix"),
        "round_number": int(data.get("round_number", 0)),
        "quali_status": data.get("quali_status", "Unknown"),
        "is_finished": bool(data.get("is_finished", False) or "finish" in str(data.get("quali_status", "")).lower()),
        "details": data.get("details", "")
    }


# ==============================================================================
# PHASE 2: RETRIEVE QUALIFYING & PENALTY-INCLUDED STARTING GRID DATAFRAME
# ==============================================================================

def get_penalty_finalized_dataframe(
    gp_name: str,
    round_number: int,
    api_key: str,
    model: str = DEFAULT_MODEL
) -> pd.DataFrame:
    """
    Prompts Gemini Flash for the full qualifying results and starting grid.
    Sends a follow-up verification prompt to ensure all FIA penalties (grid drops,
    gearbox/PU penalties, pit lane starts) are finalized, returning a DataFrame
    with the exact attributes: ["QualiPosition", "GridPosition"] (plus Driver, Team).
    """
    # Lineup reference if available in catalog
    lineup_hint = ""
    try:
        lineup_path = PROJECT_ROOT / "catalog" / "2026" / "Lineup.csv"
        if lineup_path.exists():
            lineup_df = pd.read_csv(lineup_path)
            codes = ", ".join(lineup_df["Driver"].tolist())
            lineup_hint = f"Reference Driver Codes: {codes}."
    except Exception:
        pass

    # Prompt 1: Initial Qualifying classification and grid retrieval
    step1_prompt = f"""
You are the Formula 1 Realtime Data Agent for Slipstream Oracle.
Target Event: {gp_name} (Round {round_number}).
{lineup_hint}

Retrieve the complete official Qualifying classification and Starting Grid for all 20 to 22 participating drivers.

You MUST provide:
1. 'QualiPosition': The exact qualified position achieved in the Saturday qualifying session (Q1/Q2/Q3) before any penalties.
2. 'GridPosition': The final official starting grid position for the race after applying ALL FIA grid penalties (engine changes, gearbox changes, driving reprimands, pit lane starts).
3. 'Driver': 3-letter driver code (e.g. VER, NOR, LEC, HAM, RUS, PIA, ANT, SAI, ALB, ALO, etc.).
4. 'Team': Constructor name.

Output MUST be a JSON array of objects:
[
  {{
    "Driver": "VER",
    "Team": "Red Bull Racing",
    "QualiPosition": 1,
    "GridPosition": 1
  }},
  ...
]
"""

    system_instruction = (
        "You are an official FIA race control data specialist. "
        "Provide complete, exact Formula 1 starting grid and qualifying classification tables. "
        "Strictly adhere to the requested JSON schema."
    )

    print(f"  [1/2] Fetching Qualifying Classification & Grid for {gp_name} ...")
    step1_response = call_gemini_api(
        prompt=step1_prompt,
        api_key=api_key,
        model=model,
        use_grounding=True,
        system_instruction=system_instruction
    )

    initial_grid = extract_json_payload(step1_response)

    # Prompt 2: Verification and penalty finalization prompt
    step2_prompt = f"""
Verify and finalize the following Starting Grid dataset for the {gp_name} (Round {round_number}):

{json.dumps(initial_grid, indent=2)}

Check all official FIA Stewards Decision documents and Starting Grid publications:
1. Confirm that ALL grid penalties (e.g. 5-place, 10-place, back of grid, pit-lane starts) are strictly cascaded so there are no duplicate or missing GridPosition numbers.
2. Ensure 'QualiPosition' remains the exact pre-penalty qualifying session result.
3. Ensure 'GridPosition' reflects the final, official starting order.
4. Output must be a finalized JSON array with exact keys:
   ["Driver", "Team", "QualiPosition", "GridPosition"]

Return ONLY the finalized JSON array.
"""

    print("  [2/2] Finalizing and verifying FIA penalties & starting grid positions ...")
    step2_response = call_gemini_api(
        prompt=step2_prompt,
        api_key=api_key,
        model=model,
        use_grounding=True,
        system_instruction=system_instruction
    )

    final_grid_data = extract_json_payload(step2_response)

    if not isinstance(final_grid_data, list) or len(final_grid_data) == 0:
        raise ValueError("Model failed to produce a valid list of driver grid entries.")

    df = pd.DataFrame(final_grid_data)

    # Validate required columns
    required_cols = ["QualiPosition", "GridPosition"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(
                f"Missing required attribute '{col}' in model response. Columns found: {list(df.columns)}"
            )

    # Normalize numeric columns
    df["QualiPosition"] = pd.to_numeric(df["QualiPosition"], errors="coerce")
    df["GridPosition"] = pd.to_numeric(df["GridPosition"], errors="coerce")

    # Sort sequentially by final starting grid position
    df = df.sort_values("GridPosition", ascending=True).reset_index(drop=True)

    return df


# ============================================================
# DISPLAY HELPER (MATCHING POST_QUALI.PY FORMAT)
# ============================================================

def display_grid_table(df: pd.DataFrame, gp_name: str) -> None:
    """Prints a styled F1 starting grid table for terminal verification."""
    print()
    print(f"  ╔{'═'*58}╗")
    title = f"STARTING GRID — {gp_name.upper()}"
    print(f"  ║{title:^58}║")
    print(f"  ╠{'═'*58}╣")
    print(f"  │  {'P':<4} {'Driver':<8} {'Team':<22} {'Quali':>6} {'Grid':>6}  │")
    print(f"  ├{'─'*58}┤")

    for _, row in df.iterrows():
        q = row.get("QualiPosition")
        g = row.get("GridPosition")
        driver = str(row.get("Driver", ""))
        team = str(row.get("Team", ""))[:22]

        try:
            delta = int(g - q)
            penalty_flag = f" ▼{delta:+d}" if delta != 0 else "    "
        except Exception:
            penalty_flag = "    "

        q_str = f"{int(q)}" if pd.notna(q) else "—"
        g_str = f"{int(g)}" if pd.notna(g) else "—"

        print(f"  │  {g_str:<4} {driver:<8} {team:<22} {q_str:>6} {g_str:>6} {penalty_flag}│")

    print(f"  ╚{'═'*58}╝")
    print()


# ==============================================================================
# MAIN COLLECTOR INTERFACE
# ==============================================================================

def collect_realtime_quali_data(auto_approve: bool = False) -> Optional[pd.DataFrame]:
    """
    Main interactive function:
    1. Loads Gemini API configuration from .env.
    2. Queries Gemini to detect the current ongoing Grand Prix and Qualifying status.
    3. Prompts user to approve/confirm the detected event.
    4. Upon approval, retrieves the finalized qualifying and penalty-included
       starting grid DataFrame with attributes ['QualiPosition', 'GridPosition'].
    5. Returns the DataFrame in-memory (does not create or write any CSV files).
    """
    print("\n" + "═" * 60)
    print("  SLIPSTREAM ORACLE — REALTIME QUALI AGENT (GEMINI)")
    print("═" * 60)

    # 1. Load API Key
    api_key, model = load_gemini_config()
    print(f"  Connected to Google AI Studio (Model: {model})")
    print("  Querying currently ongoing Grand Prix status ...")

    # 2. Retrieve Ongoing GP Info
    gp_info = get_current_gp_status(api_key=api_key, model=model)

    gp_name = gp_info["gp_name"]
    round_no = gp_info["round_number"]
    status_str = gp_info["quali_status"]
    is_finished = gp_info["is_finished"]

    print("\n" + "─" * 60)
    print("  CURRENT EVENT DETAILS (DETECTED VIA GEMINI):")
    print(f"    Grand Prix Name   : {gp_name}")
    print(f"    Round Number      : {round_no}")
    print(f"    Qualifying Status : {status_str} ({'FINISHED' if is_finished else 'IN PROGRESS / PENDING'})")
    if gp_info.get("details"):
        print(f"    Details           : {gp_info['details']}")
    print("─" * 60 + "\n")

    # 3. User Approval
    if not auto_approve:
        approval = input("Is this ongoing Grand Prix information correct? [y/n]: ").strip().lower()
        if approval not in ("y", "yes"):
            print("\n  Automatic detection not approved.")
            override = input("  Would you like to manually enter GP Name & Round Number? [y/n]: ").strip().lower()
            if override in ("y", "yes"):
                gp_name = input("    Enter Grand Prix Name (e.g. Austrian Grand Prix): ").strip()
                round_no = int(input("    Enter Round Number (e.g. 8): ").strip())
            else:
                print("  Operation cancelled by user. Returning None.\n")
                return None

    # 4. Fetch and finalize penalty-included grid DataFrame
    df = get_penalty_finalized_dataframe(
        gp_name=gp_name,
        round_number=round_no,
        api_key=api_key,
        model=model
    )

    # Display final grid summary
    display_grid_table(df, gp_name)
    print(f"  ✓ Successfully assembled finalized DataFrame with {len(df)} drivers.")
    print("  ✓ Columns included:", list(df.columns))
    print("  ✓ In-memory DataFrame returned without creating external CSV files.\n")

    return df


if __name__ == "__main__":
    try:
        result_df = collect_realtime_quali_data()
        if result_df is not None:
            print("Preview of returned DataFrame:")
            print(result_df[["Driver", "QualiPosition", "GridPosition"]].head())
    except Exception as e:
        print(f"\n[Error] {e}")
