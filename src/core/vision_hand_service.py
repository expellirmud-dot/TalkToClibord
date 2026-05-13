
import subprocess
import os
import shutil
import py_compile
from datetime import datetime
from src.utils.vision_utils import sys_log
from src.utils.vision_paths import ROOT_DIR, LOG_TXT

class VisionHandService:
    """
    Hand Service (มือเท้า) สำหรับจัดการ Terminal และ File Operations
    รองรับการสั่งการแบบ OTA (Over-The-Air) จาก Vision Engine ข่ะ
    """
    def __init__(self, base_dir=None):
        # แปลง Path ให้เป็น String เพื่อความชัวร์ในการเชื่อม Path ข่ะ
        self.base_dir = str(base_dir) if base_dir else str(ROOT_DIR)

    def execute_terminal(self, command):
        """รันคำสั่ง Terminal และดักจับ Output เพื่อนำมาวิเคราะห์ข่ะ"""
        try:
            sys_log("Terminal", f"Running: {command}")
            with open(LOG_TXT, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] [EXEC] {command}\n")
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.base_dir,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout
                sys_log("Terminal", "Execution Successful")
                return output if output else "✅ Command executed successfully (No output)."
            else:
                error_msg = result.stderr
                sys_log("Terminal", f"Error: {error_msg}")
                return f"❌ Terminal Error (Code {result.returncode}): {error_msg}"
        except subprocess.TimeoutExpired:
            return "❌ Error: Command timed out after 60 seconds."
        except Exception as e:
            sys_log("Terminal", f"Critical Failure: {str(e)}")
            return f"❌ Critical Exception: {str(e)}"

    def read_file(self, target_path, internal_mode=False):
        """อ่านไฟล์แบบ Sniper Read เพื่อนำโค้ดมาวิเคราะห์ข่ะ"""
        try:
            full_path = os.path.join(self.base_dir, target_path)
            if not os.path.exists(full_path):
                return f"❌ Error: File not found at {target_path}"
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not internal_mode:
                sys_log("HandService", f"Read file: {target_path}")
            return content
        except Exception as e:
            return f"❌ Read Error: {str(e)}"

    def save_file(self, target_path, content):
        """บันทึกไฟล์ลงระบบ พร้อมสร้าง Folder ให้อัตโนมัติข่ะ"""
        try:
            full_path = os.path.join(self.base_dir, target_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            sys_log("HandService", f"Saved file: {target_path}")
            return f"✅ Successfully saved to {target_path}"
        except Exception as e:
            return f"❌ Save Error: {str(e)}"

    def manage_file(self, action, source, destination=None):
        """
        ฟังก์ชันรวมสำหรับการจัดการไฟล์ (ลบ/ย้าย/เปลี่ยนชื่อ/สร้างโฟลเดอร์)
        เพื่อให้ตรงกับ Logic ใน VisionEngine ข่ะ
        """
        try:
            src_path = os.path.join(self.base_dir, source)
            
            if action == "delete":
                if os.path.isfile(src_path):
                    os.remove(src_path)
                    res = f"✅ Deleted file: {source}"
                elif os.path.isdir(src_path):
                    shutil.rmtree(src_path)
                    res = f"✅ Deleted directory: {source}"
                else:
                    return f"❌ Error: {source} not found"
                sys_log("HandService", res)
                return res

            elif action == "move" or action == "rename":
                if not destination: return "❌ Error: Destination path required"
                dest_path = os.path.join(self.base_dir, destination)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.move(src_path, dest_path)
                res = f"✅ Moved/Renamed {source} to {destination}"
                sys_log("HandService", res)
                return res

            elif action == "mkdir":
                os.makedirs(src_path, exist_ok=True)
                res = f"✅ Directory created: {source}"
                sys_log("HandService", res)
                return res

            return f"❌ Error: Unknown action '{action}'"
        except Exception as e:
            return f"❌ Manage File Error: {str(e)}"

    def verify_syntax(self, target_path):
        """ตรวจสอบ Syntax ของไฟล์ Python เพื่อป้องกันระบบพังข่ะ"""
        try:
            full_path = os.path.join(self.base_dir, target_path)
            if not target_path.endswith('.py'):
                return "ℹ️ Not a Python file, skipping syntax check."
            py_compile.compile(full_path, doraise=True)
            return "✅ Syntax OK"
        except py_compile.PyCompileError as e:
            return f"❌ Syntax Error: {str(e)}"
        except Exception as e:
            return f"❌ Verification Error: {str(e)}"

    def list_project_structure(self, target_dir="src"):
        """
        สแกนโครงสร้างโปรเจกต์แบบ Clean List (PATH_DISCOVERY)
        """
        try:
            # ใช้คำสั่ง dir /b /s สำหรับ Windows ตาม Checklist 6
            command = f"dir /b /s {target_dir}"
            result = self.execute_terminal(command)
            if result.get("status") == "success":
                return {"status": "success", "files": result.get("stdout", "").splitlines()}
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}