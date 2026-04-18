"""Stage INSPECT: attach simulation settings to ideas.

Flow: parse_idea_file → fetch_sim_options (cached) → resolve_settings → LLM chooses → build_alpha_list
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import requests

# Ensure vendor scripts are importable
VENDOR_DIR = Path(__file__).resolve().parent / "scripts" / "vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from parse_idea_file import build_context, IdeaContext
from resolve_settings import resolve_candidates
from build_alpha_list import _load_json

import ace_lib
from llm_counter import record_llm_request

logger = logging.getLogger("stage_inspect")


_LOCAL_SIGNATURE_HINTS = {
    "group_mean": "group_mean(x, weight, group)",
    "group_std_dev": "group_std_dev(x, group)",
    "group_zscore": "group_zscore(x, group)",
    "group_rank": "group_rank(x, group)",
    "group_neutralize": "group_neutralize(x, group)",
    "group_normalize": "group_normalize(x, group[, constant_check, tolerance, scale])",
    "winsorize": "winsorize(x, std)",
    "ts_mean": "ts_mean(x, d)",
    "ts_std_dev": "ts_std_dev(x, d)",
    "ts_delay": "ts_delay(x, d)",
    "ts_delta": "ts_delta(x, d)",
    "ts_backfill": "ts_backfill(x, d)",
    "ts_zscore": "ts_zscore(x, d)",
}


def _extract_function_names(*texts: str) -> set[str]:
    names: set[str] = set()
    for text in texts:
        if not text:
            continue
        names.update(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
    return names


# ── LLM helper ──────────────────────────────────────────────────────

def _call_llm(api_key: str, base_url: str, model: str,
              system_prompt: str, user_prompt: str,
              counter_path: str | Path | None = None,
              stage: str = "inspect") -> str:
    """Call OpenAI-compatible chat completion (non-streaming)."""
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
        resp = requests.post(url, headers=headers, json=payload, timeout=(15, 600))
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            body = resp.text[:500]
            raise RuntimeError(f"LLM API error {resp.status_code} (model={model}): {body}")
        break
    return resp.json()["choices"][0]["message"]["content"]


def _llm_choose_settings(api_key: str, base_url: str, model: str,
                          idea_ctx: dict, candidates: dict,
                          fixed_universe: str | None = None,
                          system_override: str | None = None,
                          counter_path: str | Path | None = None) -> dict:
    """Ask LLM to pick simulation settings from valid candidates."""
    choose_fields = "neutralization and decay"
    response_schema = '{"neutralization": "...", "decay": <int>}'
    if not fixed_universe:
        choose_fields = "neutralization, universe, and decay"
        response_schema = '{"universe": "...", "neutralization": "...", "decay": <int>}'

    system = system_override or (
        "You are a WorldQuant BRAIN expert. Given an alpha idea context and valid simulation "
        f"setting candidates, choose the BEST {choose_fields} for this alpha. "
        "Respond with ONLY a JSON object: "
        f"{response_schema}"
    )
    valid_options = candidates.get("valid_options", [])
    if fixed_universe:
        valid_options = [
            option for option in valid_options
            if str(option.get("universe") or "").upper() == str(fixed_universe).upper()
        ] or valid_options

    user = json.dumps({
        "idea": {
            "dataset": idea_ctx.get("dataset_id"),
            "region": idea_ctx.get("region"),
            "delay": idea_ctx.get("delay"),
            "template": idea_ctx.get("template"),
            "idea_description": idea_ctx.get("idea"),
        },
        "fixed_universe": fixed_universe,
        "candidates": valid_options,
    }, ensure_ascii=False, indent=2)

    raw = _call_llm(api_key, base_url, model, system, user, counter_path=counter_path, stage="inspect")

    # Extract JSON from response
    text = raw.strip()
    if "```" in text:
        for block in text.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith("{"):
                text = block
                break
    return json.loads(text)


def _fetch_or_load_operators(pipeline_dir: Path, session) -> list[dict[str, Any]]:
    """Fetch operator metadata once per pipeline and cache to file."""
    cache = pipeline_dir / "operators_snapshot.json"
    if cache.exists():
        data = _load_json(cache)
        if isinstance(data, list):
            return data

    operators: list[dict[str, Any]] = []
    try:
        df = ace_lib.get_operators(session)
        if "scope" in df.columns:
            df = df[df["scope"].fillna("") == "REGULAR"]
        keep_cols = ["name", "category", "description", "definition", "example"]
        present_cols = [col for col in keep_cols if col in df.columns]
        for row in df[present_cols].drop_duplicates(subset=["name"]).to_dict(orient="records"):
            operator = {"name": row["name"], "category": row.get("category", "")}
            for key in ("description", "definition", "example"):
                value = row.get(key)
                if value:
                    operator[key] = value
            operators.append(operator)
        cache.write_text(json.dumps(operators, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Fetched and cached operators: {cache}")
        return operators
    except Exception as exc:
        logger.warning(f"Failed to fetch operators from ACE, falling back to local validOp.json: {exc}")

    fallback = Path(__file__).resolve().parents[1] / "validOp.json"
    if fallback.exists():
        data = json.loads(fallback.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    return operators


def _select_relevant_operators(
    operators: list[dict[str, Any]],
    raw_idea: dict[str, Any],
    validation_failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep the operator context compact but targeted to the failing template."""
    mentioned_names = _extract_function_names(
        str(raw_idea.get("template") or ""),
        *[str(expr) for expr in (raw_idea.get("expression_list") or [])],
        *[str(item.get("expression") or "") for item in validation_failures],
    )
    invalid_names = set()
    for item in validation_failures:
        for error in item.get("errors") or []:
            match = re.search(r"不允许的运算符:\s*([A-Za-z_][A-Za-z0-9_]*)", str(error))
            if match:
                invalid_names.add(match.group(1))

    selected: dict[str, dict[str, Any]] = {}
    for op in operators:
        name = str(op.get("name") or "")
        if not name:
            continue
        if name in mentioned_names:
            selected[name] = op
            continue
        if invalid_names and any(name.startswith(prefix.rstrip("_")) for prefix in {"group_", "ts_"} if any(inv.startswith(prefix) for inv in invalid_names)):
            selected[name] = op
            continue
        if invalid_names and any(inv.startswith("group_") for inv in invalid_names) and name.startswith("group_"):
            selected[name] = op

    if not selected:
        for op in operators[:80]:
            name = str(op.get("name") or "")
            if name:
                selected[name] = op

    return sorted(selected.values(), key=lambda item: item.get("name", ""))[:120]


