# vision_paths.py (V3.1 - Pathlib Optimized & Robust)
from pathlib import Path

# 🎯 Get the root directory (D:/TalkToClibord/)
# Navigate from src/utils/vision_paths.py up to project root
# parents[0] = src/utils, parents[1] = src, parents[2] = ROOT
ROOT_DIR = Path(__file__).resolve().parents[2]

# Directory constants (Using Path objects for better manipulation)
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = DATA_DIR / "output"
CONFIG_DIR = DATA_DIR / "config"
HANDOFF_DIR = DATA_DIR / "handoffs"
SOUNDS_DIR = ROOT_DIR / "sounds"

# File paths (Using Path objects)
JAVIS_MD = CONFIG_DIR / "JAVIS.md"
VAULT_JSON = CONFIG_DIR / "vault.json"
CHAT_HISTORY_JSON = CACHE_DIR / "chat_history.json"
REQUEST_CACHE_JSON = CACHE_DIR / "request_cache.json"
LOG_TXT = LOG_DIR / "log.txt"
EXPENSE_LOG_CSV = LOG_DIR / "expense_log.csv"
PERFORMANCE_LOG_CSV = LOG_DIR / "performance_log.csv"

def ensure_dirs():
    """Automatically create all required directories if they are missing using pathlib"""
    dirs_to_create = [
        LOG_DIR,
        CACHE_DIR,
        OUTPUT_DIR,
        CONFIG_DIR,
        HANDOFF_DIR,
        SOUNDS_DIR
    ]
    
    created_dirs = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            try:
                # parents=True ensures all parent directories are created
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))
                print(f"[vision_paths] Created directory: {dir_path}")
            except Exception as e:
                print(f"[vision_paths] ERROR creating {dir_path}: {e}")
    
    if created_dirs:
        print(f"[vision_paths] Created {len(created_dirs)} directories")
    else:
        print(f"[vision_paths] All directories already exist")
    
    return created_dirs

def get_all_paths():
    """Get all defined paths as a dictionary of strings for backward compatibility"""
    paths = {
        "ROOT_DIR": ROOT_DIR,
        "DATA_DIR": DATA_DIR,
        "LOG_DIR": LOG_DIR,
        "CACHE_DIR": CACHE_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "CONFIG_DIR": CONFIG_DIR,
        "HANDOFF_DIR": HANDOFF_DIR,
        "SOUNDS_DIR": SOUNDS_DIR,
        "JAVIS_MD": JAVIS_MD,
        "VAULT_JSON": VAULT_JSON,
        "CHAT_HISTORY_JSON": CHAT_HISTORY_JSON,
        "REQUEST_CACHE_JSON": REQUEST_CACHE_JSON,
        "LOG_TXT": LOG_TXT,
        "EXPENSE_LOG_CSV": EXPENSE_LOG_CSV,
        "PERFORMANCE_LOG_CSV": PERFORMANCE_LOG_CSV
    }
    # Convert all Path objects to strings to prevent breaking existing code
    return {k: str(v) for k, v in paths.items()}