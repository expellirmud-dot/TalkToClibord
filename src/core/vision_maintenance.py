import os
import sys
import shutil
import logging
import threading
import json
from datetime import datetime
from pathlib import Path

# [Checklist ข้อ 10] เรียกใช้จาก src.utils เพื่อให้ตรงกับโครงสร้าง 85 ไฟล์ของเจ้านายข่ะ
try:
    from src.utils.vision_paths import ROOT_DIR, LOG_DIR, DATA_DIR, CHAT_HISTORY_JSON
    from src.utils.vision_utils import sys_log
except ImportError:
    # Fallback กรณีรันแยกไฟล์
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(ROOT_DIR, "data", "logs")
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    CHAT_HISTORY_JSON = os.path.join(DATA_DIR, "chat_history.json")
    def sys_log(task, msg, level="INFO"):
        print(f"[{level}] [{task}] {msg}")

class VisionMaintenance:
    """
    V6.3.5 - Grand Integration (Full Logic)
    ระบบดูแลตัวเองของ J.A.V.I.S. ล้าง Log และจัดการไฟล์ Backup
    """
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.backup_dir = os.path.join(ROOT_DIR, "backup")
        self.chat_history_file = CHAT_HISTORY_JSON
        
        # สร้างโฟลเดอร์ที่จำเป็นถ้ายังไม่มีข่ะ
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def _clean_log_files(self):
        """ล้างไฟล์ Log ที่ใหญ่เกิน 10MB หรือเก่าเกินไปข่ะ"""
        try:
            for filename in os.listdir(LOG_DIR):
                if filename.endswith(".log") or filename.endswith(".txt"):
                    file_path = os.path.join(LOG_DIR, filename)
                    file_stat = os.stat(file_path)
                    # ถ้าใหญ่กว่า 10MB ให้ลบทิ้งเพื่อประหยัดพื้นที่ข่ะ
                    if file_stat.st_size > 10 * 1024 * 1024:
                        os.remove(file_path)
                        sys_log("CLEANUP", f"Removed oversized log: {filename}")
        except Exception as e:
            sys_log("ERROR", f"Log cleanup failed: {e}")

    def rotate_chat_history(self, max_size_kb=500):
        """จัดการหมุนเวียนไฟล์ chat_history.json หากขนาดใหญ่เกินไปข่ะ"""
        try:
            if os.path.exists(self.chat_history_file):
                size_kb = os.path.getsize(self.chat_history_file) / 1024
                if size_kb > max_size_kb:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archive_path = os.path.join(os.path.dirname(self.chat_history_file), f"chat_history_{timestamp}.json.bak")
                    shutil.move(self.chat_history_file, archive_path)
                    sys_log("MAINTENANCE", f"Archived oversized chat history: {size_kb:.1f}KB")
                    return True
            return False
        except Exception as e:
            sys_log("ERROR", f"Chat history rotation failed: {e}")
            return False

    def clean_build_artifacts(self):
        """ล้างโฟลเดอร์ build/ และ dist/ เพื่อลด Noise ข่ะ"""
        dirs_to_clean = [
            os.path.join(ROOT_DIR, "build"),
            os.path.join(ROOT_DIR, "dist")
        ]
        count = 0
        for d in dirs_to_clean:
            if os.path.exists(d):
                try:
                    shutil.rmtree(d)
                    sys_log("MAINTENANCE", f"Cleaned build artifact: {d}")
                    count += 1
                except Exception as e:
                    sys_log("ERROR", f"Failed to clean {d}: {e}")
        return count

    def rotate_backups(self, days=7):
        """ลบไฟล์ .bak ที่เก่าเกิน 7 วัน (Logic จากไฟล์จริงของเจ้านายข่ะ)"""
        try:
            cutoff = time.time() - (days * 86400)
            count = 0
            for file_path in Path(self.backup_dir).rglob("*.bak"):
                if file_path.stat().st_mtime < cutoff:
                    file_path.unlink()
                    count += 1
            sys_log("MAINTENANCE", f"Rotated {count} old backup files.")
            return count
        except Exception as e:
            sys_log("ERROR", f"Backup rotation failed: {e}")
            return 0

    def run_full_maintenance(self):
        """สั่งรันระบบบำรุงรักษาทั้งหมดข่ะ"""
        sys_log("MAINTENANCE", "--- Engine Starting ---")
        self._clean_log_files()
        self.rotate_backups()
        self.rotate_chat_history()
        self.clean_build_artifacts()
        sys_log("MAINTENANCE", "--- System is now Optimized ---")
        return True

if __name__ == "__main__":
    import time # เพิ่มเพื่อให้รัน standalone ได้ข่ะ
    m = VisionMaintenance()
    m.run_full_maintenance()