def _llm_repair_invalid_idea(
    api_key: str,
    base_url: str,
    model: str,
    raw_idea: dict[str, Any],
    validation_failures: list[dict[str, Any]],
    operators: list[dict[str, Any]],
    system_override: str | None = None,
    counter_path: str | Path | None = None,
) -> dict[str, Any]:
    """Repair invalid expressions without changing the underlying alpha idea."""
    signature_names = _extract_function_names(
        str(raw_idea.get("template") or ""),
        *[str(item.get("expression") or "") for item in validation_failures],
    )
    signature_hints = {
        name: hint for name, hint in _LOCAL_SIGNATURE_HINTS.items()
        if name in signature_names or (name.startswith("group_") and any(sig.startswith("group_") for sig in signature_names))
    }
    if not signature_hints:
        signature_hints = dict(_LOCAL_SIGNATURE_HINTS)

    system = system_override or (
        "You are repairing a WorldQuant BRAIN alpha idea that failed local expression validation. "
        "Keep the same economic meaning and structure, but fix invalid operators, wrong operator names, "
        "wrong argument signatures, and syntax issues. Use only operators from the provided operator list, and follow the "
        "provided local signatures exactly. Respond with ONLY a JSON object: "
        '{"template":"...","idea":"...","expression_list":["..."]}'
    )
    user = json.dumps({
        "task": "Repair the invalid alpha template and expressions so they pass the local validator.",
        "rules": [
            "Do not change the alpha hypothesis unless necessary to make the expression valid.",
            "Prefer minimal edits over rewriting from scratch.",
            "Use only operator names present in operator_list.",
            "If an operator signature is wrong, fix it to match local_signatures.",
            "If all current expressions are invalid, regenerate a fresh expression_list from template and idea using validation_failures as guidance.",
            "Return at least one repaired expression in expression_list.",
        ],
        "raw_idea": {
            "template": raw_idea.get("template", ""),
            "idea": raw_idea.get("idea", ""),
            "expression_list": raw_idea.get("expression_list", []),
        },
        "validation_failures": validation_failures[:30],
        "local_signatures": signature_hints,
        "operator_list": operators,
    }, ensure_ascii=False, indent=2)

    raw = _call_llm(api_key, base_url, model, system, user, counter_path=counter_path, stage="inspect")

    text = raw.strip()
    if "```" in text:
        for block in text.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith("{"):
                text = block
                break

    repaired = json.loads(text)
    if not isinstance(repaired, dict):
        raise ValueError("LLM repair response is not a JSON object")
    expressions = repaired.get("expression_list") or []
    if not isinstance(expressions, list) or not all(isinstance(item, str) for item in expressions):
        raise ValueError("LLM repair response must contain expression_list: list[str]")
    return {
        "template": str(repaired.get("template") or raw_idea.get("template") or ""),
        "idea": str(repaired.get("idea") or raw_idea.get("idea") or ""),
        "expression_list": expressions,
    }


