# vision_utils.py (V2.1 - Path Sync Edition)
import os, csv, time, threading, queue
from datetime import datetime
from vision_config import MODELS_CONFIG
# 1. 🔗 นำเข้า Path มาตรฐานจาก vision_paths
from src.utils.vision_paths import LOG_DIR, DATA_DIR, CACHE_DIR, OUTPUT_DIR, CONFIG_DIR
# 1.5 🔗 นำเข้า ExpenseTracker (อยู่ใน root)
from vision_expense_tracker import ExpenseTracker

# Log rotation settings
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_BACKUPS = 3

log_queue = queue.Queue()

# Global ExpenseTracker V2.0 instance
# 2. 🎯 อัปเดตการเรียกใช้ ExpenseTracker ให้ใช้ LOG_DIR มาตรฐาน
expense_tracker = ExpenseTracker(logs_dir=LOG_DIR)

def rotate_log_file(log_file):
    """Rotate log file if it exceeds MAX_LOG_SIZE"""
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > MAX_LOG_SIZE:
            # Rotate backups
            for i in range(MAX_LOG_BACKUPS, 0, -1):
                old_backup = f"{log_file}.{i}"
                new_backup = f"{log_file}.{i + 1}"
                if os.path.exists(old_backup):
                    os.rename(old_backup, new_backup)
            # Move current to .1
            os.rename(log_file, f"{log_file}.1")
    except Exception as e:
        print(f"[LOG_ROTATION_ERROR] {e}")

def log_worker():
    while True:
        entry = log_queue.get()
        if entry is None: break
        try:
            if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
            log_file = os.path.join(LOG_DIR, "log.txt")
            
            # Rotate if needed
            rotate_log_file(log_file)
            
            with open(log_file, "a", encoding="utf-8") as f: f.write(entry + "\n")
        except Exception as e:
            print(f"[LOG_ERROR] {e}")
        log_queue.task_done()

threading.Thread(target=log_worker, daemon=True).start()

def sys_log(func, msg, level="INFO"):
    """Log with severity level: INFO, WARNING, ERROR, CRITICAL"""
    # 🤫 Filter: ถ้าเป็นข้อความ "ไม่เข้าใจเสียง" ให้เงียบไปเลยข่ะะ
    if msg and ("ไม่เข้าใจเสียง" in str(msg) or "Silence detected" in str(msg)):
        return
    
    try:
        # Safely convert msg to string to prevent int + list error
        safe_msg = str(msg) if msg is not None else ""
        log = f"[{datetime.now()}] [{level}] [{func}] {safe_msg}"
        print(log); log_queue.put(log)
    except Exception as e:
        print(f"[SYS_LOG_INTERNAL_ERROR] {e}")
        # Fallback to simple log
        try:
            log = f"[{datetime.now()}] [{level}] [{func}] ERROR_FORMATTING_MESSAGE"
            print(log); log_queue.put(log)
        except Exception as e:
            print(f"[SYS_LOG_CRITICAL_ERROR] Cannot format log: {e}")

def log_token_usage(model_id, in_tk, out_tk, identity=None, session_id=None):
    """Log token usage using ExpenseTracker V2.0"""
    # Use ExpenseTracker V2.0 for advanced tracking
    cost, returned_session_id = expense_tracker.log_token_usage(
        model_id, in_tk, out_tk, identity, session_id
    )
    
    # Legacy fallback: Also write to CSV for compatibility
    price_info = next((v for k, v in MODELS_CONFIG.items() if v['id'] == model_id), MODELS_CONFIG['jamie'])
    
    try:
        if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

        expense_file = os.path.join(LOG_DIR, "expense_log.csv")
        file_exists = os.path.exists(expense_file)

        with open(expense_file, "a", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)

            if not file_exists or os.path.getsize(expense_file) == 0:
                writer.writerow(["Timestamp", "Model", "Input", "Output", "Cost_THB", "Identity", "Session_ID"])

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                model_id,
                in_tk,
                out_tk,
                f"{cost:.6f}",
                identity or '',
                returned_session_id or ''
            ])
    except Exception as e:
        sys_log("Expense", f"CSV fallback error: {e}")

    return cost

