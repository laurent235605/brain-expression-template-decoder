"""Build a field blacklist for a given dataset/region/universe combination.

Rationale
---------
fundamental23 in CHN/TOP2000U has 313 fields, but roughly 20-30% have
coverage <60% or cryptic IDs whose descriptions don't match the field
name (e.g. `advances_to_vendors` described as "Advertising Expense").

Alphas built on these fields pass the raw-Sharpe stop condition while
being zombies: they hold 5 stocks for 2014-2015 and then have zero
exposure for 8+ years because the underlying data is empty.

This script scans every field, applies three independent filters, and
writes a JSON file the pipeline can inject into its generate/enhance
prompts as an explicit "DO NOT USE" list.

Usage
-----
    python build_field_blacklist.py \\
        --region CHN --delay 1 --universe TOP2000U \\
        --dataset-id fundamental23

Output written to:
    brain-orchestrator/resources/field_blacklists/<dataset>_<region>_d<delay>_<universe>.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow `python scripts/build_field_blacklist.py` from either the repo
# root or the brain-orchestrator folder.
_THIS = Path(__file__).resolve()
_ORCH = _THIS.parent.parent
_VENDOR = _ORCH / "scripts" / "vendor"
for _p in (_ORCH, _VENDOR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ace_lib  # noqa: E402  (resolved via scripts/vendor)

logger = logging.getLogger("build_field_blacklist")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Filter thresholds
# ---------------------------------------------------------------------
COVERAGE_MIN = 0.60          # reject fields with <60% coverage
DATE_COVERAGE_MIN = 0.60     # reject fields that don't cover the full time range
_BRACKETED_HINT_RE = re.compile(r"^\s*\[[^]]+\]\s*")  # strip leading "[Quarterly]"
_KEEP_WORDS = re.compile(r"[a-z0-9]+")

# Fields whose IDs are pure metadata, not signals.
_METADATA_ID_PATTERNS = [
    re.compile(p)
    for p in (
        r"fiscal_month",
        r"fiscal_year",
        r"reporting_currency",
        r"_code$",
        r"^fnd23_intfvm_",    # cryptic namespaced codes
        r"^fnd23_iu",
        r"^iu_",
    )
]


def _tokens(text: str) -> set[str]:
    return set(_KEEP_WORDS.findall(text.lower()))


def _description_matches_id(field_id: str, description: str) -> bool:
    """Heuristic: the field description should share at least one
    substantive token with the field id. `advances_to_vendors` with
    description "Advertising Expense" must fail this check.

    We strip leading bracketed hints like "[Quarterly]" and the generic
    filler word "expense".
    """
    if not description:
        return False
    cleaned_desc = _BRACKETED_HINT_RE.sub("", description)
    desc_tokens = _tokens(cleaned_desc)
    # Drop common filler tokens that match trivially.
    desc_tokens -= {"the", "a", "an", "for", "of", "on", "at", "to", "in",
                    "is", "are", "not", "by", "from", "with", "value",
                    "amount", "total", "current", "quarterly", "expense"}
    id_tokens = _tokens(field_id)
    return bool(desc_tokens & id_tokens)


def _classify(field: dict, *, mature_dataset: bool = True) -> tuple[bool, str]:
    """Return (is_blacklisted, reason)."""
    fid = str(field.get("id") or "")
    desc = str(field.get("description") or "")
    cov = float(field.get("coverage") or 0.0)
    dcov = float(field.get("dateCoverage") or 0.0)
    user_count = int(field.get("userCount") or 0)
    alpha_count = int(field.get("alphaCount") or 0)

    # 1. Coverage filter
    if cov < COVERAGE_MIN:
        return True, f"low_coverage_{cov:.2f}"
    if dcov < DATE_COVERAGE_MIN:
        return True, f"low_date_coverage_{dcov:.2f}"

    # 2. Pure metadata — never useful as a signal
    for pat in _METADATA_ID_PATTERNS:
        if pat.search(fid):
            return True, "metadata_field"

    # 3. Description-id mismatch
    if not _description_matches_id(fid, desc):
        return True, "description_id_mismatch"

    # NOTE: `userCount==0 AND alphaCount==0` on a mature dataset is a
    # yellow flag (the community has never extracted signal from it) but
    # is too aggressive as a hard blacklist — many legitimate fields have
    # simply never been used in a given region. We surface this via the
    # `low_priority` flag on the whitelist instead so the LLM can weigh it.
    return False, ""


def build(
    region: str,
    delay: int,
    universe: str,
    dataset_id: str,
    data_type: str,
    instrument_type: str,
    output_dir: Path,
) -> Path:
    logger.info(
        f"Fetching datafields: region={region} delay={delay} universe={universe} "
        f"dataset={dataset_id} type={data_type}"
    )

    session = ace_lib.start_session()
    df = ace_lib.get_datafields(
        session,
        instrument_type=instrument_type,
        region=region,
        delay=delay,
        universe=universe,
        dataset_id=dataset_id,
        data_type=data_type,
    )

    if df.empty:
        raise RuntimeError("get_datafields returned 0 rows — bad credentials or no matching dataset")

    logger.info(f"Loaded {len(df)} fields")

    fields = df.to_dict(orient="records")
    blacklist: list[dict] = []
    whitelist: list[dict] = []
    for f in fields:
        bad, reason = _classify(f)
        entry = {
            "id": f.get("id"),
            "coverage": round(float(f.get("coverage") or 0.0), 4),
            "dateCoverage": round(float(f.get("dateCoverage") or 0.0), 4),
            "userCount": int(f.get("userCount") or 0),
            "alphaCount": int(f.get("alphaCount") or 0),
            "description": (f.get("description") or "")[:160],
        }
        if bad:
            entry["reason"] = reason
            blacklist.append(entry)
        else:
            # Yellow flag: community has never used this field — still OK to
            # try, but deprioritize versus battle-tested fields.
            if entry["userCount"] == 0 and entry["alphaCount"] == 0:
                entry["low_priority"] = True
            whitelist.append(entry)

    # Rank whitelist: battle-tested fields first, community-unused last.
    for w in whitelist:
        w["_score"] = (
            w["coverage"]
            + w["dateCoverage"]
            + (0.5 if w.get("userCount", 0) > 0 else 0.0)
            - 0.02 * w["alphaCount"]  # slight penalty for already-crowded fields
            - (0.3 if w.get("low_priority") else 0.0)
        )
    whitelist.sort(key=lambda x: x["_score"], reverse=True)
    for w in whitelist:
        w.pop("_score", None)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{dataset_id}_{region}_d{delay}_{universe}.json"
    payload = {
        "dataset_id": dataset_id,
        "region": region,
        "delay": delay,
        "universe": universe,
        "instrument_type": instrument_type,
        "data_type": data_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "COVERAGE_MIN": COVERAGE_MIN,
            "DATE_COVERAGE_MIN": DATE_COVERAGE_MIN,
        },
        "total_fields": len(fields),
        "blacklisted": len(blacklist),
        "whitelisted": len(whitelist),
        "blacklist": blacklist,
        "whitelist_top": whitelist[:80],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"Wrote blacklist → {out_path}")
    logger.info(
        f"Summary: total={len(fields)} blacklisted={len(blacklist)} "
        f"whitelisted={len(whitelist)}"
    )

    # Reason breakdown
    reason_counts: dict[str, int] = {}
    for b in blacklist:
        r = b.get("reason") or "?"
        # Collapse "low_coverage_0.xx" into one bucket
        key = r.split("_")[0] + "_" + r.split("_")[1] if r.startswith("low_") else r
        reason_counts[key] = reason_counts.get(key, 0) + 1
    logger.info(f"Blacklist reasons: {reason_counts}")

    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--delay", type=int, required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--dataset-id", required=True)
    ap.add_argument("--data-type", default="MATRIX")
    ap.add_argument("--instrument-type", default="EQUITY")
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=_ORCH / "resources" / "field_blacklists",
    )
    args = ap.parse_args()

    # Pass credentials to ace_lib via env / local secrets file.
    username = os.environ.get("BRAIN_USERNAME")
    password = os.environ.get("BRAIN_PASSWORD")
    if username and password:
        secrets_path = Path.home() / "secrets" / "platform-brain.json"
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        if not secrets_path.exists() or secrets_path.stat().st_size < 5:
            secrets_path.write_text(
                json.dumps({"credentials": [username, password]}), encoding="utf-8"
            )

    try:
        build(
            region=args.region,
            delay=args.delay,
            universe=args.universe,
            dataset_id=args.dataset_id,
            data_type=args.data_type,
            instrument_type=args.instrument_type,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        logger.exception(f"Failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
