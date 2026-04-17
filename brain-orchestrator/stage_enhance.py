"""Stage ENHANCE: invoke enhance_template.py for selected ideas.

Wraps the existing trailSomeAlphas/enhance_template.py as a subprocess
with the correct environment variables for single or cross enhancement.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("stage_enhance")

# Locate the enhance_template.py script
_TRAIL_DIR = Path(__file__).resolve().parent.parent / "trailSomeAlphas"
ENHANCE_SCRIPT = _TRAIL_DIR / "enhance_template.py"


def enhance(
    action: dict,
    pipeline_dir: Path,
    round_num: int,
    llm_config: dict,
    config: dict | None = None,
) -> list[Path]:
    """Execute one enhancement action.

    Args:
        action: {"mode": "single"|"cross", "style": "...", "idea_files": [...]}
        pipeline_dir: pipeline root directory
        round_num: current enhancement round number
        llm_config: {"api_key", "base_url", "model"}
        config: pipeline config dict (data_type, brain_username, brain_password, etc.)

    Returns:
        List of newly created enhanced_templates_*.json files.
    """
    idea_files = action.get("idea_files", [])
    mode = action.get("mode", "single")
    style = action.get("style", "balanced")

    if not idea_files:
        logger.warning("Enhancement action has no idea files")
        return []

    # Resolve absolute paths — idea_files may be relative to pipeline_dir
    abs_paths = []
    for f in idea_files:
        p = Path(f)
        if not p.is_absolute():
            p = pipeline_dir / p
        if not p.exists():
            logger.error(f"Idea file not found: {p}")
            return []
        abs_paths.append(p)

    # Prepare output directory
    enhance_dir = pipeline_dir / "enhance" / f"round_{round_num}"
    enhance_dir.mkdir(parents=True, exist_ok=True)

    # Build environment for enhance_template.py
    env = os.environ.copy()
    env["MOONSHOT_API_KEY"] = llm_config["api_key"]
    env["MOONSHOT_BASE_URL"] = llm_config.get("base_url", "https://api.moonshot.cn/v1")
    env["MOONSHOT_MODEL"] = llm_config.get("model", "kimi-k2.5")
    env["PIPELINE_LLM_COUNTER_PATH"] = str((pipeline_dir / "llm_requests.jsonl"))
    env["PIPELINE_LLM_COUNTER_STAGE"] = "enhance"
    env["CROSS_PROMPT_STYLE"] = style

    # Pass DATA_TYPE for dataset CSV preparation (MATRIX/VECTOR)
    cfg = config or {}
    prompt_overrides = cfg.get("prompt_overrides") or {}
    dt = (cfg.get("data_type") or "MATRIX").strip().upper()
    if dt not in ("MATRIX", "VECTOR"):
        dt = "MATRIX"
    env["DATA_TYPE"] = dt

    # Pass UNIVERSE so enhance_template.py uses the correct universe (e.g. TOPSC1600, not TOP3000)
    universe = (cfg.get("universe") or "TOP3000").strip().upper()
    env["UNIVERSE"] = universe

    # Pass BRAIN credentials so enhance_template.py can auto-login
    if cfg.get("brain_username"):
        env["BRAIN_USERNAME"] = cfg["brain_username"]
    if cfg.get("brain_password"):
        env["BRAIN_PASSWORD"] = cfg["brain_password"]

    if mode == "cross":
        if prompt_overrides.get("enhance_cross_system_prompt"):
            env["PIPELINE_ENHANCE_CROSS_SYSTEM_PROMPT"] = str(prompt_overrides["enhance_cross_system_prompt"])
    else:
        if prompt_overrides.get("enhance_single_system_prompt"):
            env["PIPELINE_ENHANCE_SINGLE_SYSTEM_PROMPT"] = str(prompt_overrides["enhance_single_system_prompt"])

    env["PYTHONIOENCODING"] = "utf-8"

    if mode == "cross" and len(abs_paths) >= 2:
        env["IDEA_JSON_LIST"] = ";".join(str(p) for p in abs_paths)
        env.pop("IDEA_JSON", None)
    else:
        env["IDEA_JSON"] = str(abs_paths[0])
        env.pop("IDEA_JSON_LIST", None)

    logger.info(f"Running enhance_template.py mode={mode} style={style} "
                f"ideas={[p.name for p in abs_paths]}")

    if not ENHANCE_SCRIPT.exists():
        raise FileNotFoundError(f"enhance_template.py not found at {ENHANCE_SCRIPT}")

    max_retries = 2
    last_err = None
    result = None
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                [sys.executable, str(ENHANCE_SCRIPT)],
                env=env,
                cwd=str(_TRAIL_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=900,
            )
            if result.returncode != 0:
                last_err = f"enhance_template.py 退出码={result.returncode}, stderr: {result.stderr[-300:]}"
                logger.error(f"enhance_template.py failed (mode={mode}, attempt {attempt}/{max_retries}):\nstdout: {result.stdout[-800:]}\nstderr: {result.stderr[-800:]}")
                if attempt < max_retries:
                    logger.info(f"enhance_template.py 将重试 ({attempt}/{max_retries})")
                    continue
                raise RuntimeError(last_err)
            logger.info(f"enhance_template.py succeeded (mode={mode}, attempt {attempt})")
            break
        except subprocess.TimeoutExpired:
            last_err = f"enhance_template.py 超时(900s), attempt {attempt}/{max_retries}"
            logger.error(last_err)
            if attempt < max_retries:
                logger.info(f"enhance_template.py 超时后重试 ({attempt}/{max_retries})")
                continue
            raise RuntimeError(last_err)

    # Find the output files: enhance_template writes to the same directory as the primary idea
    primary_dir = abs_paths[0].parent
    enhanced_files = sorted(primary_dir.glob("enhanced_templates_*.json"), key=lambda p: p.stat().st_mtime)

    if not enhanced_files:
        # Log stdout for debugging when no output files are found
        logger.warning(f"No enhanced_templates_*.json found in {primary_dir} after enhancement (mode={mode})")
        if result.stdout:
            logger.info(f"enhance_template.py stdout (last 500): {result.stdout[-500:]}")
        return []

    # Move the newest enhanced file(s) to our round directory
    moved = []
    latest = enhanced_files[-1]
    dest = enhance_dir / latest.name
    if not dest.exists():
        dest.write_text(latest.read_text(encoding="utf-8"), encoding="utf-8")
    moved.append(dest)
    logger.info(f"Enhanced templates at: {dest}")

    # Also check for enhanced_final_expressions_*.json (has expressions)
    expr_files = sorted(primary_dir.glob("enhanced_final_expressions_*.json"), key=lambda p: p.stat().st_mtime)
    if expr_files:
        latest_expr = expr_files[-1]
        expr_dest = enhance_dir / latest_expr.name
        if not expr_dest.exists():
            expr_dest.write_text(latest_expr.read_text(encoding="utf-8"), encoding="utf-8")

    return moved
