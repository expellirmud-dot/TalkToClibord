# vision_stt_service.py (V2.1 - Path Optimized & Multi-Engine)
# STT Service สำหรับ J.A.V.I.S. - ปรับแต่ง Path ให้ยึดโยงกับระบบกลางข่ะ

import threading
import time
import pyperclip
import speech_recognition as sr
from typing import Callable, Optional, Literal
from queue import Queue, Empty
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.vision_processor import VisionProcessor
from src.utils.vision_utils import sys_log
from src.utils.vision_paths import ROOT_DIR  # [FIXED] นำเข้าพิกัดรากของระบบข่ะ

# Optional imports for alternative engines (lazy loaded)
_whisper_available = False
_vosk_available = False
try:
    import whisper
    _whisper_available = True
except ImportError:
    pass
try:
    from vosk import Model, KaldiRecognizer
    _vosk_available = True
except ImportError:
    pass


class VisionSTTService:
    """Speech-to-Text Service V2.1 - แก้ไข Hardcoded Path และรองรับ Multi-Engine ข่ะ"""
    
    def __init__(self, 
                 on_text_callback: Optional[Callable[[str], None]] = None,
                 on_status_callback: Optional[Callable[[str], None]] = None,
                 engine: Literal["google", "whisper", "vosk"] = "google",
                 whisper_model: str = "small"):
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # ปรับแต่งค่าสำหรับรับประโยคครบถ้วน
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.energy_threshold = 300
        
        self.processor = VisionProcessor()
        self.on_text_callback = on_text_callback
        self.on_status_callback = on_status_callback
        
        self.audio_queue = Queue()
        self.text_queue = Queue()
        self.processing_thread = None
        
        self.is_listening = False
        self.is_continuous_mode = False
        self.listen_thread = None
        
        self.engine = engine
        self.whisper_model_name = whisper_model
        self.whisper_model = None
        self.vosk_model = None
        self._init_engine()
        
        self._calibrate_microphone()
        
        self._microphone_lock = threading.Lock()
        self._mode_lock = threading.Lock()
        self._quiet_mode = False
        
        self._start_processing_thread()
        
        sys_log("STT", f"VisionSTTService V2.1 initialized (Engine: {engine}) ข่ะ!")
    
    def _init_engine(self):
        """Initialize selected STT engine"""
        if self.engine == "whisper" and _whisper_available:
            try:
                sys_log("STT", f"Loading Whisper model: {self.whisper_model_name}...")
                self.whisper_model = whisper.load_model(self.whisper_model_name)
                sys_log("STT", "Whisper model loaded!")
            except Exception as e:
                sys_log("STT", f"Whisper load error: {e}, falling back to Google", "ERROR")
                self.engine = "google"
        
        elif self.engine == "vosk" and _vosk_available:
            try:
                # [FIXED] เปลี่ยนจาก Hardcoded Relative Path เป็นพิกัดจาก ROOT_DIR ข่ะบอส
                model_path = os.path.join(ROOT_DIR, "models", "vosk-model-thai")
                
                if os.path.exists(model_path):
                    sys_log("STT", f"Loading Vosk model from: {model_path}")
                    self.vosk_model = Model(model_path)
                    sys_log("STT", "Vosk model loaded successfully!")
                else:
                    sys_log("STT", f"Vosk model not found at {model_path}, falling back to Google", "ERROR")
                    self.engine = "google"
            except Exception as e:
                sys_log("STT", f"Vosk load error: {e}, falling back to Google", "ERROR")
                self.engine = "google"
    
    def _calibrate_microphone(self):
        try:
            with self.microphone as source:
                sys_log("STT", "กำลัง callibrate microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                sys_log("STT", "Microphone callibrate เสร็จแล้วข่ะ!")
        except Exception as e:
            sys_log("STT", f"Microphone calibration error: {e}", "ERROR")
    
    def _start_processing_thread(self):
        self.processing_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
        self.processing_thread.start()
    
    def _process_audio_queue(self):
        while True:
            try:
                audio_data = self.audio_queue.get(timeout=0.5)
                if audio_data is None: break
                
                text = self._recognize_audio(audio_data)
                if text:
                    self.text_queue.put(text)
                    self._process_recognized_text(text, auto_send=True)
            except Empty: continue
            except Exception as e:
                sys_log("STT", f"Processing error: {e}", "ERROR")
    
    def _recognize_audio(self, audio) -> Optional[str]:
        try:
            if self.engine == "whisper" and self.whisper_model:
                import numpy as np
                import io
                import wave
                wav_data = io.BytesIO(audio.get_wav_data())
                with wave.open(wav_data, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                result = self.whisper_model.transcribe(audio_np, language='th')
                return result["text"].strip()
            elif self.engine == "vosk" and self.vosk_model:
                recognizer = KaldiRecognizer(self.vosk_model, 16000)
                wav_data = audio.get_wav_data()
                if recognizer.AcceptWaveform(wav_data):
                    import json
                    result = json.loads(recognizer.Result())
                    return result.get("text", "").strip()
            else:
                return self.recognizer.recognize_google(audio, language='th-TH')
        except Exception: return None
    
    def _fix_stt_text(self, text: str) -> str:
        return self.processor.fix_stt_text(text)
    
    def _process_recognized_text(self, text: str, auto_send: bool = True):
        if not text or not text.strip(): return
        fixed_text = self._fix_stt_text(text)
        try:
            pyperclip.copy(fixed_text)
            if not getattr(self, '_quiet_mode', False):
                sys_log("STT", f"Copied to clipboard: {fixed_text[:50]}...")
        except Exception: pass
        if self.on_status_callback:
            self.on_status_callback(f"[STT] {fixed_text}")
        if auto_send and self.on_text_callback and fixed_text.strip():
            control_commands = ['หยุด', 'ปิด', 'stop', 'exit']
            if not any(cmd in fixed_text.lower() for cmd in control_commands):
                self.on_text_callback(fixed_text)
    
    def start_continuous_mode(self):
        with self._mode_lock:
            if self.is_listening:
                self.stop_listening_mode()
                return
            if self.listen_thread and self.listen_thread.is_alive():
                self.listen_thread.join(timeout=1.0)
            self.is_listening = True
            self.is_continuous_mode = True
            self._quiet_mode = True 
        if self.on_status_callback:
            self.on_status_callback("[STT] เริ่มฟังต่อเนื่อง... (กด Alt+X เพื่อหยุด)")
        self.listen_thread = threading.Thread(target=self._continuous_listen_loop, daemon=True)
        self.listen_thread.start()
    
    def _continuous_listen_loop(self):
        while self.is_listening and self.is_continuous_mode:
            try:
                with self._microphone_lock:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=None)
                self.audio_queue.put(audio)
            except Exception: time.sleep(0.1)
    
    def start_quick_mode(self):
        with self._mode_lock:
            if self.is_listening: return
            if self.listen_thread and self.listen_thread.is_alive():
                self.listen_thread.join(timeout=1.0)
            self.is_listening = True
            self.is_continuous_mode = False
            self._quiet_mode = False
        if self.on_status_callback:
            self.on_status_callback("[STT] ฟังระยะสั้น... (F9)")
        self.listen_thread = threading.Thread(target=self._quick_listen_once, daemon=True)
        self.listen_thread.start()
    
    def _quick_listen_once(self):
        try:
            with self._microphone_lock:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=None)
            self.audio_queue.put(audio)
        except Exception: pass
        finally:
            with self._mode_lock:
                self.is_listening = False
    
    def stop_listening_mode(self):
        self.is_listening = False
        self.is_continuous_mode = False
        if self.on_status_callback:
            self.on_status_callback("[STT] หยุดฟังแล้ว")
    
    def toggle_continuous_mode(self):
        if self.is_listening and self.is_continuous_mode: self.stop_listening_mode()
        else: self.start_continuous_mode()
    
    def is_active(self) -> bool: return self.is_listening

_stt_service = None
def get_stt_service(on_text_callback=None, on_status_callback=None):
    global _stt_service
    if _stt_service is None:
        _stt_service = VisionSTTService(on_text_callback, on_status_callback)
    else:
        if on_text_callback: _stt_service.on_text_callback = on_text_callback
        if on_status_callback: _stt_service.on_status_callback = on_status_callback
    return _stt_service