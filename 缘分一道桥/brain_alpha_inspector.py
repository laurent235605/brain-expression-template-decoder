"""Quick utilities for BRAIN OS alpha inspection.

Features:
- Login with email/password (supports persona detection).
- Fetch submitted OS alphas (optional top N).
- Pull operator list and parse each alpha expression into operators and datafields.
- Query datafield detail to list other available region/settings combinations.

Note: For convenience, a test credential is wired for ad-hoc runs. Override via
env vars `BRAIN_USERNAME` and `BRAIN_PASSWORD` in real use.
"""

from __future__ import annotations

import os
import re
import json
import getpass
import itertools
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple, Union
import time
import requests
import pandas as pd

try:
    from ace_lib import start_simulation, simulation_progress, get_instrument_type_region_delay
except ImportError as e:
    print(f"Warning: ace_lib.py not found or failed to import: {e}")
    start_simulation = None
    simulation_progress = None
    get_instrument_type_region_delay = None


BASE_URL = "https://api.worldquantbrain.com"


def brain_login(username: str, password: str, max_retries: int = 3) -> requests.Session:
    """Authenticate against BRAIN API and return a live session.

    Raises a RuntimeError if persona (biometric) auth is required so callers can
    surface the URL to users.
    """

    session = requests.Session()
    session.auth = (username, password)

    for attempt in range(1, max_retries + 1):
        response = session.post(f"{BASE_URL}/authentication")

        if response.status_code == requests.codes.unauthorized:
            if response.headers.get("WWW-Authenticate") == "persona":
                location = response.headers.get("Location", "")
                raise RuntimeError(
                    "Biometric authentication required. Complete it in browser: "
                    f"{location}"
                )
            raise RuntimeError("Invalid username or password.")

        try:
            response.raise_for_status()
            return session
        except requests.HTTPError as exc:  # pragma: no cover - network path
            if attempt >= max_retries:
                raise exc

    raise RuntimeError("Authentication failed after retries.")


def fetch_alphas_by_date_range(
    session: requests.Session, start_date: str, end_date: str
) -> List[Dict]:
    """Return submitted (OS) alphas within the date range (inclusive).

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
    """
    print(f"Fetching alphas from {start_date} to {end_date}...")
    
    # Ensure dates are comparable strings (ISO format works for string comparison)
    # Append time to make full comparison easy
    # User suggested format: 2025-11-01T04:00:00.000Z
    start_iso = f"{start_date}T00:00:00Z"
    end_iso = f"{end_date}T23:59:59Z"

    alphas: List[Dict] = []
    limit = 50
    offset = 0

    while True:
        # Use server-side filtering for performance
        params = {
            "stage": "OS",
            "order": "-dateSubmitted",
            "limit": limit,
            "offset": offset,
            "dateSubmitted>": start_iso,
            "dateSubmitted<": end_iso,
        }
        resp = session.get(f"{BASE_URL}/users/self/alphas", params=params)
        resp.raise_for_status()

        payload = resp.json()
        results = payload.get("results", []) if isinstance(payload, dict) else payload
        
        if not results:
            break

        alphas.extend(results)

        offset += limit
        total = payload.get("count", 0) if isinstance(payload, dict) else 0
        
        if offset >= total or len(results) < limit:
            break

    return alphas


def fetch_alphas_by_ids(
    session: requests.Session, alpha_ids: List[str]
) -> List[Dict]:
    """Return submitted (OS) alphas by their IDs.

    Args:
        alpha_ids: List of Alpha IDs.
    """
    print(f"Fetching {len(alpha_ids)} alphas by ID...")
    alphas: List[Dict] = []

    for alpha_id in alpha_ids:
        alpha_id = alpha_id.strip()
        if not alpha_id:
            continue
            
        try:
            resp = session.get(f"{BASE_URL}/alphas/{alpha_id}")
            resp.raise_for_status()
            alpha = resp.json()
            alphas.append(alpha)
        except Exception as e:
            print(f"Error fetching alpha {alpha_id}: {e}")
            continue

    return alphas


