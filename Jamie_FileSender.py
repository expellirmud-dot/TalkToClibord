
import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import re
import ast
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- [J.A.V.I.S. UTILS & PATHS] ---
try:
    from src.utils.vision_utils import sys_log
    from src.utils.vision_paths import ROOT_DIR, LOG_TXT, JAVIS_MD, VAULT_JSON, CACHE_DIR
except ImportError:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_TXT = os.path.join(ROOT_DIR, "data", "logs", "log.txt")
    JAVIS_MD = os.path.join(ROOT_DIR, "data", "config", "JAVIS.md")
    VAULT_JSON = os.path.join(ROOT_DIR, "data", "config", "vault.json")
    CACHE_DIR = os.path.join(ROOT_DIR, "data", "cache")
    def sys_log(tag, msg): print(f"[{tag}] {msg}")

# --- [VISION HAND SERVICE V3.3] ---
class VisionHandService:
    def __init__(self, base_dir=None):
        self.base_dir = str(base_dir) if base_dir else str(ROOT_DIR)

    def save_file(self, target_path, content):
        """[AUTO-SAVE] บันทึกโค้ดลงเครื่องบอสทันทีข่ะ[cite: 5]"""
        try:
            full_path = os.path.join(self.base_dir, target_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Auto-Saved to {target_path}"
        except Exception as e:
            return f"❌ Save Error: {str(e)}"

# --- [UI: SUPREME COMMANDER] ---
class JamieFileSender(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jamie : J.A.V.I.S. Supreme Commander V3.3")
        self.geometry("800x950")
        self.attributes("-alpha", 0.98)
        ctk.set_appearance_mode("light")
        
        self.hands = VisionHandService()
        self.selected_files = []
        self.setup_ui()

    def setup_ui(self):
        # Header มินิมอลขาวสะอาดตามสไตล์บอส
        ctk.CTkLabel(self, text="J a m i E | S E N D E R", font=("Segoe UI", 26, "bold"), text_color="#2c3e50").pack(pady=20)

        # File Panel
        self.file_frame = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=15)
        self.file_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.file_frame, text="เลือกไฟล์ (Multi-Selection)", command=self.browse_files, 
                       fg_color="#3498db", hover_color="#2980b9").pack(pady=10)
        
        self.file_list_label = ctk.CTkLabel(self.file_frame, text="ยังไม่ได้เลือกไฟล์", font=("Leelawadee UI", 12))
        self.file_list_label.pack(pady=(0, 10))

        # Command Area
        ctk.CTkLabel(self, text="Supreme Command / คำถาม:", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=45)
        self.prompt_entry = ctk.CTkTextbox(self, width=710, height=120, font=("Leelawadee UI", 14), border_width=1)
        self.prompt_entry.pack(pady=10)
        self.prompt_entry.insert("0.0", "เจมี่คะ ช่วยสรุปข้อมูลหรือแก้ไขโค้ดจากไฟล์เหล่านี้ให้หน่อยค่ะ")

        # Backend Status[cite: 5]
        ctk.CTkLabel(self, text="Backend Logs & AI Analysis:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=45)
        self.res_box = ctk.CTkTextbox(self, width=710, height=300, font=("Consolas", 12), border_width=1, fg_color="#1e1e1e", text_color="#dcdcdc")
        self.res_box.pack(pady=5)
        
        self.status_lbl = ctk.CTkLabel(self, text="● READY", font=("Segoe UI", 14, "bold"), text_color="#27ae60")
        self.status_lbl.pack(pady=5)

        # ปุ่มเริ่มงานที่ใช้ Logic จากไฟล์ 7
        self.send_btn = ctk.CTkButton(self, text="SEND TO JAMIE", command=self.start_process, 
                                       width=300, height=60, font=("Segoe UI", 18, "bold"), fg_color="#2c3e50")
        self.send_btn.pack(pady=20)

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.res_box.insert("end", f"[{timestamp}] {msg}\n")
        self.res_box.see("end")

    def browse_files(self):
        files = filedialog.askopenfilenames(title="เลือกไฟล์")
        if files:
            self.selected_files = list(files)
            self.file_list_label.configure(text=f"📂 เลือกแล้ว {len(self.selected_files)} ไฟล์ข่ะ", text_color="#2c3e50")

    def start_process(self):
        if not self.selected_files:
            self.status_lbl.configure(text="● ⚠️ กรุณาเลือกไฟล์ก่อน!", text_color="#e74c3c")
            return
        self.send_btn.configure(state="disabled", text="TUNNELING...")
        threading.Thread(target=self.automation_worker, daemon=True).start()

    def automation_worker(self):
        prompt = self.prompt_entry.get("0.0", "end").strip()
        self.status_lbl.configure(text="● CONNECTING TO JAMIE...", text_color="#3498db")
        
        PATH_BASE = os.path.dirname(os.path.abspath(__file__))
        AUTOMATION_PROFILE = os.path.join(PATH_BASE, "automation_profile")
        TARGET_URL = "https://gemini.google.com/app/0d6926fe873e2abd"

        result = self.run_automation(self.selected_files, prompt, AUTOMATION_PROFILE, TARGET_URL)
        self.after(0, self.update_ui, result)

    def run_automation(self, file_paths, prompt_text, profile_dir, target_url):
        """[CORE LOGIC] ผสานความกริบจากไฟล์ 7"""
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir, headless=False, slow_mo=800
                )
                page = browser.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                self.log("Opening plus menu...")
                # 1. เช็คและเปิดเมนูบวก[cite: 7]
                plus_btn = page.locator('button:has(mat-icon[fonticon="add_2"])').first
                if plus_btn.get_attribute("aria-expanded") != "true":
                    plus_btn.click()
                
                self.log("Uploading files...")
                # 2. ส่งไฟล์ทั้งหมด[cite: 7]
                upload_option = page.locator('button[data-test-id="local-images-files-uploader-button"]')
                with page.expect_file_chooser() as fc_info:
                    upload_option.click()
                fc_info.value.set_files(file_paths)
                
                self.log("Sending command...")
                # 3. ใส่ Prompt และส่ง[cite: 7]
                page.locator('div[role="textbox"]').fill(prompt_text)
                page.locator('button:has(mat-icon[fonticon="send"])').click()

                self.log("Waiting for J.A.V.I.S. to reply...")
                # 4. รอจนปุ่มไมค์กลับมา (สัญญาณจบงานที่แม่นที่สุด)[cite: 7]
                mic_selector = 'button[data-node-type="speech_dictation_mic_button"]'
                page.wait_for_selector(mic_selector, state="visible", timeout=180000)
                
                return page.locator("message-content").last.inner_text()
            except Exception as e:
                return f"Error: {str(e)}"
            finally:
                if 'browser' in locals(): browser.close()

    def update_ui(self, result):
        self.send_btn.configure(state="normal", text="SEND TO JAMIE")
        self.log("Response Received. Checking triggers...")
        self.res_box.delete("0.0", "end")
        self.res_box.insert("0.0", result)
        
        # [SAVE TRIGGER] ดักจับโค้ดอัตโนมัติ[cite: 5]
        save_pattern = r"\[save_code\]\s*([\w\._/\\\-]+)\s*\n*```(?:python)?\n?(.*?)\n*```"
        save_match = re.search(save_pattern, result, re.DOTALL | re.IGNORECASE)
        if save_match:
            file_name, code = save_match.group(1).strip(), save_match.group(2).strip()
            save_res = self.hands.save_file(file_name, code)
            self.log(f"TRIGGERED: {save_res}")
            self.status_lbl.configure(text=f"● {save_res}", text_color="#27ae60")
        else:
            self.status_lbl.configure(text="● MISSION COMPLETED", text_color="#27ae60")

if __name__ == "__main__":
    app = JamieFileSender()
    app.mainloop()
