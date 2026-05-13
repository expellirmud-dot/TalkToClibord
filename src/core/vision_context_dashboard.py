# vision_context_dashboard.py (V3.0 - Real-time Context Monitor)
from typing import Dict, Optional

class ContextDashboard:
    """Real-time context usage monitoring with UI-compatible output"""
    
    def __init__(self, max_tokens=32000):
        self.max_tokens = max_tokens
        
        # Context components
        self.system_instruction_tokens = 0
        self.memory_tokens = 0
        self.file_data_tokens = 0
        self.user_query_tokens = 0
        
        # Dependencies
        self.context_compactor = None
    
    def set_dependencies(self, context_compactor):
        """Inject dependency from Sprint 3 module"""
        self.context_compactor = context_compactor
    
    def set_system_instruction_tokens(self, tokens: int):
        """Set system instruction token count"""
        # Ensure value is integer to prevent int + list error
        self.system_instruction_tokens = int(tokens) if tokens is not None else 0
    
    def set_memory_tokens(self, tokens: int):
        """Set memory (chat history) token count"""
        # Ensure value is integer to prevent int + list error
        self.memory_tokens = int(tokens) if tokens is not None else 0
    
    def set_file_data_tokens(self, tokens: int):
        """Set file data token count"""
        # Ensure value is integer to prevent int + list error
        self.file_data_tokens = int(tokens) if tokens is not None else 0
    
    def set_user_query_tokens(self, tokens: int):
        """Set user query token count"""
        # Ensure value is integer to prevent int + list error
        self.user_query_tokens = int(tokens) if tokens is not None else 0
    
    def get_total_tokens(self) -> int:
        """Get total current token count"""
        return (self.system_instruction_tokens + 
                self.memory_tokens + 
                self.file_data_tokens + 
                self.user_query_tokens)
    
    def get_usage_breakdown(self) -> Dict[str, float]:
        """Get breakdown of context usage as percentages"""
        total = self.get_total_tokens()
        
        if total == 0:
            return {
                "system_instruction": 0.0,
                "memory": 0.0,
                "file_data": 0.0,
                "user_query": 0.0
            }
        
        return {
            "system_instruction": (self.system_instruction_tokens / total) * 100,
            "memory": (self.memory_tokens / total) * 100,
            "file_data": (self.file_data_tokens / total) * 100,
            "user_query": (self.user_query_tokens / total) * 100
        }
    
    def get_usage_percentage(self) -> float:
        """Get total usage as percentage of max"""
        total = self.get_total_tokens()
        return (total / self.max_tokens) * 100 if self.max_tokens > 0 else 0
    
    def get_health_status(self) -> str:
        """Get health status based on usage"""
        usage = self.get_usage_percentage()
        
        if usage < 50:
            return "HEALTHY"
        elif usage < 80:
            return "WARNING"
        else:
            return "CRITICAL"
    
    def get_compaction_recommendation(self) -> Optional[str]:
        """Get recommendation for compaction"""
        usage = self.get_usage_percentage()
        
        if usage >= 80:
            return "IMMEDIATE COMPACTION REQUIRED"
        elif usage >= 70:
            return "CONSIDER COMPACTION"
        elif usage >= 50:
            return "MONITOR"
        else:
            return None
    
    def format_for_ui(self, style: str = "health_bar", usage_percentage: float = None) -> str:
        """Format context data for UI display"""
        if usage_percentage is not None:
            # Use custom usage percentage (for time-based calculation)
            usage = usage_percentage
        else:
            # Use calculated usage percentage
            usage = self.get_usage_percentage()
        
        status = self.get_health_status()
        
        if style == "detailed":
            breakdown = self.get_usage_breakdown()
            return self._format_detailed(breakdown, usage, status)
        elif style == "minimal":
            return self._format_minimal(usage, status)
        else:
            return self._format_health_bar(usage, status)
    
    def _format_health_bar(self, usage: float, status: str) -> str:
        """Format as a simple health bar"""
        bar_length = 10
        filled = int((usage / 100) * bar_length)
        empty = bar_length - filled
        
        # Color indicators (using emojis for simplicity)
        if status == "HEALTHY":
            indicator = "🟢"
        elif status == "WARNING":
            indicator = "🟡"
        else:
            indicator = "🔴"
        
        bar = "█" * filled + "░" * empty
        return f"{indicator} Context: [{bar}] {usage:.1f}%"
    
    def _format_detailed(self, breakdown: Dict[str, float], usage: float, status: str) -> str:
        """Format as detailed breakdown"""
        lines = []
        lines.append(f"Context Dashboard - {status}")
        lines.append("=" * 40)
        lines.append(f"Total Usage: {usage:.1f}% ({self.get_total_tokens()}/{self.max_tokens} tokens)")
        lines.append("")
        lines.append("Breakdown:")
        lines.append(f"  System Instruction: {breakdown['system_instruction']:.1f}%")
        lines.append(f"  Memory: {breakdown['memory']:.1f}%")
        lines.append(f"  File Data: {breakdown['file_data']:.1f}%")
        lines.append(f"  User Query: {breakdown['user_query']:.1f}%")
        
        recommendation = self.get_compaction_recommendation()
        if recommendation:
            lines.append("")
            lines.append(f"⚠ {recommendation}")
        
        return "\n".join(lines)
    
    def _format_minimal(self, usage: float, status: str) -> str:
        """Format as minimal string"""
        return f"Context: {usage:.1f}% [{status}]"
    
    def get_dictionary_output(self) -> Dict[str, any]:
        """Get dashboard data as dictionary for programmatic use"""
        return {
            "total_tokens": self.get_total_tokens(),
            "max_tokens": self.max_tokens,
            "usage_percentage": self.get_usage_percentage(),
            "health_status": self.get_health_status(),
            "breakdown": self.get_usage_breakdown(),
            "recommendation": self.get_compaction_recommendation(),
            "components": {
                "system_instruction": self.system_instruction_tokens,
                "memory": self.memory_tokens,
                "file_data": self.file_data_tokens,
                "user_query": self.user_query_tokens
            }
        }
    
    def trigger_compaction_if_needed(self) -> Optional[Dict]:
        """Trigger compaction if usage exceeds threshold"""
        if not self.context_compactor:
            return None
        
        usage = self.get_usage_percentage()
        if usage >= 80:
            print(f"[ContextDashboard] Usage at {usage:.1f}%, triggering compaction")
            
            # This would be called with actual context data
            # For now, return the compaction status
            return {
                "compaction_triggered": True,
                "usage_at_trigger": usage,
                "compaction_stats": self.context_compactor.get_compaction_stats()
            }
        
        return None
    
    def reset(self):
        """Reset all token counters"""
        self.system_instruction_tokens = 0
        self.memory_tokens = 0
        self.file_data_tokens = 0
        self.user_query_tokens = 0
        print("[ContextDashboard] Counters reset")
