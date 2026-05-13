# miniGeminiWeb.py (V2.8 - Path Slashes Restored)
import subprocess, os, json, time, threading, websocket, urllib.request
class VisionProStation:
    def __init__(self):
        self.process, self.ws = None, None
        self.storage_path = os.path.join(os.getenv('LOCALAPPDATA'), "Vision_Edge_Jarvis")
    def open(self):
        # ✅ คืนค่า \ ให้กับ Path ของ Edge ข่ะ
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        cmd = [edge_path, "https://gemini.google.com/", f"--user-data-dir={self.storage_path}", "--remote-debugging-port=9222"]
        try:
            self.process = subprocess.Popen(cmd)
            threading.Thread(target=self._connect, daemon=True).start()
        except: pass
    def _connect(self):
        for _ in range(10):
            try:
                time.sleep(2)
                res = urllib.request.urlopen("http://localhost:9222/json").read()
                ws_url = next(p["webSocketDebuggerUrl"] for p in json.loads(res) if "gemini" in p.get("url", ""))
                self.ws = websocket.create_connection(ws_url)
                return
            except: pass
    def toggle_auto_voice(self): return False
    def close(self): 
        if self.process: self.process.terminate()
