import concurrent.futures
import argparse
import datetime as dt
import hashlib
import json
import logging
import os
import sys
import time
import threading
import subprocess
import uuid
from pathlib import Path
import pandas as pd
import requests
from typing import List, Dict, Any

try:
    import ace_lib
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "APP"))
    if app_dir not in sys.path:
        sys.path.append(app_dir)
    import ace_lib

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BatchSimulator")
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent

_SUCCESS_SIM_STATUSES = {"COMPLETED", "COMPLETE", "WARNING"}
_TERMINAL_SIM_STATUSES = _SUCCESS_SIM_STATUSES | {"ERROR", "FAIL", "FAILED", "TIMEOUT"}
_ERROR_SIM_STATUSES = {"ERROR", "FAIL", "FAILED", "TIMEOUT"}


def _is_pid_running(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        try:
            proc = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return str(pid) in output and "No tasks are running" not in output
        except Exception:
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _tail_lines(path: Path, max_lines: int) -> List[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    keep = max(1, int(max_lines))
    return lines[-keep:]


def _print_task_status(tasks_dir: Path, task_id: str, tail_lines: int) -> int:
    task_dir = (tasks_dir / task_id).resolve()
    meta_file = task_dir / "meta.json"
    if not meta_file.exists():
        logger.error(f"Task not found: {task_id}")
        logger.error(f"Checked: {task_dir}")
        return 1

    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error(f"Failed to parse task meta: {meta_file}. {exc}")
        return 1

    pid = meta.get("pid")
    alive = _is_pid_running(pid if isinstance(pid, int) else None)
    state = "running" if alive else "exited"
    stdout_log = Path(meta.get("stdout_log") or (task_dir / "stdout.log"))
    stderr_log = Path(meta.get("stderr_log") or (task_dir / "stderr.log"))

    print("=" * 70)
    print("Detached Task Status")
    print(f"task_id: {meta.get('task_id', task_id)}")
    print(f"pid: {pid}")
    print(f"state: {state}")
    print(f"started_at: {meta.get('started_at')}")
    print(f"task_dir: {task_dir}")
    print(f"stdout_log: {stdout_log}")
    print(f"stderr_log: {stderr_log}")
    print("=" * 70)

    stdout_tail = _tail_lines(stdout_log, tail_lines)
    stderr_tail = _tail_lines(stderr_log, tail_lines)

    print(f"--- stdout (last {max(1, int(tail_lines))} lines) ---")
    if stdout_tail:
        for line in stdout_tail:
            print(line)
    else:
        print("<empty>")

    print(f"--- stderr (last {max(1, int(tail_lines))} lines) ---")
    if stderr_tail:
        for line in stderr_tail:
            print(line)
    else:
        print("<empty>")

    return 0


def _build_detached_child_cmd(script_path: Path, raw_argv: List[str]) -> List[str]:
    value_flags = {"--task-id", "--tasks-dir", "--status", "--tail-lines"}
    bool_flags = {"--detached"}
    filtered: List[str] = []
    i = 0
    while i < len(raw_argv):
        token = str(raw_argv[i])
        if token in bool_flags:
            i += 1
            continue
        if token in value_flags:
            i += 2
            continue
        filtered.append(token)
        i += 1
    return [sys.executable, str(script_path)] + filtered


def _launch_detached(cmd: List[str], cwd: Path, task_id: str, tasks_dir: Path, mode: str) -> tuple[int, Path]:
    task_dir = (tasks_dir / task_id).resolve()
    task_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = task_dir / "stdout.log"
    stderr_log = task_dir / "stderr.log"
    meta_file = task_dir / "meta.json"

    popen_kwargs: Dict[str, Any] = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        popen_kwargs["start_new_session"] = True

    with stdout_log.open("a", encoding="utf-8") as out, stderr_log.open("a", encoding="utf-8") as err:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=out,
            stderr=err,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            **popen_kwargs,
        )

    meta = {
        "task_id": task_id,
        "pid": proc.pid,
        "status": "running",
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": mode,
        "command": cmd,
        "cwd": str(cwd),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
    }
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return proc.pid, task_dir


def load_credentials_from_config(config_path: str) -> bool:
    """Load email/password from config JSON and set process env vars for ace_lib."""
    if not config_path:
        return False

    path_obj = Path(config_path)
    if not path_obj.is_absolute():
        path_obj = SKILL_ROOT / path_obj

    if not path_obj.exists():
        return False

    with open(path_obj, "r", encoding="utf-8") as file:
        data = json.load(file)

    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()
    if not email or not password:
        raise ValueError(f"Invalid config file: missing email/password in {path_obj}")

    os.environ["BRAIN_EMAIL"] = email
    os.environ["BRAIN_PASSWORD"] = password
    os.environ["BRAIN_CREDENTIAL_EMAIL"] = email
    os.environ["BRAIN_CREDENTIAL_PASSWORD"] = password
    logger.info(f"Loaded credentials from config file: {path_obj}")
    return True


def resolve_input_path(candidate_path: str, legacy_name: str) -> Path:
    """Resolve input file path with backward-compatible fallback."""
    path_obj = Path(candidate_path)
    if not path_obj.is_absolute():
        path_obj = SKILL_ROOT / path_obj
    if path_obj.exists():
        return path_obj

    legacy_path = SKILL_ROOT / legacy_name
    if legacy_path.exists():
        logger.info(f"Path not found: {path_obj}. Fallback to legacy file: {legacy_path}")
        return legacy_path

    return path_obj


def resolve_output_path(candidate_path: str) -> Path:
    """Resolve output CSV path and ensure parent directory exists."""
    path_obj = Path(candidate_path)
    if not path_obj.is_absolute():
        path_obj = SKILL_ROOT / path_obj
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    return path_obj


def build_default_output_csv_path(alpha_json_path: Path) -> Path:
    """Build deterministic output CSV path from alpha JSON filename."""
    safe_stem = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in alpha_json_path.stem).strip("_")
    if not safe_stem:
        safe_stem = "alpha_list"
    return resolve_output_path(f"outputs/{safe_stem}_simulation_status.csv")

