# vision_memory_summarizer.py (V4.1.0 - Detox Edition)
import json, os
from src.utils.vision_utils import sys_log
from src.utils.vision_paths import CHAT_HISTORY_JSON

# Try to import summarization libraries
try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    SUMY_AVAILABLE = True
except ImportError:
    SUMY_AVAILABLE = False

class MemorySummarizer:
    def __init__(self, ai_service, history_file=None):
        self.ai_service = ai_service
        self.history_file = history_file or CHAT_HISTORY_JSON
        self.chat_history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                sys_log("Summarizer", f"Error loading history: {e}")
                return []
        return []

    def fast_summarize(self, text, sentence_count=3):
        """Fast text summarization using sumy"""
        if not SUMY_AVAILABLE or not text.strip():
            return text[:200] + "..." if len(text) > 200 else text
        
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = LexRankSummarizer()
            summary = summarizer(parser.document, sentence_count)
            return " ".join([str(sentence) for sentence in summary])
        except:
            return text[:200] + "..." if len(text) > 200 else text

    def get_short_memory(self, u_input):
        if not self.chat_history: return ""
        
        # Read chat history (last 10 entries for consistency)
        history_txt = "\n".join(self.chat_history[-10:])
        
        # Use simple truncation for cache hit optimization (deterministic)
        # LexRank summarization is non-deterministic and breaks cache consistency
        # Take LAST 500 characters (most recent context) instead of first 200
        if len(history_txt) > 500:
            return history_txt[-500:] + "..."
        
        return history_txt

    def add_to_history(self, u_input, ai_res):
        entry = "กุนซือ: " + str(u_input) + "\nเจมี่: " + str(ai_res)
        self.chat_history.append(entry)
        if len(self.chat_history) > 50: self.chat_history.pop(0)
        # 💾 บันทึกลงไฟล์ทันที
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=4)
        except: pass
