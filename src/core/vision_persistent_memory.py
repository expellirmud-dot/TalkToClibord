# vision_persistent_memory.py (V3.1 - Persistent Memory Management)
import os
import time
from datetime import datetime
from functools import lru_cache

# Import path constants
from src.utils.vision_paths import CONFIG_DIR, JAVIS_MD, ROOT_DIR

class PersistentMemory:
    """Persistent memory layer for J.A.V.I.S. - manages JAVIS.md with cache optimization"""
    
    def __init__(self, project_dir=None):
        # Use ROOT_DIR from vision_paths.py as single source of truth
        self.project_dir = project_dir if project_dir else ROOT_DIR
        self.memory_file = JAVIS_MD
        self._cached_memory = None
        self._cache_timestamp = 0
        self._cache_ttl = 60  # Cache for 60 seconds
        
        # Ensure CONFIG_DIR exists
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                print(f"[PersistentMemory] Created CONFIG_DIR: {CONFIG_DIR}")
            except Exception as e:
                print(f"[PersistentMemory] ERROR creating CONFIG_DIR: {e}")
        
        # Initialize memory file if it doesn't exist
        self._initialize_memory_file()
        
        # Load into RAM for cache hit optimization
        self._load_into_ram()
    
    def _initialize_memory_file(self):
        """Initialize JAVIS.md with default structure if it doesn't exist"""
        try:
            if not os.path.exists(self.memory_file):
                default_content = """# J.A.V.I.S. Persistent Memory

## Project Architecture
- Frontend: Tkinter GUI (newVision.py)
- Backend: Python modules (vision_*.py)
- AI Service: Gemini API (vision_ai_service.py)
- Memory: chat_history.json, MemoryVault
- Audio: pygame.mixer for TTS
- Config: vision_config.py

## Key Decisions
- Use simple truncation for memory summarization (deterministic for cache hit)
- Static instructions loaded into RAM for context optimization
- Identity-based instruction override (INSTR_VISION_ULTIMATE for VISION)
- Expense tracking with in-memory caching (ExpenseTracker V2.0)

## Sprint Status
- Current: Sprint 1 - Foundation (Memory & Summarization)
- Status: In Progress
- Focus: Smart Context Summarizer + Persistent Memory

## Patterns and Conventions
- All vision_ modules use sys_log for logging
- Thai language support throughout
- Thread-safe operations with locks
- Error handling with try-except blocks
"""
                with open(self.memory_file, "w", encoding="utf-8") as f:
                    f.write(default_content)
                print(f"[PersistentMemory] Initialized JAVIS.md at {self.memory_file}")
        except Exception as e:
            print(f"[PersistentMemory] ERROR initializing memory file: {e}")
    
    def _load_into_ram(self):
        """Load memory file into RAM for cache hit optimization"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._cached_memory = f.read()
                self._cache_timestamp = time.time()
                print(f"[PersistentMemory] Loaded {len(self._cached_memory)} chars into RAM cache")
            else:
                self._cached_memory = ""
        except Exception as e:
            print(f"[PersistentMemory] ERROR loading into RAM: {e}")
            self._cached_memory = ""
    
    def _is_cache_valid(self):
        """Check if cache is still valid"""
        return time.time() - self._cache_timestamp < self._cache_ttl
    
    def get_memory(self, force_reload=False):
        """Get memory content with cache optimization"""
        try:
            if force_reload or not self._is_cache_valid():
                self._load_into_ram()
            return self._cached_memory
        except Exception as e:
            print(f"[PersistentMemory] ERROR getting memory: {e}")
            return ""
    
    def update_section(self, section_name, content):
        """Update a specific section in the memory file"""
        try:
            # Read current content
            current_content = self.get_memory(force_reload=True)
            
            # Find and update section
            lines = current_content.split("\n")
            in_section = False
            new_lines = []
            section_found = False
            
            for line in lines:
                if line.strip().startswith(f"## {section_name}"):
                    in_section = True
                    section_found = True
                    new_lines.append(line)
                    # Add new content
                    if isinstance(content, str):
                        new_lines.extend(content.split("\n"))
                    elif isinstance(content, list):
                        new_lines.extend(content)
                elif in_section and line.startswith("## "):
                    # End of current section
                    in_section = False
                    new_lines.append(line)
                elif not in_section:
                    new_lines.append(line)
            
            # If section not found, append it
            if not section_found:
                new_lines.append(f"\n## {section_name}")
                if isinstance(content, str):
                    new_lines.extend(content.split("\n"))
                elif isinstance(content, list):
                    new_lines.extend(content)
            
            # Write back
            new_content = "\n".join(new_lines)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Update cache
            self._cached_memory = new_content
            self._cache_timestamp = time.time()
            
            print(f"[PersistentMemory] Updated section: {section_name}")
            return True
            
        except Exception as e:
            print(f"[PersistentMemory] ERROR updating section {section_name}: {e}")
            return False
    
    def append_to_section(self, section_name, content):
        """Append content to a specific section"""
        try:
            current_content = self.get_memory(force_reload=True)
            
            # Find section and append
            lines = current_content.split("\n")
            in_section = False
            new_lines = []
            section_found = False
            
            for line in lines:
                new_lines.append(line)
                if line.strip().startswith(f"## {section_name}"):
                    in_section = True
                    section_found = True
                elif in_section and line.startswith("## "):
                    # End of current section, append before next section
                    in_section = False
                    if isinstance(content, str):
                        new_lines.extend(content.split("\n"))
                    elif isinstance(content, list):
                        new_lines.extend(content)
            
            # If section not found, append at end
            if not section_found:
                new_lines.append(f"\n## {section_name}")
                if isinstance(content, str):
                    new_lines.extend(content.split("\n"))
                elif isinstance(content, list):
                    new_lines.extend(content)
            
            # Write back
            new_content = "\n".join(new_lines)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Update cache
            self._cached_memory = new_content
            self._cache_timestamp = time.time()
            
            print(f"[PersistentMemory] Appended to section: {section_name}")
            return True
            
        except Exception as e:
            print(f"[PersistentMemory] ERROR appending to section {section_name}: {e}")
            return False
    
    def get_section(self, section_name):
        """Get content of a specific section"""
        try:
            current_content = self.get_memory()
            lines = current_content.split("\n")
            in_section = False
            section_content = []
            
            for line in lines:
                if line.strip().startswith(f"## {section_name}"):
                    in_section = True
                elif in_section and line.startswith("## "):
                    # End of current section
                    break
                elif in_section:
                    section_content.append(line)
            
            return "\n".join(section_content)
        except Exception as e:
            print(f"[PersistentMemory] ERROR getting section {section_name}: {e}")
            return ""
    
    def add_architecture_note(self, note):
        """Add architecture note to Project Architecture section"""
        return self.append_to_section("Project Architecture", f"- {note}")
    
    def add_decision(self, decision):
        """Add key decision to Key Decisions section"""
        return self.append_to_section("Key Decisions", f"- {decision}")
    
    def update_sprint_status(self, status, focus):
        """Update sprint status"""
        content = f"- Current: {status}\n- Focus: {focus}\n- Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return self.update_section("Sprint Status", content)
    
    def add_pattern(self, pattern):
        """Add pattern to Patterns and Conventions section"""
        return self.append_to_section("Patterns and Conventions", f"- {pattern}")
    
    @lru_cache(maxsize=1)
    def get_architecture(self):
        """Get architecture with caching"""
        return self.get_section("Project Architecture")
    
    @lru_cache(maxsize=1)
    def get_decisions(self):
        """Get key decisions with caching"""
        return self.get_section("Key Decisions")
