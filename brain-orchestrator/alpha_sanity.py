"""Alpha sanity gate: reject zombie alphas that pass raw-Sharpe threshold.

Why this exists
---------------
A CHN/fundamental23 pipeline recently returned two alphas at Sharpe >= 1.58
that were counted as "qualified" by the stop-condition logic:

  Alpha A: Sharpe 2.23, fitness 3.12, longCount=5, shortCount=0
  Alpha B: Sharpe 7.91, fitness 32.79, longCount=20, shortCount=0

Pulling the full alpha details showed both were zombies:
  * All PnL came from 2014-2015; 2016-2023 yearly Sharpe = 0
  * investabilityConstrained Sharpe = -2.68 / -3.65 (negative!)
  * CONCENTRATED_WEIGHT was WARNING / FAIL
  * LOW_2Y_SHARPE was WARNING / FAIL

Root cause: the LLM picked fields like `employee_retirement_assets_2` and
`amortization_intangible_assets_2` which have ~0% CHN coverage after 2015.
Sharpe 7.91 on 5 stocks over 2 years is noise, not alpha.

This module provides `validate_alpha_real()` which fetches the full
alpha record and applies a series of checks. Pipelines should count an
alpha toward the stop-condition quota only after it passes these checks.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("alpha_sanity")

# ---------------------------------------------------------------------
# Thresholds — conservative but not paranoid
# ---------------------------------------------------------------------
MIN_STOCK_COUNT = 20            # longCount + shortCount across the book
MIN_RECENT_YEARS_WITH_PNL = 2   # require non-zero pnl in the last 2 years
MIN_INVESTABILITY_SHARPE = 0.5  # after investability constraint, still positive
# BRAIN pre-submission checks that, if FAIL, mean the alpha is not submittable.
BLOCKING_CHECKS = frozenset({
    "LOW_SHARPE", "LOW_FITNESS", "LOW_TURNOVER", "HIGH_TURNOVER",
    "LOW_RETURNS", "LOW_SUB_UNIVERSE_SHARPE",
    "LOW_ROBUST_UNIVERSE_SHARPE.WITH_RATIO",
    "LOW_ROBUST_UNIVERSE_RETURNS",
    "LOW_2Y_SHARPE",
    "CONCENTRATED_WEIGHT",
})


def _safe_get(d: Any, *keys, default=None):
    """Nested dict getter that tolerates None and missing keys."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _check_stocks_covered(details: dict) -> Optional[str]:
    is_ = details.get("is") or {}
    long_count = int(is_.get("longCount") or 0)
    short_count = int(is_.get("shortCount") or 0)
    total = long_count + short_count
    if total < MIN_STOCK_COUNT:
        return (
            f"stocks_too_few({total}<{MIN_STOCK_COUNT}): "
            f"longCount={long_count} shortCount={short_count}"
        )
    return None


def _check_recent_years(yearly_stats: Optional[dict]) -> Optional[str]:
    """Look at the last two IS rows and make sure both have non-zero PnL."""
    if not yearly_stats:
        return "no_yearly_stats"
    records = yearly_stats.get("records") or []
    schema = yearly_stats.get("schema") or {}
    props = schema.get("properties") or []
    try:
        pnl_idx = next(i for i, p in enumerate(props) if p.get("name") == "pnl")
    except StopIteration:
        return "yearly_stats_missing_pnl_col"
    if not records:
        return "yearly_stats_empty"
    # Last two rows (most recent years)
    tail = records[-MIN_RECENT_YEARS_WITH_PNL:]
    zeros = sum(1 for row in tail if not row[pnl_idx])
    if zeros >= MIN_RECENT_YEARS_WITH_PNL:
        return f"zombie_last_{MIN_RECENT_YEARS_WITH_PNL}_years_no_pnl"
    return None


def _check_investability(details: dict) -> Optional[str]:
    sharpe = _safe_get(details, "is", "investabilityConstrained", "sharpe")
    if sharpe is None:
        return None  # some older alphas don't carry this — don't reject
    if float(sharpe) < MIN_INVESTABILITY_SHARPE:
        return f"investability_sharpe_{float(sharpe):.2f}<{MIN_INVESTABILITY_SHARPE}"
    return None


def _check_blocking_checks(details: dict) -> Optional[str]:
    checks = _safe_get(details, "is", "checks") or []
    if not isinstance(checks, list):
        return None
    failed = [c.get("name") for c in checks
              if c.get("name") in BLOCKING_CHECKS and c.get("result") == "FAIL"]
    if failed:
        return "blocking_checks_failed:" + ",".join(failed)
    return None


def validate_alpha_real(
    details: dict,
    yearly_stats: Optional[dict] = None,
) -> tuple[bool, list[str]]:
    """Validate that an alpha is a real, submittable candidate.

    Args:
        details: Full JSON response from `/alphas/<id>` (same shape as
            `get_alpha_details`).
        yearly_stats: Optional yearly stats response (same shape as
            `get_alpha_yearly_stats`). If omitted, the recent-years check
            is skipped and a warning reason is recorded.

    Returns:
        (passed, reasons). `reasons` is a list of short strings
        explaining each failed check — empty when `passed` is True.
    """
    reasons: list[str] = []

    # Details may arrive as {"result": {...}} when it came through MCP.
    if isinstance(details, dict) and "result" in details and "is" not in details:
        details = details["result"]
    if isinstance(yearly_stats, dict) and "result" in yearly_stats and "records" not in yearly_stats:
        yearly_stats = yearly_stats["result"]

    for check in (
        _check_stocks_covered,
        _check_investability,
        _check_blocking_checks,
    ):
        reason = check(details)
        if reason:
            reasons.append(reason)

    if yearly_stats is not None:
        ys_reason = _check_recent_years(yearly_stats)
        if ys_reason:
            reasons.append(ys_reason)
    else:
        reasons.append("yearly_stats_not_provided")

    return (len(reasons) == 0), reasons


# ---------------------------------------------------------------------
# Convenience wrapper that fetches via an authenticated wqb/requests
# session. Optional — callers can also pass pre-fetched dicts.
# ---------------------------------------------------------------------
def fetch_and_validate(
    session,
    alpha_id: str,
    api_url: str = "https://api.worldquantbrain.com",
) -> tuple[bool, list[str], dict]:
    """Fetch alpha details + yearly stats via `session`, then validate.

    Returns (passed, reasons, raw_details). `raw_details` is the full
    alpha record so callers can cache it for further reporting.
    """
    details_resp = session.get(f"{api_url}/alphas/{alpha_id}")
    if details_resp.status_code != 200:
        return False, [f"details_http_{details_resp.status_code}"], {}
    details = details_resp.json()

    ys_resp = session.get(f"{api_url}/alphas/{alpha_id}/recordsets/yearly-stats")
    yearly_stats = ys_resp.json() if ys_resp.status_code == 200 else None

    passed, reasons = validate_alpha_real(details, yearly_stats)
    return passed, reasons, details
