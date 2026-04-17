"""Central pool manager for the autopilot pipeline.

The pool is an append-only list of idea entries tracking their lifecycle
from generation through simulation and enhancement.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class PoolEntry:
    idea_file: str                        # relative path to idea_*.json
    origin: str = "gen"                   # "gen" or "enhance_round_N"
    enhanced_from: list[str] = field(default_factory=list)  # parent idea files
    inspect_status: str = "pending"       # pending / done / error
    alpha_list_file: str = ""             # relative path to alpha_list.json
    sim_status: str = "pending"           # pending / running / done / error
    sim_location: str = ""                # BRAIN API simulation progress URL
    sim_csv: str = ""                     # relative path to simulation CSV
    sim_summary: dict = field(default_factory=dict)  # {count, completed, sharpe_avg, ...}
    enhance_selected: bool = False        # whether AI selected this for enhancement
    enhance_mode: str = ""                # "single" or "cross"
    enhance_status: str = ""              # selected / running / done / error
    enhance_error: str = ""
    error: str = ""


class PoolManager:
    """Thread-safe manager for the pipeline's central pool.json."""

    def __init__(self, pool_path: Path):
        self._path = pool_path
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._load()

    # ── persistence ──────────────────────────────────────────────────

    def _load(self):
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                self._entries = raw if isinstance(raw, list) else []
            except Exception:
                self._entries = []
        else:
            self._entries = []

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._entries, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    # ── mutations ────────────────────────────────────────────────────

    def add(self, entry: PoolEntry) -> int:
        """Append-only add. Returns the index."""
        with self._lock:
            self._entries.append(asdict(entry))
            self._save()
            return len(self._entries) - 1

    def add_many(self, entries: list[PoolEntry]) -> list[int]:
        with self._lock:
            indices = []
            for e in entries:
                self._entries.append(asdict(e))
                indices.append(len(self._entries) - 1)
            self._save()
            return indices

    def update(self, index: int, **kwargs) -> None:
        """Update fields of an existing entry by index."""
        with self._lock:
            if 0 <= index < len(self._entries):
                self._entries[index].update(kwargs)
                self._save()

    def update_by_idea(self, idea_file: str, **kwargs) -> None:
        """Update entry matching a specific idea_file."""
        with self._lock:
            for entry in self._entries:
                if entry.get("idea_file") == idea_file:
                    entry.update(kwargs)
            self._save()

    def claim_for_sim(self, idea_file: str) -> bool:
        """Atomically check if idea is still pending_sim and set to running.

        Returns True if successfully claimed, False if already taken.
        """
        with self._lock:
            for entry in self._entries:
                if (entry.get("idea_file") == idea_file
                        and entry.get("inspect_status") == "done"
                        and entry.get("sim_status") == "pending"):
                    entry["sim_status"] = "running"
                    self._save()
                    return True
            return False

    def claim_for_inspect(self, idea_file: str, allow_retry: bool = False) -> bool:
        """Atomically claim an idea for inspect and set inspect_status to running.

        Main loop claims only pending ideas. Manual retry may claim errored ideas.
        Returns True if successfully claimed, False otherwise.
        """
        with self._lock:
            for entry in self._entries:
                if entry.get("idea_file") != idea_file:
                    continue
                status = entry.get("inspect_status")
                if status == "pending" or (allow_retry and status == "error"):
                    entry["inspect_status"] = "running"
                    self._save()
                    return True
            return False

    # ── queries ──────────────────────────────────────────────────────

    def all(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    def get_by_status(self, field_name: str, status: str) -> list[dict]:
        """Get entries where field_name == status."""
        with self._lock:
            return [e for e in self._entries if e.get(field_name) == status]

    def pending_inspect(self) -> list[dict]:
        return self.get_by_status("inspect_status", "pending")

    def pending_sim(self) -> list[dict]:
        return [e for e in self.all()
                if e.get("inspect_status") == "done" and e.get("sim_status") == "pending"]

    @staticmethod
    def _has_sim_success(entry: dict) -> bool:
        summary = entry.get("sim_summary") or {}
        return int(summary.get("completed") or 0) > 0

    def simulated(self) -> list[dict]:
        return [e for e in self.get_by_status("sim_status", "done") if self._has_sim_success(e)]

    def candidates_for_enhance(self) -> list[dict]:
        """Return simulated entries that haven't been selected for enhancement yet."""
        with self._lock:
            return [e for e in self._entries
                    if e.get("sim_status") == "done" and self._has_sim_success(e) and not e.get("enhance_selected")]

    def stats(self) -> dict:
        with self._lock:
            total = len(self._entries)
            inspect_done = sum(1 for e in self._entries if e.get("inspect_status") == "done")
            # Dashboard '已回测' should reflect completed alpha simulations,
            # not merely the number of ideas that produced at least one result.
            sim_done = sum(max(int((e.get("sim_summary") or {}).get("completed") or 0), 0) for e in self._entries)
            enhanced = sum(1 for e in self._entries if e.get("enhance_selected"))
            from_gen = sum(1 for e in self._entries if e.get("origin") == "gen")
            from_enhance = sum(1 for e in self._entries if str(e.get("origin", "")).startswith("enhance"))
            return {
                "total": total,
                "inspect_done": inspect_done,
                "sim_done": sim_done,
                "enhance_selected": enhanced,
                "from_gen": from_gen,
                "from_enhance": from_enhance,
            }
