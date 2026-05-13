# vision_context_builder.py (V2.1 - Cache Hit Optimized with ReferenceLoader)
import time
import hashlib
from src.utils.vision_utils import sys_log
from src.core.vision_memory_summarizer import MemorySummarizer
from src.core.vision_reference_loader import ReferenceLoader
from vision_config import MODELS_CONFIG, get_model_config_for_identity, get_thought_config, INSTR_VISION_ULTIMATE

class ContextBuilder:
    """Unified context building system with cache hit optimization"""
    
    def __init__(self, memory_summarizer=None):
        self.memory_summarizer = memory_summarizer
        self.cache = {}
        # Use ReferenceLoader for unified file loading (eliminates redundant direct open() calls)
        self.ref_loader = ReferenceLoader()
        
        # Load static instructions into RAM once (Cache Hit Optimization)
        self._static_instructions = {}
        try:
            # Pre-load all static instructions
            self._static_instructions["VISION"] = INSTR_VISION_ULTIMATE
            
            for identity_key in ["JAMIE", "PRO"]:
                model_config = get_model_config_for_identity(identity_key)
                instr = model_config.get("instruction", "")
                self._static_instructions[identity_key] = instr
            
            sys_log("Context", f"Loaded {len(self._static_instructions)} static instructions into RAM")
        except Exception as e:
            sys_log("Context", f"Error loading static instructions: {e}")
            self._static_instructions = {}
        
    def build_context(self, user_input, identity="VISION", thought="FLASH", 
                     attachments=None, memory_limit=10):
        """Build complete context with cache hit optimization"""
        try:
            # STATIC PREFIX: Load from RAM (Cache Hit Optimization)
            static_prefix = self._get_static_prefix(identity)
            
            # DYNAMIC PARTS: Memory, Files, User Input
            dynamic_parts = []
            
            # 1. Memory Summary (Dynamic - depends on user_input)
            try:
                if self.memory_summarizer:
                    memory_summary = self.memory_summarizer.get_short_memory(user_input)
                    if memory_summary and len(memory_summary.strip()) > 0:
                        dynamic_parts.append(f"[MEMORY] {memory_summary}")
            except Exception as e:
                sys_log("Context", f"Memory error: {e}")
            
            # 2. File Attachments (Dynamic - depends on attachments)
            if attachments:
                file_context = self._build_file_context(attachments)
                if file_context:
                    dynamic_parts.append(f"[FILES] {file_context}")
            
            # 3. User Input (Dynamic - MUST BE LAST for cache hit)
            dynamic_parts.append(f"[USER] {user_input}")
            
            # Combine: Static Prefix + Dynamic Parts
            if dynamic_parts:
                dynamic_suffix = "\n\n".join(dynamic_parts)
                full_context = f"{static_prefix}\n\n{dynamic_suffix}"
            else:
                full_context = static_prefix
            
            # Quiet mode: Only log when context size changes significantly
            if not hasattr(self, '_last_context_size') or abs(len(full_context) - self._last_context_size) > 500:
                sys_log("Context", f"Built context: {len(full_context)} chars (static: {len(static_prefix)}, dynamic: {len(dynamic_suffix) if dynamic_parts else 0})")
                self._last_context_size = len(full_context)
            
            return full_context
            
        except Exception as e:
            sys_log("Context", f"Context building error: {e}")
            # Fallback: Simple context
            return f"[USER] {user_input}"
    
    def _get_static_prefix(self, identity):
        """Get static instruction prefix (loaded from RAM)"""
        try:
            system_instr = self._static_instructions.get(identity, "")
            if system_instr:
                return f"[SYSTEM] {system_instr}"
            return ""
        except Exception as e:
            sys_log("Context", f"Error getting static prefix: {e}")
            return ""
    
    def _build_file_context(self, attachments):
        """[V2.2] Build file context from attachments - รองรับทั้ง list และ dict"""
        if not attachments:
            return ""
        
        file_parts = []
        # รองรับทั้ง list และ dict (backward compatibility)
        if isinstance(attachments, dict):
            file_paths = attachments.keys()
        else:
            file_paths = attachments
        
        # Sort by filename for consistent context ordering (cache hit optimization)
        try:
            for file_path in sorted(file_paths):
                try:
                    # Use ReferenceLoader for unified file loading (eliminates redundant direct open() calls)
                    result = self.ref_loader.load_file_reference(file_path, max_lines=50, lazy=False)
                    if "content" in result:
                        content = result["content"][:1000]  # First 1000 chars
                        file_parts.append(f"--- {file_path} ---\n{content}")
                    elif "error" in result:
                        sys_log("Context", f"File load error: {file_path} - {result['error']}")
                        file_parts.append(f"--- {file_path} ---\n[ERROR: {result['error']}]")
                except Exception as e:
                    sys_log("Context", f"File error {file_path}: {e}")
                    file_parts.append(f"--- {file_path} ---\n[ERROR: {e}]")
        except Exception as e:
            sys_log("Context", f"File context building error: {e}")
            return ""
        
        return "\n\n".join(file_parts)
    
    def get_cache_key(self, user_input, context, attachments=None):
        """[V2.2] Generate cache key - รองรับทั้ง list และ dict"""
        try:
            key_parts = [user_input, context]
            
            if attachments:
                file_hashes = []
                # รองรับทั้ง list และ dict (backward compatibility)
                if isinstance(attachments, dict):
                    file_paths = attachments.keys()
                else:
                    file_paths = attachments
                try:
                    for file_path in sorted(file_paths):  # Sort for consistency
                        try:
                            with open(file_path, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                                file_hashes.append(f"{file_path}:{file_hash}")
                        except FileNotFoundError:
                            file_hashes.append(f"{file_path}:not_found")
                        except PermissionError:
                            file_hashes.append(f"{file_path}:permission_denied")
                        except Exception as e:
                            file_hashes.append(f"{file_path}:error")
                    key_parts.extend(file_hashes)
                except Exception as e:
                    sys_log("Context", f"File hashing error: {e}")
            
            cache_key = hashlib.md5("|".join(key_parts).encode('utf-8')).hexdigest()
            return cache_key
            
        except Exception as e:
            sys_log("Context", f"Cache key generation error: {e}")
            # Fallback: Simple hash
            return hashlib.md5(str(time.time()).encode()).hexdigest()
