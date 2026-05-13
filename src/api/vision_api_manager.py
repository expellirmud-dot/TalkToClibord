# vision_api_manager.py (V1.1 - Centralized API Connection)
import time
from google import genai
from google.genai import types
from src.utils.vision_utils import sys_log
from vision_config import MODELS_CONFIG, FALLBACK_CHAIN, get_model_for_identity

class SafeGenerator:
    """
    Protect generator from multiple consumption by caching results.
    Fixes: Removed [Chunk X] markers and None-string concatenation.
    """

    def __init__(self, generator):
        self._generator = generator
        self._cache = []
        self._consumed = False

    def __iter__(self):
        # If already consumed, yield from cache
        if self._consumed:
            for item in self._cache:
                yield item
            return

        # Consume generator and cache results
        try:
            for chunk in self._generator:
                # Filter out None values to prevent "NoneNoneNone" strings
                if chunk is not None:
                    # Extract text if chunk is a GenAI response object, otherwise use as is
                    text = self._extract_text(chunk)
                    # Debug: log chunk info if text is empty
                    if not text:
                        print(f"[SafeGenerator] Empty text from chunk type: {type(chunk)}, str: {str(chunk)[:100]}")
                    if text:
                        self._cache.append(text)
                        yield text
        finally:
            self._consumed = True

    def _extract_text(self, chunk):
        """Helper to extract text from various GenAI chunk formats"""
        try:
            # Handle GenAI response objects with candidates/content/parts structure
            if hasattr(chunk, 'candidates') and chunk.candidates:
                text_parts = []
                for candidate in chunk.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                # Skip thought parts (internal reasoning)
                                if hasattr(part, 'thought') and part.thought:
                                    continue
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                if text_parts:
                    return ''.join(text_parts)
            # Handle simple text attribute
            if hasattr(chunk, 'text'):
                return chunk.text
            # Handle dict with text key
            if isinstance(chunk, dict) and 'text' in chunk:
                return chunk['text']
            # Handle plain string
            if isinstance(chunk, str):
                return chunk
        except Exception:
            return None
        return None

class VisionAPIClient:
    """Centralized Client to prevent redundant imports and connections"""
    
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta", timeout=600000))
        self.last_error = None
        sys_log("VisionAPIClient", "initialized successfully")

    def get_model_config(self, identity):
        """Get model configuration for identity"""
        return get_model_for_identity(identity)

    def generate_content(self, model_id, prompt, config=None):
        """Non-streaming content generation"""
        try:
            response = self.client.models.generate_content(
                model=model_id,
                config=config,
                contents=[prompt]
            )
            return response
        except Exception as e:
            sys_log("VisionAPIClient", f"API Error: {str(e)}")
            return None

    def stream_content(self, model_id, prompt, config=None):
        """Streaming content generation"""
        try:
            response = self.client.models.generate_content_stream(
                model=model_id,
                config=config,
                contents=[prompt]
            )
            return SafeGenerator(response)
        except Exception as e:
            sys_log("VisionAPIClient", f"Streaming Error: {str(e)}")
            return None

class APIConnectionManager:
    """Unified API connection management (Legacy - kept for compatibility)"""
    
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta", timeout=600000))
        self.last_error = None
        
    def stream_request(self, context, model_key="VISION", temperature=0.7, top_p=0.95):
        """Safe streaming request without debug consumption"""
        start_time = time.time()
        
        # Convert identity to model key (handles both "VISION" and "vision")
        current_key = get_model_for_identity(model_key) if model_key in ["JAMIE", "VISION", "PRO"] else model_key
        if current_key not in MODELS_CONFIG:
            current_key = "lite"
        model_id = MODELS_CONFIG[current_key]["id"]
        
        sys_log("API", f"Starting stream to {model_id}", "INFO")
        
        try:
            # Create stream without debug tests
            response_stream = self.client.models.generate_content_stream(
                model=model_id,
                config=types.GenerateContentConfig(
                    system_instruction="",  # System instruction in context
                    temperature=temperature,
                    top_p=top_p
                ),
                contents=[context]
            )
            
            connect_time = time.time() - start_time
            sys_log("API", f"Connected successfully ({connect_time:.2f}s)", "INFO")
            
            # Return safe generator
            return SafeGenerator(response_stream), model_id
            
        except Exception as e:
            error_time = time.time() - start_time
            error_msg = str(e).lower()
            self.last_error = error_msg
            
            sys_log("API", f"Stream failed ({error_time:.2f}s): {error_msg}", "ERROR")
            
            # Handle common errors
            if "temperature" in error_msg or "not supported" in error_msg:
                sys_log("API", "Temperature not supported, retrying without temp", "WARNING")
                try:
                    response_stream = self.client.models.generate_content_stream(
                        model=model_id,
                        config=types.GenerateContentConfig(system_instruction=""),
                        contents=[context]
                    )
                    return SafeGenerator(response_stream), model_id
                except Exception as retry_error:
                    sys_log("API", f"Retry failed: {retry_error}", "ERROR")
                    pass
            
            # Return error stream
            return self._error_stream(f"API Error: {e}"), model_id
    
    def _error_stream(self, error_msg):
        """Create error stream"""
        def error_gen():
            yield f"[ERROR] {error_msg}"
        return error_gen()
    
    def non_stream_request(self, context, model_key="VISION", temperature=0.7, top_p=0.95):
        """Non-streaming request for fallback"""
        start_time = time.time()
        
        # Convert identity to model key (handles both "VISION" and "vision")
        current_key = get_model_for_identity(model_key) if model_key in ["JAMIE", "VISION", "PRO"] else model_key
        if current_key not in MODELS_CONFIG:
            current_key = "lite"
        model_id = MODELS_CONFIG[current_key]["id"]
        
        try:
            response = self.client.models.generate_content(
                model=model_id,
                config=types.GenerateContentConfig(
                    system_instruction="",
                    temperature=temperature,
                    top_p=top_p
                ),
                contents=[context]
            )
            
            response_time = time.time() - start_time
            sys_log("API", f"Non-stream success ({response_time:.2f}s)", "INFO")
            
            return getattr(response, "text", str(response)), model_id
            
        except Exception as e:
            error_time = time.time() - start_time
            error_msg = str(e).lower()
            self.last_error = error_msg
            
            sys_log("API", f"Non-stream failed ({error_time:.2f}s): {error_msg}", "ERROR")
            return f"Error: {e}", model_id
