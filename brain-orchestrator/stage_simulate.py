"""Stage SIMULATE: run batch simulation for an idea's alpha list.

Wraps batch_simulator.py's BatchSimulator class to submit, poll, and
record simulation results for each idea's alpha_list.json.
"""
from __future__ import annotations

import json
import logging
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

VENDOR_DIR = Path(__file__).resolve().parent / "scripts" / "vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from batch_simulator import BatchSimulator

logger = logging.getLogger("stage_simulate")

_SIM_COMPLETED_STATUSES = {"COMPLETED", "COMPLETE", "WARNING"}
_SIM_FAILED_STATUSES = {
    "ERROR",
    "FAIL",
    "FAILED",
    "SUBMISSION_FAILED",
    "TIMEOUT",
    "BATCH_SPAWN_FAILED",
    "MISSING_RESULT",
}


def _clean_number(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not math.isfinite(float(value)):
        return None
    return value


def _load_latest_sim_rows(csv_path: Path) -> pd.DataFrame:
    """Load simulation CSV and keep only the latest row per fingerprint."""
    df = pd.read_csv(csv_path, on_bad_lines="skip")
    if df.empty:
        return df

    if "fingerprint" not in df.columns:
        return df.reset_index(drop=True)

    work_df = df.copy()
    if "timestamp" in work_df.columns:
        work_df["__sort_ts__"] = pd.to_numeric(work_df["timestamp"], errors="coerce")
    else:
        work_df["__sort_ts__"] = pd.Series(range(len(work_df)), index=work_df.index, dtype=float)
    work_df["__sort_ts__"] = work_df["__sort_ts__"].fillna(-1)
    work_df["__sort_idx__"] = range(len(work_df))
    work_df = work_df.sort_values(["__sort_ts__", "__sort_idx__"], kind="stable")
    work_df = work_df.drop_duplicates(subset=["fingerprint"], keep="last")
    work_df = work_df.drop(columns=["__sort_ts__", "__sort_idx__"], errors="ignore")
    return work_df.reset_index(drop=True)


def _summarize_csv(csv_path: Path) -> dict:
    """Read simulation CSV and produce summary statistics."""
    if not csv_path.exists():
        return {"count": 0}

    try:
        df = _load_latest_sim_rows(csv_path)
    except Exception as exc:
        logger.warning(f"Failed to read CSV {csv_path}: {exc}")
        return {"count": 0, "error": str(exc)}

    status_col = df["status"].astype(str).str.upper().str.strip() if "status" in df.columns else pd.Series(dtype=str)
    completed = df[status_col.isin(_SIM_COMPLETED_STATUSES)] if len(status_col) else pd.DataFrame()

    failed = df[status_col.isin(_SIM_FAILED_STATUSES)] if len(status_col) else pd.DataFrame()

    summary: dict[str, Any] = {
        "count": len(df),
        "completed": len(completed),
        "failed": len(failed),
    }

    if len(status_col):
        summary["status_breakdown"] = {
            str(status): int(count)
            for status, count in status_col.value_counts(dropna=False).items()
        }

    if len(failed):
        detail_col = failed["error_details"] if "error_details" in failed.columns else pd.Series(dtype=str)
        error_col = failed["error"] if "error" in failed.columns else pd.Series(dtype=str)
        error_texts = [str(v).strip() for v in pd.concat([detail_col, error_col], ignore_index=True).tolist() if str(v).strip() and str(v).strip().lower() != 'nan']
        if error_texts:
            summary["first_error"] = error_texts[0]
            summary["error_examples"] = error_texts[:3]
        else:
            failed_statuses = [str(v).strip() for v in failed.get("status", pd.Series(dtype=str)).tolist() if str(v).strip()]
            if failed_statuses:
                summary["first_error"] = failed_statuses[0]
                summary["error_examples"] = failed_statuses[:3]

    if len(completed) and "sharpe" in completed.columns:
        sharpe_vals = completed["sharpe"].astype(float)
        fitness_vals = completed["fitness"].astype(float)
        summary["sharpe_avg"] = _clean_number(round(float(sharpe_vals.mean()), 4))
        summary["sharpe_var"] = _clean_number(round(float(sharpe_vals.var()), 4) if len(sharpe_vals) > 1 else 0.0)
        summary["sharpe_max"] = _clean_number(round(float(sharpe_vals.max()), 4))
        summary["fitness_avg"] = _clean_number(round(float(fitness_vals.mean()), 4))
        summary["fitness_var"] = _clean_number(round(float(fitness_vals.var()), 4) if len(fitness_vals) > 1 else 0.0)
        summary["fitness_max"] = _clean_number(round(float(fitness_vals.max()), 4))
        summary["turnover_avg"] = _clean_number(round(float(completed["turnover"].astype(float).mean()), 4))

    return summary


def simulate_idea(
    alpha_list_path: Path,
    output_csv: Path,
    session,
    sim_multi_slots: int = 2,
    cancel_check=None,
    progress_callback=None,
    location_callback=None,
) -> dict:
    """Run batch simulation for one idea's alphas.

    One idea = one worker. Batches are processed sequentially (concurrency=1)
    so that each idea occupies exactly one multi-sim slot on the platform.

    Args:
        alpha_list_path: path to alpha_list.json
        output_csv: path to write/append simulation results CSV
        session: ace_lib session
        sim_multi_slots: max alphas per multi-simulation batch
        progress_callback: optional callable(summary_dict) called after each child result is persisted

    Returns:
        Summary dict with counts and metric averages.
    """
    alpha_list = json.loads(alpha_list_path.read_text(encoding="utf-8"))
    if not isinstance(alpha_list, list) or not alpha_list:
        logger.warning(f"Empty or invalid alpha list: {alpha_list_path}")
        return {"count": 0}

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    # Wrap progress_callback to read CSV and produce incremental summary
    def _on_batch_done():
        if progress_callback and output_csv.exists():
            try:
                summary = _summarize_csv(output_csv)
                summary["count"] = len(alpha_list)  # total from input, not CSV row count
                progress_callback(summary)
            except Exception:
                pass

    simulator = BatchSimulator(
        session,
        output_csv=str(output_csv),
        cancel_check=cancel_check,
        on_batch_start=location_callback,
        on_result_saved=_on_batch_done,
    )
    # concurrency=1: one idea occupies exactly one worker / one multi-sim slot
    simulator.run(alpha_list, batch_size=sim_multi_slots, concurrency=1,
                  on_batch_done=_on_batch_done)

    summary = _summarize_csv(output_csv)
    summary["count"] = len(alpha_list)  # ensure total is from input
    logger.info(
        f"Simulation done: {summary.get('completed', 0)}/{summary.get('count', 0)} completed, "
        f"sharpe_avg={summary.get('sharpe_avg', 'N/A')}"
    )
    return summary
