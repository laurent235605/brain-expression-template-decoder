"""Pipeline Runner: the main autopilot loop.

Phases:
  1. GENERATE  — run_pipeline.py → idea_*.json
  2. INSPECT   — attach sim settings (LLM chooses) → alpha_list.json
  3. SIMULATE  — batch_simulator → CSV results
  4. DECIDE    — rules + LLM pick enhancement strategy
  5. ENHANCE   — enhance_template.py → enhanced_templates_*.json
  6. IMPLEMENT — implement_idea.py → new idea_*.json with expressions
  → Loop back to phase 2 (INSPECT) for new ideas; pool grows
"""
from __future__ import annotations

import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from collections import deque
from pathlib import Path
from typing import Any, Optional

# Ensure vendor scripts are importable for ace_lib
VENDOR_DIR = Path(__file__).resolve().parent / "scripts" / "vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import ace_lib

from pool_manager import PoolManager, PoolEntry
from llm_counter import summarize_llm_requests
from stage_inspect import inspect_idea
from stage_simulate import simulate_idea, _summarize_csv, _load_latest_sim_rows, _SIM_COMPLETED_STATUSES
from stage_decide import decide
from stage_enhance import enhance
from stage_implement import implement_enhanced

logger = logging.getLogger("pipeline_runner")

_TRAIL_DIR = Path(__file__).resolve().parent.parent / "trailSomeAlphas"
RUN_PIPELINE_SCRIPT = _TRAIL_DIR / "run_pipeline.py"


def _render_prompt_template(template: str, mapping: dict[str, Any]) -> str:
    rendered = str(template or "")
    for key, value in mapping.items():
        rendered = rendered.replace("{{" + key + "}}", str(value if value is not None else ""))
    return rendered


class PipelineStopRequested(RuntimeError):
    """Raised when a pipeline phase is intentionally interrupted."""


class GenerateDataTypeMismatch(RuntimeError):
    """Raised when GENERATE likely failed because MATRIX/VECTOR was chosen incorrectly."""

    def __init__(self, current_data_type: str, suggested_data_type: str, raw_error: str):
        self.current_data_type = str(current_data_type or "MATRIX").upper()
        self.suggested_data_type = str(suggested_data_type or "VECTOR").upper()
        self.raw_error = str(raw_error or "")
        message = (
            f"GENERATE 检测到数据字段为空，当前 data_type={self.current_data_type}，"
            f"疑似应改为 {self.suggested_data_type}。请确认后强制重启流水线。"
        )
        if self.raw_error:
            message = f"{message} 原始错误: {self.raw_error[-300:]}"
        super().__init__(message)


def _is_probable_data_type_mismatch(error_text: str) -> bool:
    text = str(error_text or "")
    lowered = text.lower()
    has_datafield_fetch_context = (
        "get_datasets" in text
        or "get_datafields" in text
        or "fetching datafields for dataset" in lowered
        or "no fields found:" in lowered
    )
    has_explicit_data_type = "type=matrix" in lowered or "type=vector" in lowered
    return (
        (
            "keyerror: 'results'" in lowered
            and (
                has_datafield_fetch_context
                or "ace_lib.py" in lowered
            )
        )
        or (
            "no data found or empty response" in lowered
            and has_datafield_fetch_context
            and has_explicit_data_type
        )
        or ("no fields found:" in lowered and has_explicit_data_type)
    )


def _terminate_process_tree(proc: subprocess.Popen) -> None:
    """Terminate a subprocess and its children best-effort."""
    if proc.poll() is not None:
        return

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


# ── State Management ────────────────────────────────────────────────

class PipelineState:
    """Manages state.json for checkpoint/resume."""

    def __init__(self, state_path: Path):
        self._path = state_path
        self._lock = threading.Lock()
        self._state: dict = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                self._state = {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def get(self, key: str, default=None):
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any):
        with self._lock:
            self._state[key] = value
            self._save()

    def update(self, **kwargs):
        with self._lock:
            self._state.update(kwargs)
            self._save()

    def to_dict(self) -> dict:
        with self._lock:
            return dict(self._state)


# ── BRAIN Session ────────────────────────────────────────────────────

def _create_brain_session(config: dict):
    """Create authenticated ace_lib session from pipeline config or persisted ace creds."""
    with _ace_credentials_override(config):
        return ace_lib.start_session()


@contextmanager
def _ace_credentials_override(config: dict):
    """Temporarily point ace_lib auth at pipeline credentials when present."""
    username = str(config.get("brain_username", "") or "").strip()
    password = str(config.get("brain_password", "") or "").strip()
    api_url = str(config.get("brain_api_url", "https://api.worldquantbrain.com") or "https://api.worldquantbrain.com")

    original_api_url = getattr(ace_lib, "brain_api_url", api_url)
    original_get_creds = ace_lib.get_credentials
    ace_lib.brain_api_url = api_url
    if username and password:
        ace_lib.get_credentials = lambda: (username, password)

    try:
        yield
    finally:
        ace_lib.brain_api_url = original_api_url
        ace_lib.get_credentials = original_get_creds


def _refresh_brain_session(session, config: dict):
    """Refresh an ace_lib session using the same credential source as initial creation."""
    with _ace_credentials_override(config):
        return ace_lib.check_session_and_relogin(session)


# ── Phase 1: GENERATE ────────────────────────────────────────────────

