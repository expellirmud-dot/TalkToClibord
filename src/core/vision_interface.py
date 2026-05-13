#  (V6.0.4 - Hardened Edition - Optimized by Vision)
import sys, os, re, time, threading, hashlib, pyperclip, signal, keyboard, ast, json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageGrab
from concurrent.futures import ThreadPoolExecutor

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.vision_utils import estimate_tokens, log_token_usage, get_daily_expense, get_model_usage_stats, PerformanceTimer, sys_log
from vision_config import MODELS_CONFIG, INSTR_VISION_ULTIMATE, INSTR_JAMIE, get_model_for_identity, get_thought_config, IDENTITY_MODEL_MAP, GEMINI_API_KEY, UI_STYLE
from src.api.vision_ai_service import VisionAIService
from src.core.vision_live_service import VisionLiveService
from src.utils.vision_audio_core import VisionAudioCore
from src.core.vision_memory_vault import MemoryVault
from src.core.vision_memory_summarizer import MemorySummarizer
from src.core.vision_dependency_detective import DependencyDetective
from src.core.vision_hand_service import VisionHandService
from src.core.vision_context_builder import ContextBuilder
from src.utils.vision_paths import ROOT_DIR, ensure_dirs, LOG_DIR, LOG_TXT, CHAT_HISTORY_JSON
from src.api.vision_api_manager import APIConnectionManager
from src.core.miniGeminiWeb import VisionProStation
from src.utils.vision_audio_core import vision_audio

# V3.0 Sprint Modules (all in src/core/)
from src.core.vision_persistent_memory import PersistentMemory
from src.core.vision_smart_summarizer import SmartSummarizer
from src.core.vision_task_analyzer import TaskAnalyzer
from src.core.vision_reference_loader import ReferenceLoader
from src.core.vision_context_recovery import ContextRecovery
from src.core.vision_context_compactor import ContextCompactor
from src.core.vision_dependency_graph import DependencyGraph
from src.core.vision_context_dashboard import ContextDashboard
from src.core.vision_engine import VisionEngine
from src.core.vision_stt_service import VisionSTTService, get_stt_service

