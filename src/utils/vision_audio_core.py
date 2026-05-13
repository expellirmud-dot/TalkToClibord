# vision_audio_core.py (V6.0 - Streaming In-Memory Edition)
import os
import asyncio
import edge_tts
import threading
import time
import re
import io
from queue import Queue
from abc import ABC, abstractmethod
from typing import Optional
from src.utils.vision_utils import sys_log
from src.utils.vision_processor import VisionProcessor  # 🔗 เชื่อมสายสัญญาณข่ะ!

# ==========================================
# STRATEGY PATTERN: TTS Provider Interface
# ==========================================
class TTSProvider(ABC):
    @abstractmethod
    async def generate_audio(self, text: str, voice: str, output_file: str):
        pass

class EdgeTTSProvider(TTSProvider):
    """[UPGRADED] ปรับแต่งตามสั่ง: Rate -9%, Pitch +10Hz"""
    async def generate_audio(self, text: str, voice: str, output_file: str):
        communicate = edge_tts.Communicate(
            text, 
            voice, 
            rate="-9%",
            pitch="+10Hz"
        )
        await communicate.save(output_file)

# ==========================================
# VisionAudioCore - Main Audio System
# ==========================================
class VisionAudioCore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VisionAudioCore, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, app=None):
        if self._initialized: return
        self.app = app
        self.tts_queue = Queue()
        
        # 🧠 ติดตั้งสมองส่วนภาษา (Processor)
        self.processor = VisionProcessor()
        
        # 🎙️ ตั้งค่าเสียง Premwadee
        self.provider = EdgeTTSProvider()
        self.default_voice = "th-TH-PremwadeeNeural"
        self._pygame = None
        
        try:
            self._pygame = self._load_pygame()
            self._pygame.mixer.init()
            self.audio_available = True
            sys_log("AudioCore", "Pygame mixer readyข่ะ!")
        except Exception as e:
            sys_log("AudioCore", f"Mixer failed: {e}", "ERROR")
            self.audio_available = False
            
        threading.Thread(target=self._tts_worker, daemon=True).start()
        self._initialized = True

    def _split_into_chunks(self, text: str, max_len: int = 80, min_len: int = 30) -> list:
        """[STREAMING] แบ่งข้อความตามจุดพักธรรมชาติ (ไม่ตัดกลางคำ/ประโยค)"""
        if len(text) <= max_len:
            return [text] if text.strip() else []
        
        chunks = []
        current = ""
        
        # จุดพักที่เหมาะสมกับภาษาไทยและอังกฤษ
        delimiters = ['. ', '! ', '? ', '。', '！', '？', '\n', 'ๆ ', ' ']  # เรียงตาม priority
        
        i = 0
        while i < len(text):
            current += text[i]
            i += 1
            
            # เช็คว่าถึงจุดพักหรือเกิน max_len
            should_split = False
            
            if len(current) >= max_len:
                should_split = True
            elif len(current) >= min_len:
                # เช็คว่าอยู่ที่จุดพักหรือไม่
                for delim in delimiters:
                    if current.endswith(delim):
                        should_split = True
                        break
            
            if should_split and current.strip():
                chunks.append(current.strip())
                current = ""
        
        # เศษที่เหลือ
        if current.strip():
            chunks.append(current.strip())
        
        return chunks if chunks else [text]

    def speak(self, text, is_vision=False):
        """[STREAMING] แบ่งข้อความเป็น chunks แล้วส่งต่อคิวข่ะ"""
        if not self.audio_available or not text.strip(): return
        
        # 🧪 ขั้นตอนการปรุงแต่งเสียง:
        # 1. ใช้สมองของ VisionProcessor จัดการคำอ่านภาษาอังกฤษและลบอักขระพิเศษ (รวมถึง code blocks)
        clean_text = self.processor.clean_for_speech(text)
        
        if not clean_text.strip(): return
        
        # 2. แบ่งเป็น chunks ตามจุดพักประโยค (optimized: max=50, min=20)
        chunks = self._split_into_chunks(clean_text, max_len=50, min_len=20)
        
        # 3. ส่งแต่ละ chunk เข้าคิว (streaming queue)
        for chunk in chunks:
            self.tts_queue.put(chunk)
            sys_log("TTS", f"Queued ({len(chunk)} chars): {chunk[:40]}...")

    def _tts_worker(self):
        """[IN-MEMORY] พนักงานปั่นเสียงแบบไม่เขียนดิสก์ข่ะ"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            text = self.tts_queue.get()
            try:
                # 🔥 สร้างเสียงใน memory (BytesIO) แทนการเขียนไฟล์
                audio_buffer = io.BytesIO()
                
                # ใช้ edge-tts สตรีมเสียงเข้า buffer
                communicate = edge_tts.Communicate(
                    text, self.default_voice, rate="-9%", pitch="+10Hz"
                )
                
                async def stream_to_buffer():
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_buffer.write(chunk["data"])
                
                loop.run_until_complete(stream_to_buffer())
                
                # เล่นจาก memory ถ้ามีข้อมูล
                audio_buffer.seek(0)
                if audio_buffer.getbuffer().nbytes > 0:
                    # 🔊 ใช้ pygame Sound เล่นจาก buffer (ไม่ใช่ music ซึ่งต้องการไฟล์)
                    sound = self._pygame.mixer.Sound(file=audio_buffer)
                    channel = sound.play()
                    
                    # รอจนเสียงจบ (ใช้ channel.get_busy() แทน)
                    while channel and channel.get_busy():
                        time.sleep(0.03)
                
            except Exception as e:
                sys_log("TTS_Worker", f"Error: {e}", "ERROR")
            finally:
                self.tts_queue.task_done()

    def stop(self):
        """[IN-MEMORY] หยุดทันทีข่ะ!"""
        # หยุดทุกเสียงที่กำลังเล่น (Sound ทั้งหมด)
        if self._pygame:
            self._pygame.mixer.stop()
        # ล้างคิว
        with self.tts_queue.mutex:
            self.tts_queue.queue.clear()

    @staticmethod
    def _load_pygame():
        try:
            import pygame
            return pygame
        except ImportError as e:
            raise RuntimeError(
                "Optional dependency 'pygame' is required for audio playback. "
                "Install requirements-optional.txt to enable this feature."
            ) from e

# Singleton Instance
vision_audio = VisionAudioCore()