def get_alpha_fingerprint(alpha_data: dict) -> str:
    """
    Generates a unique MD5 hash for an alpha configuration data.
    Keys are sorted to ensure consistent hashing.
    """
    # Create a copy to avoid modifying original
    data_copy = alpha_data.copy()
    # Serialize with sorted keys for consistency
    alpha_json = json.dumps(data_copy, sort_keys=True)
    return hashlib.md5(alpha_json.encode('utf-8')).hexdigest()

def lookINTO_SimError_message(session: requests.Session, locations: List[str]) -> List[dict]:
    """
    Fetches simulation status from a list of location URLs to extract detailed error messages.
    """
    errors = []
    
    for loc in locations:
        if not loc:
            continue
            
        try:
            # Handle full URL or relative path
            target_url = loc if loc.startswith("http") else f"{ace_lib.brain_api_url}{loc}"
            res = session.get(target_url)
            
            if res.status_code == 200:
                data = res.json()
                # Check for various error fields common in Brain API
                error_msg = data.get("message") or data.get("error") or "Unknown error"
                status = data.get("status", "UNKNOWN")
                
                # Only collect if it's actually an error or failed state
                if status in ["ERROR", "FAIL", "FAILED"]:
                    errors.append({
                        "location": loc,
                        "status": status,
                        "message": error_msg,
                        "raw": data
                    })
        except Exception as e:
            logger.error(f"Failed to fetch error details for {loc}: {e}")
            errors.append({"location": loc, "error": str(e)})
            
    return errors

