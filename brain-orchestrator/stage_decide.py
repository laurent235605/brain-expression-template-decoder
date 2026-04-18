"""Stage DECIDE: AI picks enhancement strategy from simulated pool.

Rules pre-filter by metric thresholds, then LLM decides:
  - Which ideas to enhance (single or cross)
  - Enhancement style (conservative / balanced / aggressive / ultra-aggressive)
  - Weak+strong pairings for cross enhancement
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

import direction_radar as dr
from llm_counter import record_llm_request

logger = logging.getLogger("stage_decide")

# ── Default decision system prompt ──────────────────────────────────
# Based on WorldQuant BRAIN research best practices, ATOM principle,
# Alpha submission test requirements, and community experience.

DEFAULT_DECIDE_PROMPT = """You are a senior WorldQuant BRAIN alpha research strategist with deep quant finance expertise.

## Your Task
Given a pool of simulated alpha ideas with metrics, decide which to enhance and how.

## WorldQuant BRAIN Alpha Quality Standards (Submission Tests)
- **Sharpe Ratio**: ≥1.25 (delay-1, in-sample). Higher is better. Values 0.8–1.24 are promising but need improvement.
- **Fitness**: ≥1.0 (delay-1). Fitness = Sharpe × √(|returns|). Values 0.5–0.99 have potential.
- **Turnover**: Must be between 1%–70%. High turnover (>50%) eats into PnL. Ideal: 10%–40%.
- **Weight concentration**: Top single stock weight <10%. Diversification matters.
- **Self-correlation**: Must be <0.7 vs existing alphas in the pool.

## ATOM Principle (4 Pillars of Alpha Design)
1. **Applicability**: Expression must work across the full universe (no NaN dominance)
2. **Trustworthiness**: Must reflect genuine economic signals, not overfitting
3. **Originality**: Should be distinct from common/known approaches (low self-corr)
4. **Magnitude**: Signal strength (Sharpe/fitness) must be sufficient

## Enhancement Decision Framework
### When to Single-Enhance (one idea alone):
- Strong ideas (sharpe ≥ 0.8, fitness ≥ 0.5) that need parameter tuning
- Ideas with good Sharpe but high turnover → add decay/smoothing operators
- Ideas with low fitness but interesting signal → try different neutralization

### When to Cross-Enhance (combine 2+ ideas):
- Pair a strong idea with a weak complementary one (different data angles)
- Combine ideas from same dataset that capture different time horizons
- Merge a high-Sharpe/high-turnover idea with a low-turnover stabilizer

### Style Selection Guide:
- **conservative**: Minor tweaks (add ts_rank, group_neutralize, ts_delta). For ideas already close to passing.
- **balanced**: Moderate changes (operator substitution, decay tuning, signal combination). Default choice.
- **aggressive**: Major restructuring (new operators, cross-sectional transforms, regime filters). For weak ideas with potential.
- **ultra-aggressive**: Complete reimagining of the signal logic. Only for ideas with interesting economic premise but poor metrics.

## Direction Radar Signal Light (read the `radar` field of each candidate)
Each candidate carries a `radar` object with:
- `signal` — GREEN / YELLOW / RED (DEAD candidates are already filtered out)
- `action` — recommended enhancement action (deep_dive / cautious_enhance / structural_change)
- `dsi` — Direction Strength Index in [0,1] (higher is better)
- `sharpe_mean/max/std`, `n_sims`, `passed_submission_bar`
- `operator_families_used` — number of distinct BRAIN operator families in this idea's expressions (max 6). Low (≤2) often means "wrong bait, not empty pond" — try different operator families via structural change rather than abandoning.
- `safeguard_reasons` — why the signal was adjusted (small sample, ceiling protect, trend, ...). Use this as context.

### Mapping signal → recommended action
- **GREEN** (dsi ≥ 0.6): strong evidence of signal. Use `single` enhancement with `conservative` or `balanced` style. Preserve what works; tune parameters/decay.
- **YELLOW** (dsi 0.35–0.60): promising but under-sampled or middling. Use `single` with `balanced` style OR pair with a GREEN anchor via `cross`.
- **RED** (dsi 0.18–0.35): weak signal, needs structural change. Use `aggressive` or `ultra-aggressive` style. If `operator_families_used ≤ 2`, the idea is likely under-explored — try a different operator family. If 4+ families already and still RED, the dataset angle may be weak; consider pairing via `cross` with a stronger idea.