def fetch_operators(session: requests.Session) -> List[Dict]:
    """Fetch full operator catalog."""

    resp = session.get(f"{BASE_URL}/operators")
    resp.raise_for_status()
    operators = resp.json()
    return operators if isinstance(operators, list) else []


def _dedupe(seq: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _extract_expression(alpha: Dict) -> Optional[str]:
    """Pick the first available expression/code from an alpha payload."""

    for key in ("regular", "combo", "selection"):
        block = alpha.get(key)
        if isinstance(block, dict):
            expr = block.get("expression") or block.get("code")
            if isinstance(expr, str):
                return expr
    return None


def parse_expression(
    expression: str, operator_names: Sequence[str]
) -> Tuple[List[str], List[str]]:
    """Split an expression into operators and datafields using a token scan."""

    # Remove C-style comments /* ... */
    expression = re.sub(r"/\*[\s\S]*?\*/", "", expression)
    # Remove Python-style comments # ...
    expression = re.sub(r"#.*", "", expression)

    operator_set = set(operator_names)
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression)

    found_ops: List[str] = []
    found_fields: List[str] = []

    skip_tokens = {"if", "else", "true", "false", "nan", "inf"}

    for token in tokens:
        if token in skip_tokens:
            continue
        if token in operator_set:
            found_ops.append(token)
        else:
            found_fields.append(token)

    return _dedupe(found_ops), _dedupe(found_fields)


def analyze_alphas(
    alphas: Sequence[Dict], operators: Sequence[Dict]
) -> Dict[str, List[str]]:
    """Return combined operator and datafield lists for provided alphas."""

    operator_names = [op.get("name", "") for op in operators if isinstance(op, dict)]
    all_ops: List[str] = []
    all_fields: List[str] = []

    for alpha in alphas:
        expr = _extract_expression(alpha)
        if not expr:
            continue
        ops, fields = parse_expression(expr, operator_names)
        all_ops.extend(ops)
        all_fields.extend(fields)

    return {"operators": _dedupe(all_ops), "datafields": _dedupe(all_fields)}


def get_datafield_availability(
    session: requests.Session,
    field_name: str,
    instrument_type: str = "EQUITY",
    region: str = "USA",
    delay: int = 1,
    universe: str = "TOP3000",
) -> Dict[str, List[Dict]]:
    """Fetch detail for a datafield and summarize other available settings."""

    params = {
        "instrumentType": instrument_type,
        "region": region,
        "delay": delay,
        "universe": universe,
    }
    time.sleep(2)  # To avoid hitting rate limits
    try:
        resp = session.get(f"{BASE_URL}/data-fields/{field_name}", params=params)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"detail": {}, "availability": [], "error": "Datafield not found"}
        raise e
    detail = resp.json()

    availability_candidates = []
    for key in (
        "availability",
        "availabilities",
        "availableSettings",
        "availabilityList",
        "regionAvailability",
        "settings",
        "data",
    ):
        value = detail.get(key)
        if isinstance(value, list):
            availability_candidates.extend(value)
        elif isinstance(value, dict):
            nested = value.get("availability") or value.get("items") or value.get("list")
            if isinstance(nested, list):
                availability_candidates.extend(nested)

    def _pick(d, keys):
        for k in keys:
            val = d.get(k)
            if val is not None:
                return val
        return None

    normalized = []
    for item in availability_candidates:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "instrumentType": _pick(item, ["instrumentType", "instrument_type"]) or instrument_type,
                "region": _pick(item, ["region", "regionCode"]),
                "delay": _pick(item, ["delay", "lag"]),
                "universe": _pick(item, ["universe", "universeName"]),
            }
        )

    # Deduplicate normalized combos.
    normalized = _dedupe(
        [json.dumps(x, sort_keys=True) for x in normalized if any(x.values())]
    )
    combos = [json.loads(x) for x in normalized]

    return {"detail": detail, "availability": combos}


