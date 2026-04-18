"""Direction Radar — statistical signal-light system for alpha search decisions.

Instead of hard thresholds, evaluates each idea's simulation distribution with:
  1. Operator family diversity (鱼饵 vs 池塘 discriminator)
  2. Direction Strength Index (DSI) — composite score from 4 signals
  3. Signal light classification (GREEN/YELLOW/RED/DEAD)
  4. 5 anti-kill safeguards to prevent false negatives
  5. Mann-Whitney U test for round-over-round effect comparison
"""
from __future__ import annotations

import logging
import math
import re
from typing import Iterable

import numpy as np

logger = logging.getLogger("direction_radar")

# ── Signal constants ────────────────────────────────────────────────

SIGNAL_GREEN = "GREEN"
SIGNAL_YELLOW = "YELLOW"
SIGNAL_RED = "RED"
SIGNAL_DEAD = "DEAD"

# Null hypothesis Sharpe value for significance testing.
# Kept low (0.5) so we test "above random noise", not "above submission threshold".
DEFAULT_NULL_SHARPE = 0.5

# Submission-bar Sharpe used for pass-rate computation.
SUBMISSION_SHARPE = 1.25


# ── 6 Operator families (BRAIN platform) ────────────────────────────

OPERATOR_FAMILIES: dict[str, set[str]] = {
    "timeseries": {
        "ts_mean", "ts_sum", "ts_delta", "ts_decay_linear", "ts_decay_exp",
        "ts_rank", "ts_zscore", "ts_std_dev", "ts_corr", "ts_covariance",
        "ts_regression", "ts_backfill", "ts_min", "ts_max", "ts_arg_min",
        "ts_arg_max", "ts_median", "ts_product", "ts_skewness", "ts_kurtosis",
        "ts_partial_corr", "ts_co_skewness", "ts_co_kurtosis", "ts_entropy",
        "ts_returns", "ts_target_tvr_decay", "ts_delta_limit", "hump_decay",
        "jump_decay", "ts_ir", "ts_moment", "ts_av_diff",
    },
    "cross_section": {
        "group_zscore", "group_rank", "group_mean", "group_median",
        "group_std_dev", "group_sum", "group_backfill", "group_neutralize",
        "group_count", "group_max", "group_min", "regression_neut",
        "regression_proj", "vector_neut", "vector_proj",
        "group_vector_neut", "group_vector_proj", "group_normalize",
        "group_percentage",
    },
    "math": {
        "log", "abs", "sign", "power", "sqrt", "exp", "reverse",
        "inverse", "add", "subtract", "multiply", "divide",
        "min", "max", "signed_power", "s_log_1p", "log_diff",
        "arc_tan", "tanh", "sigmoid",
    },
    "conditional": {
        "if_else", "trade_when", "nan_mask", "filter", "keep",
        "nan_out", "clamp", "winsorize", "pasteurize", "purify",
        "truncate", "hump", "equal", "less", "greater",
    },
    "ranking": {
        "rank", "percentile", "zscore", "scale", "scale_down",
        "normalize", "quantile", "rank_by_side", "one_side",
    },
    "lag": {
        "ts_delay", "delay", "ts_shift", "shift",
    },
}

