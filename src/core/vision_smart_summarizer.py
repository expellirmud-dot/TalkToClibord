# vision_smart_summarizer.py (V3.0 - Smart Context Summarization)
import re
from typing import List, Dict, Tuple

class SmartSummarizer:
    """Smart context summarizer with key point extraction (not just truncation)"""
    
    def __init__(self, max_tokens=12000):
        self.max_tokens = max_tokens
        self.TAG_CORE = "#CORE"
        self.TAG_LOGIC = "#LOGIC"
        
        # Keywords for key point extraction
        self.key_keywords = [
            "Fixed", "Added", "Modified", "Decision", "Pattern",
            "แก้ไข", "เพิ่ม", "ปรับปรุง", "ตัดสินใจ", "รูปแบบ",
            "Bug", "Error", "Issue", "Problem", "Solution",
            "ปัญหา", "วิธีแก้", "สำเร็จ", "เสร็จสิ้น"
        ]
        
        # Priority sections
        self.priority_sections = [
            "architecture", "decision", "pattern", "bug", "fix",
            "สถาปัตยกรรม", "ตัดสินใจ", "รูปแบบ", "บั๊ก", "แก้ไข"
        ]
    
    def generate_skeleton(self, code_text):
        """สร้าง 'โครงกระดูก' ของโค้ด (ดึงเฉพาะนิยามฟังก์ชันและคลาส)"""
        if not code_text: return ""
        skeleton = []
        lines = code_text.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('@'):
                skeleton.append(stripped)
            elif stripped.startswith('def '):
                parts = stripped.split('(')
                func_name = parts[0]
                tag = self.TAG_CORE if "__init__" in stripped else self.TAG_LOGIC
                skeleton.append(f"{func_name}(...) {tag}")
            elif stripped.startswith('class '):
                # Class definition - keep as is without (...)
                skeleton.append(stripped)
        return "\n".join(skeleton)
    
    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points based on keywords"""
        if not text:
            return []
        
        key_points = []
        lines = text.split("\n")
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if line contains key keywords
            for keyword in self.key_keywords:
                if keyword.lower() in line_stripped.lower():
                    key_points.append(line_stripped)
                    break
        
        return key_points
    
    def extract_sentences_with_keywords(self, text: str) -> List[str]:
        """Extract sentences containing key keywords"""
        if not text:
            return []
        
        # Try splitting by sentence terminators first
        sentences = re.split(r'[.!?]+', text)
        
        # If no sentence terminators found, split by newlines (for code-like text)
        if len(sentences) == 1:
            sentences = text.split("\n")
        
        key_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            for keyword in self.key_keywords:
                if keyword.lower() in sentence.lower():
                    key_sentences.append(sentence)
                    break
        
        return key_sentences
    
    def prioritize_content(self, text: str) -> Tuple[List[str], List[str]]:
        """Prioritize content into high and low priority"""
        lines = text.split("\n")
        high_priority = []
        low_priority = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if high priority
            is_high = False
            for keyword in self.key_keywords:
                if keyword.lower() in line_stripped.lower():
                    high_priority.append(line_stripped)
                    is_high = True
                    break
            
            if not is_high:
                low_priority.append(line_stripped)
        
        return high_priority, low_priority
    
    def smart_truncate(self, text: str, max_chars: int = None) -> str:
        """Smart truncation that keeps key points first"""
        if max_chars is None:
            max_chars = self.max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
        
        if len(text) <= max_chars:
            return text
        
        # Extract key points
        key_points = self.extract_key_points(text)
        high_priority, low_priority = self.prioritize_content(text)
        
        # Start with key points
        result = []
        current_length = 0
        
        # Add high priority content first
        for line in high_priority:
            if current_length + len(line) + 1 > max_chars:
                break
            result.append(line)
            current_length += len(line) + 1
        
        # Add low priority content if space remains
        for line in low_priority:
            if current_length + len(line) + 1 > max_chars:
                break
            result.append(line)
            current_length += len(line) + 1
        
        # If still under limit, add more from original text
        if current_length < max_chars * 0.8:
            remaining_chars = max_chars - current_length
            original_lines = text.split("\n")
            for line in original_lines:
                line_stripped = line.strip()
                if not line_stripped or line_stripped in result:
                    continue
                if current_length + len(line_stripped) + 1 > max_chars:
                    break
                result.append(line_stripped)
                current_length += len(line_stripped) + 1
        
        summary = "\n".join(result)
        
        # Add truncation indicator
        if len(text) > max_chars:
            summary += "\n... [truncated]"
        
        return summary
    
    def summarize_with_key_extraction(self, text: str, include_metadata: bool = True) -> str:
        """Summarize with key point extraction and metadata"""
        if not text:
            return ""
        
        # Extract key points
        key_points = self.extract_key_points(text)
        key_sentences = self.extract_sentences_with_keywords(text)
        
        # Build summary
        summary_parts = []
        
        if include_metadata:
            summary_parts.append(f"[Smart Summary - {len(text)} chars, {len(key_points)} key points]")
        
        # Add key points first
        if key_points:
            summary_parts.append("\n[Key Points]")
            summary_parts.extend(key_points[:10])  # Max 10 key points
        
        # Smart truncate the rest
        remaining_text = text
        if key_points:
            # Remove key points from original text to avoid duplication
            for kp in key_points:
                remaining_text = remaining_text.replace(kp, "")
        
        truncated = self.smart_truncate(remaining_text)
        if truncated:
            summary_parts.append("\n[Context]")
            summary_parts.append(truncated)
        
        return "\n".join(summary_parts)
    
    def extract_architecture_info(self, text: str) -> Dict[str, List[str]]:
        """Extract architecture-related information"""
        arch_keywords = ["class", "def ", "import", "from ", "module", "file"]
        arch_info = {
            "classes": [],
            "functions": [],
            "imports": [],
            "files": []
        }
        
        lines = text.split("\n")
        for line in lines:
            line_stripped = line.strip()
            
            if "class " in line_stripped:
                arch_info["classes"].append(line_stripped)
            elif "def " in line_stripped:
                arch_info["functions"].append(line_stripped)
            elif line_stripped.startswith("import ") or line_stripped.startswith("from "):
                arch_info["imports"].append(line_stripped)
            elif ".py" in line_stripped or "vision_" in line_stripped:
                arch_info["files"].append(line_stripped)
        
        return arch_info
    
    def extract_decision_info(self, text: str) -> List[str]:
        """Extract decision-related information"""
        decision_keywords = ["decided", "chose", "selected", "decided to", "decision", "ตัดสินใจ", "เลือก"]
        decisions = []
        
        lines = text.split("\n")
        for line in lines:
            line_stripped = line.strip()
            for keyword in decision_keywords:
                if keyword.lower() in line_stripped.lower():
                    decisions.append(line_stripped)
                    break
        
        return decisions
    
    def get_summary_stats(self, original_text: str, summarized_text: str) -> Dict[str, int]:
        """Get statistics about summarization"""
        return {
            "original_chars": len(original_text),
            "summarized_chars": len(summarized_text),
            "compression_ratio": len(summarized_text) / len(original_text) if original_text else 0,
            "key_points_found": len(self.extract_key_points(original_text))
        }
