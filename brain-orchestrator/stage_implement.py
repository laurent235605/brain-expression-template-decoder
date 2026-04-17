"""Stage IMPLEMENT: convert enhanced templates back to idea files with expressions.

Reads enhanced_templates_*.json (list of {template, idea}) and runs
implement_idea.py for each to generate idea_*.json with expression_list.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

logger = logging.getLogger("stage_implement")

# Locate implement_idea.py
_FEATURE_IMPL_DIR = (
    Path(__file__).resolve().parent.parent
    / "trailSomeAlphas"
    / "skills"
    / "brain-feature-implementation"
)
IMPLEMENT_SCRIPT = _FEATURE_IMPL_DIR / "scripts" / "implement_idea.py"


def implement_enhanced(
    enhanced_templates_path: Path,
    dataset_folder: str,
    output_dir: Path,
) -> list[Path]:
    """Implement all enhanced templates, producing idea_*.json with expressions.

    Args:
        enhanced_templates_path: path to enhanced_templates_*.json
        dataset_folder: e.g. "fundamental28_GLB_delay1"
        output_dir: directory to collect output idea files

    Returns:
        List of paths to newly created idea_*.json files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    templates = json.loads(enhanced_templates_path.read_text(encoding="utf-8"))
    if not isinstance(templates, list):
        logger.error(f"Expected list in {enhanced_templates_path}, got {type(templates)}")
        return []

    created_ideas = []
    scripts_dir = _FEATURE_IMPL_DIR / "scripts"

    for idx, item in enumerate(templates, 1):
        template = str(item.get("template") or item.get("enhanced_template") or "").strip()
        idea_text = str(item.get("idea") or "").strip()
        if not template:
            logger.warning(f"Template {idx} is empty, skipping")
            continue

        logger.info(f"[{idx}/{len(templates)}] Implementing: {template[:60]}...")

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(IMPLEMENT_SCRIPT),
                    "--template", template,
                    "--dataset", dataset_folder,
                    "--idea", idea_text,
                ],
                cwd=str(scripts_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            if result.returncode != 0:
                logger.error(f"implement_idea.py failed for template {idx}: {result.stderr[-300:]}")
                continue
        except subprocess.TimeoutExpired:
            logger.error(f"implement_idea.py timed out for template {idx}")
            continue

    # Collect output idea files from the dataset folder
    data_dir = _FEATURE_IMPL_DIR / "data" / dataset_folder
    if data_dir.exists():
        idea_files = sorted(data_dir.glob("*_idea_*.json"), key=lambda p: p.stat().st_mtime)
        # Copy newly created files to output_dir
        for idea_file in idea_files:
            dest = output_dir / idea_file.name
            if not dest.exists():
                dest.write_text(idea_file.read_text(encoding="utf-8"), encoding="utf-8")
                created_ideas.append(dest)

    logger.info(f"Implemented {len(created_ideas)} new idea files from {len(templates)} templates")
    return created_ideas
