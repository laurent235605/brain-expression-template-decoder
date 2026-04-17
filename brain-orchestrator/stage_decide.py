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

import requests

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

## Decision Rules
- Prioritize ideas closest to passing submission tests (sharpe 0.8–1.2 range)
- Strong ideas (sharpe ≥ 1.0) → single-enhance with conservative/balanced style
- Weak ideas (sharpe 0.3–0.8) → cross-enhance with stronger partners
- Strong + weak complementary pair → allow cross-enhance when the strong idea is structurally solid but missing diversity, and the weak idea contributes a distinct operator path, horizon, or economic angle
- Very weak ideas (sharpe < 0.3) → skip unless the economic logic is compelling
- Don't enhance the same idea file twice in one round
- Maximum {max_enhance_per_round} enhancement actions per round
- **IMPORTANT**: You MUST include at least one cross-enhancement action when there are 2+ eligible candidates. Cross-enhancing creates unique signal combinations that single-enhance cannot achieve.
- At least 30% of actions should be cross-enhancement (pairing 2 complementary ideas)

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


# ── Rules pre-filter ────────────────────────────────────────────────

def rules_filter(candidates: list[dict], thresholds: dict | None = None) -> list[dict]:
    """Apply metric-based rules and categorize ideas as strong/weak/discard."""
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

        # Classify
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
    logger.info(f"Rules filter: {len(strong)} strong, {len(weak)} weak, "
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
        base_url=llm_config.get("base_url", "https://api.moonshot.cn/v1"),
        model=llm_config.get("model", "kimi-k2.5"),
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
    """Simple deterministic fallback when LLM fails."""
    strong = [e for e in filtered if e.get("_tier") == "strong"]
    weak = [e for e in filtered if e.get("_tier") == "weak"]

    actions = []
    # Cross-enhance weak+strong pair first (higher priority)
    if weak and strong:
        actions.append({
            "mode": "cross",
            "style": "aggressive",
            "idea_files": [strong[0]["idea_file"], weak[0]["idea_file"]],
            "reason": "fallback: weak+strong cross",
        })

    # Single-enhance top strong ideas
    for e in strong[:max(1, max_actions // 2)]:
        if len(actions) >= max_actions:
            break
        if e["idea_file"] in (actions[0]["idea_files"] if actions else []):
            continue
        actions.append({
            "mode": "single",
            "style": "balanced",
            "idea_files": [e["idea_file"]],
            "reason": "fallback: top strong idea",
        })

    return actions[:max_actions]


# ── Public API ───────────────────────────────────────────────────────

def decide(
    candidates: list[dict],
    llm_config: dict,
    iteration: int,
    thresholds: dict | None = None,
    max_enhance_per_round: int = 4,
    custom_prompt: str = "",
    pipeline_dir: Path | None = None,
) -> list[dict]:
    """Full decide pipeline: rules filter → LLM plan.

    Returns list of enhancement action dicts.
    """
    filtered = rules_filter(candidates, thresholds)
    if not filtered:
        return []
    return llm_decide(filtered, llm_config, iteration, max_enhance_per_round,
                      custom_prompt=custom_prompt, pipeline_dir=pipeline_dir)
