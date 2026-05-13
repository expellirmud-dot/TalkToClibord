# vision_engine.py (V1.1 - Brain Logic Core)
"""
Brain Logic Core for Vision System
Handles: Context building, Hand service commands, Token management, Compaction logic, and Self-Healing
"""
import os
import re
import time
from typing import Tuple, Optional, Dict, Any

from src.utils.vision_utils import sys_log, estimate_tokens
from src.utils.vision_paths import LOG_DIR, LOG_TXT
from vision_config import MODELS_CONFIG, get_model_for_identity


class VisionEngine:
    """Brain Logic Core - handles AI processing logic separate from UI"""
    
    def __init__(self, ai_service, hand_service, context_builder, context_compactor, summarizer, ui_callback=None):
        """
        Initialize VisionEngine with required services
        
        Args:
            ai_service: VisionAIService instance for AI operations
            hand_service: VisionHandService instance for terminal/file operations
            context_builder: ContextBuilder instance for building contexts
            context_compactor: ContextCompactor instance for token compaction
            summarizer: MemorySummarizer instance for history management
            ui_callback: Callback function to update UI
        """
        self.ai_service = ai_service
        self.hand_service = hand_service
        self.context_builder = context_builder
        self.context_compactor = context_compactor
        self.summarizer = summarizer
        self.ui_callback = ui_callback
        
        # [V4.0] Auto-Fixer Heartbeat System
        self.log_watchdog_active = False
        self.autofixer_retry_count = 0
        self.autofixer_max_retries = 3
        
        sys_log("Engine", "VisionEngine initialized V1.1")
    
    # ========================================
    # CONTEXT BUILDING & TOKEN MANAGEMENT
    # ========================================
    
    def build_final_context(self, u_input: str, active_identity: str, active_thought: str, 
                           attached_files: list, apply_compaction: bool = True) -> Tuple[str, int, str]:
        """
        Build context with optional compaction if token limit exceeded.
        
        Returns:
            (context, estimated_tokens, model_key) tuple
        """
        context = self.context_builder.build_context(
            user_input=u_input,
            identity=active_identity,
            thought=active_thought if active_identity == "VISION" else None,
            attachments=attached_files
        )
        
        sys_log("CONTEXT", f"Context built via ContextBuilder: {len(context)} chars")
        
        if not isinstance(context, str):
            context = str(context)
        
        estimated_tokens = estimate_tokens(context) if context else 0
        
        model_key = get_model_for_identity(active_identity, active_thought)
        max_tokens = MODELS_CONFIG.get(model_key, {}).get("max_input_tokens", 32000)
        threshold_tokens = int(max_tokens * 0.8)
        
        if apply_compaction and estimated_tokens > threshold_tokens:
            compaction_result = self.context_compactor.compact_context(
                current_context=context,
                conversation_history=self.summarizer.get_history() if hasattr(self.summarizer, 'get_history') else []
            )
            if compaction_result.get("compacted"):
                context = self.context_builder.build_context(
                    user_input=u_input,
                    identity=active_identity,
                    thought=active_thought if active_identity == "VISION" else None,
                    attachments=attached_files
                )
                estimated_tokens = estimate_tokens(context) if context else 0
        
        return context, estimated_tokens, model_key
    
    # ========================================
    # HAND SERVICE COMMANDS
    # ========================================
    
    def handle_hand_service_commands(self, u_input: str) -> Tuple[bool, Optional[str]]:
        """
        Detect and execute hand service commands (terminal, file management, log cleanup).
        
        Returns:
            (is_handled, result_message) tuple
        """
        u_input_lower = u_input.lower().strip()
        
        # Terminal command patterns
        terminal_keywords = ['รัน', 'execute', 'terminal', 'cmd', 'command', 'powershell']
        is_terminal = any(kw in u_input_lower for kw in terminal_keywords)
        
        # File management patterns
        file_keywords = ['ลบไฟล์', 'ย้ายไฟล์', 'สร้างโฟลเดอร์', 'delete file', 'move file', 'mkdir', 'rename']
        is_file_op = any(kw in u_input_lower for kw in file_keywords)
        
        # Log cleanup patterns
        log_keywords = ['ล้าง log', 'เคลียร์ log', 'clean log', 'clear log', 'ลบ log', 'delete log']
        is_log_cleanup = any(kw in u_input_lower for kw in log_keywords)
        
        if is_terminal:
            command = u_input
            for kw in terminal_keywords:
                if kw in u_input_lower:
                    idx = u_input_lower.find(kw)
                    if idx >= 0:
                        command = u_input[idx + len(kw):].strip()
                        break
            
            if command:
                result = self.hand_service.execute_terminal(command)
                return True, result
        
        if is_file_op:
            action = None
            source = None
            destination = None
            
            if 'ลบ' in u_input_lower or 'delete' in u_input_lower:
                action = "delete"
            elif 'ย้าย' in u_input_lower or 'move' in u_input_lower:
                action = "move"
            elif 'เปลี่ยนชื่อ' in u_input_lower or 'rename' in u_input_lower:
                action = "rename"
            elif 'สร้าง' in u_input_lower or 'mkdir' in u_input_lower:
                action = "mkdir"
            
            if action:
                quoted = re.findall(r'["\']([^"\']+)["\']', u_input)
                if quoted:
                    source = quoted[0]
                    if len(quoted) > 1:
                        destination = quoted[1]
                else:
                    words = u_input.split()
                    for i, word in enumerate(words):
                        if word.lower() in [action, 'ไฟล์', 'โฟลเดอร์', 'file', 'folder', 'directory']:
                            if i + 1 < len(words):
                                source = words[i + 1]
                                break
            
            if action and source:
                result = self.hand_service.manage_file(action, source, destination)
                return True, result
        
        if is_log_cleanup:
            result = self.clean_log_files()
            return True, result
        
        return False, None
    
    def clean_log_files(self) -> str:
        """
        Clean junk log files from LOG_DIR.
        Targets: Empty files, files older than 7 days.
        """
        sys_log("Engine", "🧹 เริ่มปฏิบัติการกวาดล้างไฟล์ขยะใน logs/...")
        try:
            from datetime import datetime
            
            deleted_count = 0
            total_saved_size = 0
            
            if not os.path.exists(LOG_DIR):
                return "❌ ไม่พบโฟลเดอร์ Log ข่ะเจ้านาย"

            for filename in os.listdir(LOG_DIR):
                file_path = os.path.join(LOG_DIR, filename)
                
                if filename == "log.txt":
                    file_size = os.path.getsize(file_path)
                    if file_size > 5 * 1024 * 1024:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"[{datetime.now()}] --- Log Flushed by Engine (Size limit reached) ---\n")
                        sys_log("Engine", "♻️ log.txt ใหญ่เกิน 5MB ทำการ Flush เรียบร้อยข่ะ")
                    continue

                file_mtime = os.path.getmtime(file_path)
                file_age_days = (time.time() - file_mtime) / (24 * 3600)
                file_size = os.path.getsize(file_path)

                if file_size == 0 or file_age_days > 7:
                    try:
                        # [FIXED] Use LOG_DIR instead of hardcoded "data/logs"
                        res = self.hand_service.manage_file("delete", file_path)
                        if "successfully" in res.lower() or "deleted" in res.lower():
                            deleted_count += 1
                            total_saved_size += file_size
                            sys_log("Engine", f"🗑️ ลบ {filename} สำเร็จ (อายุ {file_age_days:.1f} วัน)")
                        else:
                            sys_log("Engine", f"⚠️ ลบ {filename} ไม่สำเร็จ: {res}")
                    except Exception as e:
                        sys_log("Engine", f"⚠️ ลบ {filename} ไม่สำเร็จ: {e}")

            report = f"✅ กวาดบ้านเสร็จแล้วข่ะ! ลบไป {deleted_count} ไฟล์ ประหยัดพื้นที่ได้ {total_saved_size/1024:.2f} KB"
            sys_log("Engine", report)
            return report

        except Exception as e:
            error_msg = f"💥 ระบบทำความสะอาดขัดข้อง: {e}"
            sys_log("Engine", error_msg, "ERROR")
            return error_msg
    
    # ========================================
    # [V4.0] SELF-HEALING HEARTBEAT SYSTEM
    # ========================================
    
    def start_log_monitor(self, ui_callback=None):
        """Start background thread to monitor log.txt for errors"""
        import threading
        if ui_callback:
            self.ui_callback = ui_callback
        
        def monitor_loop():
            sys_log("AutoFixer", "Invincible Watchdog starting...")
            try:
                current_log_path = LOG_TXT
                last_size = os.path.getsize(current_log_path) if os.path.exists(current_log_path) else 0
                
                while self.log_watchdog_active:
                    try:
                        if os.path.exists(current_log_path):
                            current_size = os.path.getsize(current_log_path)
                            if current_size > last_size:
                                with open(current_log_path, 'r', encoding='utf-8', errors='replace') as f:
                                    f.seek(last_size)
                                    new_logs = f.read()
                                    error_keywords = ["Traceback", "Error:", "Exception:", 
                                                    "ModuleNotFoundError", "SyntaxError", "ImportError"]
                                    if any(kw in new_logs for kw in error_keywords):
                                        sys_log("AutoFixer", f"Error detected in logs: {len(new_logs)} chars")
                                        self.trigger_auto_fixer(new_logs)
                                last_size = current_size
                        time.sleep(10)
                    except Exception as inner_e:
                        sys_log("AutoFixer", f"Inner Loop Error: {inner_e}")
                        self.trigger_auto_fixer(str(inner_e))
                        time.sleep(10)
                        
            except Exception as fatal_e:
                sys_log("AutoFixer", f"Fatal Crash: {fatal_e}")
                if self.ui_callback:
                    self.ui_callback(f"\n💔 [Watchdog] หัวใจหยุดเต้นตั้งแต่เริ่ม: {fatal_e}\n")
                self.trigger_auto_fixer(f"Watchdog Critical Crash: {fatal_e}")
        
        self.log_watchdog_active = True
        watchdog_thread = threading.Thread(target=monitor_loop, daemon=True, name="LogWatchdog")
        watchdog_thread.start()
        sys_log("AutoFixer", "Log watchdog thread started")
    
    def stop_log_monitor(self):
        """Stop the log watchdog thread"""
        self.log_watchdog_active = False
        sys_log("AutoFixer", "Log watchdog stopped")
    
    def trigger_auto_fixer(self, error_content: str):
        """
        Trigger auto-fix when error is detected in logs.
        Now implements full repair cycle: Identify File -> AI Fix -> Save -> Verify.
        """
        from vision_config import INSTR_VISION_ULTIMATE
        
        if self.autofixer_retry_count >= self.autofixer_max_retries:
            msg = f"\n🚨 [Auto-Fixer] แจ้งเตือนฉุกเฉิน: พยายามซ่อมแซมครบ {self.autofixer_max_retries} ครั้งแล้วแต่ยังไม่สำเร็จ กรุณาตรวจสอบด้วยตนเองข่ะเจ้านาย!\n"
            if self.ui_callback: self.ui_callback(msg)
            sys_log("AutoFixer", "EMERGENCY: Max retries exceeded")
            return
        
        self.autofixer_retry_count += 1
        msg = f"\n🚨 [Auto-Fixer] ตรวจพบความผิดปกติ! กำลังวิเคราะห์กู้ภัย (Attempt {self.autofixer_retry_count}/{self.autofixer_max_retries})...\n"
        if self.ui_callback: self.ui_callback(msg)
        
        try:
            # 1. Identify target file from traceback
            # Regex to find: File "path/to/file.py", line ...
            file_match = re.search(r'File "([^"]+)", line', error_content)
            target_file = file_match.group(1) if file_match else None
            
            if not target_file or not target_file.endswith('.py'):
                sys_log("AutoFixer", "Could not identify target .py file from traceback. Skipping auto-save.")
                # We still try to get AI advice, but can't auto-save
                target_file = "outbox_fixed.py" 

            # 2. Extract relevant error snippet
            lines = error_content.split('\n')
            relevant_error = ""
            for i, line in enumerate(reversed(lines)):
                if any(kw in line for kw in ["Traceback", "Error:", "Exception:"]):
                    start_idx = max(0, len(lines) - i - 10)
                    relevant_error = '\n'.join(lines[start_idx:len(lines)-i+5])
                    break
            if not relevant_error:
                relevant_error = error_content[-2000:] if len(error_content) > 2000 else error_content
            
            # 3. Request fix from AI
            fix_prompt = f"""ระบบตรวจพบ Error ในไฟล์: {target_file}
Error Content:
{relevant_error}

โปรดวิเคราะห์และส่งโค้ดแก้ไขแบบ Full Code 100% สำหรับไฟล์ {target_file}
- ให้เหตุผลสั้นๆ ว่าทำไมถึงเกิด Error
- ส่งโค้ดที่แก้ไขแล้วแบบสมบูรณ์ (Full Code Only) ห้ามยุบโค้ด
- เริ่มต้นโค้ดด้วย ```python และจบด้วย ```"""
            
            try:
                response_tuple = self.ai_service.ask_stream(
                    model_key="FLASH",
                    question=fix_prompt,
                    instr=INSTR_VISION_ULTIMATE,
                    config={"temp": 0.1, "top_p": 0.8}
                )
                
                response_generator = response_tuple[0] if isinstance(response_tuple, tuple) else response_tuple
                full_response = ""
                for chunk in response_generator:
                    if chunk: full_response += str(chunk)
                
                # Extract code block
                code_match = re.search(r"```python\s*(.*?)\s*```", full_response, re.DOTALL)
                fixed_code = code_match.group(1) if code_match else full_response
                
                if not fixed_code or len(fixed_code) < 50:
                    if self.ui_callback: self.ui_callback("❌ [Auto-Fixer] AI ไม่สามารถสร้างโค้ดแก้ไขที่สมบูรณ์ได้ข่ะ\n")
                    return
                
                if self.ui_callback: self.ui_callback(f"🔧 [Auto-Fixer] AI สร้างโค้ดแก้ไขสำหรับ {target_file} แล้ว กำลังบันทึก...\n")
                
                # 4. Apply Fix (Save File)
                save_res = self.hand_service.save_file(target_file, fixed_code.strip())
                sys_log("AutoFixer", f"Saved fix to {target_file}: {save_res}")
                
                # 5. Verify Fix (Syntax Check)
                verify_res = self.hand_service.execute_terminal(f"python -m py_compile {target_file}")
                
                if "successfully" in verify_res.lower() or "OK" in verify_res or not verify_res:
                    if self.ui_callback: self.ui_callback(f"✅ [Auto-Fixer] ซ่อมแซม {target_file} และตรวจสอบ Syntax สำเร็จเรียบร้อยข่ะเจ้านาย!\n")
                    self.autofixer_retry_count = 0 
                    sys_log("AutoFixer", f"Auto-fix successful: {target_file}")
                else:
                    if self.ui_callback: self.ui_callback(f"⚠️ [Auto-Fixer] บันทึกไฟล์แล้วแต่ Syntax ยังไม่ผ่าน: {verify_res}\n")
                    sys_log("AutoFixer", f"Syntax verification failed for {target_file}")
                    
            except Exception as ai_error:
                if self.ui_callback: self.ui_callback(f"❌ [Auto-Fixer] AI Processing Error: {str(ai_error)}\n")
                sys_log("AutoFixer", f"AI processing failed: {ai_error}")
                
        except Exception as e:
            if self.ui_callback: self.ui_callback(f"❌ [Auto-Fixer] เกิดข้อผิดพลาดในการซ่อมแซม: {str(e)}\n")
            sys_log("AutoFixer", f"Auto-fixer failed: {e}")

    def parse_ai_commands(self, ai_response):
        """
        [OTA] แกะกล่องคำสั่ง <hand_service> จากคำตอบของ AI และสั่งงานทันที
        """
        import re
        pattern = r"<hand_service>(.*?)</hand_service>"
        commands = re.findall(pattern, ai_response, re.DOTALL)
        
        results = []
        for cmd_content in commands:
            try:
                action_match = re.search(r"<action>(.*?)</action>", cmd_content, re.DOTALL)
                action = action_match.group(1).strip() if action_match else None
                
                target_match = re.search(r"<target>(.*?)</target>", cmd_content, re.DOTALL)
                target = target_match.group(1).strip() if target_match else None
                
                if action == "save_file" and target:
                    content_match = re.search(r"<content>(.*?)</content>", cmd_content, re.DOTALL)
                    content = content_match.group(1) if content_match else ""
                    res = self.hand_service.save_file(target, content.strip())
                    results.append(res)
                    if target.endswith('.py'):
                        test_res = self.hand_service.execute_terminal(f"python -m py_compile {target}")
                        results.append(f"[AUTO_VERIFY] {target}: {test_res}")
                    sys_log("OTA", f"Executed save_file: {target}")
                    
                elif action == "delete" and target:
                    res = self.hand_service.manage_file("delete", target)
                    results.append(res)
                    sys_log("OTA", f"Executed delete: {target}")
                    
                elif action == "read_file" and target:
                    content = self.hand_service.read_file(target, internal_mode=True)
                    if content.startswith("❌"):
                        results.append(content)
                    else:
                        results.append(f"[AUTONOMOUS_READ] {target} สำเร็จ:\n{content}")
                    sys_log("OTA", f"Executed read_full_file: {target}")
                    
                elif action == "execute_terminal" and target:
                    sys_log("TERMINAL", f"Triggering command: {target}")
                    if self.ui_callback: 
                        self.ui_callback(f"\n⏳ กำลังรันคำสั่ง: {target} ...\n")
                    res = self.hand_service.execute_terminal(target)
                    results.append(f"[TERMINAL_RESULT] {res}")
                    sys_log("OTA", f"Executed execute_terminal: {target}")
                    
            except Exception as e:
                error_msg = f"❌ แกะคำสั่ง AI พลาดข่ะ: {e}"
                results.append(error_msg)
                sys_log("OTA", error_msg, "ERROR")
        
        return results