## Decision Rules
- Prioritize GREEN candidates first; then YELLOW; then RED (if paired or if economic story is compelling).
- Don't enhance the same idea file twice in one round.
- Maximum {max_enhance_per_round} enhancement actions per round.
- **IMPORTANT**: Include at least one `cross` action when there are 2+ eligible candidates spanning different signals. Cross-enhancing a GREEN anchor with a YELLOW/RED complementary idea creates unique signal combinations.
- At least 30% of actions should be `cross` when pool has mixed signals.
- If every candidate is RED with ≤2 operator families, issue structural changes (new operator families) rather than skipping.

## Response Format
Respond with ONLY a valid JSON array:
[{{"mode": "single"|"cross", "style": "conservative"|"balanced"|"aggressive"|"ultra-aggressive", "idea_files": ["file1.json", ...], "reason": "brief explanation of why this enhancement strategy"}}]
"""

# ── Thresholds for rules pre-filter ─────────────────────────────────

DEFAULT_THRESHOLDS = {
    "sharpe_min": 0.5,
    "fitness_min": 0.3,
    "turnover_max": 0.9,
    "completed_min": 1,
}


def _call_llm(api_key: str, base_url: str, model: str,
              system_prompt: str, user_prompt: str,
              counter_path: str | Path | None = None,
              stage: str = "decide") -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 1,
    }
    record_llm_request(counter_path, stage=stage, model=model)
    for attempt in range(5):
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    return resp.json()["choices"][0]["message"]["content"]


# ── Data loading helpers (read per-idea raw sharpes + expressions) ──

_COMPLETED_STATUSES = {"COMPLETE", "COMPLETED", "SUCCESS"}


def _load_entry_sharpes(entry: dict, pipeline_dir: Path | None) -> list[float]:
    """Load individual sharpe values for an entry from its sim CSV.

    Returns empty list if CSV is missing or unreadable.
    """
    if not pipeline_dir:
        return []
    csv_rel = entry.get("sim_csv") or ""
    if not csv_rel:
        return []
    csv_path = pipeline_dir / csv_rel
    if not csv_path.exists():
        return []
    try:
        df = pd.read_csv(csv_path, on_bad_lines="skip")
    except Exception as exc:
        logger.warning(f"Failed to read sim CSV for {entry.get('idea_file')}: {exc}")
        return []
    if df.empty or "status" not in df.columns or "sharpe" not in df.columns:
        return []
    status = df["status"].astype(str).str.upper().str.strip()
    completed = df[status.isin(_COMPLETED_STATUSES)]
    if completed.empty:
        return []
    try:
        vals = completed["sharpe"].astype(float).dropna().tolist()
    except Exception:
        return []
    return [float(v) for v in vals if not pd.isna(v)]


def _load_entry_expressions(entry: dict, pipeline_dir: Path | None) -> list[str]:
    """Load the alpha expressions belonging to this idea."""
    if not pipeline_dir:
        return []
    idea_rel = entry.get("idea_file") or ""
    if not idea_rel:
        return []
    idea_path = pipeline_dir / idea_rel
    if not idea_path.exists():
        return []
    try:
        raw = idea_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return []
    exprs = data.get("expression_list") if isinstance(data, dict) else None
    if isinstance(exprs, list):
        return [str(e) for e in exprs if isinstance(e, str)]
    return []


def _compute_prev_round_mean(
    candidates: list[dict],
    current_round: int,
    pipeline_dir: Path | None,
) -> float | None:
    """Aggregate mean Sharpe of previous round (for trend-protection safeguard).

    round 0 = origin "gen"; round N = origin "enhance_round_N".
    """
    if current_round <= 0:
        return None
    prev_tag = "gen" if current_round == 1 else f"enhance_round_{current_round - 1}"
    prev_entries = [c for c in candidates if c.get("origin") == prev_tag]
    all_sharpes: list[float] = []
    for entry in prev_entries:
        all_sharpes.extend(_load_entry_sharpes(entry, pipeline_dir))
    if not all_sharpes:
        return None
    return float(sum(all_sharpes) / len(all_sharpes))


def _detect_current_round(candidates: list[dict]) -> int:
    """Highest round number seen in candidates' origin field."""
    max_round = 0
    for c in candidates:
        origin = str(c.get("origin") or "")
        if origin.startswith("enhance_round_"):
            try:
                max_round = max(max_round, int(origin.split("_")[-1]))
            except (ValueError, IndexError):
                continue
    return max_round