def validate_setting(setting: Dict, options_df: Optional[pd.DataFrame]) -> bool:
    """Check if a setting combination is valid according to simulation options."""
    if options_df is None or options_df.empty:
        return True # Skip validation if options not available
        
    inst_type = setting.get("instrumentType", "EQUITY")
    region = setting.get("region")
    delay = setting.get("delay")
    universe = setting.get("universe")
    neutralization = setting.get("neutralization")
    
    try:
        delay = int(delay)
    except (ValueError, TypeError):
        pass

    # Iterate to find match
    for _, row in options_df.iterrows():
        row_inst = row.get('InstrumentType')
        row_region = row.get('Region')
        row_delay = row.get('Delay')
        
        try:
            row_delay = int(row_delay)
        except (ValueError, TypeError):
            pass
            
        if row_inst == inst_type and row_region == region and row_delay == delay:
            # Check universe
            valid_universes = row.get('Universe', [])
            if isinstance(valid_universes, list) and universe not in valid_universes:
                return False
            
            # Check neutralization if present in setting
            if neutralization:
                valid_neutralizations = row.get('Neutralization', [])
                if isinstance(valid_neutralizations, list) and neutralization not in valid_neutralizations:
                    return False

            return True
                
    return False


def find_common_availabilities(
    session: requests.Session, datafields: List[str]
) -> List[Dict]:
    """Find the intersection of available settings for a list of datafields.

    Returns a list of settings (region, universe, delay, instrumentType) that are
    valid for ALL provided datafields.
    """
    if not datafields:
        return []

    common_settings = None

    for field in datafields:
        # Fetch availability for this field
        info = get_datafield_availability(session, field)
        
        # If field not found or has no availability, we skip it.
        # It might be a local variable, a constant, or a vector not in the catalog.
        if info.get("error") or not info.get("availability"):
            print(f"Field '{field}' has no availability info (likely local var). Skipping constraint.")
            continue

        # Convert availability list to a set of JSON strings for set intersection
        # We use JSON strings because dicts are not hashable
        current_settings = set()
        for item in info["availability"]:
            # Normalize keys to ensure consistent JSON representation
            normalized_item = {
                "instrumentType": item.get("instrumentType"),
                "region": item.get("region"),
                "delay": item.get("delay"),
                "universe": item.get("universe"),
            }
            current_settings.add(json.dumps(normalized_item, sort_keys=True))

        if common_settings is None:
            common_settings = current_settings
        else:
            common_settings = common_settings.intersection(current_settings)
        
        # Optimization: if intersection becomes empty, we can stop early
        if not common_settings:
            print(f"Intersection became empty after checking field '{field}'.")
            return []

    # If common_settings is still None, it means no fields returned valid availability.
    if common_settings is None:
        return []

    # Convert back to list of dicts
    result = [json.loads(s) for s in common_settings]
    
    # Sort for consistent output (optional but nice)
    result.sort(key=lambda x: (x.get("region", ""), x.get("universe", ""), x.get("delay", 0)))
    
    return result


def get_alpha_variants(
    session: requests.Session, alpha: Dict, operators: List[Dict], simulation_options: Optional[pd.DataFrame] = None
) -> Dict:
    """Analyze alpha and find valid setting variants without simulating."""
    alpha_id = alpha.get("id", "Unknown")
    alpha_type = alpha.get("type")
    
    if alpha_type != "REGULAR":
        return {"id": alpha_id, "valid": False, "reason": "Not REGULAR type", "variants": []}

    expr = _extract_expression(alpha)
    if not expr:
        return {"id": alpha_id, "valid": False, "reason": "No expression found", "variants": []}

    operator_names = [op.get("name", "") for op in operators if isinstance(op, dict)]
    _, fields = parse_expression(expr, operator_names)
    
    if not fields:
        return {"id": alpha_id, "valid": False, "reason": "No datafields found", "variants": []}

    common_settings = find_common_availabilities(session, fields)
    
    if not common_settings:
        return {"id": alpha_id, "valid": False, "reason": "No common settings", "variants": []}

    original_settings = alpha.get("settings", {})
    valid_variants = []
    
    for new_setting in common_settings:
        # Construct full simulation payload (merge first to validate full settings)
        merged_settings = original_settings.copy()
        merged_settings.update(new_setting)

        # Validate against simulation options if provided
        if simulation_options is not None:
            if not validate_setting(merged_settings, simulation_options):
                continue

        # Check duplicate
        is_duplicate = True
        for key in ["region", "universe", "delay", "instrumentType"]:
            val_orig = str(original_settings.get(key, ""))
            val_new = str(new_setting.get(key, ""))
            if val_orig != val_new:
                is_duplicate = False
                break
        
        if not is_duplicate:
            # Ensure required fields for ace_lib compatibility if missing
            if "language" not in merged_settings:
                merged_settings["language"] = "FASTEXPR"

            # Add maxTrade: ON for specific regions
            # if merged_settings.get("region") in ["ASI", "JPN", "HKG", "KOR", "TWN"]:
            #     merged_settings["maxTrade"] = "ON"
            
            payload = {
                "type": "REGULAR",
                "settings": merged_settings,
                "regular": expr,
            }
            
            valid_variants.append({
                "diff_settings": new_setting,
                "simulation_payload": payload
            })
            
    return {
        "id": alpha_id,
        "dateSubmitted": alpha.get("dateSubmitted"),
        "expression": expr,
        "valid": True,
        "variants": valid_variants,
        "original_settings": original_settings
    }


