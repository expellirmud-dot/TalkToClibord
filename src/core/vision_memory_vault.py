# vision_memory_vault.py (V4.0.5)
import json, os, numpy as np, difflib
from google import genai
from src.utils.vision_utils import sys_log

class MemoryVault:
    def __init__(self, api_key, filepath=None):
        self.filepath = filepath or "vault.json"
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.vault_data = {}
        self.vector_cache = {} 
        self._load_vault()
        
    def _load_vault(self):
        if not os.path.exists(self.filepath): return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.vault_data = data.get("facts", {})
                self.vector_cache = data.get("vectors", {})
        except (json.JSONDecodeError, IOError) as e:
            from src.utils.vision_utils import sys_log
            sys_log("Vault", f"Error loading vault: {e}")
            self.vault_data = {}

    def save_fact(self, fact_dict):
        self.vault_data.update(fact_dict)
        self._save_to_disk()

    def _save_to_disk(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({"facts": self.vault_data, "vectors": self.vector_cache}, f, ensure_ascii=False, indent=4)
        except Exception as e: sys_log("Vault_Error", str(e))

    def semantic_search(self, query, top_k=3):
        if not self.vault_data: return ""
        try:
            query_emb = self.client.models.embed_content(model="text-embedding-004", contents=query).embeddings[0].values
            scored_chunks = []
            for k, v in self.vault_data.items():
                chunk_text = f"[{k}]: {v}"
                if chunk_text not in self.vector_cache:
                    emb = self.client.models.embed_content(model="text-embedding-004", contents=chunk_text).embeddings[0].values
                    self.vector_cache[chunk_text] = emb
                
                v1, v2 = np.array(query_emb), np.array(self.vector_cache[chunk_text])
                score = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                scored_chunks.append((score, chunk_text))
            
            self._save_to_disk()
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            results = [c[1] for c in scored_chunks[:top_k] if c[0] > 0.4]
            return "[SEMANTIC CONTEXT]:\n" + "\n".join(results) if results else ""
        except (KeyError, ValueError, AttributeError) as e:
            from src.utils.vision_utils import sys_log
            sys_log("Vault", f"Semantic search error: {e}")
            return ""

    def query_vault_context(self):
        if not self.vault_data: return ""
        ctx = "[VAULT DATA]:\n"
        for k, v in self.vault_data.items(): ctx += f"- {k}: {v}\n"
        return ctx
