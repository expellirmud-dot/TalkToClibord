# vision_context_compactor.py (V3.0 - Advanced Context Management)
from typing import Dict, List, Optional

class ContextCompactor:
    """Automatic context compaction at 80% threshold with persistent sync"""
    
    def __init__(self, max_tokens=32000, threshold_percent=0.8):
        self.max_tokens = max_tokens
        self.threshold_percent = threshold_percent
        self.threshold_tokens = int(max_tokens * threshold_percent)
        
        # Dependencies (will be injected)
        self.smart_summarizer = None
        self.persistent_memory = None
        
        # Compaction stats
        self.compaction_count = 0
        self.total_tokens_saved = 0
    
    def set_dependencies(self, smart_summarizer, persistent_memory):
        """Inject dependencies from Sprint 1 modules"""
        self.smart_summarizer = smart_summarizer
        self.persistent_memory = persistent_memory
    
    def estimate_current_tokens(self, context: str) -> int:
        """Estimate current token count (rough: 1 token ≈ 4 chars)"""
        return len(context) // 4
    
    def should_compact(self, current_tokens: int) -> bool:
        """Check if compaction should trigger"""
        return current_tokens >= self.threshold_tokens
    
    def get_usage_percentage(self, current_tokens: int) -> float:
        """Get current usage as percentage"""
        return (current_tokens / self.max_tokens) * 100
    
    def extract_architectural_decisions(self, conversation_history: List[str]) -> List[str]:
        """Extract architectural decisions from conversation history"""
        decisions = []
        
        decision_keywords = [
            "decision", "decided", "choose", "selected", "architecture",
            "pattern", "design", "structure", "ตัดสินใจ", "เลือก", "สถาปัตยกรรม"
        ]
        
        for entry in conversation_history:
            entry_lower = entry.lower()
            for keyword in decision_keywords:
                if keyword in entry_lower:
                    decisions.append(entry)
                    break
        
        return decisions
    
    def sync_to_persistent_memory(self, decisions: List[str]) -> bool:
        """Sync architectural decisions to JAVIS.md via PersistentMemory"""
        if not self.persistent_memory:
            print("[ContextCompactor] WARNING: PersistentMemory not set, skipping sync")
            return False

        try:
            # Filter out debug object representations
            filtered_decisions = []
            for decision in decisions:
                # Skip if contains debug object strings
                if 'sdk_http_response' in str(decision) or 'candidates=' in str(decision):
                    print(f"[ContextCompactor] Skipping debug object in decision")
                    continue
                # Skip if looks like object representation
                if 'HttpResponse(' in str(decision) or 'Candidate(' in str(decision):
                    print(f"[ContextCompactor] Skipping object representation in decision")
                    continue
                filtered_decisions.append(decision)

            for decision in filtered_decisions:
                self.persistent_memory.add_decision(decision)

            print(f"[ContextCompactor] Synced {len(filtered_decisions)} decisions to JAVIS.md (filtered from {len(decisions)})")
            return True
        except Exception as e:
            print(f"[ContextCompactor] ERROR syncing to PersistentMemory: {e}")
            return False
    
    def compact_conversation_history(self, conversation_history: List[str]) -> List[str]:
        """Compact conversation history using SmartSummarizer"""
        if not self.smart_summarizer:
            print("[ContextCompactor] WARNING: SmartSummarizer not set, using simple truncation")
            # Fallback: keep last 10 entries
            return conversation_history[-10:]
        
        try:
            # Convert history to text
            history_text = "\n".join(conversation_history)
            
            # Use smart summarization
            summary = self.smart_summarizer.summarize_with_key_extraction(history_text)
            
            # Convert back to list
            if summary:
                return [summary]
            else:
                return conversation_history[-10:]
                
        except Exception as e:
            print(f"[ContextCompactor] ERROR compacting with SmartSummarizer: {e}")
            return conversation_history[-10:]
    
    def compact_context(self,
                      current_context: str,
                      conversation_history: List[str] = None) -> Dict[str, any]:
        """Main compaction method with improved strategy"""

        if conversation_history is None:
            conversation_history = []

        current_tokens = self.estimate_current_tokens(current_context)
        usage_percent = self.get_usage_percentage(current_tokens)

        if not self.should_compact(current_tokens):
            return {
                "compacted": False,
                "current_tokens": current_tokens,
                "usage_percent": usage_percent,
                "reason": "Below threshold"
            }

        print(f"[ContextCompactor] Triggering compaction at {usage_percent:.1f}% usage")

        # Determine compaction aggressiveness based on usage
        if usage_percent >= 90:
            # Aggressive compaction for very high usage
            history_keep_ratio = 0.2  # Keep only 20% of history
            compaction_mode = "AGGRESSIVE"
        elif usage_percent >= 80:
            # Standard compaction
            history_keep_ratio = 0.4  # Keep 40% of history
            compaction_mode = "STANDARD"
        else:
            # Light compaction
            history_keep_ratio = 0.6  # Keep 60% of history
            compaction_mode = "LIGHT"

        # Extract architectural decisions before compaction
        decisions = self.extract_architectural_decisions(conversation_history)

        # Sync to persistent memory
        sync_success = self.sync_to_persistent_memory(decisions)

        # Compact conversation history with dynamic keep ratio
        compacted_history = self._compact_history_with_ratio(conversation_history, history_keep_ratio)

        # Calculate token savings
        original_history_tokens = self.estimate_current_tokens("\n".join(conversation_history))
        compacted_history_tokens = self.estimate_current_tokens("\n".join(compacted_history))
        tokens_saved = original_history_tokens - compacted_history_tokens

        # Update stats
        self.compaction_count += 1
        self.total_tokens_saved += tokens_saved

        return {
            "compacted": True,
            "current_tokens": current_tokens,
            "usage_percent": usage_percent,
            "tokens_saved": tokens_saved,
            "decisions_synced": len(decisions),
            "sync_success": sync_success,
            "compacted_history": compacted_history,
            "compaction_count": self.compaction_count,
            "total_tokens_saved": self.total_tokens_saved,
            "compaction_mode": compaction_mode,
            "history_keep_ratio": history_keep_ratio
        }

    def _compact_history_with_ratio(self, history: List[str], keep_ratio: float) -> List[str]:
        """Compact history keeping only the specified ratio of entries"""
        if not history:
            return []

        keep_count = max(1, int(len(history) * keep_ratio))

        # Keep the most recent entries
        return history[-keep_count:]
    
    def get_compaction_stats(self) -> Dict[str, any]:
        """Get compaction statistics"""
        return {
            "compaction_count": self.compaction_count,
            "total_tokens_saved": self.total_tokens_saved,
            "average_savings_per_compaction": self.total_tokens_saved / self.compaction_count if self.compaction_count > 0 else 0
        }
    
    def compact_history(self, history_file_path: str) -> bool:
        """Compact chat history file - simplified interface for vision_interface"""
        try:
            import json
            import os
            
            if not os.path.exists(history_file_path):
                print(f"[ContextCompactor] History file not found: {history_file_path}")
                return False
            
            # Load history
            with open(history_file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history or len(history) == 0:
                print("[ContextCompactor] No history to compact")
                return True
            
            # Compact using existing method
            compacted_history = self.compact_conversation_history(history)
            
            # Save back
            with open(history_file_path, 'w', encoding='utf-8') as f:
                json.dump(compacted_history, f, ensure_ascii=False, indent=2)
            
            tokens_saved = len(history) - len(compacted_history)
            print(f"[ContextCompactor] Compacted history: {len(history)} -> {len(compacted_history)} entries (saved {tokens_saved})")
            return True
            
        except Exception as e:
            print(f"[ContextCompactor] Error compacting history: {e}")
            return False
    
    def reset_stats(self):
        """Reset compaction statistics"""
        self.compaction_count = 0
        self.total_tokens_saved = 0
        print("[ContextCompactor] Stats reset")
