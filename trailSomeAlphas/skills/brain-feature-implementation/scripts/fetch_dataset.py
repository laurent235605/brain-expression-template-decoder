import json
import os
import argparse
import pandas as pd
from pathlib import Path
import sys

print("Script started...", flush=True)

# Ensure local imports work by adding the script directory to sys.path
script_dir = Path(__file__).resolve().parent
sys.path.append(str(script_dir))

try:
    import ace_lib
except ImportError:
    print("Error: Could not import 'ace_lib'. Make sure it is in the same directory.")
    sys.exit(1)

def load_config(config_path):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Fetch dataset fields from WorldQuant BRAIN")
    parser.add_argument("--datasetid", required=True, help="ID of the dataset to fetch (e.g., specific dataset ID)")
    parser.add_argument("--region", default="USA", help="Region (default: USA)")
    parser.add_argument("--delay", type=int, default=1, help="Delay (default: 1)")
    parser.add_argument("--universe", default="TOP3000", help="Universe (default: TOP3000)")
    parser.add_argument("--instrument-type", default="EQUITY", dest="instrument_type", help="Instrument Type (default: EQUITY)")
    parser.add_argument(
        "--data-type",
        default="MATRIX",
        choices=["MATRIX", "VECTOR"],
        help="Data type to request from BRAIN datafields (MATRIX or VECTOR). Default: MATRIX",
    )

    args = parser.parse_args()

    # Determine paths relative to this script
    # User requested: robust and no absolute paths hardcoded
    workspace_dir = script_dir.parent
    config_path = workspace_dir / "config.json"
    data_dir = workspace_dir / "data"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Load configuration
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    if not config:
        sys.exit(1)

    # Extract credentials (env override -> config)
    email = os.environ.get("BRAIN_USERNAME") or os.environ.get("BRAIN_EMAIL")
    password = os.environ.get("BRAIN_PASSWORD")
    if not email or not password:
        creds = config.get("BRAIN_CREDENTIALS", {})
        email = email or creds.get("email")
        password = password or creds.get("password")

    if not email or not password:
        print("Error: BRAIN credentials missing. Set BRAIN_USERNAME/BRAIN_PASSWORD or config.json")
        sys.exit(1)

    # Override ace_lib.get_credentials to use our config values
    # ace_lib.start_session() internally calls get_credentials()
    ace_lib.get_credentials = lambda: (email, password)

    try:
        print(f"Logging in as {email}...")
        session = ace_lib.start_session()
        
        print(f"Fetching datafields for dataset: {args.datasetid} (Region: {args.region}, Delay: {args.delay})...")
        
        # Fetch datafields using the library function
        df = ace_lib.get_datafields(
            session, 
            dataset_id=args.datasetid, 
            region=args.region, 
            delay=args.delay,
            universe=args.universe,
            instrument_type=args.instrument_type,
            data_type=args.data_type,
        )

        if df is None or df.empty:
            print("Error: No data found or empty response.")
            sys.exit(1)

        # Construct a safe filename and folder name
        safe_dataset_id = "".join([c for c in args.datasetid if c.isalnum() or c in ('-','_')])
        folder_name = f"{safe_dataset_id}_{args.region}_delay{args.delay}"
        dataset_folder = data_dir / folder_name
        dataset_folder.mkdir(parents=True, exist_ok=True)

        filename = f"{folder_name}.csv"
        output_path = dataset_folder / filename

        print(f"Saving {len(df)} records to {output_path}...")
        df.to_csv(output_path, index=False)
        print("Success.")

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