class ProjectJAVIS:
    # ========================================
    # SYSTEM INITIALIZATION
    # ========================================
    def __init__(self):
        # [V3.0] Initialize directory structure first
        ensure_dirs()
        
        signal.signal(signal.SIGINT, lambda sig, frame: os._exit(0))
        self.is_running = True
        self.is_processing = False
        self.is_continuous = False
        self.is_live = False
        self.voice_on = True
        
        # [FIXED] เพิ่มตัวแปรสถานะเพื่อป้องกัน Attribute Error ใน Dashboard
        self.attached_files = []  
        self.ram_context = []
        self.file_token_cache = {} 
        
        # [V3.0] UI State Variables & Identity
        self.active_identity = "JAMIE"
        self.active_thought = "FLASH"
        self._reflex_count = 0  
        self.MAX_REFLEX_DEPTH = 4
        
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._last_command_length = 0
        
        self.persistent_memory = PersistentMemory()
        self.smart_summarizer = SmartSummarizer()
        self.task_analyzer = TaskAnalyzer()
        self.reference_loader = ReferenceLoader()
        self.context_recovery = ContextRecovery()
        self.context_compactor = ContextCompactor()
        self.dependency_graph = DependencyGraph()
        self.context_dashboard = ContextDashboard()
        
        self.ai_service = VisionAIService(GEMINI_API_KEY)
        self.hand_service = VisionHandService()
        self.audio_core = VisionAudioCore(self)
        self.dependency_detective = DependencyDetective(ROOT_DIR)
        self.memory_vault = MemoryVault(GEMINI_API_KEY)
        self.memory_summarizer = MemorySummarizer(self.ai_service)
        self.context_builder = ContextBuilder()
        self.api_manager = APIConnectionManager(GEMINI_API_KEY)
        self.live_service = VisionLiveService(self.ai_service.client, MODELS_CONFIG["vision"]["id"], INSTR_VISION_ULTIMATE)
        self.web_station = VisionProStation()
        
        self.engine = VisionEngine(
            self.ai_service, 
            self.hand_service, 
            self.context_builder, 
            self.context_compactor, 
            self.smart_summarizer
        )
        self.engine.ui_callback = self.append_text
        
        self.root = tk.Tk()
        self.setup_ui()
        self.set_indicator("READY")
        
        self._update_identity_buttons()
        self._update_thought_buttons()
        self._load_handoff_state()
        self._start_log_monitor()
        self._start_context_dashboard_timer()
        
        # [STT V1.0] Initialize STT Service with callbacks
        self.stt_service = get_stt_service(
            on_text_callback=self._handle_stt_text,
            on_status_callback=self._handle_stt_status
        )
        self._setup_stt_hotkeys()
        
    def _setup_stt_hotkeys(self):
        """Setup keyboard hotkeys for STT (Alt+X toggle, F9 quick)"""
        try:
            # Alt+X: Toggle continuous STT mode
            keyboard.add_hotkey('alt+x', self._toggle_stt_mode)
            # F9: Quick STT mode (listen once)
            keyboard.add_hotkey('f9', self._quick_stt_mode)
            sys_log("STT", "Hotkeys registered: Alt+X (toggle), F9 (quick)")
        except Exception as e:
            sys_log("STT", f"Hotkey registration error: {e}", "ERROR")
    
    def _toggle_stt_mode(self):
        """Toggle continuous STT mode (Alt+X) - แสดงผลในช่อง input อย่างเดียว ไม่ส่ง AI"""
        self.stt_service.toggle_continuous_mode()
        status = "ON" if self.stt_service.is_active() else "OFF"
        self.set_indicator(f"STT {status}")
        # Alt+X mode: แสดงผลอย่างเดียว
        self._stt_auto_send = False
    
    def _quick_stt_mode(self):
        """Quick STT mode (F9) - ฟังครั้งเดียวแล้วส่งต่อให้ AI"""
        self.stt_service.start_quick_mode()
        # F9 mode: ส่งต่อให้ AI
        self._stt_auto_send = True
    
    def _handle_stt_text(self, text: str):
        """Handle STT text: copy to clipboard, update UI, [optional] send to AI"""
        # Update input box with recognized text
        if hasattr(self, 'input_box'):
            self.input_box.delete("1.0", tk.END)
            self.input_box.insert("1.0", text)
        
        # ส่งต่อให้ AI เฉพาะ F9 mode (ไม่ใช่ Alt+X)
        if getattr(self, '_stt_auto_send', False) and text.strip():
            vision_audio.speak(f"รับทราบข่ะ: {text[:30]}...")
            self._process_command(text)
    
    def _handle_stt_status(self, status: str):
        """Handle STT status updates"""
        self.set_indicator(status.replace("[STT]", "").strip()[:20])
        sys_log("STT", status)
        
    def _load_handoff_state(self):
        try:
            handoff_data = self.context_recovery.get_latest_handoff()
            if handoff_data:
                self.append_text(f"[🔄 Context Recovery: Loaded {len(handoff_data.get('memory', ''))} chars from previous session]\n")
        except Exception as e:
            sys_log("RECOVERY", f"Handoff load error: {e}")

    def _start_log_monitor(self):
        try:
            if hasattr(self, 'engine'):
                self.engine.start_log_monitor(ui_callback=self.append_text)
                sys_log("AUTO_FIXER", "Engine log monitor started")
        except Exception as e:
            sys_log("AUTO_FIXER", f"Log monitor start error: {e}")

    def _start_context_dashboard_timer(self):
        """Start periodic context dashboard updates"""
        def update_dashboard():
            if self.is_running:
                # [FIXED] Force update to run on main thread and catch any loose errors
                try:
                    self._update_context_dashboard()
                except Exception as e:
                    sys_log("DASHBOARD", f"Timer update error: {e}")
                self.root.after(3000, update_dashboard) # อัปเดตทุก 3 วิให้ไวขึ้น
        
        self.root.after(1000, update_dashboard)

    def _graceful_exit(self):
        try:
            self.append_text("\n[💾 Saving session state...]\n")
            task_description = f"Session with {self.active_identity} identity"
            progress = f"Active session, {len(self.attached_files)} files attached"
            self.context_recovery.auto_snapshot(task_description, progress, self.attached_files)
            
            self.append_text("[✅ Session saved successfully]\n")
            self.is_running = False
            self.close_web()
            
            if self.executor:
                self.executor.shutdown(wait=False)
            
            self.root.destroy()
            os._exit(0)
        except Exception as e:
            sys_log("EXIT", f"Graceful exit error: {e}")
            os._exit(1)

    # ========================================
    # UI MANAGEMENT
    # ========================================
    def _update_context_dashboard(self):
        """[V6.3.5] Enhanced Context Dashboard with Context Caching"""
        try:
            # 1. Get model-specific token limit
            model_key = get_model_for_identity(self.active_identity, self.active_thought)
            max_limit = MODELS_CONFIG.get(model_key, {}).get("max_input_tokens", 12000)
            self.context_dashboard.max_tokens = max_limit
            
            # 2. Get current query from input box for real-time preview
            try:
                current_query = self.input_box.get("1.0", tk.END).strip()
            except Exception as e:
                current_query = ""
            
            # 3. Check if we need to rebuild context (avoid unnecessary builds)
            # Only rebuild if query changed or attachments changed
            query_hash = hash(current_query + str(sorted(self.attached_files)))
            
            if hasattr(self, '_last_context_hash') and self._last_context_hash == query_hash:
                # Use cached values - no need to rebuild
                if hasattr(self, '_cached_context_data'):
                    self._update_ui_from_cache()
                    return
            
            # 4. Build actual context with current query for real-time preview
            try:
                actual_context = self.context_builder.build_context(
                    identity=self.active_identity,
                    user_input=current_query,  # Include current input for preview
                    attachments=self.attached_files
                )
            except Exception as e:
                actual_context = ""
            
            # 5. Calculate real tokens from actual context
            total_tokens = 0
            system_tokens = 0
            memory_tokens = 0
            file_tokens = 0
            query_tokens = 0
            
            if actual_context:
                total_tokens = estimate_tokens(actual_context)
                
                sections = actual_context.split("\n\n")
                for section in sections:
                    if section.startswith("[SYSTEM]"):
                        system_tokens = estimate_tokens(section)
                    elif section.startswith("[MEMORY]"):
                        memory_tokens = estimate_tokens(section)
                    elif section.startswith("[FILES]"):
                        file_tokens = estimate_tokens(section)
                    elif section.startswith("[USER]"):
                        query_tokens = estimate_tokens(section)
            
            # 6. Cache the results
            self._last_context_hash = query_hash
            self._cached_context_data = {
                'total_tokens': total_tokens,
                'system_tokens': system_tokens,
                'memory_tokens': memory_tokens,
                'file_tokens': file_tokens,
                'query_tokens': query_tokens,
                'model_key': model_key,
                'max_limit': max_limit
            }
            
            # 7. Update dashboard
            self._update_dashboard_with_data()
            
        except Exception as e:
            # Reduce error logging frequency
            if not hasattr(self, '_last_dashboard_error_time') or \
               time.time() - self._last_dashboard_error_time > 30:  # Log error only once per 30 seconds
                sys_log("DASHBOARD", f"Dashboard update error: {e}")
                self._last_dashboard_error_time = time.time()

    def _update_ui_from_cache(self):
        """Update UI from cached data to avoid unnecessary context building"""
        try:
            if hasattr(self, '_cached_context_data'):
                data = self._cached_context_data
                
                # Update dashboard with cached values
                self.context_dashboard.set_system_instruction_tokens(int(data['system_tokens']))
                self.context_dashboard.set_memory_tokens(int(data['memory_tokens']))
                self.context_dashboard.set_file_data_tokens(int(data['file_tokens']))
                self.context_dashboard.set_user_query_tokens(int(data['query_tokens']))
                
                # Get TPM Available data
                tpm_available = self._get_tpm_available()
                
                # Calculate percentages
                payload_usage_percentage = (data['total_tokens'] / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
                tpm_available_percentage = (tpm_available / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
                
                # Format UI
                health_bar = self.context_dashboard.format_for_ui(style="health_bar", usage_percentage=payload_usage_percentage)
                
                token_text = f"{data['model_key'].upper()} | Payload: {data['total_tokens']:,}/{data['max_limit']:,} TK"
                token_text += f" | TPM Available: {tpm_available:,}/{data['max_limit']:,} ({tpm_available_percentage:.1f}%)"
                
                # Add warnings
                if payload_usage_percentage >= 90:
                    token_text += " | Payload High"
                elif tpm_available < data['total_tokens']:
                    token_text += " | Insufficient Quota"
                
                # Update UI
                def refresh_labels():
                    try:
                        self.context_dashboard_label.config(text=health_bar)
                        self.token_lbl.config(text=token_text)
                    except Exception: pass
                
                self.root.after(0, refresh_labels)
                
        except Exception as e:
            sys_log("DASHBOARD", f"Cache update error: {e}")

    def _update_dashboard_with_data(self):
        """Update dashboard with current data"""
        try:
            if not hasattr(self, '_cached_context_data'):
                return
            
            data = self._cached_context_data
            
            # Update dashboard
            self.context_dashboard.set_system_instruction_tokens(int(data['system_tokens']))
            self.context_dashboard.set_memory_tokens(int(data['memory_tokens']))
            self.context_dashboard.set_file_data_tokens(int(data['file_tokens']))
            self.context_dashboard.set_user_query_tokens(int(data['query_tokens']))
            
            # Get TPM Available data
            tpm_available = self._get_tpm_available()
            
            # Calculate percentages
            payload_usage_percentage = (data['total_tokens'] / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
            tpm_available_percentage = (tpm_available / data['max_limit']) * 100 if data['max_limit'] > 0 else 0
            
            # Format UI
            health_bar = self.context_dashboard.format_for_ui(style="health_bar", usage_percentage=payload_usage_percentage)
            
            token_text = f"{data['model_key'].upper()} | Payload: {data['total_tokens']:,}/{data['max_limit']:,} TK"
            token_text += f" | TPM Available: {tpm_available:,}/{data['max_limit']:,} ({tpm_available_percentage:.1f}%)"
            
            # Add warnings
            if payload_usage_percentage >= 90:
                token_text += " | Payload High"
            elif tpm_available < data['total_tokens']:
                token_text += " | Insufficient Quota"
            
            # Log only when significant changes occur
            if not hasattr(self, '_last_logged_tokens') or \
               abs(data['total_tokens'] - self._last_logged_tokens) > 100:  # Log only when tokens change by >100
                sys_log("DASHBOARD", f"Updated: {data['total_tokens']} tokens ({payload_usage_percentage:.1f}%)")
                self._last_logged_tokens = data['total_tokens']
            
            # Update UI
            def refresh_labels():
                try:
                    self.context_dashboard_label.config(text=health_bar)
                    self.token_lbl.config(text=token_text)
                except Exception: pass
            
            self.root.after(0, refresh_labels)

            # [FIXED] Integrate Warning and Compaction check here safely
            usage = self.context_dashboard.get_usage_percentage()
            if 70 <= usage < 80:
                if not hasattr(self, '_warning_shown_at_70'):
                    self.append_text(f"\n[⚠️ Memory usage at {usage:.1f}% - Consider clearing memory with /memory clear]\n")
                    self._warning_shown_at_70 = True

            compaction_result = self.context_dashboard.trigger_compaction_if_needed()
            if compaction_result and compaction_result.get("compaction_triggered"):
                self.append_text(f"\n[⚠️ {compaction_result.get('usage_at_trigger', 0):.1f}% usage - Compaction triggered]\n")
            
        except Exception as e:
            sys_log("DASHBOARD", f"Dashboard update error: {e}")

    def _get_tpm_available(self):
        """[V7.1] คำนวณโควตา TPM แบบ Real-time แยกตาม Identity (Vision=16k, อื่นๆ=200k)"""
        try:
            current_time = time.time()
            
            # 1. กำหนดขีดจำกัดตามตัวตน (Identity-based Limit)
            # Vision = 16,000 | Jamie/Pro = 200,000
            current_limit = 16000 if self.active_identity == "VISION" else 200000
            
            # 2. ตรวจสอบการเริ่มระบบครั้งแรก
            if not hasattr(self, '_tpm_quota'):
                self._tpm_quota = current_limit
                self._max_tpm_quota = current_limit
                self._last_refill_time = current_time
            
            # 3. จัดการกรณีบอสสลับตัวตนกลางคัน (Limit เปลี่ยน)
            if self._max_tpm_quota != current_limit:
                # ถ้าสลับจาก 200k มาหา 16k แล้วโควตาเดิมเกินขีดจำกัด ให้ปัดลงทันที
                if self._tpm_quota > current_limit:
                    self._tpm_quota = current_limit
                self._max_tpm_quota = current_limit

            # 4. คำนวณการคืนโควตา (Refill Rate) แบบวินาทีต่อวินาที
            # สูตร: (โควตาสูงสุด / 60 วินาที)
            time_passed = current_time - self._last_refill_time
            refill_rate = self._max_tpm_quota / 60.0 
            refill_amount = time_passed * refill_rate
            
            # 5. เติมน้ำลงถัง (แต่ห้ามเกินขีดจำกัด)
            if refill_amount > 0:
                self._tpm_quota = min(self._tpm_quota + refill_amount, self._max_tpm_quota)
                self._last_refill_time = current_time
            
            return int(self._tpm_quota)
            
        except Exception as e:
            # กรณี Error ให้คืนค่า safe limit ตามตัวตนปัจจุบัน
            return 16000 if self.active_identity == "VISION" else 200000

    def _consume_tpm_quota(self, tokens):
        """Consume TPM quota when request is successful"""
        try:
            if hasattr(self, '_tpm_quota') and self._tpm_quota >= tokens:
                self._tpm_quota -= tokens
                sys_log("TPM", f"Consumed {tokens} tokens (remaining: {self._tpm_quota:,})")
                return True
            else:
                sys_log("TPM", f"Insufficient quota: need {tokens}, have {self._tpm_quota}")
                return False
        except Exception as e:
            sys_log("TPM", f"Consume TPM quota error: {e}")
            return False

    def set_indicator(self, status, detail=""):
        states = {
            "READY": {"color": "#2ecc71", "text": "READY"},
            "THINKING": {"color": "#3498db", "text": "AI THINKING"},
            "WORKING": {"color": "#f1c40f", "text": "SNIPER WORKING"},
            "EXECUTING": {"color": "#e67e22", "text": "EXECUTING"},
            "ERROR": {"color": "#e74c3c", "text": "ERROR"}
        }

        state = states.get(status, states["READY"])
        display_text = f"{state['text']} {f'| {detail}' if detail else ''}"

        def update_ui():
            try:
                self.status_dot.config(fg=state["color"])
                self.status_label.config(text=display_text.upper())
                self.root.update()
            except Exception as e:
                sys_log("UI", f"Status update error: {e}")

        self.root.after(0, update_ui)

    def _execute_terminal_safe(self, command):
        self.set_indicator("EXECUTING")
        self.append_text(f"\n[🚀 TERMINAL RUNNING] > {command}\n")
        try:
            result = self.hand_service.execute_terminal(command)
            self.append_text(f"[✅ TERMINAL COMPLETE] {result}\n")
            return result
        except Exception as e:
            self.append_text(f"[❌ TERMINAL ERROR] {e}\n")
            return f"❌ Error: {e}"

    def setup_ui(self):
        self.root.title("J.A.V.I.S. V6.0.4")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", UI_STYLE.get("alpha", 0.95))
        self.root.overrideredirect(True)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry("450x650+" + str(sw-460) + "+" + str(sh-700)) # เพิ่มความสูงโดยรวม
        self.root.configure(bg=UI_STYLE.get("bg_color", "#ffffff"))
        
        # --- Dashboard Frame ---
        dashboard_frame = tk.Frame(self.root, bg="#ffffff")
        dashboard_frame.pack(side='top', fill='x', pady=5, padx=10)
        self.context_dashboard_label = tk.Label(dashboard_frame, text="🟢 Context: [░░░░░░░░░░░░] 0.0%", font=(UI_STYLE.get("font_family", "Segoe UI"), 8), bg=UI_STYLE.get("bg_color", "#ffffff"), fg="#2ecc71")
        self.context_dashboard_label.pack(side=tk.LEFT, padx=2)
        self.token_lbl = tk.Label(dashboard_frame, text="Token: 0 | 0.00 ฿", font=(UI_STYLE.get("font_family", "Segoe UI"), 8), bg=UI_STYLE.get("bg_color", "#ffffff"), fg="#95a5a6")
        self.token_lbl.pack(side=tk.RIGHT, padx=2)
        
        # --- Header Frame ---
        header_frame = tk.Frame(self.root, bg="#ffffff")
        header_frame.pack(side='top', fill='x', pady=2, padx=10)
        tk.Button(header_frame, text="Exit ✖", font=(UI_STYLE.get("font_family", "Segoe UI"), 9, "bold"), command=lambda: os._exit(0), bg=UI_STYLE.get("bg_color", "#ffffff"), fg="#e74c3c", bd=0).pack(side=tk.RIGHT)

        # --- Status Bar Frame (Packed at bottom to prevent clipping) ---
        self.status_frame = tk.Frame(self.root, bg=UI_STYLE.get("bg_color", "#ffffff"))
        self.status_frame.pack(side='bottom', fill='x', padx=20, pady=5)
        self.status_dot = tk.Label(self.status_frame, text="●", fg="#2ecc71", bg=UI_STYLE.get("bg_color", "#ffffff"), font=(UI_STYLE.get("font_family", "Segoe UI"), 12))
        self.status_dot.pack(side='left')
        self.status_label = tk.Label(
            self.status_frame, text="READY", fg=UI_STYLE.get("fg_color", "#2c3e50"),
            bg=UI_STYLE.get("bg_color", "#ffffff"), font=(UI_STYLE.get("font_family", "Segoe UI"), 9, "bold")
        )
        self.status_label.pack(side='left', padx=5)

        # --- Input Frame (Packed above Status Bar) ---
        input_frame = tk.Frame(self.root, bg="#ffffff")
        # [FIXED] เพิ่ม pady ให้มีพื้นที่หายใจ และให้ height มากพอสำหรับฟอนต์ขนาด 12
        input_frame.pack(side='bottom', fill='x', padx=10, pady=(5, 10))
        
        # [FIXED] เพิ่มความสูงช่อง Text (height=4 -> 5) และปรับ padding ภายใน
        self.input_box = tk.Text(input_frame, height=5, font=(UI_STYLE.get("font_family", "Segoe UI"), UI_STYLE.get("font_size_base", 12)), 
                            bg="#f5f5f7", fg="#1d1d1f", bd=0, wrap=tk.WORD, padx=12, pady=12, 
                            highlightthickness=1, highlightbackground="#d2d2d7", highlightcolor="#007aff", 
                            insertbackground=UI_STYLE.get("cursor_color", "#3498db"))
        self.input_box.pack(side=tk.LEFT, fill='both', expand=True, padx=(0,10))
        self.input_box.bind("<Control-Return>", lambda e: self.send_command())
        
        self.send_btn = tk.Button(input_frame, text="Send", font=(UI_STYLE.get("font_family", "Segoe UI"), 10, "bold"), command=self.send_command, bg="#007aff", fg="#ffffff", bd=0, padx=15, cursor="hand2")
        self.send_btn.pack(side=tk.RIGHT, fill='y')

        # --- Controls Area (Identity & Tools) ---
        id_frame = tk.Frame(self.root, bg="#ffffff")
        id_frame.pack(side='top', fill='x', padx=10, pady=2)
        tk.Label(id_frame, text="Identity:", bg=UI_STYLE.get("bg_color", "#ffffff"), font=(UI_STYLE.get("font_family", "Segoe UI"), 9, "bold"), width=8, anchor="w").pack(side=tk.LEFT)
        self.btn_i_jamie = tk.Button(id_frame, text="Jamie", command=lambda: self.select_identity("JAMIE"), width=8, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_i_jamie.pack(side=tk.LEFT, padx=2)
        self.btn_i_vision = tk.Button(id_frame, text="Vision", command=lambda: self.select_identity("VISION"), width=8, bg="#333333", fg="#ffffff", bd=1, relief="flat")
        self.btn_i_vision.pack(side=tk.LEFT, padx=2)
        self.btn_i_pro = tk.Button(id_frame, text="Vision|Pro", command=lambda: self.select_identity("PRO"), width=10, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_i_pro.pack(side=tk.LEFT, padx=2)

        th_frame = tk.Frame(self.root, bg="#ffffff")
        th_frame.pack(side='top', fill='x', padx=10, pady=2)
        tk.Label(th_frame, text="Thought:", bg=UI_STYLE.get("bg_color", "#ffffff"), font=(UI_STYLE.get("font_family", "Segoe UI"), 9, "bold"), width=8, anchor="w").pack(side=tk.LEFT)
        self.btn_t_flash = tk.Button(th_frame, text="Flash", command=lambda: self.select_thought("FLASH"), width=8, bg="#f1c40f", fg="#333333", bd=1, relief="flat")
        self.btn_t_flash.pack(side=tk.LEFT, padx=2)
        self.btn_t_think = tk.Button(th_frame, text="Think", command=lambda: self.select_thought("THINK"), width=8, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_t_think.pack(side=tk.LEFT, padx=2)
        self.btn_t_pro = tk.Button(th_frame, text="Pro", command=lambda: self.select_thought("PRO"), width=8, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_t_pro.pack(side=tk.LEFT, padx=2)

        tool_frame = tk.Frame(self.root, bg="#ffffff")
        tool_frame.pack(side='top', fill='x', padx=10, pady=5)
        self.btn_attach = tk.Button(tool_frame, text="File", command=self.attach_file, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_attach.pack(side=tk.LEFT, padx=2)
        self.btn_web = tk.Button(tool_frame, text="Web", command=self.open_web, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_web.pack(side=tk.LEFT, padx=2)
        self.btn_read = tk.Button(tool_frame, text="Read", command=self.read_answer, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_read.pack(side=tk.LEFT, padx=2)
        self.btn_mic = tk.Button(tool_frame, text="Mic", command=self.toggle_mic, bg="#f8f9fa", fg="#333333", bd=1, relief="flat")
        self.btn_mic.pack(side=tk.LEFT, padx=2)
        self.btn_compact = tk.Button(tool_frame, text="Compact", command=self._manual_compact_memory, bg="#e74c3c", fg="#ffffff", bd=1, relief="flat")
        self.btn_compact.pack(side=tk.RIGHT, padx=2)

        # --- Output Area (Packed last to fill remaining space) ---
        self.output_box = tk.Text(self.root, bg=UI_STYLE.get("bg_color", "#ffffff"), fg="#1d1d1f", 
                                font=(UI_STYLE.get("font_family", "Segoe UI"), UI_STYLE.get("font_size_base", 11)), 
                                wrap=tk.WORD, bd=0, padx=UI_STYLE.get("padding_x", 15), pady=UI_STYLE.get("padding_y", 10), 
                                highlightthickness=0, spacing1=UI_STYLE.get("line_spacing", 2))
        self.output_box.pack(padx=10, pady=5, fill='both', expand=True)
        
        # Context Menu
        self._create_context_menu(self.input_box)
        self.input_box.bind("<Control-c>", lambda e: self._handle_copy())
        self.input_box.bind("<Control-a>", lambda e: self._handle_select_all())
        self.input_box.bind("<Control-x>", lambda e: self._handle_cut())
        self.input_box.bind("<Control-v>", lambda e: self._handle_paste())

    # ========================================
    # IDENTITY & MODEL MANAGEMENT
    # ========================================
    def is_code_task(self, query):
        """[V6.3.5] Code task detection - returns boolean only"""
        query_lower = query.lower()
        code_keywords = ['bug','วิชั่น', 'error','บัก','โค้ด', 'เออเร่อ', 'debug', 'analyze', 'fix', 'แก้โค้ด', 'สแกน', 'deep scan', 'system_auto']
        return any(keyword in query_lower for keyword in code_keywords)

    def select_identity(self, identity):
        self.active_identity = identity
        self._update_identity_buttons()
        self.append_text(f"[🔄 Identity switched to {identity}]\n")
        # Update context dashboard immediately for new model limits
        self._update_context_dashboard()

    def select_thought(self, thought):
        self.active_thought = thought
        self._update_thought_buttons()
        self.append_text(f"[🔄 Thought model switched to {thought}]\n")
        # Update context dashboard immediately for new model limits
        self._update_context_dashboard()

    def _update_identity_buttons(self):
        btns = {
            "JAMIE": self.btn_i_jamie,
            "VISION": self.btn_i_vision,
            "PRO": self.btn_i_pro
        }
        for identity, btn in btns.items():
            if self.active_identity == identity:
                btn.configure(bg="#333333", fg="#ffffff")
            else:
                btn.configure(bg="#f8f9fa", fg="#333333")

    def _update_thought_buttons(self):
        self.btn_t_flash.configure(bg="#f1c40f" if self.active_thought == "FLASH" else "#f8f9fa", fg="#333333")
        self.btn_t_think.configure(bg="#f1c40f" if self.active_thought == "THINK" else "#f8f9fa", fg="#333333")
        self.btn_t_pro.configure(bg="#f1c40f" if self.active_thought == "PRO" else "#f8f9fa", fg="#333333")

    # ========================================
    # CORE FUNCTIONALITY
    # ========================================
    def send_command(self):
        command = self.input_box.get("1.0", tk.END).strip()
        if not command:
            return
        vision_audio.speak("รับทราบข่ะเจ้านาย")

        self.input_box.delete("1.0", tk.END)
        self.append_text(f"[👤 User] {command}\n")
        self._last_command_length = len(command)
        self.set_indicator("THINKING")
        
        future = self.executor.submit(self._process_command, command)
        def handle_result(f):
            try:
                result = f.result()
                self.root.after(0, lambda: self._handle_ai_response(result))
            except Exception as e:
                self.root.after(0, lambda: self._handle_error(e))
        future.add_done_callback(handle_result)

    def _save_chat_history(self, role, text):
        try:
            history = []
            if os.path.exists(str(CHAT_HISTORY_JSON)):
                with open(CHAT_HISTORY_JSON, 'r', encoding='utf-8') as f:
                    try:
                        history = json.load(f)
                    except json.JSONDecodeError:
                        pass

            clean_text = text
            if role != "user":
                clean_text = re.sub(r'\[🤖.*?\]\s*', '', text).strip()

            history.append({"role": role, "parts": [clean_text]})
            if len(history) > 50:
                history = history[-50:]

            with open(CHAT_HISTORY_JSON, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            sys_log("Memory", f"Save history error: {e}")

    def _save_to_outbox(self, content):
        """💾 [ROBUST] บันทึกเนื้อหา AI ลง outbox_fixed.py อัตโนมัติ"""
        try:
            outbox_path = os.path.join(ROOT_DIR, "outbox_fixed.py")
            
            # Improved Regex: Support multiple types of code blocks
            code_blocks = re.findall(r"```(?:python)?\s*(.*?)\s*```", content, re.DOTALL)
            
            if code_blocks:
                # [Vision Logic] เลือก Block ที่ยาวที่สุด ซึ่งมักจะเป็น Full Code ที่ AI ส่งมา
                clean_code = max(code_blocks, key=len).strip()
            elif "```" in content:
                # Fallback for unmatched blocks
                match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
                clean_code = match.group(1).strip() if match else content
            else:
                clean_code = content

            with open(outbox_path, "w", encoding="utf-8") as f:
                f.write(clean_code)
                vision_audio.speak("เซฟเรียบร้อยข่ะ")
            sys_log("Interface", f"Saved to outbox: {outbox_path}")
        except Exception as e:
            sys_log("Interface", f"Outbox save error: {e}")

    def _process_command(self, command):
        try:
            # Check for manual compact command
            if command.strip().lower() in ['/compact', '/memory compact', '/compact memory']:
                self._manual_compact_memory()
                return "Memory compaction initiated"
            
            # Check for memory status command
            if command.strip().lower() in ['/memory', '/memory status']:
                return self._show_memory_status()
            
            # [V6.3.5] Check if code task and set effective identity
            is_code = self.is_code_task(command)
            effective_identity = "VISION" if is_code else self.active_identity
            self._save_chat_history("user", command)
            actual_model_key = get_model_for_identity(self.active_identity, self.active_thought)

            context = self.context_builder.build_context(
                identity=effective_identity,
                user_input=command,
                attachments=self.attached_files
            )

            token_est = estimate_tokens(context)
            
            # Check if we have enough TPM quota before sending
            available_quota = self._get_tpm_available()
            
            if available_quota < token_est:
                self.append_text(f"[TPM] Insufficient quota: need {token_est}, have {available_quota}\n")
                self.append_text("[TPM] Waiting for quota refill...\n")
                return "Please wait - insufficient TPM quota"
            
            self.set_indicator("THINKING", f"SENDING {token_est} TOKENS")

            # Send request
            response = self.ai_service.process_request(query=command, context=context, identity=effective_identity, model=actual_model_key)
            
            # Consume quota only if successful
            if response and not response.startswith("Error") and not response.startswith("Please wait"):
                self._consume_tpm_quota(token_est)
            
            return response
        except Exception as e:
            return f"Error processing command: {e}"

    def _handle_ai_response(self, response):
        """[FIXED] Restored truncated parsing logic and safely wrapped in try-except"""
        try:
            self.append_text(f"[🤖 {self.active_identity}] {response}\n")
            self._save_to_outbox(response)
            self._save_chat_history("model", response)

            results = self.engine.parse_ai_commands(response)
            try: 
                log_token_usage(self.active_identity, self._last_command_length, len(response))
            except Exception: 
                pass

            if results:
                if self._reflex_count >= self.MAX_REFLEX_DEPTH:
                    self.set_indicator("READY", "REFLEX LIMIT REACHED")
                    self.append_text(f"\n[🛡️ SAFETY: Loop Depth {self._reflex_count} Reached]\n")
                    self._reflex_count = 0
                    return

                self.set_indicator("WORKING", "REFLEX LOOPING...")
                self._reflex_count += 1

                feedback_text = "\n[SYSTEM_FEEDBACK]\n" + "\n".join(str(r) for r in results)
                self.append_text(f"\n{feedback_text}\n")

                auto_command = f"{feedback_text}\n[SYSTEM_AUTO] วิเคราะห์โค้ดหรือซ่อมแซมไฟล์ทันที"
                future = self.executor.submit(self._process_command, auto_command)
                
                def handle_reflex_result(f):
                    try: 
                        self.root.after(0, lambda: self._handle_ai_response(f.result()))
                    except Exception as e: 
                        self.root.after(0, lambda: self._handle_error(e))
                
                future.add_done_callback(handle_reflex_result)
            else:
                self.set_indicator("READY", "COMPLETED")
                self._reflex_count = 0 
                
        except Exception as e:
            self._handle_error(f"AI Response parsing error: {e}")

    def _handle_error(self, error):
        self.set_indicator("ERROR")
        self.append_text(f"[❌ Error] {error}\n")

    def append_text(self, text):
        self.output_box.insert(tk.END, text)
        self.output_box.see(tk.END)
        self.root.update_idletasks()

    # ========================================
    # UTILITY METHODS
    # ========================================
    def attach_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Files", "*.py *.txt *.*")])
        if file_path:
            self.attached_files.append(file_path)
            self.append_text(f"[📁 Attached] {os.path.basename(file_path)}\n")

    def open_web(self):
        self.web_station.open()
        self.append_text("[🌐 Web opened]\n")

    def close_web(self):
        self.web_station.close()

    def read_answer(self):
        try:
            content = self.output_box.get("1.0", tk.END)
            for line in reversed(content.split('\n')):
                if line.startswith("[🤖"):
                    vision_audio.speak(line.replace("[🤖 VISION]", "").replace("[🤖 JAMIE]", "").strip())
                    return self.append_text("[🔊 Reading]\n")
            self.append_text("[❌ No AI response]\n")
        except Exception as e:
            self.append_text(f"[❌ Read error: {e}]\n")

    def toggle_mic(self):
        self.voice_on = not self.voice_on
        self.append_text(f"[🎤 Voice {'ON' if self.voice_on else 'OFF'}]\n")

    def toggle_live(self):
        self.is_live = not self.is_live
        self.append_text(f"[🎥 Live Mode {'ON' if self.is_live else 'OFF'}]\n")
        self.live_service.start() if self.is_live else self.live_service.stop()

    def save_ui_output(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_box.get("1.0", tk.END))
                self.append_text(f"[💾 Saved]\n")
        except Exception: pass

    def _create_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Copy", command=lambda: widget.event_generate("<Control-c>"))
        menu.add_command(label="Paste", command=self._handle_paste)
        menu.add_command(label="Select All", command=lambda: widget.event_generate("<Control-a>"))
        widget.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))

    def _handle_copy(self):
        try: pyperclip.copy(self.input_box.selection_get())
        except Exception: pass

    def _handle_select_all(self):
        self.input_box.tag_add(tk.SEL, "1.0", tk.END)

    def _handle_cut(self):
        try:
            pyperclip.copy(self.input_box.selection_get())
            self.input_box.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except Exception: pass

    def _handle_paste(self):
        try: self.input_box.insert(tk.INSERT, pyperclip.paste())
        except Exception: pass

    def _manual_compact_memory(self):
        """Manual memory compaction triggered by user"""
        try:
            self.set_indicator("WORKING", "COMPACTING MEMORY")
            self.append_text(f"\n[Manual Memory Compaction]\n")
            
            # Perform compaction
            self.context_compactor.compact_history(CHAT_HISTORY_JSON)
            
            # Update dashboard
            self._update_context_dashboard()
            
            self.append_text(f"[Compaction complete]\n")
            self.set_indicator("READY")
            
        except Exception as e:
            self.append_text(f"[Compaction failed: {e}]\n")
            self.set_indicator("ERROR")

    def _show_memory_status(self):
        """Show current memory status"""
        try:
            # Read chat history
            if os.path.exists(CHAT_HISTORY_JSON):
                with open(CHAT_HISTORY_JSON, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # Calculate tokens
                history_text = json.dumps(history, ensure_ascii=False)
                memory_tokens = estimate_tokens(history_text)
                
                status = f"[Memory Status]\n"
                status += f"Current: {memory_tokens:,} tokens\n"
                
                if memory_tokens > 5000:
                    status += f"[Memory usage is high - consider compacting]\n"
                    status += f"Type '/compact' to compact memory\n"
                else:
                    status += f"[Memory usage is normal]\n"
                
                return status
            else:
                return "[No chat history found]"
                
        except Exception as e:
            return f"[Error checking memory status: {e}]"

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ProjectJAVIS()
    app.run()