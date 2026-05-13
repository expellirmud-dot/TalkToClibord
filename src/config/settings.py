import os

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY environment variable is not set!\n"
        "Please set it using: set GEMINI_API_KEY=your_api_key_here (Windows)\n"
        "or export GEMINI_API_KEY=your_api_key_here (Linux/Mac)"
    )

UI_STYLE = {
    "font_family": "Prompt",
    "font_size_base": 10,
    "font_size_code": 10,
    "theme": "minimal_transparent",
    "alpha": 0.95,
    "fg_color": "#2c3e50",
    "bg_color": "white",
    "cursor_color": "#3498db",
    "padding_x": 15,
    "padding_y": 15,
    "line_spacing": 5
}

FALLBACK_CHAIN = ["vision", "flash", "lite", "fallback_lite"]

TTS_VOICES = [
    "Zephyr (Bright)", "Puck (Upbeat)", "Charon (ให้ข้อมูล)", "เกาหลี (หนักแน่น)", "Fenrir (ตื่นเต้นง่าย)", "Leda (วัยรุ่น)",
    "Orus (Firm)", "Aoede (Breezy)", "Callirrhoe (สบายๆ)", "Autonoe (Bright)", "Enceladus (Breathy)", "Iapetus (Clear)",
    "Umbriel (สบายๆ)", "Algieba (ราบรื่น)", "Despina (Smooth)", "Erinome (ล้าง)", "Algenib (Gravelly)", "Rasalgethi (ให้ข้อมูล)",
    "Laomedeia (Upbeat)", "Achernar (Soft)", "Alnilam (Firm)", "Schedar (Even)", "Gacrux (ผู้ใหญ่)", "Pulcherrima (Forward)",
    "Achird (เป็นมิตร)", "Zubenelgenubi (สบายๆ)", "Vindemiatrix (อ่อนโยน)", "Sadachbia (Lively)", "Sadaltager (มีความรู้)", "Sulafat (Warm)"
]
DEFAULT_VOICE = "Leda (วัยรุ่น)"