# ── Per-candidate analysis (DSI + signal + family diversity) ────────

def analyze_candidate(
    entry: dict,
    pipeline_dir: Path | None = None,
    prev_round_mean: float | None = None,
) -> dict:
    """Attach radar analysis to a pool entry.

    Returns the original entry merged with:
      _sharpes, _dsi, _family_stats, _signal, _action, _reasons, _tier
    """
    enriched = dict(entry)

    sharpes = _load_entry_sharpes(entry, pipeline_dir)
    expressions = _load_entry_expressions(entry, pipeline_dir)

    # Fallback to sim_summary aggregates when CSV unavailable
    if not sharpes:
        summary = entry.get("sim_summary") or {}
        if summary.get("sharpe_avg") is not None:
            sharpes = [float(summary.get("sharpe_avg") or 0)]
            if summary.get("sharpe_max") is not None:
                sharpes.append(float(summary.get("sharpe_max")))

    family_stats = dr.operator_family_stats(expressions)
    dsi_info = dr.compute_dsi(sharpes) if sharpes else {
        "dsi": 0.0, "n": 0, "mean": 0.0, "max": 0.0, "std": 0.0,
        "s_ttest": 0.0, "s_ceiling": 0.0, "s_passrate": 0.0, "s_consist": 0.0,
        "passed": 0,
    }
    signal_info = dr.assign_signal(
        dsi_info,
        operator_family_count=family_stats["family_count"],
        sharpes=sharpes,
        prev_round_mean=prev_round_mean,
    )

    # Map signal → tier used by LLM decision prompt
    tier_map = {
        dr.SIGNAL_GREEN: "strong",
        dr.SIGNAL_YELLOW: "weak",
        dr.SIGNAL_RED: "weak",
        dr.SIGNAL_DEAD: "discard",
    }

    enriched["_sharpes"] = sharpes
    enriched["_dsi"] = dsi_info
    enriched["_family_stats"] = family_stats
    enriched["_signal"] = signal_info["signal"]
    enriched["_action"] = signal_info["action"]
    enriched["_reasons"] = signal_info["reasons"]
    enriched["_tier"] = tier_map[signal_info["signal"]]
    return enriched


# ── Rules pre-filter (signal-light based) ───────────────────────────

def rules_filter(
    candidates: list[dict],
    thresholds: dict | None = None,
    pipeline_dir: Path | None = None,
    prev_round_mean: float | None = None,
) -> list[dict]:
    """Categorize candidates using the Direction Radar signal light system.

    Falls back to threshold-based classification only when pipeline_dir is
    None (e.g., unit tests without on-disk artifacts).
    """
    # Legacy path: no pipeline_dir → use simple thresholds
    if pipeline_dir is None:
        return _legacy_rules_filter(candidates, thresholds)

    results: list[dict] = []
    discarded: list[tuple[str, str]] = []
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0, "DEAD": 0}

    for entry in candidates:
        summary = entry.get("sim_summary", {})
        completed = int(summary.get("completed") or 0)
        if completed < 1:
            discarded.append((entry.get("idea_file", "?"), "no_completed_sims"))
            continue

        # Turnover is a hard hygiene check — still drops >90% ideas
        turnover_avg = float(summary.get("turnover_avg") or 1)
        if turnover_avg > 0.9:
            discarded.append((entry.get("idea_file", "?"),
                              f"turnover_too_high({turnover_avg:.2f})"))
            continue

        enriched = analyze_candidate(entry, pipeline_dir, prev_round_mean)
        signal = enriched["_signal"]
        counts[signal] += 1

        if signal == dr.SIGNAL_DEAD:
            dsi = enriched["_dsi"]
            discarded.append((entry.get("idea_file", "?"),
                              f"DEAD(dsi={dsi['dsi']}, mean={dsi['mean']}, "
                              f"max={dsi['max']}, fams={enriched['_family_stats']['family_count']})"))
            continue

        results.append(enriched)

    logger.info(
        f"Direction Radar: GREEN={counts['GREEN']}, YELLOW={counts['YELLOW']}, "
        f"RED={counts['RED']}, DEAD={counts['DEAD']}, "
        f"discarded_total={len(discarded)}"
    )
    if discarded:
        for idea, reason in discarded[:5]:
            logger.info(f"  Discarded {idea}: {reason}")
        if len(discarded) > 5:
            logger.info(f"  ... and {len(discarded) - 5} more")

    return results


