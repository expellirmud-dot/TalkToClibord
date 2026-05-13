# vision_context_recovery.py (V3.1 - Session Continuity & Handoff)
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# Import path constants
from src.utils.vision_paths import HANDOFF_DIR, ROOT_DIR

class ContextRecovery:
    """Session continuity with handoff notes and context reconstruction"""
    
    def __init__(self, project_dir=None):
        # Use ROOT_DIR from vision_paths.py as single source of truth
        self.project_dir = project_dir if project_dir else ROOT_DIR
        self.handoff_dir = HANDOFF_DIR
        self._ensure_handoff_dir()
        
        # Current session state
        self._current_session_id = None
        self._current_handoff = None
    
    def _ensure_handoff_dir(self):
        """Ensure handoff directory exists"""
        try:
            if not os.path.exists(self.handoff_dir):
                os.makedirs(self.handoff_dir, exist_ok=True)
                print(f"[ContextRecovery] Created handoff directory: {self.handoff_dir}")
        except Exception as e:
            print(f"[ContextRecovery] ERROR creating handoff directory: {e}")
    
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_handoff(self, 
                      project_state: str = "",
                      files_modified: List[str] = None,
                      architectural_decisions: List[str] = None,
                      patterns_established: List[str] = None,
                      next_steps: List[str] = None,
                      open_questions: List[str] = None) -> Dict:
        """Create handoff notes for session continuity"""
        
        if files_modified is None:
            files_modified = []
        if architectural_decisions is None:
            architectural_decisions = []
        if patterns_established is None:
            patterns_established = []
        if next_steps is None:
            next_steps = []
        if open_questions is None:
            open_questions = []
        
        session_id = self.generate_session_id()
        
        handoff = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "project_state": project_state,
            "files_modified": files_modified,
            "architectural_decisions": architectural_decisions,
            "patterns_established": patterns_established,
            "next_steps": next_steps,
            "open_questions": open_questions
        }
        
        self._current_session_id = session_id
        self._current_handoff = handoff
        
        return handoff
    
    def save_handoff(self, handoff: Dict) -> bool:
        """Save handoff notes to disk"""
        try:
            if not handoff.get("session_id"):
                print("[ContextRecovery] ERROR: Handoff missing session_id")
                return False
            
            handoff_file = os.path.join(self.handoff_dir, f"handoff_{handoff['session_id']}.json")
            
            with open(handoff_file, 'w', encoding='utf-8') as f:
                json.dump(handoff, f, indent=2, ensure_ascii=False)
            
            print(f"[ContextRecovery] Saved handoff to {handoff_file}")
            return True
            
        except Exception as e:
            print(f"[ContextRecovery] ERROR saving handoff: {e}")
            return False
    
    def load_handoff(self, session_id: str) -> Optional[Dict]:
        """Load handoff notes from disk"""
        try:
            handoff_file = os.path.join(self.handoff_dir, f"handoff_{session_id}.json")
            
            if not os.path.exists(handoff_file):
                print(f"[ContextRecovery] Handoff file not found: {handoff_file}")
                return None
            
            with open(handoff_file, 'r', encoding='utf-8') as f:
                handoff = json.load(f)
            
            self._current_session_id = session_id
            self._current_handoff = handoff
            
            print(f"[ContextRecovery] Loaded handoff from {handoff_file}")
            return handoff
            
        except Exception as e:
            print(f"[ContextRecovery] ERROR loading handoff: {e}")
            return None
    
    def get_latest_handoff(self) -> Optional[Dict]:
        """Get the most recent handoff"""
        try:
            handoff_files = [f for f in os.listdir(self.handoff_dir) if f.startswith("handoff_") and f.endswith(".json")]
            
            if not handoff_files:
                return None
            
            # Sort by timestamp (extract from filename)
            handoff_files.sort(reverse=True)
            latest_file = handoff_files[0]
            session_id = latest_file.replace("handoff_", "").replace(".json", "")
            
            return self.load_handoff(session_id)
            
        except Exception as e:
            print(f"[ContextRecovery] ERROR getting latest handoff: {e}")
            return None
    
    def reconstruct_context(self, handoff: Dict) -> str:
        """Reconstruct working context from handoff notes"""
        if not handoff:
            return "No handoff data available for context reconstruction."
        
        context_parts = []
        
        # Header
        context_parts.append(f"[Context Reconstruction - Session {handoff.get('session_id', 'Unknown')}]")
        context_parts.append(f"Timestamp: {handoff.get('timestamp', 'Unknown')}")
        context_parts.append("=" * 60)
        
        # Project State
        if handoff.get("project_state"):
            context_parts.append("\n[Project State]")
            context_parts.append(handoff["project_state"])
        
        # Files Modified
        if handoff.get("files_modified"):
            context_parts.append("\n[Files Modified]")
            for file in handoff["files_modified"]:
                context_parts.append(f"- {file}")
        
        # Architectural Decisions
        if handoff.get("architectural_decisions"):
            context_parts.append("\n[Architectural Decisions]")
            for decision in handoff["architectural_decisions"]:
                context_parts.append(f"- {decision}")
        
        # Patterns Established
        if handoff.get("patterns_established"):
            context_parts.append("\n[Patterns Established]")
            for pattern in handoff["patterns_established"]:
                context_parts.append(f"- {pattern}")
        
        # Next Steps
        if handoff.get("next_steps"):
            context_parts.append("\n[Next Steps]")
            for i, step in enumerate(handoff["next_steps"], 1):
                context_parts.append(f"{i}. {step}")
        
        # Open Questions
        if handoff.get("open_questions"):
            context_parts.append("\n[Open Questions]")
            for question in handoff["open_questions"]:
                context_parts.append(f"- {question}")
        
        return "\n".join(context_parts)
    
    def create_comprehensive_handoff(self, 
                                    current_task: str,
                                    completed_work: List[str],
                                    files_modified: List[str],
                                    decisions_made: List[str],
                                    patterns: List[str],
                                    next_steps: List[str]) -> Dict:
        """Create comprehensive handoff with all critical information"""
        
        handoff = self.create_handoff(
            project_state=f"Current task: {current_task}",
            files_modified=files_modified,
            architectural_decisions=decisions_made,
            patterns_established=patterns,
            next_steps=next_steps,
            open_questions=[]
        )
        
        handoff["completed_work"] = completed_work
        
        return handoff
    
    def auto_snapshot(self, 
                     task_description: str,
                     progress: str,
                     files_touched: List[str] = None) -> bool:
        """Automatically snapshot current state"""
        if files_touched is None:
            files_touched = []
        
        handoff = self.create_handoff(
            project_state=f"Task: {task_description}\nProgress: {progress}",
            files_modified=files_touched,
            architectural_decisions=[],
            patterns_established=[],
            next_steps=[f"Continue task: {task_description}"],
            open_questions=[]
        )
        
        return self.save_handoff(handoff)
    
    def recover_and_continue(self, session_id: str = None) -> Optional[str]:
        """Recover context and provide continuation prompt"""
        if session_id:
            handoff = self.load_handoff(session_id)
        else:
            handoff = self.get_latest_handoff()
        
        if not handoff:
            return None
        
        context = self.reconstruct_context(handoff)
        
        # Add continuation prompt
        next_steps = handoff.get("next_steps", [])
        if next_steps:
            context += f"\n\n[Continuation Prompt]\n"
            context += f"Based on the handoff notes, the next steps are:\n"
            for i, step in enumerate(next_steps, 1):
                context += f"{i}. {step}\n"
        
        return context
    
    def merge_handoffs(self, handoff_ids: List[str]) -> Optional[Dict]:
        """Merge multiple handoffs into one"""
        if not handoff_ids:
            return None
        
        merged = {
            "session_id": f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "files_modified": [],
            "architectural_decisions": [],
            "patterns_established": [],
            "next_steps": [],
            "open_questions": []
        }
        
        for session_id in handoff_ids:
            handoff = self.load_handoff(session_id)
            if handoff:
                # Merge lists (avoid duplicates)
                merged["files_modified"].extend(handoff.get("files_modified", []))
                merged["architectural_decisions"].extend(handoff.get("architectural_decisions", []))
                merged["patterns_established"].extend(handoff.get("patterns_established", []))
                merged["next_steps"].extend(handoff.get("next_steps", []))
                merged["open_questions"].extend(handoff.get("open_questions", []))
        
        # Remove duplicates
        for key in ["files_modified", "architectural_decisions", "patterns_established", "next_steps", "open_questions"]:
            merged[key] = list(dict.fromkeys(merged[key]))
        
        return merged
    
    def cleanup_old_handoffs(self, keep_count: int = 5):
        """Clean up old handoff files, keeping only the most recent"""
        try:
            handoff_files = [f for f in os.listdir(self.handoff_dir) if f.startswith("handoff_") and f.endswith(".json")]
            
            if len(handoff_files) <= keep_count:
                return
            
            # Sort by filename (which contains timestamp)
            handoff_files.sort(reverse=True)
            
            # Delete old files
            for old_file in handoff_files[keep_count:]:
                old_path = os.path.join(self.handoff_dir, old_file)
                os.remove(old_path)
                print(f"[ContextRecovery] Cleaned up old handoff: {old_file}")
                
        except Exception as e:
            print(f"[ContextRecovery] ERROR cleaning up handoffs: {e}")