def run_simulation_payload(
    session: requests.Session,
    payload: Dict,
) -> Tuple[bool, Union[Dict, str]]:
    """Send a simulation request and wait for the result.
    
    Returns: (success, result_or_error_message)
    """
    if not start_simulation or not simulation_progress:
        return False, "Simulation tools (ace_lib) not available or failed to import."

    settings = payload.get("settings", {})
    print(f"  -> Submitting simulation for {settings.get('region')} / {settings.get('universe')}...")
    
    try:
        resp = start_simulation(session, payload)
        
        # Check if response is valid (status code 200-299)
        if not resp.ok:
             error_msg = f"Simulation API Error: {resp.status_code} - {resp.text}"
             print(f"  -> {error_msg}")
             return False, error_msg
             
        result = simulation_progress(session, resp)
        if result.get("completed"):
            return True, result.get("result")
        else:
            msg = result.get("message") or "Simulation failed or incomplete."
            print(f"  -> {msg}")
            return False, msg
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  -> Error during simulation: {e}")
        return False, str(e)

# Deprecated but kept for compatibility if needed
def run_simulation_for_setting(
    session: requests.Session,
    expression: str,
    settings: Dict,
) -> Optional[Dict]:
    payload = {
        "type": "REGULAR",
        "settings": settings,
        "regular": expression,
    }
    success, res = run_simulation_payload(session, payload)
    return res if success else None


