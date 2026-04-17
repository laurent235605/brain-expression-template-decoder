"""
Enhanced Alpha Template Generator Script

This script generates alpha templates with interactive user input for:
- JSON file path selection
- User authentication
- Simulation parameters
- Multi-simulation mode support
- Real-time log monitoring
"""

import asyncio
import json
import os
import getpass
import logging
import threading
import time
import sys
from functools import partial
from multiprocessing.pool import ThreadPool
try:
    import msvcrt  # For Windows password input with asterisks
except ImportError:
    msvcrt = None
from pathlib import Path

import ace_lib

# FIX: Change working directory to script location to ensure logs are created in the right place
# This prevents the "Permission denied" error when trying to create logs in system directories
# The wqb.wqb_logger() function creates log files relative to the current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(script_dir)
    print(f"📁 工作目录已设置为: {os.getcwd()}")
    print(f"📝 日志文件将创建在: {os.getcwd()}")
    
    # Verify the directory is writable
    if not os.access(script_dir, os.W_OK):
        print(f"⚠️  警告: 目录 {script_dir} 不可写，日志可能无法创建")
    else:
        print(f"✅ 目录 {script_dir} 可写，日志将正常创建")
        
except Exception as e:
    print(f"⚠️  警告: 无法更改工作目录到 {script_dir}: {e}")
    print(f"📝 日志文件将创建在当前工作目录: {os.getcwd()}")


COMPAT_LOG_FILENAME = "wqb_compat.log"