def _legacy_rules_filter(candidates: list[dict], thresholds: dict | None) -> list[dict]:
    """Fallback threshold-based filter (used when pipeline_dir unavailable)."""
    th = thresholds or DEFAULT_THRESHOLDS
    results = []
    for entry in candidates:
        summary = entry.get("sim_summary", {})
        completed = summary.get("completed", 0)
        if completed < th.get("completed_min", 1):
            continue
        sharpe_avg = float(summary.get("sharpe_avg") or 0)
        fitness_avg = float(summary.get("fitness_avg") or 0)
        turnover_avg = float(summary.get("turnover_avg") or 1)
        if sharpe_avg >= th["sharpe_min"] and fitness_avg >= th["fitness_min"]:
            tier = "strong"
        elif sharpe_avg >= th["sharpe_min"] * 0.5 or fitness_avg >= th["fitness_min"] * 0.5:
            tier = "weak"
        else:
            tier = "discard"
        if turnover_avg > th["turnover_max"]:
            tier = "discard"
        if tier != "discard":
            results.append({**entry, "_tier": tier})
    strong = [r for r in results if r["_tier"] == "strong"]
    weak = [r for r in results if r["_tier"] == "weak"]
    logger.info(f"Legacy rules filter: {len(strong)} strong, {len(weak)} weak, "
                f"{len(candidates) - len(results)} discarded")
    return results


# ── LLM decision ────────────────────────────────────────────────────

def llm_decide(
    filtered: list[dict],
    llm_config: dict,
    iteration: int,
    max_enhance_per_round: int = 4,
    custom_prompt: str = "",
    pipeline_dir: Path | None = None,
) -> list[dict]:
    """Ask LLM to create an enhancement plan from filtered candidates.

    Returns list of enhancement actions:
      [{"mode": "single"|"cross", "style": "...", "idea_files": [...], "reason": "..."}]
    """
    if not filtered:
        logger.info("No candidates passed rules filter — skipping LLM decision")
        return []

    # Build compact pool summary for the LLM
    pool_summary = []
    for entry in filtered:
        item = {
            "idea_file": entry.get("idea_file"),
            "tier": entry.get("_tier"),
            "origin": entry.get("origin"),
            "sim": entry.get("sim_summary", {}),
        }
        # Attach Direction Radar analysis so LLM can reason about signal strength
        if entry.get("_signal"):
            dsi = entry.get("_dsi") or {}
            fam_stats = entry.get("_family_stats") or {}
            item["radar"] = {
                "signal": entry["_signal"],
                "action": entry.get("_action"),
                "dsi": dsi.get("dsi"),
                "sharpe_mean": dsi.get("mean"),
                "sharpe_max": dsi.get("max"),
                "sharpe_std": dsi.get("std"),
                "n_sims": dsi.get("n"),
                "passed_submission_bar": dsi.get("passed"),
                "operator_families_used": fam_stats.get("family_count"),
                "safeguard_reasons": entry.get("_reasons") or [],
            }
        # Read idea content so LLM sees the actual alpha research idea
        if pipeline_dir:
            idea_rel = entry.get("idea_file", "")
            idea_path = pipeline_dir / idea_rel if idea_rel else None
            if idea_path and idea_path.exists():
                try:
                    raw = idea_path.read_text(encoding="utf-8")
                    try:
                        idea_data = json.loads(raw)
                        item["idea"] = idea_data
                    except json.JSONDecodeError:
                        item["idea"] = raw[:2000]
                except Exception:
                    pass
        pool_summary.append(item)

    system = custom_prompt if custom_prompt else DEFAULT_DECIDE_PROMPT.format(
        max_enhance_per_round=max_enhance_per_round,
    )

    user = json.dumps({
        "iteration": iteration,
        "candidates": pool_summary,
    }, ensure_ascii=False, indent=2)

    raw = _call_llm(
        api_key=llm_config["api_key"],
        base_url=llm_config.get("base_url", "https://api.deepseek.com/v1"),
        model=llm_config.get("model", "deepseek-reasoner"),
        system_prompt=system,
        user_prompt=user,
        counter_path=llm_config.get("counter_path"),
        stage="decide",
    )

    # Parse response
    text = raw.strip()
    if "```" in text:
        for block in text.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith("["):
                text = block
                break

    try:
        actions = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"LLM returned invalid JSON: {text[:200]}")
        return _fallback_plan(filtered, max_enhance_per_round)

    if not isinstance(actions, list):
        actions = [actions]

    # Validate and cap
    valid = []
    for a in actions[:max_enhance_per_round]:
        mode = a.get("mode", "single")
        idea_files = a.get("idea_files", [])
        style = a.get("style", "balanced")
        if not idea_files:
            continue
        if mode == "cross" and len(idea_files) < 2:
            mode = "single"
        valid.append({
            "mode": mode,
            "style": style,
            "idea_files": idea_files,
            "reason": a.get("reason", ""),
        })

    # Ensure at least one cross action when enough candidates exist
    has_cross = any(a["mode"] == "cross" for a in valid)
    if not has_cross and len(filtered) >= 2:
        strong = [e for e in filtered if e.get("_tier") == "strong"]
        weak = [e for e in filtered if e.get("_tier") == "weak"]
        used_files = {f for a in valid for f in a["idea_files"]}
        pair = []
        for pool in (strong, weak):
            for e in pool:
                if e["idea_file"] not in used_files and len(pair) < 2:
                    pair.append(e["idea_file"])
        if len(pair) < 2:
            for e in filtered:
                if e["idea_file"] not in used_files and e["idea_file"] not in pair and len(pair) < 2:
                    pair.append(e["idea_file"])
        if len(pair) >= 2:
            if len(valid) >= max_enhance_per_round:
                # Replace last single action with cross
                valid[-1] = {
                    "mode": "cross",
                    "style": "aggressive",
                    "idea_files": pair,
                    "reason": "auto-replaced: ensure cross diversity",
                }
            else:
                valid.append({
                    "mode": "cross",
                    "style": "aggressive",
                    "idea_files": pair,
                    "reason": "auto-injected: ensure cross diversity",
                })
            logger.info(f"Auto-injected cross action: {pair}")

    return valid


