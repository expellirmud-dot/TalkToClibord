# vision_live_service.py (V4.6 - Persistent Connection)
import asyncio, threading, io, base64, PIL.Image, time
from google.genai import types
from src.utils.vision_utils import sys_log

class VisionLiveService:
    def __init__(self, client, model_id, instr):
        self.client, self.model_id, self.instr = client, model_id, instr
        self.is_running = False
        try:
            import pyaudio
        except ImportError as e:
            raise RuntimeError(
                "Optional dependency 'pyaudio' is required for live audio. "
                "Install requirements-optional.txt to enable this feature."
            ) from e
        self._pyaudio = pyaudio
        self.p = pyaudio.PyAudio()
        self.chunk, self.send_rate, self.receive_rate = 1024, 16000, 24000
        self.audio_in_queue, self.out_queue = None, None

    def start(self, voice_name, app_instance, enable_vision=True):
        self.is_running = True
        threading.Thread(target=lambda: asyncio.run(self._live_loop(voice_name, enable_vision)), daemon=True).start()

    def stop(self): 
        self.is_running = False
        sys_log("Live", " ปิดท่อเสียงข่ะ")

    async def _live_loop(self, voice_name, enable_vision):
        start_time = time.time()
        sys_log("Live", f" เริ่ม Live Service ({voice_name})")
        
        config = types.LiveConnectConfig(
            system_instruction=self.instr,
            generation_config=types.GenerationConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name.split(' ')[0])
                ))
            )
        )
        try:
            connect_time = time.time()
            sys_log("Live", f" กำลังเชื่อมต่อ ({time.time() - start_time:.2f}s)")
            
            async with (self.client.aio.live.connect(model=self.model_id, config=config)) as session, asyncio.TaskGroup() as tg:
                connection_time = time.time() - connect_time
                sys_log("Live", f" เชื่อมต่อสำเร็จ ({connection_time:.2f}s)")
                
                self.audio_in_queue, self.out_queue = asyncio.Queue(), asyncio.Queue(maxsize=15)
                tg.create_task(self._send_realtime(session))
                tg.create_task(self._send_mic())
                tg.create_task(self._receive_loop(session))
                tg.create_task(self._play_audio())
                if enable_vision: tg.create_task(self._screen_loop())
                while self.is_running: await asyncio.sleep(0.5)
        except asyncio.CancelledError as e: sys_log("Live_Fatal", str(e))

    async def _receive_loop(self, session):
        start_time = time.time()
        sys_log("Live", "🎧 เริ่มรับข้อมูลจาก AI")
        
        try:
            async for response in session.receive():
                if not self.is_running: 
                    elapsed = time.time() - start_time
                    sys_log("Live", f"⏱️ หยุดการรับ ({elapsed:.2f}s)")
                    break
                if data := response.data: 
                    self.audio_in_queue.put_nowait(data)
                if text := response.text: 
                    print(f"💬 [Live]: {text}", end="\r")
        except Exception as e: 
            elapsed = time.time() - start_time
            sys_log("Live_Receive", f"❌ รับข้อมูลผิดพลาด ({elapsed:.2f}s): {str(e)}")

    async def _send_mic(self):
        start_time = time.time()
        sys_log("Live", "🎤 เริ่มส่งเสียงไมค์")
        
        try:
            stream = await asyncio.to_thread(self.p.open, format=self._pyaudio.paInt16, channels=1, rate=self.send_rate, input=True, frames_per_buffer=self.chunk)
            chunks_sent = 0
            while self.is_running:
                data = await asyncio.to_thread(stream.read, self.chunk, exception_on_overflow=False)
                try: 
                    self.out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
                    chunks_sent += 1
                except: pass
            stream.close()
            elapsed = time.time() - start_time
            sys_log("Live", f"🎤 หยุดส่งเสียง ({elapsed:.2f}s, {chunks_sent} chunks)")
        except Exception as e: 
            elapsed = time.time() - start_time
            sys_log("Live_Mic", f"❌ ส่งเสียงผิดพลาด ({elapsed:.2f}s): {str(e)}")

    async def _send_realtime(self, session):
        while self.is_running:
            try:
                msg = await asyncio.wait_for(self.out_queue.get(), timeout=1.0)
                await session.send(input=msg)
            except: continue

    async def _play_audio(self):
        start_time = time.time()
        sys_log("Live", "🔊 เริ่มเล่นเสียง AI")
        
        try:
            stream = self.p.open(format=self._pyaudio.paInt16, channels=1, rate=self.receive_rate, output=True)
            chunks_played = 0
            
            while self.is_running:
                try:
                    data = await asyncio.wait_for(self.audio_in_queue.get(), timeout=1.0)
                    stream.write(data)
                    chunks_played += 1
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    sys_log("Live_PlayAudio", str(e))
            stream.close()
            elapsed = time.time() - start_time
            sys_log("Live", f"🔊 หยุดเล่นเสียง ({elapsed:.2f}s, {chunks_played} chunks)")
        except Exception as e:
            elapsed = time.time() - start_time
            sys_log("Live_PlayAudio", f"❌ เล่นเสียงผิดพลาด ({elapsed:.2f}s): {str(e)}")

    async def _screen_loop(self):
        import mss
        start_time = time.time()
        sys_log("Live", "📸 เริ่มจับภาพหน้าจอ")
        
        screenshots_taken = 0
        while self.is_running:
            try:
                with mss.mss() as sct:
                    i = sct.grab(sct.monitors[0])
                    img = PIL.Image.frombytes("RGB", i.size, i.bgra, "raw", "BGRX")
                    img.thumbnail([1024, 1024])
                    buf = io.BytesIO(); img.save(buf, format="jpeg", quality=80); buf.seek(0)
                    self.out_queue.put_nowait({"mime_type": "image/jpeg", "data": base64.b64encode(buf.read()).decode()})
                    screenshots_taken += 1
            except Exception as e:
                sys_log("Screen_Capture", str(e))
            await asyncio.sleep(1.0)
        
        elapsed = time.time() - start_time
        sys_log("Live", f"📸 หยุดจับภาพ ({elapsed:.2f}s, {screenshots_taken} screenshots)")