def phase_generate(
    pipeline_dir: Path,
    config: dict,
    log_cb=None,
    stop_check=None,
    proc_cb=None,
) -> list[Path]:
    """Run run_pipeline.py to generate initial ideas. Streams output via log_cb."""
    gen_dir = pipeline_dir / "gen"
    gen_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    prompt_overrides = config.get("prompt_overrides") or {}
    env["PIPELINE_LLM_COUNTER_PATH"] = str(pipeline_dir / "llm_requests.jsonl")
    env["PIPELINE_LLM_COUNTER_STAGE"] = "generate"
    if config.get("moonshot_api_key"):
        env["MOONSHOT_API_KEY"] = config["moonshot_api_key"]
    if config.get("moonshot_base_url"):
        env["MOONSHOT_BASE_URL"] = config["moonshot_base_url"]
    if config.get("brain_username"):
        env["BRAIN_USERNAME"] = config["brain_username"]
    if config.get("brain_password"):
        env["BRAIN_PASSWORD"] = config["brain_password"]
    if prompt_overrides.get("generate_system_prompt"):
        env["PIPELINE_GENERATE_SYSTEM_PROMPT"] = str(prompt_overrides["generate_system_prompt"])

    def _run_generate_once(current_data_type: str) -> None:
        cmd = [
            sys.executable, str(RUN_PIPELINE_SCRIPT),
            "--data-category", config["data_category"],
            "--region", config["region"],
            "--delay", str(config["delay"]),
            "--dataset-id", config["dataset_id"],
            "--universe", config.get("universe", "TOP3000"),
            "--data-type", current_data_type,
        ]
        if config.get("moonshot_api_key"):
            cmd.extend(["--moonshot-api-key", config["moonshot_api_key"]])
        if config.get("moonshot_model"):
            cmd.extend(["--moonshot-model", config["moonshot_model"]])
        if config.get("brain_username"):
            cmd.extend(["--username", config["brain_username"]])
        if config.get("brain_password"):
            cmd.extend(["--password", config["brain_password"]])

        logger.info(f"Running GENERATE phase (run_pipeline.py, data_type={current_data_type})...")
        proc = subprocess.Popen(
            cmd, env=env, cwd=str(_TRAIL_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        if proc_cb:
            proc_cb(proc)

        all_output = []
        try:
            if proc.stdout:
                for line in proc.stdout:
                    stripped = line.rstrip("\n")
                    all_output.append(stripped)
                    if log_cb:
                        log_cb(stripped)
        finally:
            if proc_cb:
                proc_cb(None)

        exit_code = proc.wait()
        if stop_check and stop_check():
            raise PipelineStopRequested("GENERATE 已被中断")
        if exit_code != 0:
            err_tail = "\n".join(all_output[-20:])
            logger.error(f"run_pipeline.py failed:\n{err_tail}")
            if "KeyError" in err_tail and "count" in err_tail:
                raise RuntimeError(
                    "GENERATE 失败: BRAIN API 返回异常 (可能是会话过期或凭据错误)。"
                    "请确保已在主页登录BRAIN且密码正确。"
                )
            if "KeyboardInterrupt" in err_tail:
                raise RuntimeError(
                    "GENERATE 失败: run_pipeline 在等待 Moonshot/Kimi 流式响应时被中断。"
                    "这通常表示手动停止、父进程要求终止，或本地网络连接在长连接期间被打断。"
                )
            raise RuntimeError(f"GENERATE phase failed: {err_tail[-300:]}")

    data_type = str(config.get("data_type", "MATRIX") or "MATRIX").upper()
    if data_type not in ("MATRIX", "VECTOR"):
        data_type = "MATRIX"

    try:
        _run_generate_once(data_type)
    except RuntimeError as exc:
        if _is_probable_data_type_mismatch(str(exc)) and data_type in ("MATRIX", "VECTOR"):
            retry_data_type = "VECTOR" if data_type == "MATRIX" else "MATRIX"
            raise GenerateDataTypeMismatch(data_type, retry_data_type, str(exc)) from exc
        else:
            raise

    # Collect generated idea files
    dataset_folder = f"{config['dataset_id']}_{config['region']}_delay{config['delay']}"
    feature_data_dir = (
        _TRAIL_DIR / "skills" / "brain-feature-implementation" / "data" / dataset_folder
    )

    idea_files = []
    if feature_data_dir.exists():
        for f in sorted(feature_data_dir.glob("*_idea_*.json")):
            dest = gen_dir / f.name
            if not dest.exists():
                dest.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            idea_files.append(dest)

    logger.info(f"GENERATE produced {len(idea_files)} idea files")
    return idea_files


# ── Phase 2: INSPECT ────────────────────────────────────────────────

def phase_inspect(ideas: list[dict], pipeline_dir: Path, session, llm_config: dict,
                  pool: PoolManager, config: dict | None = None, log_cb=None) -> None:
    """Inspect all pending ideas and update pool."""
    fixed_universe = str((config or {}).get("universe") or "").strip().upper() or None

    def _log(msg, level="info"):
        if log_cb:
            log_cb(msg, level=level, phase="inspect")
        getattr(logger, level, logger.info)(msg)

    for i, entry in enumerate(ideas, 1):
        idea_file = entry["idea_file"]
        if not pool.claim_for_inspect(idea_file):
            continue
        idea_path = Path(idea_file)
        if not idea_path.is_absolute():
            idea_path = pipeline_dir / idea_path

        stem = idea_path.stem
        output_dir = _inspect_output_dir(pipeline_dir, idea_file)

        try:
            _log(f"INSPECT [{i}/{len(ideas)}]: {stem}")
            alpha_list_path = inspect_idea(
                idea_path=idea_path,
                output_dir=output_dir,
                session=session,
                pipeline_dir=pipeline_dir,
                llm_config=llm_config,
                fixed_universe=fixed_universe,
                repair_invalid_on_retry=True,
            )
            pool.update_by_idea(
                entry["idea_file"],
                inspect_status="done",
                alpha_list_file=str(alpha_list_path.relative_to(pipeline_dir)),
            )
            _log(f"INSPECT [{i}/{len(ideas)}]: {stem} → 完成")
        except Exception as exc:
            _log(f"INSPECT [{i}/{len(ideas)}] 失败: {stem}: {exc}", level="error")
            pool.update_by_idea(entry["idea_file"], inspect_status="error", error=str(exc))


def _inspect_output_dir(pipeline_dir: Path, idea_file: str | Path) -> Path:
    """Build a unique inspect output directory from the idea's relative path.

    This prevents collisions when the same idea filename exists under gen/ and
    implement/round_N/.
    """
    rel = Path(idea_file)
    if rel.is_absolute():
        try:
            rel = rel.relative_to(pipeline_dir)
        except ValueError:
            rel = Path(rel.name)
    safe_name = rel.with_suffix("").as_posix().replace("/", "__").replace("\\", "__")
    return pipeline_dir / "inspect" / safe_name


# ── Phase 3: SIMULATE ───────────────────────────────────────────────

def _sim_csv_name(idea_file: str) -> str:
    """Derive a unique simulation CSV filename from an idea_file relative path.

    For 'gen/foo.json' -> 'foo_simulation_status.csv'
    For 'implement/round_17/foo.json' -> 'round_17_foo_simulation_status.csv'
    This avoids CSV collisions when enhanced ideas share the same stem.
    """
    parts = Path(idea_file).parts  # e.g. ('implement', 'round_17', 'foo.json')
    stem = Path(idea_file).stem
    # If the idea comes from a round directory, prefix with round name
    if len(parts) >= 3 and parts[-2].startswith("round_"):
        return f"{parts[-2]}_{stem}_simulation_status.csv"
    return f"{stem}_simulation_status.csv"


def _manual_enhance_round() -> int:
    return int(time.time())


def _resolve_sim_summary_state(summary: dict | None, final: bool = False) -> tuple[str | None, str]:
    summary = summary or {}
    count = int(summary.get("count") or 0)
    completed = int(summary.get("completed") or 0)
    failed = int(summary.get("failed") or 0)
    accounted = completed + failed

    if count <= 0:
        if final:
            return "error", summary.get("first_error") or "未生成有效回测结果"
        return None, ""

    if not final and accounted < count:
        return None, ""

    if completed > 0:
        return "done", ""

    if failed > 0:
        return "error", summary.get("first_error") or "全部回测失败"

    return "error", summary.get("first_error") or "回测已结束，但未识别到成功结果"


def _is_timeout_retryable_sim_error(entry: dict | None) -> bool:
    entry = entry or {}
    summary = entry.get("sim_summary") or {}
    status_breakdown = summary.get("status_breakdown") or {}

    for status, count in status_breakdown.items():
        if str(status).upper().strip() == "TIMEOUT" and int(count or 0) > 0:
            return True

    error_candidates = [
        entry.get("error", ""),
        summary.get("first_error", ""),
        " ".join(summary.get("error_examples") or []),
    ]
    merged = " ".join(str(item or "") for item in error_candidates).upper()
    return "TIMEOUT" in merged


def phase_simulate(pipeline_dir: Path, session, pool: PoolManager,
                   sim_multi_slots: int = 2, sim_concurrent: int = 2,
                   log_cb=None, abort_check=None,
                   stop_check=None,
                   get_worker_limit=None,
                   on_sim_done=None) -> None:
    """Simulate all inspected-but-not-simulated ideas using ThreadPoolExecutor.

    Each idea gets its own worker (concurrency=1 inside simulate_idea).
    sim_concurrent controls how many ideas run in parallel across workers.

    Args:
        abort_check: optional callable(idea_file) -> bool. If provided and returns
                     True for an idea, that idea's simulation is cancelled /
                     skipped and its status is NOT overwritten to 'done'.
        stop_check: optional callable() -> bool. When it returns True, workers
                stop picking up new ideas and only let already-running sims
                finish gracefully.
        get_worker_limit: optional callable() -> int. Returns the current desired
                          worker count. When workers are reduced, excess workers
                          finish their current idea but don't pick new ones.
        on_sim_done: optional callable(). Called after each idea finishes sim
                     successfully. Used to trigger incremental DECIDE.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _log(msg, level="info"):
        if log_cb:
            log_cb(msg, level=level, phase="simulate")
        getattr(logger, level, logger.info)(msg)

    pending = pool.pending_sim()
    if not pending:
        _log("无待回测的Idea")
        return

    total = len(pending)
    _log(f"SIMULATE: {total} 个Idea待回测, 使用 {sim_concurrent} 个Worker并行")

    # Counter for log indexing (shared across workers)
    _counter_lock = threading.Lock()
    _counter = [0]  # mutable for closure
    _stop_notice_logged = [False]

    def _worker_loop():
        """Long-running worker: loop picking up pending ideas until drained."""
        while True:
            if stop_check and stop_check():
                with _counter_lock:
                    if not _stop_notice_logged[0]:
                        _stop_notice_logged[0] = True
                        _log("收到停止请求: 不再领取新的回测任务，当前正在运行的回测会收尾后退出", level="warning")
                return

            # Dynamic worker limit: graceful reduction
            if get_worker_limit:
                limit = get_worker_limit()
                running_count = len([e for e in pool.all() if e.get('sim_status') == 'running'])
                if running_count >= limit:
                    return  # excess worker exits

            # Find next pending idea via atomic claim
            entry = None
            for candidate in pool.pending_sim():
                idea_file = candidate["idea_file"]
                if abort_check and abort_check(idea_file):
                    continue
                if not candidate.get("alpha_list_file"):
                    continue
                if pool.claim_for_sim(idea_file):
                    entry = candidate
                    break

            if entry is None:
                return  # no more work

            idea_file = entry["idea_file"]
            stem = Path(idea_file).stem
            with _counter_lock:
                _counter[0] += 1
                idx = _counter[0]

            alpha_list_path = pipeline_dir / entry["alpha_list_file"]
            output_csv = pipeline_dir / "sim" / _sim_csv_name(idea_file)
            _log(f"SIMULATE [{idx}/{total}]: {stem} 开始回测")

            cancel_fn = (lambda _ref=idea_file: abort_check(_ref)) if abort_check else None

            def _progress(summary, _ref=idea_file, _csv=output_csv):
                update_fields = {"sim_summary": summary}
                sim_status, error_text = _resolve_sim_summary_state(summary, final=False)
                if sim_status:
                    update_fields["sim_status"] = sim_status
                    update_fields["sim_csv"] = str(_csv.relative_to(pipeline_dir))
                    update_fields["error"] = error_text if sim_status == "error" else ""
                pool.update_by_idea(_ref, **update_fields)

            def _on_location(url, _ref=idea_file):
                pool.update_by_idea(_ref, sim_location=url)

            try:
                summary = simulate_idea(
                    alpha_list_path=alpha_list_path,
                    output_csv=output_csv,
                    session=session,
                    sim_multi_slots=sim_multi_slots,
                    cancel_check=cancel_fn,
                    progress_callback=_progress,
                    location_callback=_on_location,
                )
                if abort_check and abort_check(idea_file):
                    _log(f"SIMULATE [{idx}/{total}]: {stem} 已被中断", level="warning")
                else:
                    completed = summary.get('completed', 0)
                    failed = summary.get('failed', 0)
                    cnt = summary.get('count', 0)
                    sharpe = summary.get('sharpe_avg', 'N/A')
                    sim_status, error_text = _resolve_sim_summary_state(summary, final=True)
                    pool.update_by_idea(
                        idea_file,
                        sim_status=sim_status,
                        sim_csv=str(output_csv.relative_to(pipeline_dir)),
                        sim_summary=summary,
                        error=error_text,
                    )
                    if sim_status == "error":
                        _log(
                            f"SIMULATE [{idx}/{total}]: {stem} 失败 {completed}/{cnt}, error={error_text or 'N/A'}",
                            level="error",
                        )
                    else:
                        _log(f"SIMULATE [{idx}/{total}]: {stem} 完成 {completed}/{cnt}, sharpe_avg={sharpe}")
                    if on_sim_done:
                        try:
                            on_sim_done()
                        except Exception:
                            pass
                if stop_check and stop_check():
                    return
            except Exception as exc:
                _log(f"SIMULATE [{idx}/{total}] 失败: {stem}: {exc}", level="error")
                pool.update_by_idea(idea_file, sim_status="error", error=str(exc))
                if stop_check and stop_check():
                    return

    with ThreadPoolExecutor(max_workers=sim_concurrent) as executor:
        futures = [executor.submit(_worker_loop) for _ in range(sim_concurrent)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                _log(f"SIMULATE worker异常: {exc}", level="error")


# ── Phase 4–6: DECIDE → ENHANCE → IMPLEMENT ─────────────────────────

def _next_enhance_round(pipeline_dir: Path) -> int:
    """Compute the next enhance round number by scanning existing round_* directories."""
    enhance_dir = pipeline_dir / "enhance"
    if not enhance_dir.exists():
        return 1
    existing = []
    for d in enhance_dir.iterdir():
        if d.is_dir() and d.name.startswith("round_"):
            try:
                existing.append(int(d.name.split("_", 1)[1]))
            except (ValueError, IndexError):
                pass
    return max(existing, default=0) + 1


def phase_decide_enhance_implement(
    pipeline_dir: Path, session, pool: PoolManager,
    llm_config: dict, config: dict, iteration: int,
    log_cb=None,
) -> list[Path]:
    """Run AI decision, enhancement, implementation. Returns new idea files."""
    def _log(msg, level="info", phase="decide"):
        if log_cb:
            log_cb(msg, level=level, phase=phase)
        logger.info(msg) if level == "info" else getattr(logger, level, logger.info)(msg)

    candidates = pool.candidates_for_enhance()
    if not candidates:
        _log("没有待增强的候选Idea", phase="decide")
        return []

    # Compute the actual enhance round number from existing directories
    round_num = _next_enhance_round(pipeline_dir)

    # Phase 4: DECIDE
    _log(f"DECIDE: 正在从 {len(candidates)} 个候选中选择增强目标...", phase="decide")
    decide_prompt_override = str((config.get("prompt_overrides") or {}).get("decide_system_prompt") or "")
    if decide_prompt_override:
        decide_prompt_override = _render_prompt_template(
            decide_prompt_override,
            {"MAX_ENHANCE_PER_ROUND": config.get("max_enhance_per_round", 4)},
        )
    actions = decide(
        candidates=candidates,
        llm_config=llm_config,
        iteration=iteration,
        max_enhance_per_round=config.get("max_enhance_per_round", 4),
        custom_prompt=decide_prompt_override or config.get("decide_prompt", ""),
        pipeline_dir=pipeline_dir,
    )

    if not actions:
        _log("AI 决策: 本轮无需增强", phase="decide")
        return []

    _log(f"DECIDE 完成: 选出 {len(actions)} 个增强任务 (enhance round {round_num})", phase="decide")

    # Save decision
    decision_path = pipeline_dir / "enhance" / f"round_{round_num}" / "decision.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")

    # Mark selected ideas
    for action in actions:
        mode = action.get("mode", "single")
        for f in action.get("idea_files", []):
            pool.update_by_idea(f, enhance_selected=True, enhance_mode=mode, enhance_status="selected", enhance_error="")

    # Phase 5: ENHANCE
    _log(f"ENHANCE: 开始增强 {len(actions)} 个模板...", phase="enhance")
    all_new_ideas = []
    for i, action in enumerate(actions):
        idea_files = action.get("idea_files", [])
        try:
            for idea_file in idea_files:
                pool.update_by_idea(idea_file, enhance_status="running", enhance_error="")
            _log(f"ENHANCE [{i+1}/{len(actions)}]: 正在增强...", phase="enhance")
            enhanced_files = enhance(
                action=action,
                pipeline_dir=pipeline_dir,
                round_num=round_num,
                llm_config=llm_config,
                config=config,
            )
            for idea_file in idea_files:
                pool.update_by_idea(idea_file, enhance_status="done", enhance_error="")
            _log(f"ENHANCE [{i+1}/{len(actions)}]: 产出 {len(enhanced_files)} 个增强文件", phase="enhance")
        except Exception as exc:
            for idea_file in idea_files:
                pool.update_by_idea(idea_file, enhance_status="error", enhance_error=str(exc))
            _log(f"ENHANCE 失败: {exc}", level="error", phase="enhance")
            continue

        # Phase 6: IMPLEMENT each enhanced template
        dataset_folder = f"{config['dataset_id']}_{config['region']}_delay{config['delay']}"
        impl_dir = pipeline_dir / "implement" / f"round_{round_num}"

        for et_path in enhanced_files:
            try:
                _log(f"IMPLEMENT: 正在实现 {et_path.name}...", phase="implement")
                new_ideas = implement_enhanced(
                    enhanced_templates_path=et_path,
                    dataset_folder=dataset_folder,
                    output_dir=impl_dir,
                )
                _log(f"IMPLEMENT: {et_path.name} → {len(new_ideas)} 个新Idea", phase="implement")
                all_new_ideas.extend(new_ideas)
            except Exception as exc:
                _log(f"IMPLEMENT 失败: {et_path.name}: {exc}", level="error", phase="implement")

    _log(f"DECIDE/ENHANCE/IMPLEMENT 完成: 共产出 {len(all_new_ideas)} 个新Idea", phase="implement")
    return all_new_ideas


# ── Main Pipeline Runner ────────────────────────────────────────────

class PipelineRunner:
    """Runs the full autopilot pipeline loop."""

    def __init__(self, pipeline_id: str, pipeline_dir: Path, config: dict):
        self.pipeline_id = pipeline_id
        self.pipeline_dir = pipeline_dir
        self.config = config
        self.state = PipelineState(pipeline_dir / "state.json")
        self.pool = PoolManager(pipeline_dir / "pool.json")
        self._llm_counter_path = pipeline_dir / "llm_requests.jsonl"
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._activity_log: deque = deque(maxlen=500)
        self._log_path = pipeline_dir / "activity_log.jsonl"
        self._log_file_lock = threading.Lock()
        self._load_activity_log()
        self._current_phase: str = ""
        # Abort tracking: idea_file strings whose sim should be cancelled
        self._abort_ideas: set = set()
        self._abort_lock = threading.Lock()
        # SSE subscribers: list of queue.Queue, one per active EventSource connection
        self._subscribers: list[queue.Queue] = []
        self._sub_lock = threading.Lock()
        # Background DECIDE: thread-safe spawning from any sim worker thread
        self._decide_bg_lock = threading.Lock()
        self._decide_bg_thread: Optional[threading.Thread] = None
        self._decide_bg_session = None
        # Flag: main loop is running DECIDE directly — suppress _trigger_decide
        self._main_deciding = False
        self._active_proc: Optional[subprocess.Popen] = None
        self._active_proc_lock = threading.Lock()

    def _set_active_proc(self, proc: Optional[subprocess.Popen]):
        with self._active_proc_lock:
            self._active_proc = proc

    def _terminate_active_proc(self, reason: str = "") -> bool:
        with self._active_proc_lock:
            proc = self._active_proc
        if proc is None or proc.poll() is not None:
            return False

        _terminate_process_tree(proc)
        if reason:
            self.log_activity(reason, level="warning", phase=self._current_phase or "generate")
        return True

    def abort_idea(self, idea_file: str) -> bool:
        """Request cancellation of a running simulation for an idea."""
        with self._abort_lock:
            self._abort_ideas.add(idea_file)
        self.pool.update_by_idea(idea_file, sim_status="aborted", error="用户手动中断")
        self.log_activity(f"用户中断回测: {Path(idea_file).stem}", level="warning", phase="simulate")
        return True

    def save_config(self):
        """Persist current config to config.json (strips sensitive keys)."""
        _sensitive_keys = {"password", "api_key", "apikey", "secret", "token", "username", "email"}
        safe = {k: v for k, v in self.config.items()
                if not any(s in k.lower() for s in _sensitive_keys)}
        cfg_path = self.pipeline_dir / "config.json"
        tmp = cfg_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(cfg_path)

    def retry_inspect_idea(self, idea_file: str) -> bool:
        """Manually retry a failed inspect for a specific idea in the background."""
        entry = next((item for item in self.pool.all() if item.get("idea_file") == idea_file), None)
        if entry is None:
            return False
        if not self.pool.claim_for_inspect(idea_file, allow_retry=True):
            raise RuntimeError("该Idea当前不处于可重试的INSPECT状态")

        def _bg():
            idea_path = Path(idea_file)
            if not idea_path.is_absolute():
                idea_path = self.pipeline_dir / idea_path
            stem = idea_path.stem
            output_dir = _inspect_output_dir(self.pipeline_dir, idea_file)

            try:
                self.pool.update_by_idea(
                    idea_file,
                    alpha_list_file="",
                    sim_summary={},
                    error="",
                )
                self.log_activity(f"手动重试INSPECT: {stem}", phase="inspect")

                alpha_list_path = inspect_idea(
                    idea_path=idea_path,
                    output_dir=output_dir,
                    session=self._session,
                    pipeline_dir=self.pipeline_dir,
                    llm_config=self.llm_config,
                    fixed_universe=self.config.get("universe"),
                    repair_invalid_on_retry=True,
                )

                update_fields = {
                    "inspect_status": "done",
                    "alpha_list_file": str(alpha_list_path.relative_to(self.pipeline_dir)),
                    "error": "",
                }
                try:
                    alpha_list = json.loads(alpha_list_path.read_text(encoding="utf-8"))
                    update_fields["sim_summary"] = {"count": len(alpha_list)}
                except Exception:
                    pass

                self.pool.update_by_idea(idea_file, **update_fields)
                self.log_activity(f"手动INSPECT完成: {stem}", phase="inspect")
                self.trigger_sim()
            except Exception as exc:
                self.pool.update_by_idea(idea_file, inspect_status="error", error=str(exc))
                self.log_activity(f"手动INSPECT失败: {stem}: {exc}", level="error", phase="inspect")

        if not self.is_running() or getattr(self, "_session", None) is None:
            raise RuntimeError("流水线未运行，无法重试INSPECT")

        t = threading.Thread(target=_bg, daemon=True, name=f"retry-inspect-{Path(idea_file).stem}")
        t.start()
        return True

    def retry_idea(self, idea_file: str) -> bool:
        """Retry or resume an aborted/errored idea using existing CSV state when available."""
        with self._abort_lock:
            self._abort_ideas.discard(idea_file)

        entry = next((item for item in self.pool.all() if item.get("idea_file") == idea_file), None)
        if entry is None:
            return False

        summary = dict(entry.get("sim_summary") or {})
        sim_csv = entry.get("sim_csv", "")
        if not sim_csv:
            inferred = self.pipeline_dir / "sim" / _sim_csv_name(idea_file)
            if inferred.exists():
                sim_csv = str(inferred.relative_to(self.pipeline_dir))

        if sim_csv:
            csv_path = self.pipeline_dir / sim_csv
            if csv_path.exists():
                csv_summary = _summarize_csv(csv_path)
                if summary.get("count"):
                    csv_summary["count"] = max(int(summary.get("count") or 0), int(csv_summary.get("count") or 0))
                summary.update(csv_summary)

        self.pool.update_by_idea(idea_file, sim_status="pending", error="", sim_summary=summary, sim_csv=sim_csv)
        completed = int(summary.get("completed") or 0)
        total = int(summary.get("count") or 0)
        action = "继续回测" if sim_csv or completed > 0 else "重试回测"
        self.log_activity(f"{action}: {Path(idea_file).stem} ({completed}/{total})", phase="simulate")
        self.trigger_sim()
        return True

    def continue_idea(self, idea_file: str) -> bool:
        """Backward-compatible alias for retry_idea auto-resume behavior."""
        return self.retry_idea(idea_file)

    def retry_enhance_idea(self, idea_file: str) -> bool:
        """Manually retry a failed single-idea enhancement in the background."""
        entry = next((item for item in self.pool.all() if item.get("idea_file") == idea_file), None)
        if entry is None:
            return False
        if entry.get("enhance_mode") != "single":
            raise RuntimeError("仅支持单增任务手动重试")
        if not entry.get("enhance_selected"):
            raise RuntimeError("该Idea尚未被选中增强")

        def _bg():
            round_num = _manual_enhance_round()
            action = {
                "mode": "single",
                "style": "balanced",
                "idea_files": [idea_file],
            }
            try:
                self.pool.update_by_idea(idea_file, enhance_status="running", enhance_error="")
                self.log_activity(f"手动重试增强: {Path(idea_file).stem}", phase="enhance")
                enhanced_files = enhance(
                    action=action,
                    pipeline_dir=self.pipeline_dir,
                    round_num=round_num,
                    llm_config=self.llm_config,
                    config=self.config,
                )
                self.pool.update_by_idea(idea_file, enhance_status="done", enhance_error="")
                self.log_activity(f"手动ENHANCE完成: {Path(idea_file).stem} → {len(enhanced_files)} 个增强文件", phase="enhance")

                dataset_folder = f"{self.config['dataset_id']}_{self.config['region']}_delay{self.config['delay']}"
                impl_dir = self.pipeline_dir / "implement" / f"round_{round_num}"
                new_count = 0
                for et_path in enhanced_files:
                    try:
                        self.log_activity(f"手动IMPLEMENT: 正在实现 {et_path.name}...", phase="implement")
                        new_ideas = implement_enhanced(
                            enhanced_templates_path=et_path,
                            dataset_folder=dataset_folder,
                            output_dir=impl_dir,
                        )
                        self.log_activity(f"手动IMPLEMENT: {et_path.name} → {len(new_ideas)} 个新Idea", phase="implement")
                        new_count += len(new_ideas)
                        for idea_path in new_ideas:
                            rel = str(idea_path.relative_to(self.pipeline_dir))
                            self.pool.add(PoolEntry(
                                idea_file=rel,
                                origin=f"enhance_round_{round_num}",
                            ))
                    except Exception as exc:
                        self.log_activity(f"手动IMPLEMENT失败: {et_path.name}: {exc}", level="error", phase="implement")
                self.log_activity(f"手动增强完成: {Path(idea_file).stem}, 新增 {new_count} 个Idea", phase="implement")
            except Exception as exc:
                self.pool.update_by_idea(idea_file, enhance_status="error", enhance_error=str(exc))
                self.log_activity(f"手动ENHANCE失败: {Path(idea_file).stem}: {exc}", level="error", phase="enhance")

        t = threading.Thread(target=_bg, daemon=True, name=f"retry-enhance-{Path(idea_file).stem}")
        t.start()
        return True

    def trigger_sim(self):
        """Spawn extra simulation workers immediately for pending ideas.

        Called when sim_concurrent is increased via API so new workers
        start working right away instead of waiting for the next loop iteration.
        """
        if not self.is_running():
            return
        session = getattr(self, "_session", None)
        if session is None:
            return
        pending = self.pool.pending_sim()
        if not pending:
            return

        sim_concurrent = self.config.get("sim_concurrent", self.config.get("concurrency", 2))
        sim_multi_slots = self.config.get("sim_multi_slots", self.config.get("batch_size", 2))
        self.log_activity(
            f"Worker扩容: 立即启动回测 ({len(pending)} 个待回测, {sim_concurrent} worker)",
            phase="simulate",
        )

        def _get_limit():
            return self.config.get("sim_concurrent", self.config.get("concurrency", 2))

        def _bg():
            def _log(msg, level="info", phase="simulate"):
                self.log_activity(msg, level=level, phase="simulate")
            phase_simulate(
                self.pipeline_dir, session, self.pool,
                sim_multi_slots=sim_multi_slots,
                sim_concurrent=sim_concurrent,
                log_cb=_log,
                abort_check=self._is_idea_aborted,
                stop_check=self._stop_event.is_set,
                get_worker_limit=_get_limit,
                on_sim_done=self._after_sim_done,
            )

        t = threading.Thread(target=_bg, daemon=True, name=f"trigger-sim-{self.pipeline_id}")
        t.start()

    def _after_sim_done(self):
        """Run immediate stop evaluation after each completed simulation.

        Order matters: stop conditions based on Sharpe / completed counts / submitted
        counts should preempt any new DECIDE or SIM pickup.
        """
        reason = self.apply_stop_conditions_now()
        if reason or self._stop_event.is_set():
            return
        self._trigger_decide()

    def _trigger_decide(self):
        """Try to run DECIDE in background for any candidates ready for enhancement.

        Thread-safe: uses _decide_bg_lock to prevent concurrent spawning.
        Called after each idea finishes simulation (from any source).
        """
        if self._stop_event.is_set():
            return
        if not self.is_running():
            return

        with self._decide_bg_lock:
            # Don't spawn if the main loop is running DECIDE directly
            if self._main_deciding:
                return
            # Don't spawn if a background decide is already running
            if self._decide_bg_thread is not None and self._decide_bg_thread.is_alive():
                return
            candidates = self.pool.candidates_for_enhance()
            if not candidates:
                return

            self.log_activity(
                f"DECIDE: {len(candidates)} 个候选可增强, 后台启动AI决策",
                phase="decide",
            )

            def _bg_decide():
                try:
                    with self._decide_bg_lock:
                        sess = self._decide_bg_session
                    if sess is None:
                        sess = _create_brain_session(self.config)
                    else:
                        try:
                            sess = _refresh_brain_session(sess, self.config)
                        except Exception:
                            sess = _create_brain_session(self.config)
                    with self._decide_bg_lock:
                        self._decide_bg_session = sess

                    def _log(msg, level="info", phase="decide"):
                        self.log_activity(msg, level=level, phase=phase)

                    iteration = self.state.get("iteration", 0)
                    new_ideas = phase_decide_enhance_implement(
                        self.pipeline_dir, sess, self.pool,
                        self.llm_config, self.config, iteration,
                        log_cb=_log,
                    )
                    if new_ideas:
                        latest_round = max((_next_enhance_round(self.pipeline_dir) - 1), 1)
                        for p in new_ideas:
                            rel = str(p.relative_to(self.pipeline_dir))
                            self.pool.add(PoolEntry(
                                idea_file=rel,
                                origin=f"enhance_round_{latest_round}",
                            ))
                        self.log_activity(
                            f"后台DECIDE完成: 新增 {len(new_ideas)} 个Idea入池",
                            phase="decide",
                        )
                except Exception as exc:
                    self.log_activity(f"后台DECIDE失败: {exc}", level="error", phase="decide")

            self._decide_bg_thread = threading.Thread(target=_bg_decide, daemon=True)
            self._decide_bg_thread.start()

    def _is_idea_aborted(self, idea_file: str) -> bool:
        """Check if an idea has been flagged for abort."""
        with self._abort_lock:
            return idea_file in self._abort_ideas

    def subscribe(self) -> queue.Queue:
        """Register a new SSE subscriber. Returns a Queue that receives log entries."""
        q: queue.Queue = queue.Queue()
        with self._sub_lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        """Remove an SSE subscriber."""
        with self._sub_lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def _broadcast(self, entry: dict):
        """Push log entry to all SSE subscribers."""
        with self._sub_lock:
            dead = []
            for q in self._subscribers:
                try:
                    q.put_nowait(entry)
                except Exception:
                    dead.append(q)
            for q in dead:
                try:
                    self._subscribers.remove(q)
                except ValueError:
                    pass

    def _load_activity_log(self):
        """Load persisted activity log from disk on init."""
        if self._log_path.exists():
            try:
                with open(self._log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                self._activity_log.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                logger.info(f"Loaded {len(self._activity_log)} log entries from {self._log_path.name}")
            except Exception as exc:
                logger.warning(f"Failed to load activity log: {exc}")

    def _persist_log_entry(self, entry: dict):
        """Append one log entry to the JSONL file on disk."""
        with self._log_file_lock:
            try:
                self._log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                pass  # don't let log persistence break the pipeline

    def log_activity(self, msg: str, level: str = "info", phase: str = ""):
        """Append a timestamped activity entry, persist to disk, and broadcast to SSE."""
        p = phase or self._current_phase
        entry = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "level": level,
            "msg": msg,
            "phase": p,
        }
        self._activity_log.append(entry)
        self._persist_log_entry(entry)
        self._broadcast(entry)
        getattr(logger, level, logger.info)(f"[{self.pipeline_id}] {msg}")

    def get_activity_log(self, n: int = 50) -> list[dict]:
        """Return the last n activity entries."""
        return list(self._activity_log)[-n:]

    @property
    def llm_config(self) -> dict:
        return {
            "api_key": self.config.get("moonshot_api_key", ""),
            "base_url": self.config.get("moonshot_base_url", "https://api.moonshot.cn/v1"),
            "model": self.config.get("moonshot_model", "kimi-k2.5"),
            "counter_path": str(self._llm_counter_path),
            "prompt_overrides": self.config.get("prompt_overrides") or {},
        }

    def _default_stop_conditions(self) -> dict:
        return {
            "sharpe_target_count": {
                "min_sharpe": None,
                "target_count": None,
                "use_abs": False,
            },
            "max_pool_ideas": None,
            "max_alpha_submitted": None,
            "max_sim_completed": None,
            "max_iterations": None,
            "diminishing_returns": {
                "enabled": False,
                "min_sharpe": None,
                "lookback_rounds": 2,
                "degrade_ratio": 0.5,
                "min_baseline_samples": 20,
            },
        }

    def get_stop_conditions(self) -> dict:
        defaults = self._default_stop_conditions()
        raw = self.config.get("stop_conditions") or {}
        merged = json.loads(json.dumps(defaults, ensure_ascii=False))
        if not isinstance(raw, dict):
            return merged
        for key in ("max_pool_ideas", "max_alpha_submitted", "max_sim_completed", "max_iterations"):
            if key in raw:
                merged[key] = raw.get(key)
        if isinstance(raw.get("sharpe_target_count"), dict):
            merged["sharpe_target_count"].update(raw.get("sharpe_target_count") or {})
        if isinstance(raw.get("diminishing_returns"), dict):
            merged["diminishing_returns"].update(raw.get("diminishing_returns") or {})
        return merged

    def _collect_stop_condition_metrics(self, stop_conditions: dict | None = None) -> dict:
        stop_conditions = stop_conditions or self.get_stop_conditions()
        entries = self.pool.all()
        sharpe_cfg = stop_conditions.get("sharpe_target_count") or {}
        dr_cfg = stop_conditions.get("diminishing_returns") or {}
        sharpe_threshold = sharpe_cfg.get("min_sharpe")
        sharpe_use_abs = bool(sharpe_cfg.get("use_abs"))
        dr_threshold = dr_cfg.get("min_sharpe")
        if dr_threshold is None:
            dr_threshold = sharpe_threshold if sharpe_threshold is not None else 1.0

        metrics = {
            "pool_ideas": len(entries),
            "iterations": int(self.state.get("iteration", 0) or 0),
            "alpha_submitted": 0,
            "sim_completed": 0,
            "qualified_sharpe_count": 0,
            "qualified_sharpe_threshold": sharpe_threshold,
            "qualified_sharpe_use_abs": sharpe_use_abs,
            "enhance_rounds": [],
        }
        enhance_rounds: dict[int, dict] = {}

        for entry in entries:
            summary = entry.get("sim_summary") or {}
            entry_submitted = 0
            entry_completed = max(int(summary.get("completed") or 0), 0)
            qualified_for_sharpe = 0
            qualified_for_diminishing = 0

            sim_csv_rel = entry.get("sim_csv") or ""
            if sim_csv_rel:
                csv_path = self.pipeline_dir / sim_csv_rel
                if csv_path.exists():
                    try:
                        df = _load_latest_sim_rows(csv_path)
                        entry_submitted = len(df)
                        if not df.empty and "status" in df.columns:
                            status_col = df["status"].astype(str).str.upper().str.strip()
                            completed_df = df[status_col.isin(_SIM_COMPLETED_STATUSES)]
                        else:
                            completed_df = df.iloc[0:0]
                        entry_completed = max(entry_completed, len(completed_df))
                        if not completed_df.empty and "sharpe" in completed_df.columns:
                            sharpe_series = completed_df["sharpe"].astype(float)
                            if sharpe_threshold is not None:
                                compare_series = sharpe_series.abs() if sharpe_use_abs else sharpe_series
                                qualified_for_sharpe = int((compare_series >= float(sharpe_threshold)).sum())
                            qualified_for_diminishing = int((sharpe_series >= float(dr_threshold)).sum())
                    except Exception:
                        pass

            if not entry_submitted:
                status_breakdown = summary.get("status_breakdown") or {}
                if isinstance(status_breakdown, dict) and status_breakdown:
                    try:
                        entry_submitted = sum(int(v or 0) for v in status_breakdown.values())
                    except Exception:
                        entry_submitted = 0
                if not entry_submitted:
                    entry_submitted = entry_completed + max(int(summary.get("failed") or 0), 0)

            metrics["alpha_submitted"] += max(entry_submitted, 0)
            metrics["sim_completed"] += max(entry_completed, 0)
            metrics["qualified_sharpe_count"] += max(qualified_for_sharpe, 0)

            origin = str(entry.get("origin") or "")
            if origin.startswith("enhance_round_"):
                try:
                    round_num = int(origin.split("enhance_round_", 1)[1])
                except (TypeError, ValueError):
                    round_num = None
                if round_num is not None:
                    round_stats = enhance_rounds.setdefault(round_num, {
                        "round": round_num,
                        "submitted": 0,
                        "completed": 0,
                        "qualified": 0,
                    })
                    round_stats["submitted"] += max(entry_submitted, 0)
                    round_stats["completed"] += max(entry_completed, 0)
                    round_stats["qualified"] += max(qualified_for_diminishing, 0)

        metrics["enhance_rounds"] = []
        for round_num in sorted(enhance_rounds.keys()):
            item = enhance_rounds[round_num]
            completed = int(item.get("completed") or 0)
            qualified = int(item.get("qualified") or 0)
            item["qualified_rate"] = round(qualified / completed, 4) if completed > 0 else None
            metrics["enhance_rounds"].append(item)
        return metrics

    def _check_diminishing_returns(self, stop_conditions: dict, metrics: dict) -> str:
        cfg = stop_conditions.get("diminishing_returns") or {}
        if not cfg.get("enabled"):
            return ""
        rounds = list(metrics.get("enhance_rounds") or [])
        if len(rounds) < 2:
            return ""
        lookback_rounds = max(int(cfg.get("lookback_rounds") or 2), 1)
        min_baseline_samples = max(int(cfg.get("min_baseline_samples") or 20), 1)
        degrade_ratio = float(cfg.get("degrade_ratio") or 0.5)
        if len(rounds) <= lookback_rounds:
            return ""

        recent_rounds = rounds[-lookback_rounds:]
        baseline_rounds = rounds[:-lookback_rounds]
        baseline_completed = sum(int(item.get("completed") or 0) for item in baseline_rounds)
        recent_completed = sum(int(item.get("completed") or 0) for item in recent_rounds)
        if baseline_completed < min_baseline_samples or recent_completed < min_baseline_samples:
            return ""

        baseline_qualified = sum(int(item.get("qualified") or 0) for item in baseline_rounds)
        recent_qualified = sum(int(item.get("qualified") or 0) for item in recent_rounds)
        baseline_rate = baseline_qualified / baseline_completed if baseline_completed > 0 else 0.0
        recent_rate = recent_qualified / recent_completed if recent_completed > 0 else 0.0
        if baseline_rate <= 0:
            return ""
        if recent_rate <= baseline_rate * degrade_ratio:
            threshold = cfg.get("min_sharpe")
            threshold_text = f", Sharpe>={threshold:g}" if isinstance(threshold, (int, float)) else ""
            return (
                f"触发停止条件: 最近 {lookback_rounds} 轮增强合格率降至 {recent_rate:.2%}，"
                f"低于历史基线 {baseline_rate:.2%} 的 {degrade_ratio:g} 倍{threshold_text}"
            )
        return ""

    def evaluate_stop_conditions(self) -> tuple[str, dict]:
        stop_conditions = self.get_stop_conditions()
        metrics = self._collect_stop_condition_metrics(stop_conditions)
        sharpe_cfg = stop_conditions.get("sharpe_target_count") or {}
        min_sharpe = sharpe_cfg.get("min_sharpe")
        target_count = sharpe_cfg.get("target_count")
        sharpe_use_abs = bool(sharpe_cfg.get("use_abs"))
        if min_sharpe is not None and target_count is not None:
            qualified_count = int(metrics.get("qualified_sharpe_count") or 0)
            if qualified_count >= int(target_count):
                sharpe_label = "|Sharpe|" if sharpe_use_abs else "Sharpe"
                return f"触发停止条件: {sharpe_label} >= {float(min_sharpe):g} 的结果已达到 {qualified_count} 个", metrics

        max_pool_ideas = stop_conditions.get("max_pool_ideas")
        if max_pool_ideas is not None and int(metrics.get("pool_ideas") or 0) >= int(max_pool_ideas):
            return f"触发停止条件: 池中 idea 总数达到 {int(metrics.get('pool_ideas') or 0)} / {int(max_pool_ideas)}", metrics

        max_alpha_submitted = stop_conditions.get("max_alpha_submitted")
        if max_alpha_submitted is not None and int(metrics.get("alpha_submitted") or 0) >= int(max_alpha_submitted):
            return f"触发停止条件: 累计回测提交量达到 {int(metrics.get('alpha_submitted') or 0)} / {int(max_alpha_submitted)}", metrics

        max_sim_completed = stop_conditions.get("max_sim_completed")
        if max_sim_completed is not None and int(metrics.get("sim_completed") or 0) >= int(max_sim_completed):
            return f"触发停止条件: 累计回测完成量达到 {int(metrics.get('sim_completed') or 0)} / {int(max_sim_completed)}", metrics

        max_iterations = stop_conditions.get("max_iterations")
        if max_iterations is not None and int(metrics.get("iterations") or 0) >= int(max_iterations):
            return f"触发停止条件: 迭代次数达到 {int(metrics.get('iterations') or 0)} / {int(max_iterations)}", metrics

        diminishing_reason = self._check_diminishing_returns(stop_conditions, metrics)
        if diminishing_reason:
            return diminishing_reason, metrics
        return "", metrics

    def apply_stop_conditions_now(self) -> str:
        reason, metrics = self.evaluate_stop_conditions()
        self.state.set("stop_metrics", metrics)
        if reason and not self._stop_event.is_set():
            self.stop(reason=reason, source="auto")
            self.log_activity(reason, level="warning", phase=self._current_phase or "idle")
        return reason

    def start(self):
        """Start pipeline in background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning(f"Pipeline {self.pipeline_id} already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name=f"pipeline-{self.pipeline_id}")
        self._thread.start()
        self.state.update(
            status="running",
            error="",
            error_code="",
            suggested_data_type="",
            stop_reason="",
            stop_source="",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            last_checkpoint=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    def stop(self, force: bool = False, reason: str = "", source: str = "manual"):
        """Request graceful stop after current iteration."""
        self._stop_event.set()
        self.state.update(
            status="stopping",
            stop_reason=reason or self.state.get("stop_reason", "") or "用户手动停止",
            stop_source=source or self.state.get("stop_source", "") or "manual",
        )
        if force:
            self._terminate_active_proc("已强制终止当前阶段子进程")
        logger.info(f"Stop requested for pipeline {self.pipeline_id}")

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "running": self.is_running(),
            "dataset_id": self.config.get("dataset_id", ""),
            "region": self.config.get("region", ""),
            "delay": self.config.get("delay", ""),
            "universe": self.config.get("universe", ""),
            "data_type": self.config.get("data_type", "MATRIX"),
            "decide_prompt": self.config.get("decide_prompt", ""),
            "sim_concurrent": self.config.get("sim_concurrent", 2),
            "sim_multi_slots": self.config.get("sim_multi_slots", 2),
            "stop_conditions": self.get_stop_conditions(),
            "llm_request_counts": summarize_llm_requests(self._llm_counter_path),
            **self.state.to_dict(),
            "pool_stats": self.pool.stats(),
        }

    def _run_loop(self):
        """Main loop: generate → (inspect → simulate → decide → enhance → implement) → repeat"""
        self._current_phase = "init"
        try:
            session = _create_brain_session(self.config)
            self._session = session          # expose for trigger_sim()
            self.log_activity("BRAIN 会话已创建")
        except Exception as exc:
            self.log_activity(f"创建BRAIN会话失败: {exc}", "error")
            self.state.update(status="error", error=str(exc))
            self._broadcast({"__event__": "done", "success": False, "error": str(exc)})
            return

        iteration = self.state.get("iteration", 0)

        # Phase 1: GENERATE (only on first run)
        if iteration == 0 and self.pool.size() == 0:
            self._current_phase = "generate"
            self.state.set("phase", "generate")
            self.log_activity("开始 GENERATE 阶段 — 生成初始Idea")
            try:
                def _gen_log(line, level="info", phase="generate"):
                    self.log_activity(line, level=level, phase=phase)
                idea_files = phase_generate(
                    self.pipeline_dir,
                    self.config,
                    log_cb=_gen_log,
                    stop_check=self._stop_event.is_set,
                    proc_cb=self._set_active_proc,
                )
                for idea_path in idea_files:
                    rel = str(idea_path.relative_to(self.pipeline_dir))
                    self.pool.add(PoolEntry(idea_file=rel, origin="gen"))
                self.state.set("gen_count", len(idea_files))
                self.state.update(error_code="", suggested_data_type="")
                self.log_activity(f"GENERATE 完成: 产出 {len(idea_files)} 个Idea")
                self.apply_stop_conditions_now()
            except PipelineStopRequested as exc:
                self.log_activity(str(exc), "warning", phase="generate")
                self.state.update(status="stopped", phase="generate", error="")
                self._broadcast({"__event__": "done", "success": True, "stopped": True})
                return
            except GenerateDataTypeMismatch as exc:
                self.log_activity(str(exc), "warning", phase="generate")
                self.state.update(
                    status="error",
                    phase="generate",
                    error=str(exc),
                    error_code="generate_data_type_mismatch",
                    suggested_data_type=exc.suggested_data_type,
                )
                self._broadcast({
                    "__event__": "done",
                    "success": False,
                    "error": str(exc),
                    "error_code": "generate_data_type_mismatch",
                    "suggested_data_type": exc.suggested_data_type,
                })
                return
            except Exception as exc:
                self.log_activity(f"GENERATE 失败: {exc}", "error")
                self.state.update(
                    status="error",
                    phase="generate",
                    error=str(exc),
                    error_code="",
                    suggested_data_type="",
                )
                self._broadcast({"__event__": "done", "success": False, "error": str(exc)})
                return

        # Main loop: interleaved inspect+sim pipeline, then decide/enhance
        while not self._stop_event.is_set():
            iteration += 1
            self.state.update(iteration=iteration, phase="simulate")
            self.log_activity(f"=== 迭代 {iteration} 开始 | 池中 {self.pool.size()} 个Idea ===")

            # Re-authenticate periodically
            try:
                session = _refresh_brain_session(session, self.config)
            except Exception:
                try:
                    session = _create_brain_session(self.config)
                    self._session = session
                    self.log_activity("BRAIN 会话已重新创建")
                except Exception as exc:
                    self.log_activity(f"会话重认证失败: {exc}", "error")
                    self.state.update(status="error", error=f"Session failed: {exc}")
                    self._broadcast({"__event__": "done", "success": False, "error": str(exc)})
                    return

            sim_multi_slots = self.config.get("sim_multi_slots", self.config.get("batch_size", 2))
            sim_concurrent = self.config.get("sim_concurrent", self.config.get("concurrency", 2))

            # Phase 2a: SIMULATE any previously-pending ideas first (from prior runs/restarts)
            pre_pending_sim = self.pool.pending_sim()
            if pre_pending_sim:
                self._current_phase = "simulate"
                self.state.set("phase", "simulate")
                n = len(pre_pending_sim)
                self.log_activity(f"SIMULATE: 发现 {n} 个已检查但未回测的Idea, 先补回测", phase="simulate")
                def _pre_sim_log(msg, level="info", phase="simulate"):
                    self._current_phase = "simulate"
                    self.log_activity(msg, level=level, phase="simulate")
                def _get_limit():
                    return self.config.get("sim_concurrent", self.config.get("concurrency", 2))
                phase_simulate(
                    self.pipeline_dir, session, self.pool,
                    sim_multi_slots=sim_multi_slots,
                    sim_concurrent=sim_concurrent,
                    log_cb=_pre_sim_log,
                    abort_check=self._is_idea_aborted,
                    stop_check=self._stop_event.is_set,
                    get_worker_limit=_get_limit,
                    on_sim_done=self._after_sim_done,
                )
                self.apply_stop_conditions_now()

            if self._stop_event.is_set():
                break

            # Phase 2b+3: INSPECT (parallel) → SIMULATE (parallel)
            # Inspect ideas in parallel (up to 5 threads), then simulate all.
            pending_inspect = self.pool.pending_inspect()
            if pending_inspect:
                self._current_phase = "inspect"
                self.state.set("phase", "inspect")
                total_inspect = len(pending_inspect)
                inspect_concurrent = min(5, total_inspect)
                self.log_activity(f"INSPECT: 开始并行检查 {total_inspect} 个Idea ({inspect_concurrent} 线程)", phase="inspect")

                from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed

                def _inspect_one(idx_i, entry):
                    """Inspect a single idea in a worker thread."""
                    if self._stop_event.is_set():
                        return
                    idea_file = entry["idea_file"]
                    if not self.pool.claim_for_inspect(idea_file):
                        return
                    idea_path = Path(idea_file)
                    if not idea_path.is_absolute():
                        idea_path = self.pipeline_dir / idea_path
                    stem = idea_path.stem

                    self.log_activity(f"INSPECT [{idx_i}/{total_inspect}]: {stem}", phase="inspect")
                    try:
                        from stage_inspect import inspect_idea
                        output_dir = _inspect_output_dir(self.pipeline_dir, idea_file)
                        alpha_list_path = inspect_idea(
                            idea_path=idea_path,
                            output_dir=output_dir,
                            session=session,
                            pipeline_dir=self.pipeline_dir,
                            llm_config=self.llm_config,
                            fixed_universe=self.config.get("universe"),
                        )
                        self.pool.update_by_idea(
                            entry["idea_file"],
                            inspect_status="done",
                            alpha_list_file=str(alpha_list_path.relative_to(self.pipeline_dir)),
                        )
                        try:
                            _al = json.loads(alpha_list_path.read_text(encoding="utf-8"))
                            self.pool.update_by_idea(entry["idea_file"], sim_summary={"count": len(_al)})
                        except Exception:
                            pass
                        self.log_activity(f"INSPECT [{idx_i}/{total_inspect}]: {stem} → 完成", phase="inspect")
                    except Exception as exc:
                        self.log_activity(f"INSPECT [{idx_i}/{total_inspect}] 失败: {stem}: {exc}", level="error", phase="inspect")
                        self.pool.update_by_idea(entry["idea_file"], inspect_status="error", error=str(exc))

                executor = ThreadPoolExecutor(max_workers=inspect_concurrent)
                futures = {
                    executor.submit(_inspect_one, i, entry): entry
                    for i, entry in enumerate(pending_inspect, 1)
                }
                try:
                    for future in _as_completed(futures, timeout=300):
                        try:
                            future.result(timeout=180)
                        except Exception as exc:
                            entry = futures[future]
                            self.log_activity(f"INSPECT worker异常: {entry.get('idea_file','?')}: {exc}", level="error", phase="inspect")
                except TimeoutError:
                    self.log_activity(f"INSPECT 超时(300s), 取消剩余任务", level="warning", phase="inspect")
                    for f in futures:
                        f.cancel()
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)

                done_count = len([e for e in self.pool.all() if e.get('inspect_status') == 'done'])
                err_count = len([e for e in self.pool.all() if e.get('inspect_status') == 'error'])
                self.log_activity(f"INSPECT 完成: {done_count}成功/{err_count}失败", phase="inspect")

                # Now SIMULATE all newly-inspected ideas in parallel
                newly_pending_sim = self.pool.pending_sim()
                if newly_pending_sim and not self._stop_event.is_set():
                    self._current_phase = "simulate"
                    self.state.set("phase", "simulate")
                    self.log_activity(f"SIMULATE: 开始回测 {len(newly_pending_sim)} 个已检查Idea", phase="simulate")
                    def _inspect_sim_log(msg, level="info", phase="simulate"):
                        self._current_phase = "simulate"
                        self.log_activity(msg, level=level, phase="simulate")
                    def _get_limit_inspect_sim():
                        return self.config.get("sim_concurrent", self.config.get("concurrency", 2))
                    phase_simulate(
                        self.pipeline_dir, session, self.pool,
                        sim_multi_slots=sim_multi_slots,
                        sim_concurrent=sim_concurrent,
                        log_cb=_inspect_sim_log,
                        abort_check=self._is_idea_aborted,
                        stop_check=self._stop_event.is_set,
                        get_worker_limit=_get_limit_inspect_sim,
                        on_sim_done=self._after_sim_done,
                    )

                sim_done = int(self.pool.stats().get("sim_done") or 0)
                self.log_activity(f"INSPECT+SIM 完成: inspect {done_count}成功/{err_count}失败, 已回测 {sim_done}", phase="simulate")
                self.apply_stop_conditions_now()

            # Also run any ideas that became sim-pending during this inspect loop
            # (e.g. from prior error recovery or missed in interleaved flow)
            post_pending_sim = self.pool.pending_sim()
            if post_pending_sim:
                self._current_phase = "simulate"
                self.state.set("phase", "simulate")
                self.log_activity(f"SIMULATE: 补回测 {len(post_pending_sim)} 个已检查但未回测的Idea", phase="simulate")
                def _post_sim_log(msg, level="info", phase="simulate"):
                    self._current_phase = "simulate"
                    self.log_activity(msg, level=level, phase="simulate")
                def _get_limit_post():
                    return self.config.get("sim_concurrent", self.config.get("concurrency", 2))
                phase_simulate(
                    self.pipeline_dir, session, self.pool,
                    sim_multi_slots=sim_multi_slots,
                    sim_concurrent=sim_concurrent,
                    log_cb=_post_sim_log,
                    abort_check=self._is_idea_aborted,
                    stop_check=self._stop_event.is_set,
                    get_worker_limit=_get_limit_post,
                    on_sim_done=self._after_sim_done,
                )
                self.apply_stop_conditions_now()

            if self._stop_event.is_set():
                break

            # Wait for any running background DECIDE to finish
            with self._decide_bg_lock:
                bg_thread = self._decide_bg_thread
            if bg_thread is not None and bg_thread.is_alive():
                self.log_activity("等待后台DECIDE+ENHANCE+IMPLEMENT完成...", phase="decide")
                bg_thread.join()

            # Final DECIDE for any remaining candidates not yet covered
            remaining_candidates = self.pool.candidates_for_enhance()
            final_new_ideas = []
            if remaining_candidates:
                self._current_phase = "decide"
                self.state.set("phase", "decide")
                self.log_activity(
                    f"DECIDE: 处理剩余 {len(remaining_candidates)} 个候选",
                    phase="decide",
                )

                def _dei_log(msg, level="info", phase="decide"):
                    self._current_phase = phase
                    self.state.set("phase", phase)
                    self.log_activity(msg, level=level, phase=phase)

                # Suppress _trigger_decide while main loop runs DECIDE
                self._main_deciding = True
                try:
                    final_new_ideas = phase_decide_enhance_implement(
                        self.pipeline_dir, session, self.pool,
                        self.llm_config, self.config, iteration,
                        log_cb=_dei_log,
                    )
                except Exception as exc:
                    self.log_activity(f"主循环DECIDE失败: {exc}", level="error", phase="decide")
                    final_new_ideas = []
                finally:
                    self._main_deciding = False

                for idea_path in final_new_ideas:
                    rel = str(idea_path.relative_to(self.pipeline_dir))
                    latest_round = max((_next_enhance_round(self.pipeline_dir) - 1), 1)
                    self.pool.add(PoolEntry(
                        idea_file=rel,
                        origin=f"enhance_round_{latest_round}",
                    ))
                self.apply_stop_conditions_now()

            total_new = len(final_new_ideas)
            self._current_phase = "idle"
            self.log_activity(f"迭代 {iteration} 完成: 新增 {total_new} 个Idea, 池中共 {self.pool.size()} 个")
            self.state.update(
                phase="idle",
                last_completed_iteration=iteration,
                pool_size=self.pool.size(),
                last_checkpoint=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            self.apply_stop_conditions_now()

            if self._stop_event.is_set():
                break

            if not total_new and not self.pool.pending_inspect():
                # Check if everything is stuck in error state
                all_entries = self.pool.all()
                inspect_errors = [e for e in all_entries if e.get('inspect_status') == 'error']
                sim_errors = [e for e in all_entries if e.get('sim_status') == 'error']
                sim_aborted = [e for e in all_entries if e.get('sim_status') == 'aborted']
                pending_sim_count = len(self.pool.pending_sim())

                if inspect_errors and not pending_sim_count:
                    # Retry errored inspections after cooldown.
                    # Recompute the retry list after the wait so manual retries that
                    # moved items to running/done are removed immediately from auto retry.
                    self.log_activity(
                        f"检测到 {len(inspect_errors)} 个INSPECT失败的Idea, 60秒后重新检查待重试列表...",
                        level="warning", phase="inspect"
                    )
                    for _ in range(60):
                        if self._stop_event.is_set():
                            break
                        time.sleep(1)
                    if not self._stop_event.is_set():
                        current_errors = [e for e in self.pool.all() if e.get('inspect_status') == 'error']
                        current_entries = {e.get('idea_file'): e for e in current_errors}
                        reset_count = 0
                        for e in current_errors:
                            self.pool.update_by_idea(e['idea_file'], inspect_status='pending', error='')
                            reset_count += 1
                        skipped_count = max(len(inspect_errors) - reset_count, 0)
                        if reset_count:
                            self.log_activity(
                                f"自动INSPECT重试列表已更新: 重置 {reset_count} 个当前仍失败的Idea为pending, 跳过 {skipped_count} 个已恢复/手动处理中Idea",
                                phase="inspect",
                            )
                        else:
                            self.log_activity(
                                "自动INSPECT重试列表已更新: 所有失败Idea都已恢复或正在手动处理中, 本轮无需自动重试",
                                phase="inspect",
                            )
                elif sim_errors:
                    retryable_sim_errors = [e for e in sim_errors if _is_timeout_retryable_sim_error(e)]
                    non_retryable_sim_errors = [e for e in sim_errors if not _is_timeout_retryable_sim_error(e)]
                    self.log_activity(
                        f"检测到 {len(sim_errors)} 个SIMULATE失败的Idea, 其中 {len(retryable_sim_errors)} 个TIMEOUT可自动重试, 60秒后重新检查待重试列表..."
                        + (f" 已跳过 {len(non_retryable_sim_errors)} 个非TIMEOUT错误Idea" if non_retryable_sim_errors else "")
                        + (f" 已跳过 {len(sim_aborted)} 个aborted状态Idea" if sim_aborted else ""),
                        level="warning", phase="simulate"
                    )
                    for _ in range(60):
                        if self._stop_event.is_set():
                            break
                        time.sleep(1)
                    if not self._stop_event.is_set():
                        current_errors = [e for e in self.pool.all() if e.get('sim_status') == 'error']
                        retryable_current_errors = [e for e in current_errors if _is_timeout_retryable_sim_error(e)]
                        reset_count = 0
                        for e in retryable_current_errors:
                            self.pool.update_by_idea(e['idea_file'], sim_status='pending', error='')
                            reset_count += 1
                        skipped_count = max(len(sim_errors) - reset_count, 0)
                        if reset_count:
                            self.log_activity(
                                f"自动SIM重试列表已更新: 仅重置 {reset_count} 个TIMEOUT失败SIM为pending, 跳过 {skipped_count} 个非TIMEOUT/已恢复/手动处理中Idea",
                                phase="simulate",
                            )
                        else:
                            self.log_activity(
                                "自动SIM重试列表已更新: 当前无TIMEOUT失败SIM需要自动重试, 本轮无需自动重试",
                                phase="simulate",
                            )
                else:
                    # No new ideas produced and nothing pending — wait before retrying
                    self.log_activity("本轮无新Idea产出, 等待60秒后重试...")
                    for _ in range(60):
                        if self._stop_event.is_set():
                            break
                        time.sleep(1)

        stop_reason = str(self.state.get("stop_reason", "") or "").strip()
        self.state.set("status", "stopped")
        final_msg = f"流水线已停止, 共完成 {iteration} 次迭代"
        if stop_reason:
            final_msg += f" | {stop_reason}"
        self.log_activity(final_msg)
        self._broadcast({"__event__": "done", "success": True, "iterations": iteration})



# ── Pipeline Registry (in-process) ──────────────────────────────────

_pipelines: dict[str, PipelineRunner] = {}
_registry_lock = threading.Lock()


def create_pipeline(config: dict) -> PipelineRunner:
    """Create a new pipeline from config."""
    if not config.get("pipeline_id"):
        # Build a descriptive ID: dataset_region_delay_universe_timestamp
        ds = config.get('dataset_id', 'ds')[:20]
        rg = config.get('region', 'XX')
        dl = config.get('delay', '?')
        uni = config.get('universe', '')
        ts = int(time.time())
        pipeline_id = f"{ds}_{rg}_d{dl}_{uni}_{ts}"
        # Sanitize: only keep alnum, dash, underscore
        import re as _re
        pipeline_id = _re.sub(r'[^A-Za-z0-9_-]', '_', pipeline_id)
    else:
        pipeline_id = config["pipeline_id"]
    config["pipeline_id"] = pipeline_id

    orchestrator_root = Path(__file__).resolve().parent
    pipeline_dir = orchestrator_root / "pipelines" / pipeline_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    # Persist config — strip ALL sensitive fields, keep only pipeline parameters
    config_path = pipeline_dir / "config.json"
    _sensitive_keys = {"password", "api_key", "apikey", "secret", "token", "username", "email"}
    safe_config = {
        k: v for k, v in config.items()
        if not any(s in k.lower() for s in _sensitive_keys)
    }
    config_path.write_text(json.dumps(safe_config, ensure_ascii=False, indent=2), encoding="utf-8")

    runner = PipelineRunner(pipeline_id, pipeline_dir, config)

    with _registry_lock:
        _pipelines[pipeline_id] = runner

    return runner


def get_pipeline(pipeline_id: str) -> Optional[PipelineRunner]:
    with _registry_lock:
        return _pipelines.get(pipeline_id)


GLOBAL_WORKER_LIMIT = 8


def list_pipelines() -> list[dict]:
    """List all known pipelines with their status."""
    with _registry_lock:
        results = []
        for pid, runner in _pipelines.items():
            results.append(runner.status())
        return results


def global_worker_usage() -> dict:
    """Return global worker limit and current usage across all pipelines."""
    with _registry_lock:
        used = sum(
            r.config.get("sim_concurrent", 2)
            for r in _pipelines.values()
            if r.is_running()
        )
        return {"limit": GLOBAL_WORKER_LIMIT, "used": used}


def load_existing_pipelines():
    """Scan pipelines/ directory and register any existing pipelines (for resume on restart)."""
    orchestrator_root = Path(__file__).resolve().parent
    pipelines_dir = orchestrator_root / "pipelines"
    if not pipelines_dir.exists():
        return
    archived_ids = set(_load_archive_index().keys())

    for d in pipelines_dir.iterdir():
        if d.is_dir() and (d / "config.json").exists():
            pid = d.name
            if pid in archived_ids:
                logger.info(f"Skip archived pipeline during startup load: {pid}")
                continue
            with _registry_lock:
                if pid in _pipelines:
                    continue
            try:
                config = json.loads((d / "config.json").read_text(encoding="utf-8"))
                config["pipeline_id"] = pid
                runner = PipelineRunner(pid, d, config)
                # Fix stale status: if state.json says "running" but no thread
                # is alive (server was force-killed), reset to "stopped".
                stale_status = runner.state.get("status", "")
                if stale_status in ("running", "stopping") and not runner.is_running():
                    runner.state.set("status", "stopped")
                    logger.info(f"Pipeline {pid}: reset stale status '{stale_status}' → 'stopped'")
                # Fix stale pool entries: running sims from a dead process
                stale_running = [e for e in runner.pool.all() if e.get("sim_status") == "running"]
                for e in stale_running:
                    runner.pool.update_by_idea(
                        e["idea_file"],
                        sim_status="aborted",
                        sim_location="",
                        error="服务重启, 上次回测中断",
                    )
                if stale_running:
                    logger.info(f"Pipeline {pid}: reset {len(stale_running)} stale running sims → aborted")
                with _registry_lock:
                    _pipelines[pid] = runner
                logger.info(f"Loaded existing pipeline: {pid}")
            except Exception as exc:
                logger.warning(f"Failed to load pipeline {pid}: {exc}")


# ── Archive / Delete ─────────────────────────────────────────────────

import shutil

_ARCHIVE_FILE = Path(__file__).resolve().parent / "pipelines" / "_archived.json"


def _load_archive_index() -> dict:
    """Load the archive index from disk. Returns {pipeline_id: metadata}."""
    if _ARCHIVE_FILE.exists():
        try:
            return json.loads(_ARCHIVE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_archive_index(index: dict):
    _ARCHIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = _ARCHIVE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_ARCHIVE_FILE)


def delete_pipeline(pipeline_id: str) -> bool:
    """Stop, unregister, and permanently delete a pipeline and its files."""
    with _registry_lock:
        runner = _pipelines.get(pipeline_id)
    if runner:
        if runner.is_running():
            runner.stop(force=True)
            # Wait briefly for graceful stop
            for _ in range(30):
                if not runner.is_running():
                    break
                time.sleep(0.5)
        pipeline_dir = runner.pipeline_dir
        with _registry_lock:
            _pipelines.pop(pipeline_id, None)
    else:
        # Not in registry — try filesystem directly
        orchestrator_root = Path(__file__).resolve().parent
        pipeline_dir = orchestrator_root / "pipelines" / pipeline_id
        if not pipeline_dir.exists():
            return False

    # Remove from archive index if present
    archive_idx = _load_archive_index()
    if pipeline_id in archive_idx:
        del archive_idx[pipeline_id]
        _save_archive_index(archive_idx)

    # Delete files
    if pipeline_dir.exists():
        shutil.rmtree(pipeline_dir, ignore_errors=True)
        logger.info(f"Deleted pipeline {pipeline_id} at {pipeline_dir}")

    return True


def archive_pipeline(pipeline_id: str) -> bool:
    """Move a pipeline from the active list into archive (files stay on disk)."""
    with _registry_lock:
        runner = _pipelines.get(pipeline_id)
    if not runner:
        return False
    if runner.is_running():
        runner.stop()
        for _ in range(30):
            if not runner.is_running():
                break
            time.sleep(0.5)

    # Save status snapshot into archive index
    archive_idx = _load_archive_index()
    archive_idx[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "dataset_id": runner.config.get("dataset_id", ""),
        "region": runner.config.get("region", ""),
        "delay": runner.config.get("delay", ""),
        "universe": runner.config.get("universe", ""),
        "pool_stats": runner.pool.stats(),
        "archived_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save_archive_index(archive_idx)

    # Unregister from active pipelines
    with _registry_lock:
        _pipelines.pop(pipeline_id, None)

    logger.info(f"Archived pipeline {pipeline_id}")
    return True


def restore_pipeline(pipeline_id: str) -> Optional[PipelineRunner]:
    """Restore an archived pipeline back to the active list."""
    archive_idx = _load_archive_index()
    if pipeline_id not in archive_idx:
        return None

    orchestrator_root = Path(__file__).resolve().parent
    pipeline_dir = orchestrator_root / "pipelines" / pipeline_id
    config_path = pipeline_dir / "config.json"
    if not config_path.exists():
        return None

    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["pipeline_id"] = pipeline_id
    runner = PipelineRunner(pipeline_id, pipeline_dir, config)

    # Fix stale state
    stale_status = runner.state.get("status", "")
    if stale_status in ("running", "stopping"):
        runner.state.set("status", "stopped")

    with _registry_lock:
        _pipelines[pipeline_id] = runner

    # Remove from archive index
    del archive_idx[pipeline_id]
    _save_archive_index(archive_idx)

    logger.info(f"Restored pipeline {pipeline_id} from archive")
    return runner


def list_archived() -> list[dict]:
    """Return list of archived pipeline summaries."""
    return list(_load_archive_index().values())