class BatchSimulator:
    def __init__(self, session: ace_lib.SingleSession, output_csv="alpha_simulation_status.csv", cancel_check=None, on_batch_start=None, on_result_saved=None):
        self.session = session
        self.output_csv = output_csv
        self._cancel_check = cancel_check  # callable returning True to abort
        self._on_batch_start = on_batch_start  # callable(progress_url) when batch submission gets Location
        self._on_result_saved = on_result_saved  # callable() after each child result is persisted
        self.completed_fingerprints = set()
        self.csv_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.stats = {
            "skipped": 0,
            "submitted": 0,
            "completed": 0,
            "failed": 0,
        }
        self.csv_columns = [
            "fingerprint",
            "alpha_type",
            "regular_expression",
            "selection_expression",
            "combo_expression",
            "settings_json",
            "simulate_data_json",
            "sim_id",
            "status",
            "timestamp",
            "alpha_id",
            "pnl",
            "sharpe",
            "turnover",
            "fitness",
            "error",
            "error_details",
        ]
        
        # Initialize or load state
        self._load_state()

    def _reset_run_stats(self):
        with self.stats_lock:
            self.stats = {
                "skipped": 0,
                "submitted": 0,
                "completed": 0,
                "failed": 0,
            }

    def _inc_stat(self, key: str, value: int = 1):
        with self.stats_lock:
            self.stats[key] = self.stats.get(key, 0) + value

    @staticmethod
    def _alpha_metadata(alpha_data: dict) -> dict:
        """Build persistent metadata for traceability in CSV."""
        settings = alpha_data.get("settings", {})
        simulate_payload = {k: v for k, v in alpha_data.items() if k != "settings"}
        return {
            "alpha_type": alpha_data.get("type", ""),
            "regular_expression": alpha_data.get("regular", ""),
            "selection_expression": alpha_data.get("selection", ""),
            "combo_expression": alpha_data.get("combo", ""),
            "settings_json": json.dumps(settings, ensure_ascii=False, sort_keys=True),
            "simulate_data_json": json.dumps(simulate_payload, ensure_ascii=False, sort_keys=True),
        }

    def _load_state(self):
        """Loads existing simulation state from CSV to support resuming."""
        try:
            if not pd.io.common.file_exists(self.output_csv):
                 logger.info(f"No existing state file found at {self.output_csv}. Starting fresh.")
                 return

            df = pd.read_csv(self.output_csv, on_bad_lines="skip")
            # Assuming 'fingerprint' and 'status' columns exist
            if 'fingerprint' in df.columns and 'status' in df.columns:
                status_norm = df['status'].astype(str).str.upper().str.strip()
                # Same CSV auto-resume rule: any successful row for a fingerprint marks it done.
                completed = df[status_norm.isin(_SUCCESS_SIM_STATUSES)]
                self.completed_fingerprints = set(completed['fingerprint'].tolist())
                logger.info(f"Loaded {len(self.completed_fingerprints)} completed alphas from {self.output_csv}")
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")

    @staticmethod
    def _fill_record_metrics(record: dict, full_stats: dict) -> None:
        is_stats = (full_stats or {}).get("is", {})
        record["pnl"] = is_stats.get("pnl", 0)
        record["sharpe"] = is_stats.get("sharpe", 0)
        record["turnover"] = is_stats.get("turnover", 0)
        record["fitness"] = is_stats.get("fitness", 0)

    def _process_single_alpha(self, alpha_input: dict, alpha_meta_by_fp: Dict[str, dict], progress_url: str):
        """Handle a single submitted alpha without waiting for multisim children."""
        fp = get_alpha_fingerprint(alpha_input)
        sim_id = progress_url.rstrip("/").split("/")[-1]
        started_at = time.time()
        max_wait_seconds = 15 * 60
        last_parent_data: Dict[str, Any] = {}
        sim_status = "UNKNOWN"
        alpha_id = None

        while time.time() - started_at <= max_wait_seconds:
            if self._cancel_check and self._cancel_check():
                logger.warning("Single simulation cancelled during polling.")
                self._save_result({
                    "fingerprint": fp,
                    **alpha_meta_by_fp.get(fp, {}),
                    "sim_id": sim_id,
                    "status": "CANCELLED",
                    "timestamp": time.time(),
                })
                self._inc_stat("failed", 1)
                return

            parent_resp = self.session.get(progress_url)
            if parent_resp.status_code == 429:
                retry_after = parent_resp.headers.get("Retry-After", 5)
                time.sleep(float(retry_after))
                continue

            if parent_resp.status_code != 200:
                logger.warning(f"Single simulation {progress_url} check failed: {parent_resp.status_code}")
                time.sleep(2)
                continue

            parent_data = parent_resp.json()
            last_parent_data = parent_data
            sim_status = str(parent_data.get("status") or "UNKNOWN").upper().strip()
            alpha_id = parent_data.get("alpha")
            retry_after = parent_resp.headers.get("Retry-After") or parent_resp.headers.get("retry-after")

            if retry_after:
                time.sleep(float(retry_after))
                continue

            if alpha_id and sim_status not in _ERROR_SIM_STATUSES:
                break
            if sim_status in _TERMINAL_SIM_STATUSES:
                break

            time.sleep(2)

        record = {
            "fingerprint": fp,
            **alpha_meta_by_fp.get(fp, {}),
            "sim_id": sim_id,
            "status": sim_status,
            "timestamp": time.time(),
            "alpha_id": alpha_id,
            "pnl": 0,
            "sharpe": 0,
            "turnover": 0,
            "fitness": 0,
        }

        if alpha_id and sim_status not in _ERROR_SIM_STATUSES:
            try:
                full_stats = ace_lib.get_simulation_result_json(self.session, alpha_id)
                if full_stats:
                    self._fill_record_metrics(record, full_stats)
            except Exception as e:
                logger.error(f"Failed to fetch stats for alpha {alpha_id}: {e}")
            message = last_parent_data.get("message")
            if message:
                record["error_details"] = message
            if sim_status not in _SUCCESS_SIM_STATUSES:
                record["status"] = "COMPLETED"
            self._save_result(record)
            self.completed_fingerprints.add(fp)
            self._inc_stat("completed", 1)
            return

        if sim_status in _ERROR_SIM_STATUSES:
            error_details = lookINTO_SimError_message(self.session, [f"/simulations/{sim_id}"])
            if error_details:
                record["error_details"] = error_details[0].get("message", "")
            elif last_parent_data.get("message"):
                record["error_details"] = last_parent_data.get("message", "")
            self._save_result(record)
            self._inc_stat("failed", 1)
            return

        timeout_status = sim_status if sim_status == "TIMEOUT" else "BATCH_SPAWN_FAILED"
        record["status"] = timeout_status
        record["error"] = last_parent_data.get("message") or f"Parent status: {sim_status}"
        self._save_result(record)
        self._inc_stat("failed", 1)

    def _submit_with_retry(self, submit_payload, max_retries: int = 8):
        """Submit simulation batch with backoff on platform concurrency/rate limits."""
        for attempt in range(max_retries):
            resp = ace_lib.start_simulation(self.session, submit_payload)
            if resp.status_code in [200, 201, 202]:
                return resp

            if resp.status_code == 429:
                retry_after = 0
                try:
                    retry_after = int(float(resp.headers.get("Retry-After", 0)))
                except Exception:
                    retry_after = 0
                detail_text = ""
                try:
                    detail_text = (resp.json() or {}).get("detail", "")
                except Exception:
                    detail_text = resp.text

                # For platform concurrency limit, wait progressively longer.
                wait_seconds = retry_after if retry_after > 0 else min(20 + attempt * 10, 120)
                logger.warning(
                    f"Batch submission throttled (attempt {attempt + 1}/{max_retries}): {detail_text}. "
                    f"Retry in {wait_seconds}s"
                )
                time.sleep(wait_seconds)
                continue

            return resp

        return resp

    def _save_result(self, result_dict: dict):
        """Thread-safe write to CSV."""
        write_ok = False
        with self.csv_lock:
            try:
                normalized = {key: result_dict.get(key, "") for key in self.csv_columns}
                df = pd.DataFrame([normalized], columns=self.csv_columns)
                
                # Append to CSV, create header if file doesn't exist
                write_header = not pd.io.common.file_exists(self.output_csv)
                df.to_csv(self.output_csv, mode='a', header=write_header, index=False)
                write_ok = True
            except Exception as e:
                logger.error(f"Failed to write result to CSV: {e}")
        if write_ok and self._on_result_saved:
            try:
                self._on_result_saved()
            except Exception:
                pass

    def process_batch(self, alpha_batch: List[dict]):
        """
        Submits a batch of alphas, polls their individual status (avoiding multisimulation_progress),
        and records results.
        """
        # 1. Filter batch for duplicates
        clean_batch = []
        alpha_meta_by_fp = {}
        skipped_in_batch = 0
        
        for alpha in alpha_batch:
            fp = get_alpha_fingerprint(alpha)
            if fp in self.completed_fingerprints:
                skipped_in_batch += 1
                continue
            
            clean_batch.append(alpha)
            alpha_meta_by_fp[fp] = self._alpha_metadata(alpha)

        if skipped_in_batch > 0:
            self._inc_stat("skipped", skipped_in_batch)
            logger.info(f"Resume detected: skipped {skipped_in_batch} already completed alpha(s) in this batch.")

        if not clean_batch:
            return

        # 2. Submit batch
        logger.info(f"Submitting batch of {len(clean_batch)} alphas...")
        self._inc_stat("submitted", len(clean_batch))
        try:
            # ace_lib.start_simulation handles the POST to /simulations
            submit_payload = clean_batch[0] if len(clean_batch) == 1 else clean_batch
            resp = self._submit_with_retry(submit_payload)
            
            if resp.status_code not in [200, 201, 202]:
                logger.error(f"Batch submission failed: {resp.status_code} - {resp.text}")
                # Record failure for all in batch
                for alpha in clean_batch:
                    fp = get_alpha_fingerprint(alpha)
                    self._save_result({
                        "fingerprint": fp,
                        **alpha_meta_by_fp.get(fp, {}),
                        "status": "SUBMISSION_FAILED", 
                        "error": resp.text,
                        "timestamp": time.time()
                    })
                self._inc_stat("failed", len(clean_batch))
                return

            # 3. Get batch progress URL and initial Poll
            # The response to a list submission usually points to a parent simulation monitor
            progress_url = resp.headers.get("Location")
            if not progress_url:
                logger.error("No Location header in batch submission response.")
                return

            # Notify caller of new batch location URL
            if self._on_batch_start and progress_url:
                try:
                    self._on_batch_start(progress_url)
                except Exception:
                    pass

            if len(clean_batch) == 1:
                self._process_single_alpha(clean_batch[0], alpha_meta_by_fp, progress_url)
                return

            # Wait for the batch to initialize and spawn children
            # We need to poll the PARENT to get the list of CHILDREN IDs
            children_ids = []
            max_wait_seconds = 15 * 60
            started_at = time.time()
            parent_status = "UNKNOWN"
            last_parent_data = {}
            
            logger.info(f"Waiting for batch to spawn children ({progress_url})...")
            while time.time() - started_at <= max_wait_seconds:
                if self._cancel_check and self._cancel_check():
                    logger.warning("Simulation cancelled during parent polling.")
                    for alpha in clean_batch:
                        fp = get_alpha_fingerprint(alpha)
                        self._save_result({
                            "fingerprint": fp,
                            **alpha_meta_by_fp.get(fp, {}),
                            "status": "CANCELLED",
                            "timestamp": time.time()
                        })
                    self._inc_stat("failed", len(clean_batch))
                    return

                parent_resp = self.session.get(progress_url)
                if parent_resp.status_code == 429:
                    retry_after = parent_resp.headers.get("Retry-After", 5)
                    time.sleep(float(retry_after))
                    continue

                if parent_resp.status_code == 200:
                    parent_data = parent_resp.json()
                    last_parent_data = parent_data
                    parent_status = parent_data.get("status")
                    
                    # Brain API typically returns a 'children' list
                    children = parent_data.get("children", [])
                    if children:
                        children_ids = children
                        break
                    
                    # While parent is in progress, API may return only {"progress": ...} + Retry-After
                    retry_after = parent_resp.headers.get("Retry-After") or parent_resp.headers.get("retry-after")
                    if retry_after:
                        time.sleep(float(retry_after))
                        continue

                    # If completed/error but still no children, stop waiting
                    if parent_status in _TERMINAL_SIM_STATUSES and not children:
                        break

                time.sleep(2)
            
            if not children_ids:
                # Single simulation mode is handled before entering child polling.
                if len(clean_batch) == 1 and parent_status in _TERMINAL_SIM_STATUSES:
                    alpha_input = clean_batch[0]
                    fp = get_alpha_fingerprint(alpha_input)
                    sim_id = progress_url.rstrip("/").split("/")[-1]
                    sim_status = last_parent_data.get("status", parent_status)
                    alpha_id = last_parent_data.get("alpha")

                    record = {
                        "fingerprint": fp,
                        **alpha_meta_by_fp.get(fp, {}),
                        "sim_id": sim_id,
                        "status": sim_status,
                        "timestamp": time.time(),
                        "alpha_id": alpha_id,
                        "pnl": 0,
                        "sharpe": 0,
                        "turnover": 0,
                        "fitness": 0,
                    }

                    if sim_status in _SUCCESS_SIM_STATUSES and alpha_id:
                        try:
                            full_stats = ace_lib.get_simulation_result_json(self.session, alpha_id)
                            if full_stats:
                                self._fill_record_metrics(record, full_stats)
                        except Exception as e:
                            logger.error(f"Failed to fetch stats for alpha {alpha_id}: {e}")
                    elif sim_status in ["ERROR", "FAIL", "FAILED"]:
                        error_details = lookINTO_SimError_message(self.session, [f"/simulations/{sim_id}"])
                        if error_details:
                            record["error_details"] = error_details[0].get("message", "")

                    self._save_result(record)
                    if sim_status in _SUCCESS_SIM_STATUSES:
                        self.completed_fingerprints.add(fp)
                        self._inc_stat("completed", 1)
                    else:
                        self._inc_stat("failed", 1)
                    return

                logger.error(f"Failed to retrieve children IDs. Parent status: {parent_status}")
                # Log failure for checking
                for alpha in clean_batch:
                    fp = get_alpha_fingerprint(alpha)
                    self._save_result({
                        "fingerprint": fp,
                        **alpha_meta_by_fp.get(fp, {}),
                        "status": "BATCH_SPAWN_FAILED",
                        "error": f"Parent status: {parent_status}",
                        "timestamp": time.time()
                    })
                self._inc_stat("failed", len(clean_batch))
                return

            if parent_status in _ERROR_SIM_STATUSES and children_ids:
                logger.warning(
                    f"Parent simulation ended with {parent_status}; finalizing {len(children_ids)} children as failed without waiting for long polling."
                )
                results = {}
                child_locations = [f"/simulations/{child_id}" for child_id in children_ids]
                detailed_errors = lookINTO_SimError_message(self.session, child_locations)
                error_by_location = {
                    item.get("location"): item
                    for item in detailed_errors
                    if isinstance(item, dict) and item.get("location")
                }

                for child_id in children_ids:
                    loc = f"/simulations/{child_id}"
                    detail = error_by_location.get(loc, {})
                    results[child_id] = {
                        "status": detail.get("status") or parent_status,
                        "alpha": None,
                        "message": detail.get("message") or last_parent_data.get("message") or f"Parent multisim status: {parent_status}",
                    }

                for i, alpha_input in enumerate(clean_batch):
                    fp = get_alpha_fingerprint(alpha_input)
                    child_id = children_ids[i] if i < len(children_ids) else None
                    res_data = results.get(child_id, {"status": parent_status, "message": f"Parent multisim status: {parent_status}"})
                    record = {
                        "fingerprint": fp,
                        **alpha_meta_by_fp.get(fp, {}),
                        "sim_id": child_id,
                        "status": res_data.get("status", parent_status),
                        "timestamp": time.time(),
                        "alpha_id": None,
                        "pnl": 0,
                        "sharpe": 0,
                        "turnover": 0,
                        "fitness": 0,
                        "error_details": res_data.get("message", ""),
                    }
                    self._save_result(record)
                    self._inc_stat("failed", 1)
                return

            logger.info(f"Batch spawned {len(children_ids)} children. Polling individually...")

            # 4. Poll Children Individually
            # Store mapping of sim_id -> index in clean_batch to map back to inputs
            if len(children_ids) != len(clean_batch):
                logger.warning(f"Count mismatch: sent {len(clean_batch)}, got {len(children_ids)} children.")
                # If mismatch, we can't reliably map back to clean_batch by index if strictly relying on position.
                # However, usually Brain preserves order. We proceed with index mapping.
            
            # active_sims: map sim_id -> index in clean_batch
            active_sims = {child_id: idx for idx, child_id in enumerate(children_ids)}
            results = {} # Store final results by sim_id
            
            # Polling loop (bounded wait to avoid infinite hangs)
            child_wait_started = time.time()
            child_wait_limit_seconds = 30 * 60
            while active_sims:
                if time.time() - child_wait_started > child_wait_limit_seconds:
                    logger.error("Child polling timeout reached; marking remaining simulations as timeout.")
                    for sim_id in list(active_sims.keys()):
                        results[sim_id] = {"status": "TIMEOUT", "alpha": None}
                    active_sims.clear()
                    break

                # Copy keys to iterate while modifying
                current_sim_ids = list(active_sims.keys())
                
                for sim_id in current_sim_ids:
                    sim_url = f"{ace_lib.brain_api_url}/simulations/{sim_id}"
                    
                    try:
                        sim_resp = self.session.get(sim_url)
                        
                        # Handle rate limits or temporary issues
                        if sim_resp.status_code == 429:
                            retry_after = sim_resp.headers.get("Retry-After", 5)
                            time.sleep(min(float(retry_after), 10))
                            continue
                        
                        if sim_resp.status_code != 200:
                            logger.warning(f"Sim {sim_id} check failed: {sim_resp.status_code}")
                            continue

                        sim_data = sim_resp.json()
                        status = sim_data.get("status")

                        # If still in progress, respect Retry-After for timing
                        if status not in _TERMINAL_SIM_STATUSES:
                            ra = sim_resp.headers.get("Retry-After") or sim_resp.headers.get("retry-after")
                            if ra:
                                time.sleep(min(float(ra), 15))
                            continue

                        if status in _TERMINAL_SIM_STATUSES:
                            # Simulation finished
                            results[sim_id] = sim_data
                            # Remove from active set
                            if sim_id in active_sims:
                                del active_sims[sim_id]
                            
                    except Exception as e:
                        logger.error(f"Error polling child {sim_id}: {e}")
                
                if active_sims:
                    # Check cancel before next polling cycle
                    if self._cancel_check and self._cancel_check():
                        logger.warning("Simulation cancelled by user. Marking remaining as CANCELLED.")
                        for sid in list(active_sims.keys()):
                            results[sid] = {"status": "CANCELLED", "alpha": None}
                        active_sims.clear()
                        break
                    time.sleep(3) # Wait before next cycle

            # 5. Process and Save Results
            # We iterate through indices of clean_batch to ensure we save a result for every input alpha
            for i, alpha_input in enumerate(clean_batch):
                fp = get_alpha_fingerprint(alpha_input)
                
                # Try to get the corresponding sim_id if available
                child_id = children_ids[i] if i < len(children_ids) else None
                
                if child_id and child_id in results:
                    res_data = results[child_id]
                    sim_status = res_data.get("status", "UNKNOWN")
                    alpha_id = res_data.get("alpha")
                    
                    record = {
                        "fingerprint": fp,
                        **alpha_meta_by_fp.get(fp, {}),
                        "sim_id": child_id,
                        "status": sim_status,
                        "timestamp": time.time(),
                        "alpha_id": alpha_id,
                        "pnl": 0,
                        "sharpe": 0,
                        "turnover": 0,
                        "fitness": 0
                    }
                    
                    # If successful, fetch detailed result
                    if sim_status in _SUCCESS_SIM_STATUSES and alpha_id:
                        try:
                            # Use ace_lib logic to get full result
                            full_stats = ace_lib.get_simulation_result_json(self.session, alpha_id)
                            if full_stats:
                                self._fill_record_metrics(record, full_stats)
                                
                        except Exception as e:
                            logger.error(f"Failed to fetch stats for alpha {alpha_id}: {e}")

                    # If failed, look into error
                    elif sim_status in _ERROR_SIM_STATUSES:
                        error_details = lookINTO_SimError_message(self.session, [f"/simulations/{child_id}"])
                        if error_details:
                            # Save first error found
                            record["error_details"] = error_details[0].get("message", "")
                            # record["raw_error"] = str(error_details[0]) # Optional: too verbose for CSV usually

                    self._save_result(record)
                    # Mark as completed in memory so we don't re-run in this session
                    if sim_status in _SUCCESS_SIM_STATUSES:
                        self.completed_fingerprints.add(fp)
                        self._inc_stat("completed", 1)
                    else:
                        self._inc_stat("failed", 1)
                else:
                    # Case where we didn't get a result for this index (e.g. child count mismatch or lost)
                    self._save_result({
                        "fingerprint": fp,
                        **alpha_meta_by_fp.get(fp, {}),
                        "status": "MISSING_RESULT",
                        "error": "No child simulation found for this index",
                        "timestamp": time.time()
                    })
                    self._inc_stat("failed", 1)

        except Exception as e:
            logger.error(f"Critical error in batch processing: {e}", exc_info=True)

    def run(self, alpha_list: List[dict], batch_size: int = 3, concurrency: int = 2, on_batch_done=None):
        """
        Main entry point to run the simulation manager.
        on_batch_done: optional callback invoked (with no args) after each batch finishes.
        """
        self._reset_run_stats()
        total = len(alpha_list)
        input_fingerprints = {get_alpha_fingerprint(alpha) for alpha in alpha_list}
        already_completed_in_input = len(input_fingerprints & self.completed_fingerprints)
        pending_in_input = len(input_fingerprints - self.completed_fingerprints)

        logger.info(f"Starting simulation run for {total} alphas. Batch size: {batch_size}, Workers: {concurrency}")
        logger.info(
            f"Resume check: recognized {already_completed_in_input}/{len(input_fingerprints)} completed from {self.output_csv}; "
            f"pending {pending_in_input}."
        )
        
        # Split into batches
        batches = [alpha_list[i:i + batch_size] for i in range(0, total, batch_size)]
        
        # Run batches in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.process_batch, batch) for batch in batches]
            
            # Wait for all to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Worker exception: {e}")
                # Notify caller that a batch finished (for incremental progress)
                if on_batch_done:
                    try:
                        on_batch_done()
                    except Exception:
                        pass
                if self._cancel_check and self._cancel_check():
                    logger.warning("Cancellation detected, skipping remaining futures.")
                    break

        logger.info(
            f"All batches processed. Run summary -> skipped: {self.stats['skipped']}, "
            f"submitted: {self.stats['submitted']}, completed: {self.stats['completed']}, failed: {self.stats['failed']}"
        )


