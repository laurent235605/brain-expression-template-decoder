from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import ace_lib


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea", required=True, help="idea_context.json")
    ap.add_argument("--settings_json", required=True, help="JSON string of settings config")
    ap.add_argument("--out", required=True, help="alpha_list.json (will append if exists)")
    args = ap.parse_args()

    idea_ctx = _load_json(Path(args.idea).resolve())
    
    try:
        settings_doc = json.loads(args.settings_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string provided for --settings_json: {e}")

    # Support wrapped key "resolved" or flat dict
    resolved_raw = settings_doc.get("resolved", settings_doc)
    if not isinstance(resolved_raw, dict):
        raise ValueError("Settings file must contain settings dict or 'resolved' key")

    # Robustness: Normalize keys to lowercase to handle PascalCase (Region vs region)
    # and camelCase (nanHandling vs nanhandling) inconsistencies.
    resolved = {k.lower(): v for k, v in resolved_raw.items()}
    
    out_path = Path(args.out).resolve()
    existing_alphas = []
    if out_path.exists():
        try:
            existing_alphas = _load_json(out_path)
            if not isinstance(existing_alphas, list):
                print(f"Warning: Existing file {out_path} is not a list. Overwriting.")
                existing_alphas = []
        except Exception as e:
            print(f"Warning: Could not read existing {out_path}: {e}. Overwriting.")
            existing_alphas = []

    expressions = idea_ctx.get("expression_list") or []
    if not isinstance(expressions, list) or not all(isinstance(x, str) for x in expressions):
        raise ValueError("idea_context.json must contain expression_list: list[str]")

    new_alphas = [
        ace_lib.generate_alpha(
            regular=expr,
            alpha_type="REGULAR",
            region=resolved["region"],
            universe=resolved["universe"],
            delay=int(resolved["delay"]),
            decay=int(resolved.get("decay", 0)),
            neutralization=resolved["neutralization"],
            truncation=float(resolved.get("truncation", 0.08)),
            pasteurization=resolved.get("pasteurization", "ON"),
            test_period=resolved.get("testperiod", "P0Y0M0D"),
            unit_handling=resolved.get("unithandling", "VERIFY"),
            nan_handling=resolved.get("nanhandling", "OFF"),
            max_trade=resolved.get("maxtrade", "OFF"),
            visualization=bool(resolved.get("visualization", False)),
        )
        for expr in expressions
    ]
    
    final_list = existing_alphas + new_alphas

    out_path.write_text(json.dumps(final_list, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(new_alphas)} new alphas. Total: {len(final_list)} alphas in {out_path}")


if __name__ == "__main__":
    main()
