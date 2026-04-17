from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import ace_lib
from scripts.load_credentials import load_credentials


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        required=True,
        help="Output snapshot JSON file (e.g., sim_options_snapshot.json)",
    )
    args = ap.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    creds = load_credentials(skill_dir=skill_dir)

    # Ensure ace_lib uses configured API base for normal requests.
    # NOTE: get_instrument_type_region_delay historically hard-coded the URL; we patch ace_lib to respect brain_api_url.
    ace_lib.brain_api_url = creds.brain_api_url

    def _get_credentials():
        return creds.username, creds.password

    ace_lib.get_credentials = _get_credentials  # type: ignore[assignment]

    s = ace_lib.start_session()
    df = ace_lib.get_instrument_type_region_delay(s)

    payload = {
        "brain_api_url": creds.brain_api_url,
        "rows": df.to_dict(orient="records"),
    }

    out_path = Path(args.out).resolve()
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote simulation options snapshot: {out_path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
