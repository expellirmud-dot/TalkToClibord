# vision_task_analyzer.py (V3.0 - Task Segmentation & Chunking)
import re
import json
from typing import List, Dict, Tuple, Optional
from src.utils.vision_utils import estimate_tokens

class TaskAnalyzer:
    """Task segmentation and chunking for complex requests"""
    
    def __init__(self, max_tokens_per_task=5000, max_files_per_task=3):
        self.max_tokens_per_task = max_tokens_per_task
        self.max_files_per_task = max_files_per_task
        
        # Task complexity indicators
        self.complexity_keywords = [
            "and", "then", "after", "also", "plus", "additionally",
            "และ", "แล้ว", "หลังจาก", "นอกจากนี้", "เพิ่มเติม"
        ]
        
        # File pattern for detection
        self.file_pattern = r'[\w_\-\.]+\.(py|txt|md|json|yaml|yml|csv)'
        
    def extract_file_references(self, text: str) -> List[str]:
        """Extract file references from user input"""
        # Match full filenames with extensions
        files = re.findall(r'[\w_\-\.]+\.(?:py|txt|md|json|yaml|yml|csv)', text)
        # Also check for @file patterns
        at_files = re.findall(r'@([\w_\-\.]+\.(?:py|txt|md|json|yaml|yml|csv))', text)
        return list(set(files + at_files))
    
    def detect_multiple_instructions(self, text: str) -> bool:
        """Detect if text contains multiple instructions"""
        # Check for complexity keywords
        for keyword in self.complexity_keywords:
            if keyword.lower() in text.lower():
                return True
        
        # Check for multiple sentences
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 3:
            return True
        
        # Check for multiple verbs/actions
        action_patterns = [
            r'\b(create|build|implement|add|fix|modify|update|delete|remove)\b',
            r'\b(สร้าง|สร้าง|เพิ่ม|แก้ไข|ปรับปรุง|ลบ|เอาออก)\b'
        ]
        
        action_count = 0
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            action_count += len(matches)
        
        return action_count > 1
    
    def analyze_task_complexity(self, user_input: str, file_count: int = 0) -> Dict[str, any]:
        """Analyze task complexity"""
        estimated_tokens = estimate_tokens(user_input)
        files = self.extract_file_references(user_input)
        actual_file_count = len(files) + file_count
        
        is_multiple = self.detect_multiple_instructions(user_input)
        
        complexity_score = 0
        if estimated_tokens > self.max_tokens_per_task:
            complexity_score += 2
        if actual_file_count > self.max_files_per_task:
            complexity_score += 2
        if is_multiple:
            complexity_score += 1
        
        return {
            "estimated_tokens": estimated_tokens,
            "file_count": actual_file_count,
            "has_multiple_instructions": is_multiple,
            "complexity_score": complexity_score,
            "requires_chunking": complexity_score >= 2
        }
    
    def split_task_by_keywords(self, user_input: str) -> List[str]:
        """Split task by complexity keywords"""
        # Split by common separators
        separators = [' and ', ' then ', ' after that ', ' also ', ' plus ', ' และ ', ' แล้ว ', ' หลังจาก ']
        
        parts = [user_input]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        # Filter empty parts
        parts = [p.strip() for p in parts if p.strip()]
        
        return parts
    
    def split_task_by_files(self, user_input: str, files: List[str]) -> List[Dict]:
        """Split task by file references"""
        if not files:
            return [{"description": user_input, "files": [], "priority": 1}]
        
        tasks = []
        for i, file in enumerate(files):
            task = {
                "description": f"Work on {file}",
                "files": [file],
                "priority": i + 1,
                "dependencies": [] if i == 0 else [i - 1]
            }
            tasks.append(task)
        
        return tasks
    
    def generate_sub_tasks(self, user_input: str, files: List[str] = None) -> List[Dict]:
        """Generate sub-tasks with dependencies"""
        if files is None:
            files = self.extract_file_references(user_input)
        
        complexity = self.analyze_task_complexity(user_input, len(files))
        
        # If simple task, return as single task
        if not complexity["requires_chunking"]:
            return [{
                "id": 1,
                "description": user_input,
                "files": files,
                "priority": 1,
                "dependencies": [],
                "estimated_tokens": complexity["estimated_tokens"]
            }]
        
        # Complex task - split into sub-tasks
        sub_tasks = []
        
        # Strategy 1: Split by files if many files
        if len(files) > self.max_files_per_task:
            file_chunks = [files[i:i+self.max_files_per_task] for i in range(0, len(files), self.max_files_per_task)]
            
            for i, chunk in enumerate(file_chunks):
                sub_task = {
                    "id": i + 1,
                    "description": f"Process files: {', '.join(chunk)}",
                    "files": chunk,
                    "priority": i + 1,
                    "dependencies": [] if i == 0 else [i],
                    "estimated_tokens": estimate_tokens(f"Process {len(chunk)} files")
                }
                sub_tasks.append(sub_task)
        
        # Strategy 2: Split by instructions if multiple instructions
        elif complexity["has_multiple_instructions"]:
            parts = self.split_task_by_keywords(user_input)
            
            for i, part in enumerate(parts):
                sub_task = {
                    "id": i + 1,
                    "description": part,
                    "files": files if i == 0 else [],
                    "priority": i + 1,
                    "dependencies": [] if i == 0 else [i],
                    "estimated_tokens": estimate_tokens(part)
                }
                sub_tasks.append(sub_task)
        
        # Strategy 3: Split by token count
        elif complexity["estimated_tokens"] > self.max_tokens_per_task:
            # Rough split by character count
            chars_per_task = self.max_tokens_per_task * 4
            parts = []
            current_part = ""
            current_length = 0
            
            sentences = re.split(r'[.!?]+', user_input)
            for sentence in sentences:
                sentence = sentence.strip()
                if current_length + len(sentence) > chars_per_task and current_part:
                    parts.append(current_part)
                    current_part = sentence
                    current_length = len(sentence)
                else:
                    current_part += ". " + sentence if current_part else sentence
                    current_length += len(sentence)
            
            if current_part:
                parts.append(current_part)
            
            for i, part in enumerate(parts):
                sub_task = {
                    "id": i + 1,
                    "description": part,
                    "files": files if i == 0 else [],
                    "priority": i + 1,
                    "dependencies": [] if i == 0 else [i],
                    "estimated_tokens": estimate_tokens(part)
                }
                sub_tasks.append(sub_task)
        
        return sub_tasks if sub_tasks else [{"id": 1, "description": user_input, "files": files, "priority": 1, "dependencies": [], "estimated_tokens": complexity["estimated_tokens"]}]
    
    def get_execution_order(self, sub_tasks: List[Dict]) -> List[Dict]:
        """Get execution order based on dependencies"""
        # Sort by priority
        sorted_tasks = sorted(sub_tasks, key=lambda x: x["priority"])
        
        # Simple topological sort based on dependencies
        executed = []
        remaining = sorted_tasks.copy()
        
        while remaining:
            # Find tasks with no unmet dependencies
            ready = []
            for task in remaining:
                deps = task.get("dependencies", [])
                unmet_deps = [d for d in deps if d not in [t["id"] for t in executed]]
                if not unmet_deps:
                    ready.append(task)
            
            if not ready:
                # Circular dependency or missing dependency - add first remaining
                ready = [remaining[0]]
            
            executed.extend(ready)
            remaining = [t for t in remaining if t not in ready]
        
        return executed
    
    def format_task_plan(self, sub_tasks: List[Dict]) -> str:
        """Format task plan for display"""
        ordered_tasks = self.get_execution_order(sub_tasks)
        
        plan = f"[Task Plan - {len(ordered_tasks)} sub-tasks]\n"
        plan += "=" * 50 + "\n"
        
        for task in ordered_tasks:
            deps = task.get("dependencies", [])
            dep_str = f" (depends on: {deps})" if deps else ""
            files_str = f" [files: {', '.join(task['files'])}]" if task.get('files') else ""
            
            plan += f"Task {task['id']}: {task['description']}{dep_str}{files_str}\n"
            plan += f"  Priority: {task['priority']} | Est. tokens: {task['estimated_tokens']}\n"
        
        return plan
    
    def to_json(self, sub_tasks: List[Dict]) -> str:
        """Convert sub-tasks to JSON format"""
        return json.dumps(sub_tasks, indent=2, ensure_ascii=False)
    
    def from_json(self, json_str: str) -> List[Dict]:
        """Load sub-tasks from JSON format"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            from src.utils.vision_utils import sys_log
            sys_log("TaskAnalyzer", f"Error parsing JSON: {e}")
            return []