def estimate_tokens(text): return len(text) // 4
def is_actually_code(t): return bool(t and any(s in t for s in ['def ', 'import ', 'class ', '=']))

def check_token_limit(system_instruction, input_tokens, output_tokens, model_key=None, identity=None):
    """ตรวจสอบว่า token ไม่เกิน limit ตามโมเดลที่เลือก
    
    Args:
        system_instruction: คำสั่งระบบ
        input_tokens: จำนวน token ของ input
        output_tokens: จำนวน token ของ output ที่คาดว่าจะได้
        model_key: key ของโมเดลใน MODELS_CONFIG (เช่น 'jamie', 'vision', 'pro')
        identity: Identity ที่ใช้ (JAMIE, VISION, PRO) - ใช้ถ้าไม่ระบุ model_key
    
    Returns:
        tuple: (can_proceed, total_est, max_tokens, message)
    """
    # Get model config
    if model_key and model_key in MODELS_CONFIG:
        config = MODELS_CONFIG[model_key]
    elif identity:
        # Map identity to model
        identity_map = {"JAMIE": "jamie", "VISION": "vision", "PRO": "pro"}
        model = identity_map.get(identity, "jamie")
        config = MODELS_CONFIG.get(model, MODELS_CONFIG["jamie"])
    else:
        # Default to jamie (Flash-Lite) limits
        config = MODELS_CONFIG["jamie"]
    
    max_input = config.get("max_input_tokens", 32000)
    max_output = config.get("max_output_tokens", 8000)
    model_name = config.get("identity", "Unknown")
    
    system_tokens = estimate_tokens(system_instruction)
    total_est = system_tokens + input_tokens + output_tokens
    
    # Check against limits
    input_ok = input_tokens <= max_input
    output_ok = output_tokens <= max_output
    total_ok = total_est <= (max_input + max_output)
    
    can_proceed = input_ok and output_ok and total_ok
    
    # Build message
    if not can_proceed:
        issues = []
        if not input_ok:
            issues.append(f"Input ({input_tokens:,}) > limit ({max_input:,})")
        if not output_ok:
            issues.append(f"Output ({output_tokens:,}) > limit ({max_output:,})")
        if not total_ok:
            issues.append(f"Total ({total_est:,}) > combined limit")
        message = f"[{model_name}] Token limit exceeded: {'; '.join(issues)}"
    else:
        message = f"[{model_name}] Token OK: {total_est:,} / {(max_input + max_output):,}"
    
    return can_proceed, total_est, (max_input + max_output), message

def check_vision_rate_limit(required_tokens, request_history=None):
    """Check Gemma rate limits for Vision identity
    
    Args:
        required_tokens: Tokens needed for this request
        request_history: List of (timestamp, tokens) tuples for recent requests
    
    Returns:
        tuple: (can_proceed, wait_seconds, message)
    """
    import time
    
    now = time.time()
    config = MODELS_CONFIG["vision"]
    limits = config.get("rate_limits", {})
    
    rpm_limit = limits.get("rpm", 30)
    tpm_limit = limits.get("tpm", 16000)
    rpd_limit = limits.get("rpd", 14400)
    
    if request_history is None:
        request_history = []
    
    # Check RPM (requests per minute)
    recent_requests = [t for t, _ in request_history if now - t < 60]
    if len(recent_requests) >= rpm_limit:
        wait = 60 - (now - recent_requests[0])
        return False, wait, f"RPM limit ({rpm_limit}) reached. Wait {wait:.1f}s"
    
    # Check TPM (tokens per minute)
    recent_tokens = sum(toks for t, toks in request_history if now - t < 60)
    if recent_tokens + required_tokens > tpm_limit:
        return False, 10, f"TPM limit ({tpm_limit}) would be exceeded"
    
    # Check RPD (requests per day)
    today_requests = [t for t, _ in request_history if now - t < 86400]
    if len(today_requests) >= rpd_limit:
        return False, 3600, f"RPD limit ({rpd_limit}) reached. Wait for next day"
    
    return True, 0, f"Rate limit OK: {len(recent_requests)}/{rpm_limit} RPM, {recent_tokens}/{tpm_limit} TPM"