def _fallback_plan(filtered: list[dict], max_actions: int) -> list[dict]:
    """Deterministic fallback used when LLM fails OR returns an empty plan.

    Strategy: signal-light aware. Even if LLM gives up, we still attempt
    enhancement for the most promising (by DSI ceiling) candidates.

      GREEN → conservative/balanced single enhancement
      YELLOW → balanced single enhancement
      RED   → aggressive structural change (prefer cross with any GREEN/YELLOW)
      DEAD  → already filtered out upstream

    Always emits at least 1 action when filtered is non-empty.
    """
    def _ceiling(e: dict) -> float:
        dsi = e.get("_dsi") or {}
        return float(dsi.get("max") or e.get("sim_summary", {}).get("sharpe_max") or 0)

    def _sort_key(e: dict) -> tuple:
        dsi = e.get("_dsi") or {}
        return (float(dsi.get("dsi") or 0), _ceiling(e))

    green = sorted([e for e in filtered if e.get("_signal") == dr.SIGNAL_GREEN],
                   key=_sort_key, reverse=True)
    yellow = sorted([e for e in filtered if e.get("_signal") == dr.SIGNAL_YELLOW],
                    key=_sort_key, reverse=True)
    red = sorted([e for e in filtered if e.get("_signal") == dr.SIGNAL_RED],
                 key=_sort_key, reverse=True)

    # Legacy entries without radar analysis — treat by tier
    legacy_strong = [e for e in filtered
                     if not e.get("_signal") and e.get("_tier") == "strong"]
    legacy_weak = [e for e in filtered
                   if not e.get("_signal") and e.get("_tier") == "weak"]

    actions: list[dict] = []
    used: set[str] = set()

    def _push(mode: str, style: str, files: list[str], reason: str):
        for f in files:
            if f in used:
                return
        if not files:
            return
        actions.append({"mode": mode, "style": style,
                        "idea_files": files, "reason": f"fallback: {reason}"})
        used.update(files)

    # 1. GREEN → conservative single
    for e in green:
        if len(actions) >= max_actions:
            break
        _push("single", "conservative", [e["idea_file"]], "GREEN deep_dive")

    # 2. RED + (GREEN|YELLOW) → aggressive cross (structural change with anchor)
    if len(actions) < max_actions:
        anchors = green + yellow
        for red_e in red:
            if len(actions) >= max_actions or not anchors:
                break
            anchor = next((a for a in anchors if a["idea_file"] not in used), None)
            if anchor and red_e["idea_file"] not in used:
                _push("cross", "aggressive",
                      [anchor["idea_file"], red_e["idea_file"]],
                      "RED structural_change paired with anchor")

    # 3. YELLOW → balanced single
    for e in yellow:
        if len(actions) >= max_actions:
            break
        _push("single", "balanced", [e["idea_file"]], "YELLOW cautious_enhance")

    # 4. Legacy strong + weak cross (backward compatible)
    if len(actions) < max_actions and legacy_strong and legacy_weak:
        _push("cross", "aggressive",
              [legacy_strong[0]["idea_file"], legacy_weak[0]["idea_file"]],
              "legacy weak+strong cross")

    # 5. Last resort: ensure at least 1 action if any candidate exists
    if not actions and filtered:
        best = max(filtered, key=_sort_key)
        _push("single", "aggressive", [best["idea_file"]],
              "last-resort: highest DSI candidate")

    return actions[:max_actions]