_OP_PATTERN = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\(")


def _classify_operator(op_name: str) -> str | None:
    for family, ops in OPERATOR_FAMILIES.items():
        if op_name in ops:
            return family
    return None


def extract_operators(expression: str) -> set[str]:
    """Extract operator identifiers (known BRAIN ops) from an expression."""
    candidates = _OP_PATTERN.findall(expression.lower())
    return {c for c in candidates if _classify_operator(c) is not None}


def operator_family_stats(expressions: Iterable[str]) -> dict:
    """Count distinct operator families used across a list of expressions.

    Returns:
        {
          "family_count": int,           # number of distinct families
          "families": {family: count},   # usage count per family
          "operators": {op_name: count}, # usage count per operator
          "total_ops": int,              # total operator invocations
        }
    """
    families: dict[str, int] = {}
    operators: dict[str, int] = {}
    total = 0
    for expr in expressions:
        for op in extract_operators(expr):
            operators[op] = operators.get(op, 0) + 1
            family = _classify_operator(op)
            if family:
                families[family] = families.get(family, 0) + 1
                total += 1
    return {
        "family_count": len(families),
        "families": families,
        "operators": operators,
        "total_ops": total,
    }


# ── Statistical helpers ─────────────────────────────────────────────

def wilson_lower_bound(passed: int, total: int, confidence: float = 0.95) -> float:
    """Wilson-score lower confidence bound for a binomial proportion.

    Handles small samples gracefully (returns 0 for n=0).
    """
    if total <= 0:
        return 0.0
    # z for two-sided CI at `confidence` level
    from scipy.stats import norm
    z = float(norm.ppf(1 - (1 - confidence) / 2))
    p = passed / total
    denominator = 1 + z * z / total
    center = p + z * z / (2 * total)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return max(0.0, (center - margin) / denominator)


def bimodality_coefficient(samples: list[float]) -> float:
    """Sarle's bimodality coefficient. BC > 0.556 suggests bimodal distribution.

    BC = (skew^2 + 1) / (kurtosis + 3*(n-1)^2 / ((n-2)*(n-3)))
    """
    n = len(samples)
    if n < 4:
        return 0.0
    arr = np.asarray(samples, dtype=float)
    if float(arr.std()) == 0:
        return 0.0
    from scipy.stats import skew, kurtosis
    g = float(skew(arr, bias=False))
    k = float(kurtosis(arr, bias=False, fisher=True))  # excess kurtosis
    numerator = g * g + 1
    denominator = k + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def significance_score(
    sharpes: list[float],
    null_hypothesis: float = DEFAULT_NULL_SHARPE,
) -> float:
    """Return 1 - p_value (clipped to [0,1]) for one-sided test that mean > null.

    Uses t-test when n >= 8, Bootstrap (1000 resamples) otherwise.
    """
    n = len(sharpes)
    if n == 0:
        return 0.0
    arr = np.asarray(sharpes, dtype=float)

    if n < 8:
        rng = np.random.default_rng(42)
        boot = [float(rng.choice(arr, size=n, replace=True).mean()) for _ in range(1000)]
        # P(bootstrap mean <= null) approximates p-value for H1: mean > null
        p_value = sum(1 for m in boot if m <= null_hypothesis) / len(boot)
    else:
        from scipy.stats import ttest_1samp
        result = ttest_1samp(arr, null_hypothesis, alternative="greater")
        p_value = float(result.pvalue)
        if math.isnan(p_value):
            p_value = 0.5

    return max(0.0, min(1.0, 1 - p_value))


# ── DSI (Direction Strength Index) ──────────────────────────────────

def compute_dsi(
    sharpes: list[float],
    null_hypothesis: float = DEFAULT_NULL_SHARPE,
    submission_bar: float = SUBMISSION_SHARPE,
) -> dict:
    """Compose DSI from four signals:

    ① Significance (0.30): Is mean Sharpe credibly above random noise?
    ② Ceiling    (0.25): How good is the best individual result?
    ③ Pass rate  (0.25): Wilson lower bound on fraction passing submission bar.
    ④ Consistency(0.20): Inverse coefficient of variation (stability).
    """
    n = len(sharpes)
    if n == 0:
        return {
            "dsi": 0.0, "s_ttest": 0.0, "s_ceiling": 0.0,
            "s_passrate": 0.0, "s_consist": 0.0,
            "mean": 0.0, "std": 0.0, "max": 0.0, "n": 0,
        }

    arr = np.asarray(sharpes, dtype=float)
    mean = float(arr.mean())
    std = float(arr.std())
    max_val = float(arr.max())

    # ① significance
    s_ttest = significance_score(sharpes, null_hypothesis)

    # ② ceiling — normalize best individual to [0,1] using 2*submission_bar as ceiling
    s_ceiling = min(1.0, max_val / (2 * submission_bar))

    # ③ passrate — Wilson lower bound
    passed = int(sum(1 for s in sharpes if s >= submission_bar))
    s_passrate = wilson_lower_bound(passed, n)

    # ④ consistency — inverse CV, scaled to [0,1]
    cv = std / (abs(mean) + 1e-6)
    s_consist = 1.0 / (1.0 + cv)

    dsi = 0.30 * s_ttest + 0.25 * s_ceiling + 0.25 * s_passrate + 0.20 * s_consist

    return {
        "dsi": round(float(dsi), 4),
        "s_ttest": round(s_ttest, 4),
        "s_ceiling": round(s_ceiling, 4),
        "s_passrate": round(s_passrate, 4),
        "s_consist": round(s_consist, 4),
        "mean": round(mean, 4),
        "std": round(std, 4),
        "max": round(max_val, 4),
        "n": n,
        "passed": passed,
    }


# ── Signal Light assignment with 5 safeguards ───────────────────────

# DSI → signal thresholds.
DSI_GREEN = 0.60
DSI_YELLOW = 0.35
DSI_RED = 0.18


def assign_signal(
    dsi_info: dict,
    operator_family_count: int,
    sharpes: list[float] | None = None,
    prev_round_mean: float | None = None,
) -> dict:
    """Map DSI + safeguards to a signal light.

    Safeguards (applied in order):
      1. Small sample: n<5 caps at YELLOW; 5≤n<10 cannot be DEAD.
      2. Ceiling protection: max Sharpe ≥ 1.2 cannot be DEAD.
      3. Bimodal protection: BC > 0.556 with n≥8 upgrades DEAD→RED.
      4. Triple evidence for DEAD: need n≥10 AND mean<0.3 AND max<0.8 AND ≥4 families.
      5. Trend protection: mean improving over previous round upgrades RED→YELLOW.
    """
    n = int(dsi_info.get("n", 0))
    mean = float(dsi_info.get("mean", 0.0))
    max_val = float(dsi_info.get("max", 0.0))
    dsi = float(dsi_info.get("dsi", 0.0))

    # Base signal from DSI
    if dsi >= DSI_GREEN:
        signal = SIGNAL_GREEN
    elif dsi >= DSI_YELLOW:
        signal = SIGNAL_YELLOW
    elif dsi >= DSI_RED:
        signal = SIGNAL_RED
    else:
        signal = SIGNAL_DEAD

    reasons: list[str] = []

    # Safeguard 1 — small sample
    if n < 5 and signal in (SIGNAL_RED, SIGNAL_DEAD, SIGNAL_GREEN):
        signal = SIGNAL_YELLOW
        reasons.append(f"small_sample(n={n}<5)_cap_yellow")
    elif 5 <= n < 10 and signal == SIGNAL_DEAD:
        signal = SIGNAL_RED
        reasons.append(f"small_sample(n={n}<10)_no_dead")

    # Safeguard 2 — ceiling protection
    if max_val >= 1.2 and signal == SIGNAL_DEAD:
        signal = SIGNAL_RED
        reasons.append(f"ceiling_protect(max={max_val:.2f}≥1.2)")

    # Safeguard 3 — bimodal protection
    if signal == SIGNAL_DEAD and sharpes and len(sharpes) >= 8:
        bc = bimodality_coefficient(sharpes)
        if bc > 0.556:
            signal = SIGNAL_RED
            reasons.append(f"bimodal_protect(BC={bc:.3f})")

    # Safeguard 4 — triple evidence for DEAD
    if signal == SIGNAL_DEAD:
        evidence_ok = (n >= 10 and mean < 0.3 and max_val < 0.8
                       and operator_family_count >= 4)
        if not evidence_ok:
            signal = SIGNAL_RED
            reasons.append(
                f"insufficient_evidence_for_dead(n={n},mean={mean:.2f},"
                f"max={max_val:.2f},families={operator_family_count})"
            )

    # Safeguard 5 — trend protection
    if (prev_round_mean is not None and mean > prev_round_mean
            and signal == SIGNAL_RED):
        signal = SIGNAL_YELLOW
        reasons.append(f"trend_improving({prev_round_mean:.2f}→{mean:.2f})")

    # Attach recommended action
    action_map = {
        SIGNAL_GREEN: "deep_dive",        # add budget, conservative enhance
        SIGNAL_YELLOW: "cautious_enhance", # try 1-2 structural variants
        SIGNAL_RED: "structural_change",   # aggressive/ultra-aggressive
        SIGNAL_DEAD: "abandon",            # discard, record anti-pattern
    }

    return {
        "signal": signal,
        "action": action_map[signal],
        "reasons": reasons,
    }


# ── Mann-Whitney U: round-over-round comparison ─────────────────────

def compare_rounds(round_a_sharpes: list[float],
                   round_b_sharpes: list[float]) -> dict:
    """Statistically compare two rounds of Sharpe values.

    round_a = earlier round, round_b = newer round.
    Returns effect size r in [-1, 1] (positive = round_b is better).
    """
    from scipy.stats import mannwhitneyu
    n_a = len(round_a_sharpes)
    n_b = len(round_b_sharpes)
    if n_a == 0 or n_b == 0:
        return {"ok": False, "reason": "empty_round", "n_a": n_a, "n_b": n_b}

    result = mannwhitneyu(round_b_sharpes, round_a_sharpes,
                          alternative="two-sided")
    u_stat = float(result.statistic)
    p_value = float(result.pvalue)
    effect_size = 2 * u_stat / (n_a * n_b) - 1

    if effect_size > 0.5:
        interp = "large_improvement"
    elif effect_size > 0.3:
        interp = "medium_improvement"
    elif effect_size > 0.0:
        interp = "slight_improvement"
    elif effect_size > -0.3:
        interp = "stagnant"
    elif effect_size > -0.5:
        interp = "medium_regression"
    else:
        interp = "large_regression"

    return {
        "ok": True,
        "u_stat": u_stat,
        "p_value": round(p_value, 4),
        "effect_size": round(float(effect_size), 4),
        "significant": p_value < 0.05,
        "interpretation": interp,
        "n_a": n_a,
        "n_b": n_b,
    }