def process_alpha_variants(
    session: requests.Session, alpha: Dict, operators: List[Dict], simulation_options: Optional[pd.DataFrame] = None
) -> List[Dict]:
    """Analyze alpha, find common availabilities, and simulate variants.
    
    Returns a list of simulation results (new alphas).
    """
    generated_alphas = []
    
    alpha_id = alpha.get("id", "Unknown")
    alpha_type = alpha.get("type")
    
    if alpha_type != "REGULAR":
        print(f"Skipping Alpha {alpha_id}: Type is {alpha_type}, not REGULAR.")
        return []

    print(f"\nProcessing Alpha {alpha_id}...")

    # Extract expression
    expr = _extract_expression(alpha)
    if not expr:
        print("  -> No expression found.")
        return []

    # Parse datafields
    operator_names = [op.get("name", "") for op in operators if isinstance(op, dict)]
    _, fields = parse_expression(expr, operator_names)
    
    if not fields:
        print("  -> No datafields found to check availability.")
        return []

    # Find common availabilities
    print(f"  -> Checking availability for {len(fields)} fields...")
    common_settings = find_common_availabilities(session, fields)
    
    if not common_settings:
        print("  -> No common settings found.")
        return []

    print(f"  -> Found {len(common_settings)} valid setting combinations.")
    
    # Base settings from original alpha
    original_settings = alpha.get("settings", {})
    
    for i, new_setting in enumerate(common_settings):
        print(f"\n  [Variant {i+1}/{len(common_settings)}]")

        # Merge settings: keep original unless overwritten by new availability
        # Availability gives: region, universe, delay, instrumentType
        # Original has: decay, neutralization, truncation, etc.
        merged_settings = original_settings.copy()
        merged_settings.update(new_setting)

        # Validate against simulation options if provided
        if simulation_options is not None:
            if not validate_setting(merged_settings, simulation_options):
                print(f"  -> Skipping: Invalid simulation setting combination ({new_setting.get('region')}/{new_setting.get('universe')}).")
                continue

        # Check if this variant duplicates the original alpha's settings
        is_duplicate = True
        for key in ["region", "universe", "delay", "instrumentType"]:
            # Compare as strings to handle potential type mismatches (e.g. delay int vs str)
            val_orig = str(original_settings.get(key, ""))
            val_new = str(new_setting.get(key, ""))
            if val_orig != val_new:
                is_duplicate = False
                break
        
        if is_duplicate:
            print(f"  -> Skipping: Settings match original alpha ({new_setting.get('region')}/{new_setting.get('universe')}).")
            continue
        
        # Add maxTrade: ON for specific regions
        # if merged_settings.get("region") in ["ASI", "JPN", "HKG", "KOR", "TWN"]:
        #     merged_settings["maxTrade"] = "ON"
        
        # Run simulation
        result = run_simulation_for_setting(session, expr, merged_settings)
        
        if result:
            # Print some stats
            stats = result.get("is", {})
            sharpe = stats.get("sharpe", "N/A")
            returns = stats.get("returns", "N/A")
            turnover = stats.get("turnover", "N/A")
            new_alpha_id = result.get("id")
            print(f"  -> Result: ID={new_alpha_id}, Sharpe={sharpe}, Returns={returns}, Turnover={turnover}")
            
            # Add metadata about origin
            result["_origin_alpha_id"] = alpha_id
            result["_origin_variant_settings"] = new_setting
            generated_alphas.append(result)
            
    return generated_alphas


def main() -> None:
    """Interactive main function."""
    print("=== BRAIN Alpha Variant Generator ===")
    
    # 1. Interactive Login
    username = input("Enter BRAIN Username (Email): ").strip()
    if not username:
        print("Username is required.")
        return
        
    password = getpass.getpass("Enter BRAIN Password: ").strip()
    if not password:
        print("Password is required.")
        return

    try:
        print(f"Logging in as {username}...")
        session = brain_login(username, password)
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 2. Date Range
    print("\n--- Date Range Selection ---")
    start_date = input("Enter Start Date (YYYY-MM-DD): ").strip()
    end_date = input("Enter End Date (YYYY-MM-DD): ").strip()
    
    # Basic validation
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    # Fetch Alphas
    alphas = fetch_alphas_by_date_range(session, start_date, end_date)
    print(f"Fetched {len(alphas)} alphas from {start_date} to {end_date}.")
    
    if not alphas:
        print("No alphas found in this range. Exiting.")
        return

    print("Fetching operator catalog...")
    operators = fetch_operators(session)
    
    print("Fetching simulation options...")
    simulation_options = None
    if get_instrument_type_region_delay:
        try:
            simulation_options = get_instrument_type_region_delay(session)
            print("Simulation options fetched successfully.")
        except Exception as e:
            print(f"Warning: Failed to fetch simulation options: {e}")
    else:
        print("Warning: get_instrument_type_region_delay not available.")

    # 3. Process Alphas
    all_generated_alphas = []
    
    for i, alpha in enumerate(alphas):
        new_alphas = process_alpha_variants(session, alpha, operators, simulation_options)
        all_generated_alphas.extend(new_alphas)

    # 4. Output
    if all_generated_alphas:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_alphas_{timestamp}.json"
        
        print(f"\nTotal generated alphas: {len(all_generated_alphas)}")
        print(f"Saving results to {filename}...")
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_generated_alphas, f, indent=2, ensure_ascii=False)
            
        print("Done.")
    else:
        print("\nNo new alphas were generated.")

if __name__ == "__main__":
    main()