def get_compat_logger():
    """Create a logger compatible with the existing web log viewer."""
    logger = logging.getLogger("simulator_wqb_compat")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(COMPAT_LOG_FILENAME, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def build_web_session(username=None, password=None):
    """Build an ace_lib session using web credentials first, then fall back to defaults."""
    logger = get_compat_logger()
    ace_lib.logger = logger

    original_get_credentials = ace_lib.get_credentials
    should_override_credentials = bool(username and password)

    if should_override_credentials:
        ace_lib.get_credentials = lambda: (username, password)

    try:
        session = ace_lib.start_session()
        expiry = ace_lib.check_session_timeout(session)
        if expiry <= 0:
            raise RuntimeError("Authentication failed")
        return session, logger
    finally:
        ace_lib.get_credentials = original_get_credentials


def clamp_concurrent_count(concurrent_count, logger):
    """Clamp concurrent count to ace_lib supported range while keeping user flow uninterrupted."""
    if concurrent_count < 1:
        logger.warning("并发数量小于 1，已自动调整为 1")
        return 1
    if concurrent_count > 8:
        logger.warning("并发数量超过 ace_lib 支持上限 8，已自动调整为 8")
        return 8
    return concurrent_count


def clamp_multi_slot_count(alpha_count_per_slot, logger):
    """Clamp multi-simulation slot size to ace_lib supported range."""
    if alpha_count_per_slot < 2:
        logger.warning("每槽 alpha 数量小于 2，已自动调整为 2")
        return 2
    if alpha_count_per_slot > 10:
        logger.warning("每槽 alpha 数量超过 ace_lib 支持上限 10，已自动调整为 10")
        return 10
    return alpha_count_per_slot


def validate_expression_payload(expressions):
    """Validate the minimum structure expected by ace_lib."""
    normalized = []
    for index, expr in enumerate(expressions, start=1):
        if not isinstance(expr, dict):
            raise ValueError(f"第 {index} 个表达式不是对象")

        alpha_type = str(expr.get("type") or "REGULAR").upper()
        settings = expr.get("settings")
        if not isinstance(settings, dict):
            raise ValueError(f"第 {index} 个表达式缺少 settings")

        if alpha_type == "SUPER":
            if not expr.get("selection") or not expr.get("combo"):
                raise ValueError(f"第 {index} 个 SUPER Alpha 缺少 selection 或 combo")
            expr["type"] = "SUPER"
        else:
            if not expr.get("regular"):
                raise ValueError(f"第 {index} 个 REGULAR Alpha 缺少 regular")
            expr["type"] = "REGULAR"

        normalized.append(expr)

    return normalized


def normalize_web_alpha_list(expressions, start_position=0, random_shuffle=False):
    """Normalize expressions from the web payload into ace_lib-compatible alpha dicts."""
    expressions = coerce_settings_types(expressions)
    expressions = validate_expression_payload(expressions)

    if start_position > 0:
        expressions = expressions[start_position:]

    if random_shuffle:
        import random
        random.shuffle(expressions)

    return expressions


def summarize_ace_results(results, use_multi_sim=False, alpha_count_per_slot=None):
    """Summarize ace_lib-compatible simulation results for the web response."""
    alpha_ids = [item["alpha_id"] for item in results if item.get("alpha_id")]
    successful_count = len(alpha_ids)
    failed_count = len(results) - successful_count
    return {
        "total": len(results),
        "successful": successful_count,
        "failed": failed_count,
        "alphaIds": alpha_ids,
        "use_multi_sim": use_multi_sim,
        "alpha_count_per_slot": alpha_count_per_slot if use_multi_sim else None,
    }


def run_single_simulations(session, alpha_list, concurrent_count, logger):
    """Run single simulations with progress logs compatible with the web viewer."""
    results = []
    total = len(alpha_list)
    logger.info("开始 ace_lib 单 alpha 并发回测，总数=%s，并发=%s", total, concurrent_count)

    with ThreadPool(concurrent_count) as pool:
        for index, result in enumerate(
            pool.imap_unordered(partial(ace_lib.simulate_single_alpha, session), alpha_list),
            start=1,
        ):
            results.append(result)
            alpha_id = result.get("alpha_id") or "FAILED"
            logger.info("单 alpha 回测进度 %s/%s，alpha_id=%s", index, total, alpha_id)

    return results


def run_multi_simulations(session, alpha_list, concurrent_count, alpha_count_per_slot, logger):
    """Run multi-simulations with batch progress logs compatible with the web viewer."""
    total_alphas = len(alpha_list)
    tasks = [
        alpha_list[i : i + alpha_count_per_slot]
        for i in range(0, total_alphas, alpha_count_per_slot)
    ]
    results = []
    completed_alphas = 0

    logger.info(
        "开始 ace_lib multi-sim 回测，alpha 总数=%s，槽数=%s，每槽=%s，并发=%s",
        total_alphas,
        len(tasks),
        alpha_count_per_slot,
        concurrent_count,
    )

    with ThreadPool(concurrent_count) as pool:
        for slot_index, batch_results in enumerate(
            pool.imap_unordered(partial(ace_lib.simulate_multi_alpha, session), tasks),
            start=1,
        ):
            results.extend(batch_results)
            completed_alphas += len(batch_results)
            logger.info(
                "multi-sim 槽进度 %s/%s，已完成 alpha %s/%s",
                slot_index,
                len(tasks),
                completed_alphas,
                total_alphas,
            )

    return results


def run_ace_simulations(session, alpha_list, concurrent_count, use_multi_sim, alpha_count_per_slot, logger):
    """Run ace_lib simulations while preserving the existing web-facing flow."""
    concurrent_count = clamp_concurrent_count(concurrent_count, logger)

    if not use_multi_sim:
        return run_single_simulations(session, alpha_list, concurrent_count, logger), False, None

    alpha_count_per_slot = clamp_multi_slot_count(alpha_count_per_slot, logger)

    if any(item.get("type") == "SUPER" for item in alpha_list):
        logger.warning("检测到 SUPER Alpha，ace_lib 的 multi-sim 不支持，已自动降级为单 alpha 并发回测")
        return run_single_simulations(session, alpha_list, concurrent_count, logger), False, None

    multi_sim_msg = (
        f"[MULTI-SIMULATION MODE] 以下是multi simulation的记录，"
        f"你的设计是1个multi simulation中有{alpha_count_per_slot}个alpha，"
        f"因此需将实际回测数乘以该乘数，才得到实际已完成的Alpha个数。"
    )
    logger.info("=" * 80)
    logger.info(multi_sim_msg)
    logger.info("=" * 80)
    return (
        run_multi_simulations(session, alpha_list, concurrent_count, alpha_count_per_slot, logger),
        True,
        alpha_count_per_slot,
    )

def get_password_with_asterisks(prompt):
    """Get password input with asterisks shown for each character"""
    if msvcrt is None:
        return getpass.getpass(prompt)
    
    print(prompt, end='', flush=True)
    password = ""
    
    while True:
        char = msvcrt.getch()
        
        # Handle Enter key (carriage return)
        if char == b'\r':
            print()  # New line
            break
        # Handle Backspace
        elif char == b'\x08':
            if len(password) > 0:
                password = password[:-1]
                # Move cursor back, print space, move cursor back again
                print('\b \b', end='', flush=True)
        # Handle Ctrl+C
        elif char == b'\x03':
            print()
            raise KeyboardInterrupt
        # Handle regular characters
        else:
            try:
                # Convert bytes to string
                char_str = char.decode('utf-8')
                if char_str.isprintable():
                    password += char_str
                    print('*', end='', flush=True)
            except UnicodeDecodeError:
                pass  # Ignore non-printable characters
    
    return password


def coerce_settings_types(expressions):
    """Ensure numeric settings like truncation are correctly cast to numbers, not strings."""
    for expr in expressions:
        settings = expr.get("settings", {})

        if "truncation" in settings:
            try:
                settings["truncation"] = float(settings["truncation"])
            except (ValueError, TypeError):
                pass

        if "delay" in settings:
            try:
                settings["delay"] = int(settings["delay"])
            except (ValueError, TypeError):
                pass

        if "decay" in settings:
            try:
                settings["decay"] = int(float(settings["decay"]))
            except (ValueError, TypeError):
                pass

        if "visualization" in settings and isinstance(settings["visualization"], str):
            settings["visualization"] = settings["visualization"].lower() == "true"

    return expressions


def get_json_filepath():
    """Ask user to input the directory/filepath of expressions_with_settings.json"""
    while True:
        print("\n" + "="*60)
        print("JSON 文件配置")
        print("="*60)
        filepath = input("请复制粘贴 expressions_with_settings.json （即以json格式储存的带有setting的表达式列表）的目录或完整路径: ").strip()
        
        # Remove quotes if user copied with quotes
        filepath = filepath.strip('"').strip("'")
        
        # Check if it's a directory and try to find the file
        if os.path.isdir(filepath):
            json_path = os.path.join(filepath, "expressions_with_settings.json")
        else:
            json_path = filepath
            
        # Verify file exists
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✓ 成功加载 JSON 文件: {json_path}")
                return json_path, data
            except json.JSONDecodeError:
                print("❌ 错误: JSON 文件格式无效，请检查文件。")
            except Exception as e:
                print(f"❌ 读取文件错误: {e}")
        else:
            print("❌ 错误: 文件未找到，请检查路径后重试。")

def get_user_credentials():
    """Ask user for brain username and password with asterisk password input"""
    print("\n" + "="*60)
    print("BRAIN 身份验证")
    print("="*60)
    
    username = input("请输入您的 BRAIN 用户名: ").strip()
    password = get_password_with_asterisks("请输入您的 BRAIN 密码 (显示为 *): ")
    
    return username, password

def test_authentication(username, password):
    """Test authentication and return session if successful"""
    print("\n" + "="*60)
    print("API连通验证")
    print("="*60)
    
    try:
        session, logger = build_web_session(username, password)
        expiry = ace_lib.check_session_timeout(session)
        print(f"连接测试结果: session_expiry = {expiry}")

        if expiry > 0:
            print("✓ 身份验证成功！")
            return session, logger
        else:
            print("❌ 身份验证失败，请检查您的用户名和密码。")
            return None, None
            
    except Exception as e:
        print(f"❌ 身份验证错误: {e}")
        return None, None

def get_simulation_parameters(expressions_count, json_path):
    """Get simulation parameters from user with validation"""
    print("\n" + "="*60)
    print("回测参数设置")
    print("="*60)
    print(f"JSON 中的表达式总数: {expressions_count}")
    
    # Get starting position
    while True:
        try:
            where_to_start = int(input(f"从列表中第几个表达式开始 (0 到 {expressions_count-1}): "))
            if 0 <= where_to_start < expressions_count:
                if where_to_start > 0:
                    print(f"\n⚠️  警告: 原始 JSON 文件将被直接覆盖！")
                    print(f"📝 原始文件: {expressions_count} 个表达式")
                    print(f"🔪 切割后: {expressions_count - where_to_start} 个表达式")
                    print(f"📂 文件位置: {json_path}")
                    print(f"\n🚨 重要提示: 如果您不希望覆盖原始文件，请立即关闭终端并手动备份文件！")
                    print(f"⏰ 5秒后将继续执行覆盖操作...")
                    
                    # Give user 5 seconds to think/close terminal
                    import time
                    for i in range(5, 0, -1):
                        print(f"倒计时: {i} 秒...", end='\r')
                        time.sleep(1)
                    print("             ")  # Clear countdown line
                    
                    confirm = input("(继续程序,开始回测y/返回并重选列表起始位置n): ").lower().strip()
                    if confirm != 'y':
                        print("请重新选择表达式列表起始位置。")
                        continue
                break
            else:
                print(f"❌ 起始位置无效，必须在 0 到 {expressions_count-1} 之间")
        except ValueError:
            print("❌ 请输入有效数字。")
    
    # Get concurrent count
    while True:
        try:
            concurrent_count = int(input("请输入并发回测数量 (最小值 1): "))
            if concurrent_count >= 1:
                break
            else:
                print("❌ 并发数量必须大于等于 1。")
        except ValueError:
            print("❌ 请输入有效数字。")
    
    return where_to_start, concurrent_count

def cut_json_file(json_path, expressions_with_settings, where_to_start):
    """Cut the JSON file from the starting point and overwrite the original file"""
    if where_to_start == 0:
        return expressions_with_settings  # No cutting needed
    
    # Cut the expressions list
    cut_expressions = expressions_with_settings[where_to_start:]
    
    # Overwrite the original JSON file
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(cut_expressions, f, ensure_ascii=False, indent=2)
        print(f"✓ 原始 JSON 文件已被覆盖")
        print(f"📊 新文件包含 {len(cut_expressions)} 个表达式")
        return cut_expressions
    except Exception as e:
        print(f"❌ 覆盖 JSON 文件失败: {e}")
        print(f"⚠️  将使用原始数据继续运行")
        return expressions_with_settings

def shuffle_json_file(json_path, expressions_with_settings):
    """Randomly shuffle the JSON elements and overwrite the file"""
    import random
    
    # Create a copy and shuffle it
    shuffled_expressions = expressions_with_settings.copy()
    random.shuffle(shuffled_expressions)
    
    # Overwrite the JSON file with shuffled data
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(shuffled_expressions, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON 文件已随机打乱并覆盖")
        print(f"🔀 已打乱 {len(shuffled_expressions)} 个表达式的顺序")
        return shuffled_expressions
    except Exception as e:
        print(f"❌ 打乱 JSON 文件失败: {e}")
        print(f"⚠️  将使用原始顺序继续运行")
        return expressions_with_settings

def get_random_shuffle_choice():
    """Ask user if they want to randomly shuffle the expressions"""
    print("\n" + "="*60)
    print("随机模式选择")
    print("="*60)
    print("是否要随机打乱表达式顺序？")
    print("💡 这将改变表达式在文件中的排列顺序,以达到随机回测的目的")
    
    while True:
        choice = input("选择随机模式? (y/n): ").lower().strip()
        if choice in ['y', 'n']:
            return choice == 'y'
        else:
            print("❌ 请输入 y 或 n")

def get_multi_simulation_choice():
    """Ask user if they want to use multi-simulation mode"""
    print("\n" + "="*60)
    print("多重回测(multi-simulatioin)模式选择")
    print("="*60)
    print("是否要使用多重回测(multi-simulatioin)模式？")
    print("💡 多重回测(multi-simulatioin)可以将多个alpha组合在一个回测槽中运行")
    
    while True:
        choice = input("使用多重回测(multi-simulatioin)模式? (y/n): ").lower().strip()
        if choice in ['y', 'n']:
            return choice == 'y'
        else:
            print("❌ 请输入 y 或 n")

def get_alpha_count_per_slot():
    """Ask user how many alphas to put in one multi-simulation slot"""
    print("\n" + "="*60)
    print("多重回测(multi-simulatioin)槽配置")
    print("="*60)
    print("每个多重回测(multi-simulatioin)槽中放置多少个alpha？")
    print("💡 范围: 2-10 个alpha")
    
    while True:
        try:
            alpha_count = int(input("每个槽的alpha数量 (2-10): "))
            if 2 <= alpha_count <= 10:
                return alpha_count
            else:
                print("❌ 数量必须在 2 到 10 之间")
        except ValueError:
            print("❌ 请输入有效数字。")

def monitor_log_file(logger, stop_event, use_multi_sim=False, alpha_count_per_slot=None):
    """Monitor log file and print new lines in real-time"""
    print("\n📊 开始监控日志文件...")
    
    # Get current directory to look for log files
    current_dir = os.getcwd()
    log_file_path = None
    
    # First, try to find any existing compatible log files (including older ones)
    print("🔍 查找回测日志文件...")
    
    # Look for any wqb*.log files in current directory
    wqb_files = []
    try:
        for file in os.listdir(current_dir):
            if file.startswith('wqb') and file.endswith('.log'):
                file_path = os.path.join(current_dir, file)
                wqb_files.append((file_path, os.path.getmtime(file_path)))
    except Exception as e:
        print(f"⚠️  扫描目录失败: {e}")
        return
    
    if wqb_files:
        # Sort by modification time, get the newest one
        log_file_path = sorted(wqb_files, key=lambda x: x[1], reverse=True)[0][0]
        print(f"✓ 监控已找到的最新日志文件: {log_file_path}")
    else:
        # Wait for new log file to be created
        print("等待新的回测日志文件创建...")
        start_time = time.time()
        
        while not stop_event.is_set() and (time.time() - start_time) < 30:  # Wait max 30 seconds
            try:
                for file in os.listdir(current_dir):
                    if file.startswith('wqb') and file.endswith('.log'):
                        file_path = os.path.join(current_dir, file)
                        # Check if file was created recently (within last 120 seconds)
                        if os.path.getctime(file_path) > (time.time() - 120):
                            log_file_path = file_path
                            break
            except Exception:
                pass
            
            if log_file_path:
                break
            time.sleep(1)
        
        if not log_file_path:
            print("⚠️  未找到回测日志文件，日志监控已禁用。")
            print("💡 提示: 日志文件通常在开始回测后才会创建")
            return
        else:
            print(f"✓ 找到新日志文件: {log_file_path}")
    
    if stop_event.is_set():
        return
    
    print("="*60)
    
    # Display multi-simulation information if applicable
    if use_multi_sim and alpha_count_per_slot:
        print("📌 重要提示：")
        print(f"以下是multi simulation的记录，你的设计是1个multi simulation中有{alpha_count_per_slot}个alpha，")
        print(f"因此需将实际回测数乘以该乘数，才得到实际已完成的Alpha个数。")
        print("="*60)
    
    try:
        # Start monitoring from current end of file
        with open(log_file_path, 'r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while not stop_event.is_set():
                line = f.readline()
                if line:
                    # Clean up the log line and print it
                    clean_line = line.rstrip()
                    if clean_line:  # Only print non-empty lines
                        print(f"[日志] {clean_line}")
                else:
                    time.sleep(0.2)
    except Exception as e:
        print(f"⚠️  监控日志文件时出错: {e}")

async def automated_main(json_file_content, username, password, start_position=0, concurrent_count=3, 
                        random_shuffle=False, use_multi_sim=False, alpha_count_per_slot=3):
    """Automated main function for web interface - takes all parameters at once"""
    try:
        print("🧠 BRAIN Alpha 模板回测器 (自动模式)")
        print("="*60)
        
        # Parse JSON content directly
        import json
        expressions_with_settings = json.loads(json_file_content)
        expressions_with_settings = normalize_web_alpha_list(
            expressions_with_settings,
            start_position=start_position,
            random_shuffle=random_shuffle,
        )
        expressions_count = len(expressions_with_settings)
        
        print(f"📊 已加载 {expressions_count} 个 alpha 配置")
        
        # Setup logger and session
        session, logger = build_web_session(username, password)
        expiry = ace_lib.check_session_timeout(session)
        print(f"连接测试结果: session_expiry = {expiry}")

        if expiry <= 0:
            print("❌ 身份验证失败")
            return {"success": False, "error": "Authentication failed"}
        
        print("✅ 身份验证成功！")
        if start_position > 0:
            print(f"🔪 已从位置 {start_position} 开始切割，剩余 {len(expressions_with_settings)} 个表达式")
        
        if random_shuffle:
            print(f"🔀 已随机打乱 {len(expressions_with_settings)} 个表达式的顺序")
        
        print(f"🔄 使用 {concurrent_count} 个并发回测")
        
        # Start log monitoring in background
        stop_log_monitor = threading.Event()
        log_thread = threading.Thread(
            target=monitor_log_file, 
            args=(logger, stop_log_monitor, use_multi_sim, alpha_count_per_slot),
            daemon=True
        )
        log_thread.start()

        print("\n" + "="*60)
        print("运行回测")
        print("="*60)
        
        if use_multi_sim:
            print("开始多重回测(multi-simulatioin)并发回测...")
        else:
            print("开始并发回测...")
        
        try:
            resps, actual_use_multi_sim, actual_alpha_count_per_slot = await asyncio.to_thread(
                run_ace_simulations,
                session,
                expressions_with_settings, 
                concurrent_count, 
                use_multi_sim,
                alpha_count_per_slot,
                logger,
            )
        finally:
            # Stop log monitoring
            stop_log_monitor.set()
            # Give the log thread a moment to print remaining logs
            time.sleep(0.5)
        
        summary = summarize_ace_results(
            resps,
            use_multi_sim=actual_use_multi_sim,
            alpha_count_per_slot=actual_alpha_count_per_slot,
        )
        
        print("\n" + "="*60)
        print("回测结果")
        print("="*60)
        
        if actual_use_multi_sim:
            print(f"成功完成 {len(resps)} 个多重回测(multi-simulatioin)槽的回测")
        else:
            print(f"成功完成 {len(resps)} 个回测")
        
        if summary["alphaIds"]:
            print("\nAlpha IDs:")
            for index, alpha_id in enumerate(summary["alphaIds"], start=1):
                print(f"  {index:4d}. {alpha_id}")
        
        print("\n✅ 处理完成!")

        return {"success": True, "results": summary}
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Main function with interactive workflow"""
    print("🧠 BRAIN Alpha 模板回测器")
    print("="*60)
    
    # Step 1: Get JSON file and load expressions
    json_path, expressions_with_settings = get_json_filepath()
    expressions_with_settings = coerce_settings_types(expressions_with_settings)
    expressions_count = len(expressions_with_settings)
    
    print(f"\n📊 已从以下位置加载 {expressions_count} 个 alpha 配置:")
    print(f"   {json_path}")
    
    # Step 2: Get credentials and test authentication
    session = None
    logger = None
    
    while session is None:
        username, password = get_user_credentials()
        session, logger = test_authentication(username, password)
        
        if session is None:
            retry = input("\n是否要重试? (y/n): ").lower().strip()
            if retry != 'y':
                print("正在退出...")
                return
    
    # Step 3: Get simulation parameters
    where_to_start, concurrent_count = get_simulation_parameters(expressions_count, json_path)
    
    # Step 3.5: Cut JSON file if needed
    if where_to_start > 0:
        print(f"\n🔪 正在切割 JSON 文件...")
        expressions_with_settings = cut_json_file(json_path, expressions_with_settings, where_to_start)
        where_to_start = 0  # Reset to 0 since we cut the file
    
    # Step 3.6: Ask for random shuffle option
    if get_random_shuffle_choice():
        print(f"\n🔀 正在随机打乱表达式顺序...")
        expressions_with_settings = shuffle_json_file(json_path, expressions_with_settings)
    
    # Step 3.7: Ask for multi-simulation mode
    use_multi_sim = get_multi_simulation_choice()
    alpha_count_per_slot = None
    
    if use_multi_sim:
        alpha_count_per_slot = get_alpha_count_per_slot()
        print(f"\n✓ 已转换为多重回测(multi-simulatioin)格式")
        print(f"📊 原始表达式数: {len(expressions_with_settings)}")
        print(f"🎯 每槽alpha数: {alpha_count_per_slot}")
    
    # Calculate how many expressions will be processed
    print(f"🔄 使用 {concurrent_count} 个并发回测")
    
    # Step 4: Write multi-simulation info to log if applicable
    if use_multi_sim and alpha_count_per_slot and logger:
        multi_sim_msg = (f"[MULTI-SIMULATION MODE] 以下是multi simulation的记录，"
                        f"你的设计是1个multi simulation中有{alpha_count_per_slot}个alpha，"
                        f"因此需将实际回测数乘以该乘数，才得到实际已完成的Alpha个数。")
        logger.info("="*80)
        logger.info(multi_sim_msg)
        logger.info("="*80)
    
    # Step 5: Start log monitoring in background
    stop_log_monitor = threading.Event()
    log_thread = threading.Thread(
        target=monitor_log_file, 
        args=(logger, stop_log_monitor, use_multi_sim, alpha_count_per_slot),
        daemon=True
    )
    log_thread.start()
    
    # Step 6: Run simulations
    print("\n" + "="*60)
    print("运行回测")
    print("="*60)
    if use_multi_sim:
        print("开始多重回测(multi-simulatioin)并发回测...")
    else:
        print("开始并发回测...")
    
    try:
        resps, actual_use_multi_sim, actual_alpha_count_per_slot = await asyncio.to_thread(
            run_ace_simulations,
            session,
            expressions_with_settings,
            concurrent_count,
            use_multi_sim,
            alpha_count_per_slot or 3,
            logger,
        )
        
        # Stop log monitoring
        stop_log_monitor.set()
        time.sleep(0.5)

        summary = summarize_ace_results(
            resps,
            use_multi_sim=actual_use_multi_sim,
            alpha_count_per_slot=actual_alpha_count_per_slot,
        )
        
        # Print results
        print("\n" + "="*60)
        print("回测结果")
        print("="*60)
        
        if actual_use_multi_sim:
            print(f"成功完成 {len(resps)} 个多重回测(multi-simulatioin)槽的回测")
        else:
            print(f"成功完成 {len(resps)} 个回测")

        if summary["alphaIds"]:
            print("\nAlpha IDs:")
            for index, alpha_id in enumerate(summary["alphaIds"], start=1):
                print(f"  {index:4d}. {alpha_id}")
                
    except KeyboardInterrupt:
        print("\n\n⚠️  回测被用户中断")
        stop_log_monitor.set()
    except Exception as e:
        print(f"\n❌ 回测错误: {e}")
        stop_log_monitor.set()
    
    print("\n✅ 处理完成!")

if __name__ == '__main__':
    asyncio.run(main()) 