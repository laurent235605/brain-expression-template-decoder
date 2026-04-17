from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))


@dataclass(frozen=True)
class ResolvedSettings:
    instrumentType: str
    region: str
    delay: int
    universe: str
    neutralization: str
    decay: int = 0
    truncation: float = 0.08
    pasteurization: str = "ON"
    testPeriod: str = "P0Y0M0D"
    unitHandling: str = "VERIFY"
    nanHandling: str = "OFF"
    maxTrade: str = "OFF"
    language: str = "FASTEXPR"
    visualization: bool = False


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_candidates(idea_ctx: dict[str, Any], options_snapshot: dict[str, Any]) -> dict[str, Any]:
    region = str(idea_ctx["region"])
    delay = int(idea_ctx["delay"])

    rows = options_snapshot.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("options snapshot 'rows' must be a list")

    # Filter for matching Instrument/Region/Delay
    candidates = [
        r
        for r in rows
        if r.get("InstrumentType") == "EQUITY" and r.get("Region") == region and int(r.get("Delay")) == delay
    ]

    if not candidates:
        raise RuntimeError(
            f"No valid settings found for InstrumentType=EQUITY, Region={region}, Delay={delay}. "
            "Re-fetch options or adjust region/delay."
        )

    # In practice, usually there's only one 'row' per (Instrument, Region, Delay) combination 
    # that contains the lists of valid Universes and Neutralizations.
    # But we'll return all matches just in case.
    
    return {
        "context": {
            "dataset": idea_ctx.get("dataset_id"),
            "region": region,
            "delay": delay
        },
        "valid_options": candidates
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea", required=True, help="idea_context.json")
    ap.add_argument("--options", required=True, help="sim_options_snapshot.json")
    ap.add_argument("--out", required=True, help="Output settings_candidates.json")
    args = ap.parse_args()

    idea_path = Path(args.idea).resolve()
    opt_path = Path(args.options).resolve()
    out_path = Path(args.out).resolve()

    idea_ctx = _load_json(idea_path)
    options = _load_json(opt_path)

    payload = resolve_candidates(idea_ctx, options)

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote candidates: {out_path}")
    print("Next step: AI should inspect these candidates and the 'idea' text to choose specific settings.")


if __name__ == "__main__":
    main()