def _should_attempt_llm_repair(ctx: IdeaContext) -> bool:
    """Repair only validator-style operator/signature issues, not arbitrary empty ideas."""
    if ctx.expression_list or not ctx.validation_failures:
        return False

    repair_markers = (
        "不允许的运算符",
        "需要至少",
        "参数",
        "operator",
        "signature",
        "非法字符",
        "语法错误",
        "无法解析表达式",
    )
    for item in ctx.validation_failures:
        for error in item.get("errors") or []:
            text = str(error)
            if any(marker in text for marker in repair_markers):
                return True
    return False


# ── Sim options cache ────────────────────────────────────────────────

def _fetch_or_load_sim_options(pipeline_dir: Path, session) -> dict:
    """Fetch sim options once per pipeline, cache to file."""
    cache = pipeline_dir / "sim_options_snapshot.json"
    if cache.exists():
        return _load_json(cache)

    df = ace_lib.get_instrument_type_region_delay(session)
    payload = {"rows": df.to_dict(orient="records")}
    cache.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Fetched and cached sim options: {cache}")
    return payload


# ── Public API ───────────────────────────────────────────────────────

def inspect_idea(
    idea_path: Path,
    output_dir: Path,
    session,
    pipeline_dir: Path,
    llm_config: dict,
    fixed_universe: str | None = None,
    repair_invalid_on_retry: bool = False,
) -> Path:
    """Run the full inspect flow for one idea file.

    Args:
        idea_path: absolute path to idea_*.json
        output_dir: directory to write inspect outputs (idea_context, candidates, alpha_list)
        session: ace_lib session
        pipeline_dir: pipeline root (for sim_options cache)
        llm_config: {"api_key", "base_url", "model"}

    Returns:
        Path to the generated alpha_list.json
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_idea = _load_json(idea_path)
    prompt_overrides = llm_config.get("prompt_overrides") or {}

    # Step 1: parse idea
    ctx = build_context(idea_path)
    should_repair_on_retry = repair_invalid_on_retry and not ctx.expression_list and bool(ctx.validation_failures)
    if (should_repair_on_retry or _should_attempt_llm_repair(ctx)) and repair_invalid_on_retry:
        invalid_ctx_path = output_dir / "idea_context_invalid.json"
        invalid_ctx_path.write_text(json.dumps(asdict(ctx), ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"INSPECT repairing invalid expressions via validator feedback: {idea_path.name}")

        operators = _select_relevant_operators(
            _fetch_or_load_operators(pipeline_dir, session),
            raw_idea,
            ctx.validation_failures,
        )
        repaired_idea = _llm_repair_invalid_idea(
            api_key=llm_config["api_key"],
            base_url=llm_config.get("base_url", "https://api.deepseek.com/v1"),
            model=llm_config.get("model", "deepseek-reasoner"),
            raw_idea=raw_idea,
            validation_failures=ctx.validation_failures,
            operators=operators,
            system_override=str(prompt_overrides.get("inspect_repair_system_prompt") or "") or None,
            counter_path=llm_config.get("counter_path"),
        )

        repair_meta = {
            "source_idea": str(idea_path),
            "repaired": repaired_idea,
            "validation_failures": ctx.validation_failures,
            "operators_used": operators,
        }
        (output_dir / "repair_attempt.json").write_text(
            json.dumps(repair_meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        repaired_idea_path = output_dir / idea_path.name
        repaired_idea_path.write_text(json.dumps(repaired_idea, ensure_ascii=False, indent=2), encoding="utf-8")
        ctx = build_context(repaired_idea_path)

    ctx_dict = asdict(ctx)
    ctx_path = output_dir / "idea_context.json"
    ctx_path.write_text(json.dumps(ctx_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Parsed idea: {len(ctx.expression_list)} expressions")

    if not ctx.expression_list:
        raise ValueError(f"No valid expressions in {idea_path}")

    # Step 2: resolve candidates
    sim_options = _fetch_or_load_sim_options(pipeline_dir, session)
    candidates = resolve_candidates(ctx_dict, sim_options)
    cand_path = output_dir / "settings_candidates.json"
    cand_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    # Step 3: LLM chooses settings
    chosen = _llm_choose_settings(
        api_key=llm_config["api_key"],
        base_url=llm_config.get("base_url", "https://api.deepseek.com/v1"),
        model=llm_config.get("model", "deepseek-reasoner"),
        idea_ctx=ctx_dict,
        candidates=candidates,
        fixed_universe=fixed_universe,
        system_override=str(prompt_overrides.get("inspect_settings_system_prompt") or "") or None,
        counter_path=llm_config.get("counter_path"),
    )
    logger.info(f"LLM chose settings: {chosen}")

    # Merge chosen settings with defaults
    resolved = {
        "region": ctx.region,
        "delay": ctx.delay,
        "universe": fixed_universe or chosen.get("universe", "TOP3000"),
        "neutralization": chosen.get("neutralization", "SUBINDUSTRY"),
        "decay": chosen.get("decay", 0),
        "truncation": 0.08,
        "pasteurization": "ON",
        "testPeriod": "P0Y0M0D",
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "maxTrade": "OFF",
    }
    settings_path = output_dir / "chosen_settings.json"
    settings_path.write_text(json.dumps({"resolved": resolved}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Step 4: build alpha list
    alpha_list = []
    for expr in ctx.expression_list:
        alpha_list.append(
            ace_lib.generate_alpha(
                regular=expr,
                alpha_type="REGULAR",
                region=resolved["region"],
                universe=resolved["universe"],
                delay=int(resolved["delay"]),
                decay=int(resolved["decay"]),
                neutralization=resolved["neutralization"],
                truncation=float(resolved["truncation"]),
                pasteurization=resolved["pasteurization"],
                test_period=resolved["testPeriod"],
                unit_handling=resolved["unitHandling"],
                nan_handling=resolved["nanHandling"],
                max_trade=resolved["maxTrade"],
                visualization=False,
            )
        )

    alpha_list_path = output_dir / "alpha_list.json"
    alpha_list_path.write_text(json.dumps(alpha_list, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Built alpha list: {len(alpha_list)} alphas → {alpha_list_path}")

    return alpha_list_path
