from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def record_llm_request(counter_path: str | Path | None, stage: str, model: str = "", extra: dict[str, Any] | None = None) -> None:
    if not counter_path or not stage:
        return
    path = Path(counter_path)
    event = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": str(stage),
    }
    if model:
        event["model"] = str(model)
    if isinstance(extra, dict) and extra:
        event["extra"] = extra
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def summarize_llm_requests(counter_path: str | Path | None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total": 0,
        "by_stage": {},
        "last_request": None,
    }
    if not counter_path:
        return summary

    path = Path(counter_path)
    if not path.exists():
        return summary

    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                stage = str(event.get("stage") or "unknown")
                summary["total"] += 1
                summary["by_stage"][stage] = int(summary["by_stage"].get(stage) or 0) + 1
                summary["last_request"] = {
                    "at": event.get("at"),
                    "stage": stage,
                    "model": event.get("model", ""),
                }
    except Exception:
        return summary

    return summary