class PerformanceTimer:
    def __init__(self, process_name):
        self.process_name = process_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        sys_log("PERF", f"{self.process_name}: {elapsed:.3f}s", level="INFO")

        #  1 performance log
        try:
            if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
            perf_file = os.path.join(LOG_DIR, "performance_log.csv")
            with open(perf_file, "a", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    self.process_name,
                    f"{elapsed:.3f}"
                ])
        except Exception as e:
            sys_log("PERF", f"Log error: {e}", level="ERROR")

def get_total_expense():
    """Get total expense using ExpenseTracker V2.0"""
    try:
        return expense_tracker.get_total_expense()
    except Exception as e:
        sys_log("EXPENSE", f"Error getting total expense: {e}")
        return 0.0

def get_daily_expense():
    """Get daily expense using ExpenseTracker V2.0"""
    try:
        return expense_tracker.get_daily_expense()
    except Exception as e:
        sys_log("EXPENSE", f"Error getting daily expense: {e}")
        return 0.0

def get_model_usage_stats():
    """Get model usage statistics from ExpenseTracker V2.0"""
    try:
        stats = expense_tracker.get_identity_breakdown()
        return stats
    except Exception as e:
        sys_log("Expense", f"Model stats error: {e}")
        return {}

def get_real_time_expense_dashboard():
    """Get real-time expense dashboard data"""
    try:
        return expense_tracker.get_real_time_stats()
    except Exception as e:
        sys_log("Expense", f"Dashboard error: {e}")
        return {}

def predict_expense_cost(text, model_id, identity=None):
    """Predict expense cost for given text using ExpenseTracker V2.0"""
    try:
        cost, tokens = expense_tracker.predict_cost(text, model_id, identity)
        return cost, tokens
    except Exception as e:
        sys_log("Expense", f"Cost prediction error: {e}")
        return 0.0, 0

def set_expense_budget(daily=None, monthly=None, minute=None):
    """Set expense budget limits"""
    try:
        expense_tracker.set_budget_limits(daily, monthly, minute)
        return True
    except Exception as e:
        sys_log("Expense", f"Budget set error: {e}")
        return False

def get_session_expense(session_id):
    """Get expenses for a specific session"""
    try:
        return expense_tracker.get_session_expenses(session_id)
    except Exception as e:
        sys_log("Expense", f"Session expense error: {e}")
        return []

def display_expense_dashboard():
    """Generate formatted expense dashboard for UI display"""
    try:
        stats = expense_tracker.get_real_time_stats()
        
        dashboard = f"""
📊 EXPENSE DASHBOARD V2.0
{'='*50}
💰 Daily Expense: {stats['daily_expense']:.2f} THB
💰 Monthly Expense: {stats['monthly_expense']:.2f} THB
💰 Minute Expense: {stats['minute_expense']:.2f} THB
📝 In-Memory Records: {stats['in_memory_records']}
💵 In-Memory Cost: {stats['in_memory_cost']:.2f} THB
🔄 Active Sessions: {stats['active_sessions']}
⏰ Last Flush: {datetime.fromtimestamp(stats['last_flush']).strftime('%H:%M:%S')}

IDENTITY BREAKDOWN:
{'-'*50}
"""
        for identity, data in stats['identity_breakdown'].items():
            dashboard += f"👤 {identity}: {data['cost']:.4f} THB ({data['tokens']} tokens, {data['count']} requests)\n"
        
        return dashboard
        
    except Exception as e:
        sys_log("Expense", f"Dashboard display error: {e}")
        return "Error loading dashboard"