def main():
    parser = argparse.ArgumentParser(description="Batch simulate alphas with resume support.")
    parser.add_argument("--alpha-json", default="data/alpha_list.json", help="Path to alpha list JSON file")
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Path to status CSV file. If omitted, auto uses outputs/<alpha_json_filename>_simulation_status.csv",
    )
    parser.add_argument("--batch-size", type=int, default=3, help="Number of alphas per submission batch")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent batches")
    parser.add_argument("--config", default="configs/config.json", help="Path to credential config JSON")
    parser.add_argument("--detached", action="store_true", help="Launch batch simulation in background and return immediately")
    parser.add_argument("--task-id", default=None, help="Optional task id for detached mode")
    parser.add_argument("--tasks-dir", default="outputs/tasks", help="Task directory root for detached mode")
    parser.add_argument("--status", default=None, help="Show detached task status by task id and exit")
    parser.add_argument("--tail-lines", type=int, default=40, help="Tail lines for --status output")
    args = parser.parse_args()

    tasks_dir = Path(args.tasks_dir)
    if not tasks_dir.is_absolute():
        tasks_dir = (SKILL_ROOT / tasks_dir).resolve()
    else:
        tasks_dir = tasks_dir.resolve()

    if args.status and str(args.status).strip():
        raise SystemExit(_print_task_status(tasks_dir=tasks_dir, task_id=str(args.status).strip(), tail_lines=args.tail_lines))

    if args.detached:
        task_id = args.task_id.strip() if args.task_id and args.task_id.strip() else f"sim_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        child_cmd = _build_detached_child_cmd(Path(__file__).resolve(), sys.argv[1:])
        mode = f"batch_bs{int(args.batch_size)}_cc{int(args.concurrency)}"
        try:
            pid, task_dir = _launch_detached(cmd=child_cmd, cwd=SKILL_ROOT, task_id=task_id, tasks_dir=tasks_dir, mode=mode)
        except Exception as exc:
            logger.error(f"Failed to launch detached process: {exc}")
            raise SystemExit(2)

        print("Detached task launched.")
        print(f"task_id={task_id}")
        print(f"pid={pid}")
        print(f"task_dir={task_dir}")
        print(f"stdout_log={task_dir / 'stdout.log'}")
        print(f"stderr_log={task_dir / 'stderr.log'}")
        raise SystemExit(0)

    resolved_config = resolve_input_path(args.config, "config.json")
    load_credentials_from_config(str(resolved_config))

    alpha_json_path = resolve_input_path(args.alpha_json, "alpha_list.json")
    if args.output_csv:
        output_csv_path = resolve_output_path(args.output_csv)
    else:
        output_csv_path = build_default_output_csv_path(alpha_json_path)
    logger.info(f"Using output CSV: {output_csv_path}")

    with open(alpha_json_path, "r", encoding="utf-8") as file:
        alpha_list = json.load(file)

    if not isinstance(alpha_list, list):
        raise ValueError(f"alpha json must be a list, got: {type(alpha_list)}")

    session = ace_lib.start_session()
    simulator = BatchSimulator(session, output_csv=str(output_csv_path))
    simulator.run(alpha_list, batch_size=args.batch_size, concurrency=args.concurrency)


if __name__ == "__main__":
    main()
