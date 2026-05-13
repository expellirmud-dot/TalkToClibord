# vision_ai_service.py (V5.0.0 - Detox Edition - Clean Pipe)
from google import genai
from google.genai import types
import time, json, sys, os, threading, asyncio, re, glob

from src.utils.vision_utils import sys_log, estimate_tokens, log_token_usage
from vision_config import MODELS_CONFIG, FALLBACK_CHAIN, INSTR_VISION_ULTIMATE, INSTR_JAMIE
from src.api.vision_api_manager import VisionAPIClient

class VisionAIService:
    def __init__(self, api_key):
        # Use centralized VisionAPIClient (Single Source of Truth)
        self.api_client = VisionAPIClient(api_key)
        # Keep direct client for backward compatibility
        self.client = self.api_client.client

    def process_request(self, query, context=None, identity="VISION", model="vision"):
        """Process request with AI (wrapper for ask_stream)"""
        # Select instruction based on identity
        if identity == "JAMIE":
            instr = INSTR_JAMIE
        else:
            instr = INSTR_VISION_ULTIMATE
        
        # Call ask_stream and collect all chunks
        response_stream, model_id = self.ask_stream(
            model_key=model,
            question=query,
            instr=instr,
            context=context
        )
        
        # Collect all text from stream
        full_response = ""
        for chunk in response_stream:
            full_response += chunk
        
        return full_response

    def _check_instruction_support(self, model_id):
        """ตรวจสอบว่าโมเดลรองรับ System Instruction หรือไม่ (Gemma ไม่รองรับ)"""
        return "gemma" not in model_id.lower()

    def _prepare_prompt(self, question, context):
        """รวม Context และ Question เข้าด้วยกัน"""
        if context and len(str(context).strip()) > 0:
            return f"{context}\n\n{question}"
        return question

    def _execute_request(self, model_id, prompt, instr, image=None, config=None, stream=True):
        """
        Core Engine สำหรับเรียก API ของ GenAI 
        รองรับทั้งแบบ Stream และ Non-Stream ในที่เดียว (DRY Principle)
        
        สำหรับ Gemma: ดึง system_instruction ออกและต่อหัว contents แทน
        """
        p_temp = config.get("temp", 0.7) if config else 0.7
        p_top_p = config.get("top_p", 0.95) if config else 0.95
        supports_instruction = self._check_instruction_support(model_id)

        gen_config = types.GenerateContentConfig(
            temperature=p_temp, 
            top_p=p_top_p
        )
        
        # จัดการ contents สำหรับ Gemma (ไม่รองรับ system_instruction)
        if supports_instruction and instr:
            gen_config.system_instruction = instr
            contents = [image, prompt] if image else [prompt]
        elif not supports_instruction and instr:
            # Gemma: ต่อ system_instruction เข้ากับ prompt
            combined_prompt = f"{instr}\n\n{prompt}"
            contents = [image, combined_prompt] if image else [combined_prompt]
        else:
            contents = [image, prompt] if image else [prompt]

        if stream:
            return self.client.models.generate_content_stream(
                model=model_id,
                config=gen_config,
                contents=contents
            )
        else:
            return self.client.models.generate_content(
                model=model_id,
                config=gen_config,
                contents=contents
            )

    def ask_stream(self, model_key, question, instr, context=None, image=None, config=None):
        """
        Clean Pipe: รับ context และ question มาใช้งานโดยตรง
        ไม่มีการแสกนไฟล์ซ้ำภายในฟังก์ชันนี้
        """
        start_time = time.time()
        current_key = model_key if model_key in MODELS_CONFIG else "lite"
        target_id = MODELS_CONFIG[current_key]["id"]
        
        # รวม Context และ Question (Manager จัดการ context ให้เสร็จก่อนส่งมา)
        prompt_body = self._prepare_prompt(question, context)
        
        # 2. Token & Context Management
        estimated_tokens = estimate_tokens(prompt_body)
        model_config = MODELS_CONFIG.get(current_key, {})
        max_tokens = model_config.get("max_input_tokens", 16000)
        context_buffer = model_config.get("context_buffer", 4000)
        
        sys_log("AI_Service", f"📊 Context: {estimated_tokens:,} tokens (limit: {max_tokens:,})")

        # จัดการกรณี Context เกิน
        if estimated_tokens > (max_tokens - context_buffer):
            sys_log("AI_Service", f"⚠️ Context too large, triggering truncation", "WARNING")
            
            def warning_generator():
                yield f"⚠️ Context ใหญ่เกินไปสำหรับโมเดล {current_key}\n"
                yield f"📊 ขนาด: {estimated_tokens:,} tokens (limit: {max_tokens - context_buffer:,})\n"
                yield f"🔄 ระบบกำลังตัดทอนข้อมูลเพื่อให้ทำงานต่อได้...\n\n"

            # Truncate context
            if context:
                reduced_context = str(context)[:8000] + "\n\n[CONTEXT TRUNCATED]"
                prompt_body = self._prepare_prompt(question, reduced_context)
            
            # สร้าง Wrapper Generator เพื่อส่งคำเตือนก่อนแล้วตามด้วย AI Response
            def wrapped_stream():
                yield from warning_generator()
                try:
                    response_stream = self._execute_request(target_id, prompt_body, instr, image, config, stream=True)
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                except Exception as e:
                    yield f"\n❌ เกิดข้อผิดพลาดขณะประมวลผล: {e}"

            return wrapped_stream(), target_id

        # 3. Main Execution with Fallback
        try:
            sys_log("AI_Service", f"🚀 Sending to: {target_id} | Mode: {current_key}")
            response_stream = self._execute_request(target_id, prompt_body, instr, image, config, stream=True)
            
            if response_stream is None:
                raise Exception("API returned None generator")
                
            connect_time = time.time() - start_time
            sys_log("AI_Service", f"✅ Connected ({connect_time:.2f}s)")
            
            # แปลง response_stream ให้เป็น generator ของ text เพื่อความง่ายในการใช้งานภายนอก
            def text_only_stream():
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
            
            return text_only_stream(), target_id

        except Exception as e:
            return self._handle_stream_fallback(e, current_key, prompt_body, instr, image, config)

    def _handle_stream_fallback(self, error, current_key, prompt_body, instr, image, config):
        """ระบบจัดการ Fallback สำหรับ Stream (เมื่อโมเดลหลักล้มเหลว)"""
        error_msg = str(error).lower()
        target_id = MODELS_CONFIG.get(current_key, {}).get("id", "unknown")
        sys_log("Fallback", f"🔄 {current_key} Error: {error}")

        # Rate Limit Handling
        if any(kw in error_msg for kw in ["429", "resource_exhausted", "quota"]):
            retry_match = re.search(r'retry in ([\d.]+)s', error_msg)
            wait_time = float(retry_match.group(1)) if retry_match else 30.0
            sys_log("RATE_LIMIT", f"⚠️ Rate limit hit. Waiting {wait_time:.1f}s", "WARNING")
            
            def rate_limit_stream():
                yield f"⚠️ Rate Limit: ใกล้เกินขีดจำกัด\n🔄 ระบบจะรอ {wait_time:.0f} วินาทีแล้วลองใหม่\n"
            return rate_limit_stream(), target_id

        # Safety Filter
        if any(kw in error_msg for kw in ["safety", "blocked", "prompt"]):
            def safety_stream():
                yield "❌ ยกเลิกการประมวลผล: พร้อมต์ติดกรองคำหรือระบบรักษาความปลอดภัย"
            return safety_stream(), target_id

        # Fallback Chain Logic
        fallback_key = FALLBACK_CHAIN.get(current_key)
        if fallback_key and fallback_key in MODELS_CONFIG:
            sys_log("Fallback", f"🔄 Switching to fallback model: {fallback_key}", "WARNING")
            
            def fallback_stream_wrapper():
                yield f"⚠️ โมเดล {current_key} ขัดข้อง กำลังสลับไปใช้ {fallback_key}...\n\n"
                try:
                    fb_id = MODELS_CONFIG[fallback_key]["id"]
                    response_stream = self._execute_request(fb_id, prompt_body, instr, image, config, stream=True)
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                except Exception as fb_error:
                    yield f"\n❌ Fallback ล้มเหลวเช่นกัน: {fb_error}"
            
            return fallback_stream_wrapper(), MODELS_CONFIG[fallback_key]["id"]

        # Final Error
        def final_error_stream():
            yield f"❌ เกิดข้อผิดพลาดร้ายแรงและไม่มีโมเดลสำรอง: {error}"
        return final_error_stream(), target_id

    def ask(self, model_key, question, instr, context=None, image=None, config=None):
        """
        ฟังก์ชันสำหรับการเรียก API แบบ Non-Streaming 
        (ใช้เป็น Fallback ใน newVision.py เมื่อ Stream ล้มเหลว)
        """
        start_time = time.time()
        current_key = model_key if model_key in MODELS_CONFIG else "lite"
        target_id = MODELS_CONFIG[current_key]["id"]
        
        prompt_body = self._prepare_prompt(question, context)
        
        try:
            sys_log("AI_Service", f"🚀 Sending (Non-Stream) to: {target_id} | Mode: {current_key}")
            response = self._execute_request(target_id, prompt_body, instr, image, config, stream=False)
            
            process_time = time.time() - start_time
            sys_log("AI_Service", f"✅ Completed ({process_time:.2f}s)")
            
            return response.text, target_id

        except Exception as e:
            return self._handle_fallback(e, current_key, prompt_body, instr, image, config)

    def _handle_fallback(self, error, current_key, prompt_body, instr, image, config):
        """ระบบจัดการ Fallback สำหรับ Non-Stream"""
        error_msg = str(error).lower()
        sys_log("Fallback", f"🔄 Non-Stream Error ({current_key}): {error}")

        if any(kw in error_msg for kw in ["safety", "blocked", "prompt"]):
            return "❌ ยกเลิกการประมวลผล: พร้อมต์ติดกรองคำหรือระบบรักษาความปลอดภัย", "error"

        fallback_key = FALLBACK_CHAIN.get(current_key)
        if fallback_key and fallback_key in MODELS_CONFIG:
            sys_log("Fallback", f"🔄 Switching to fallback model: {fallback_key}", "WARNING")
            try:
                fb_id = MODELS_CONFIG[fallback_key]["id"]
                response = self._execute_request(fb_id, prompt_body, instr, image, config, stream=False)
                return f"[⚠️ สลับใช้โมเดลสำรอง {fallback_key}]\n\n{response.text}", fb_id
            except Exception as fb_error:
                return f"❌ Fallback ล้มเหลว: {fb_error}", "error"

        return f"❌ เกิดข้อผิดพลาด: {error}", "error"