# ── Public API ───────────────────────────────────────────────────────

def _log_round_comparison(
    candidates: list[dict],
    current_round: int,
    pipeline_dir: Path | None,
) -> None:
    """Log Mann-Whitney U comparison between current and previous round."""
    if current_round <= 0 or pipeline_dir is None:
        return
    prev_tag = "gen" if current_round == 1 else f"enhance_round_{current_round - 1}"
    curr_tag = f"enhance_round_{current_round}"
    prev_sharpes: list[float] = []
    curr_sharpes: list[float] = []
    for c in candidates:
        origin = str(c.get("origin") or "")
        sharpes = _load_entry_sharpes(c, pipeline_dir)
        if origin == prev_tag:
            prev_sharpes.extend(sharpes)
        elif origin == curr_tag:
            curr_sharpes.extend(sharpes)

    if not prev_sharpes or not curr_sharpes:
        return

    result = dr.compare_rounds(prev_sharpes, curr_sharpes)
    if not result.get("ok"):
        return

    logger.info(
        f"Round comparison [{prev_tag} → {curr_tag}]: "
        f"effect_size={result['effect_size']}, p={result['p_value']}, "
        f"verdict={result['interpretation']}, "
        f"significant={result['significant']}"
    )


def decide(
    candidates: list[dict],
    llm_config: dict,
    iteration: int,
    thresholds: dict | None = None,
    max_enhance_per_round: int = 4,
    custom_prompt: str = "",
    pipeline_dir: Path | None = None,
) -> list[dict]:
    """Full decide pipeline: radar analysis → rules filter → LLM plan → fallback.

    Returns list of enhancement action dicts.
    """
    current_round = _detect_current_round(candidates)

    # Cross-round effect test (for logging/telemetry only)
    _log_round_comparison(candidates, current_round, pipeline_dir)

    # Compute previous-round mean for the trend-protection safeguard
    prev_mean = _compute_prev_round_mean(candidates, current_round, pipeline_dir)
    if prev_mean is not None:
        logger.info(f"Previous round mean Sharpe: {prev_mean:.4f}")

    filtered = rules_filter(candidates, thresholds, pipeline_dir=pipeline_dir,
                            prev_round_mean=prev_mean)
    if not filtered:
        logger.info("All candidates filtered out (DEAD/discarded) — nothing to enhance")
        return []

    actions = llm_decide(filtered, llm_config, iteration, max_enhance_per_round,
                         custom_prompt=custom_prompt, pipeline_dir=pipeline_dir)

    # If LLM declined to enhance but we still have promising candidates,
    # fall back deterministically instead of giving up ("本轮无需增强").
    if not actions and filtered:
        logger.warning(
            "LLM returned empty plan but Direction Radar still sees "
            f"{len(filtered)} non-DEAD candidates — applying fallback plan"
        )
        actions = _fallback_plan(filtered, max_enhance_per_round)
        if actions:
            logger.info(f"Fallback plan produced {len(actions)} action(s)")

    return actions
