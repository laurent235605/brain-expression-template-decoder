import sys
import subprocess
# --- Dependency Check & Auto-Install ---
required_imports = [
    ("getpass", None),
    ("json", None),
    ("logging", None),
    ("os", None),
    ("threading", None),
    ("time", None),
    ("functools", None),
    ("multiprocessing", None),
    ("pathlib", None),
    ("typing", None),
    ("urllib.parse", None),
    ("pandas", "pandas"),
    ("requests", "requests"),
    ("tqdm", "tqdm"),
    ("pandas.io.formats.style", "pandas"),
]
for mod, pipname in required_imports:
    try:
        if "." in mod:
            __import__(mod.split(".")[0])
        else:
            __import__(mod)
    except ImportError:
        if pipname:
            print(f"Installing missing package: {pipname}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pipname])
        else:
            print(f"Module {mod} is a built-in or not installable via pip.")
# --- Script Description ---
"""
Autosimulator for WorldQuant BRAIN platform
- Timestamped logger
- Authentication with biometric check
- User-specified alpha JSON input
- Single/multi simulation mode
- Simulation worker: sends jobs, retries, saves locations
- Result worker: fetches results, saves to JSON
"""
import os
import sys
import time
import json
import threading
import logging
from functools import partial
from multiprocessing.pool import ThreadPool
from datetime import datetime
from pathlib import Path
import requests
import getpass

# Platform specific imports
if sys.platform == 'win32':
    import msvcrt
else:
    import tty
    import termios
import ace_lib

# --- Logger Setup ---
def setup_logger():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'autosim_{timestamp}.log'
    logger = logging.getLogger(f'autosim_{timestamp}')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(log_filename)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger, log_filename

logger, log_filename = setup_logger()

# --- Authentication ---
def get_credentials():
    email = input("Email: ").strip()
    print("Password: ", end='', flush=True)
    password = []
    
    try:
        if sys.platform == 'win32':
            # Windows: Use msvcrt.getch()
            while True:
                char = msvcrt.getch()
                
                # Handle Enter key
                if char in [b'\r', b'\n']:
                    print()  # New line
                    break
                
                # Handle Backspace
                elif char == b'\x08':  # Backspace
                    if password:
                        password.pop()
                        # Move cursor back, print space, move cursor back again
                        print('\b \b', end='', flush=True)
                
                # Handle Ctrl+C
                elif char == b'\x03':  # Ctrl+C
                    print()
                    raise KeyboardInterrupt
                
                # Handle printable characters (ASCII)
                elif 32 <= ord(char) <= 126:  # Printable ASCII range
                    password.append(char.decode('ascii'))
                    print('*', end='', flush=True)
                
                # Handle extended characters
                else:
                    try:
                        decoded_char = char.decode('utf-8')
                        if decoded_char.isprintable():
                            password.append(decoded_char)
                            print('*', end='', flush=True)
                    except UnicodeDecodeError:
                        continue
        else:
            # Unix/macOS: Use tty and termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    char = sys.stdin.read(1)
                    
                    # Handle Enter key
                    if char in ['\r', '\n']:
                        print('\r\n', end='', flush=True)
                        break
                    
                    # Handle Backspace
                    elif char in ['\x7f', '\x08']:
                        if password:
                            password.pop()
                            print('\b \b', end='', flush=True)
                    
                    # Handle Ctrl+C
                    elif char == '\x03':
                        print('\r\n', end='', flush=True)
                        raise KeyboardInterrupt
                    
                    # Handle printable characters
                    elif char.isprintable():
                        password.append(char)
                        print('*', end='', flush=True)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
    except Exception as e:
        # Fallback to getpass
        print(f"\nError reading password: {e}")
        print("Falling back to getpass...")
        return (email, getpass.getpass())

    return (email, ''.join(password))

def authenticate():
    ace_lib.logger = logger
    original_get_credentials = ace_lib.get_credentials
    ace_lib.get_credentials = get_credentials
    try:
        session = ace_lib.start_session()
        expiry = ace_lib.check_session_timeout(session)
        logger.info(f'连接测试结果: session_expiry = {expiry}')
        if expiry <= 0:
            logger.error('身份验证失败，请检查您的用户名和密码。')
            return authenticate()
        logger.info('身份验证成功。')
        return session
    finally:
        ace_lib.get_credentials = original_get_credentials

# --- User Input ---
MASTER_LOG_PATH = "autosim_master_log.json"

def update_master_log(input_json_path, latest_index):
    """
    Update the master log file with the latest successful index for the given input file name.
    """
    import os, json
    file_name = os.path.basename(input_json_path)
    log_data = {}
    # Read existing log if present
    if os.path.exists(MASTER_LOG_PATH):
        try:
            with open(MASTER_LOG_PATH, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception:
            log_data = {}
    # Update with latest index
    log_data[file_name] = latest_index
    # Atomic write
    tmp_path = MASTER_LOG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
    os.replace(tmp_path, MASTER_LOG_PATH)
def get_user_json():
    import re
    while True:
        raw_path = input('Enter path to alpha JSON file: ').strip()
        json_path = re.sub(r'^["\']+|["\']+$', '', raw_path.strip())
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    alpha_list = json.load(f)
                # Check master log for previous progress
                file_name = os.path.basename(json_path)
                start_index = 0
                if os.path.exists(MASTER_LOG_PATH):
                    try:
                        with open(MASTER_LOG_PATH, 'r', encoding='utf-8') as logf:
                            log_data = json.load(logf)
                        if file_name in log_data:
                            last_index = log_data[file_name]
                            print(f'Last time you simulated to position {last_index}.')
                            resp = input(f'Do you want to start from {last_index + 1}? (Y/n) Or enter another starting index: ').strip()
                            if resp.lower() in ['', 'y', 'yes']:
                                start_index = last_index + 1
                            elif resp.isdigit():
                                start_index = int(resp)
                            else:
                                print('Invalid input, starting from 0.')
                                start_index = 0
                    except Exception:
                        pass
                # Slice alpha_list to start from chosen index
                class AlphaList(list):
                    pass
                alpha_list = AlphaList(alpha_list[start_index:])
                alpha_list._start_index = start_index
                return alpha_list, json_path
            except Exception as e:
                logger.error(f'Error reading JSON file: {e}')
        else:
            logger.error(f'JSON file not found: {json_path}')
        print('Please enter a valid path to your alpha JSON file.')

def get_simulation_mode():
    mode = input('Select simulation mode (single/multi): ').strip().lower()
    if mode not in ['single', 'multi']:
        logger.error('Invalid mode. Choose "single" or "multi".')
        sys.exit(1)
    batch_size = None
    if mode == 'multi':
        while True:
            try:
                batch_size = int(input('Enter number of elements per multi-simulation batch (2-10): ').strip())
                if 2 <= batch_size <= 10:
                    break
                else:
                    print('Batch size must be between 2 and 10.')
            except Exception:
                print('Please enter a valid integer between 2 and 10.')
    return mode, batch_size

def get_retry_timeout():
    try:
        timeout = int(input('Enter retry timeout in seconds (default 60): ').strip())
        if timeout < 1:
            timeout = 60
    except Exception:
        timeout = 60
    return timeout


def get_concurrent_count():
    try:
        count = int(input('Enter concurrent simulation count (1-8, default 3): ').strip())
        if count < 1:
            count = 3
    except Exception:
        count = 3
    return count


def coerce_settings_types(expressions):
    """Ensure numeric settings are converted to expected types before simulation."""
    for expr in expressions:
        settings = expr.get('settings', {})

        if 'truncation' in settings:
            try:
                settings['truncation'] = float(settings['truncation'])
            except (ValueError, TypeError):
                pass

        if 'delay' in settings:
            try:
                settings['delay'] = int(settings['delay'])
            except (ValueError, TypeError):
                pass

        if 'decay' in settings:
            try:
                settings['decay'] = int(float(settings['decay']))
            except (ValueError, TypeError):
                pass

        if 'visualization' in settings and isinstance(settings['visualization'], str):
            settings['visualization'] = settings['visualization'].lower() == 'true'

    return expressions


def validate_expression_payload(expressions):
    """Validate the minimum alpha payload structure expected by ace_lib."""
    normalized = []
    for index, expr in enumerate(expressions, start=1):
        if not isinstance(expr, dict):
            raise ValueError(f'第 {index} 个表达式不是对象')

        alpha_type = str(expr.get('type') or 'REGULAR').upper()
        settings = expr.get('settings')
        if not isinstance(settings, dict):
            raise ValueError(f'第 {index} 个表达式缺少 settings')

        if alpha_type == 'SUPER':
            if not expr.get('selection') or not expr.get('combo'):
                raise ValueError(f'第 {index} 个 SUPER Alpha 缺少 selection 或 combo')
            expr['type'] = 'SUPER'
        else:
            if not expr.get('regular'):
                raise ValueError(f'第 {index} 个 REGULAR Alpha 缺少 regular')
            expr['type'] = 'REGULAR'

        normalized.append(expr)

    return normalized


def clamp_concurrent_count(concurrent_count):
    if concurrent_count < 1:
        logger.warning('并发数量小于 1，已自动调整为 1')
        return 1
    if concurrent_count > 8:
        logger.warning('并发数量超过 ace_lib 支持上限 8，已自动调整为 8')
        return 8
    return concurrent_count


def clamp_multi_slot_count(alpha_count_per_slot):
    if alpha_count_per_slot < 2:
        logger.warning('每槽 alpha 数量小于 2，已自动调整为 2')
        return 2
    if alpha_count_per_slot > 10:
        logger.warning('每槽 alpha 数量超过 ace_lib 支持上限 10，已自动调整为 10')
        return 10
    return alpha_count_per_slot


def write_json_atomic(path, payload):
    temp_path = path + '.tmp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)


def fetch_serializable_result(session, alpha_id, simulate_data):
    if not alpha_id:
        return {
            'alpha_id': None,
            'simulate_data': simulate_data,
            'error': 'Simulation failed',
        }

    result = ace_lib.get_simulation_result_json(session, alpha_id)
    return {
        'alpha_id': alpha_id,
        'simulate_data': simulate_data,
        'result': result,
    }


def persist_run_state(location_path, result_path, mode, ordered_results, total_count, start_index):
    completed = sum(1 for item in ordered_results if item is not None)
    alpha_ids = [item['alpha_id'] for item in ordered_results if item and item.get('alpha_id')]

    write_json_atomic(location_path, {
        'mode': mode,
        'total': total_count,
        'completed': completed,
        'start_index': start_index,
        'alpha_ids': alpha_ids,
        'updated_at': datetime.now().isoformat(),
    })

    write_json_atomic(result_path, {
        'mode': mode,
        'total': total_count,
        'completed': completed,
        'start_index': start_index,
        'results': [item for item in ordered_results if item is not None],
    })


def run_single_simulations(session, alpha_entries, concurrent_count, start_index, json_path, location_path, result_path):
    ordered_results = [None] * len(alpha_entries)
    completed_positions = set()
    contiguous_latest = start_index - 1

    def worker(entry):
        position, absolute_index, alpha = entry
        result = ace_lib.simulate_single_alpha(session, alpha)
        serializable = fetch_serializable_result(session, result.get('alpha_id'), result.get('simulate_data'))
        return position, absolute_index, serializable

    with ThreadPool(concurrent_count) as pool:
        for position, absolute_index, serializable in pool.imap_unordered(worker, alpha_entries):
            ordered_results[position] = serializable
            completed_positions.add(position)

            while (contiguous_latest - start_index + 1) in completed_positions:
                contiguous_latest += 1
            if contiguous_latest >= start_index:
                update_master_log(json_path, contiguous_latest)

            persist_run_state(location_path, result_path, 'single', ordered_results, len(alpha_entries), start_index)
            logger.info(f'单 alpha 回测进度 {len(completed_positions)}/{len(alpha_entries)}，alpha_id={serializable.get("alpha_id") or "FAILED"}')

    return [item for item in ordered_results if item is not None]


def run_multi_simulations(session, alpha_entries, concurrent_count, batch_size, start_index, json_path, location_path, result_path):
    ordered_results = [None] * len(alpha_entries)
    completed_positions = set()
    contiguous_latest = start_index - 1
    tasks = [
        alpha_entries[i:i + batch_size]
        for i in range(0, len(alpha_entries), batch_size)
    ]

    def worker(batch_entries):
        positions = [position for position, _, _ in batch_entries]
        absolute_indices = [absolute_index for _, absolute_index, _ in batch_entries]
        alpha_batch = [alpha for _, _, alpha in batch_entries]
        results = ace_lib.simulate_multi_alpha(session, alpha_batch)
        serializable = [
            fetch_serializable_result(session, item.get('alpha_id'), item.get('simulate_data'))
            for item in results
        ]
        return positions, absolute_indices, serializable

    with ThreadPool(concurrent_count) as pool:
        for positions, absolute_indices, serializable_batch in pool.imap_unordered(worker, tasks):
            for position, absolute_index, serializable in zip(positions, absolute_indices, serializable_batch):
                ordered_results[position] = serializable
                completed_positions.add(position)

            while (contiguous_latest - start_index + 1) in completed_positions:
                contiguous_latest += 1
            if contiguous_latest >= start_index:
                update_master_log(json_path, contiguous_latest)

            persist_run_state(location_path, result_path, 'multi', ordered_results, len(alpha_entries), start_index)
            logger.info(f'multi-sim 回测进度 {len(completed_positions)}/{len(alpha_entries)}')

    return [item for item in ordered_results if item is not None]


def run_ace_simulations(session, alpha_list, mode, concurrent_count, json_path, location_path, result_path, start_index, batch_size=None):
    concurrent_count = clamp_concurrent_count(concurrent_count)
    alpha_entries = [
        (position, start_index + position, alpha)
        for position, alpha in enumerate(alpha_list)
    ]

    if mode == 'single':
        return run_single_simulations(session, alpha_entries, concurrent_count, start_index, json_path, location_path, result_path)

    batch_size = clamp_multi_slot_count(batch_size or 2)
    if any(item.get('type') == 'SUPER' for item in alpha_list):
        logger.warning('检测到 SUPER Alpha，ace_lib 的 multi-sim 不支持，已自动降级为单 alpha 并发回测')
        return run_single_simulations(session, alpha_entries, concurrent_count, start_index, json_path, location_path, result_path)

    logger.info(
        f'[MULTI-SIMULATION MODE] 采用 ace_lib multi-sim，单槽 {batch_size} 个 alpha，并发 {concurrent_count} 个槽'
    )
    return run_multi_simulations(session, alpha_entries, concurrent_count, batch_size, start_index, json_path, location_path, result_path)

# --- Main ---
def main():
    session = authenticate()
    alpha_list, json_path = get_user_json()
    start_index = getattr(alpha_list, '_start_index', 0)
    alpha_list = validate_expression_payload(coerce_settings_types(alpha_list))
    mode, batch_size = get_simulation_mode()
    concurrent_count = get_concurrent_count()
    retry_timeout = get_retry_timeout()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    location_path = f'autosim_locations_{timestamp}.json'
    result_path = f'autosim_results_{timestamp}.json'

    logger.info(f'开始使用 ace 核心回测，模式={mode}，并发={concurrent_count}，起始索引={start_index}，失败重试等待={retry_timeout}s')
    results = run_ace_simulations(
        session,
        alpha_list,
        mode,
        concurrent_count,
        json_path,
        location_path,
        result_path,
        start_index,
        batch_size=batch_size,
    )

    success_count = sum(1 for item in results if item.get('alpha_id'))
    failure_count = len(results) - success_count
    logger.info(f'回测完成。成功={success_count}，失败={failure_count}，结果文件={result_path}')
    print('\n' + '=' * 60)
    print('回测完成')
    print('=' * 60)
    print(f'总数: {len(results)}')
    print(f'成功: {success_count}')
    print(f'失败: {failure_count}')
    print(f'结果文件: {result_path}')
    print(f'进度文件: {location_path}')

if __name__ == '__main__':
    main()
