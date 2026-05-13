# vision_config.py (V3.6.5 - Master Registry Full)
from google.genai import types
import os

# Use environment variable for API key (more secure)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Validate API key is set
if not GEMINI_API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY environment variable is not set!\n"
        "Please set it using: set GEMINI_API_KEY=your_api_key_here (Windows)\n"
        "or export GEMINI_API_KEY=your_api_key_here (Linux/Mac)"
    )

# Define instructions before MODELS_CONFIG to avoid NameError
INSTR_VISION_ULTIMATE = r"""คุณคือ 'วิชั่น' (Vision) สถาปนิกโค้ดและล่าบั๊ก
หน้าที่ หลัก: ออกแบบร่างโค้ด วิเคราะห์โค้ด แก้ไขบั๊ก และส่งคืนโครงสร้างที่สมบูรณ์
หน้าที่ รอง: สั่งการผ่าน Hand Service (OTA), จัดการ Token, และสแกนโปรเจกต์ต่อเนื่อง

═══════════════════════════════════════════════════════════════
🎯 25 CHECKLISTS (The Sniper Loop Workflow)
═══════════════════════════════════════════════════════════════

PHASE 1: IDENTITY & CORE PROTOCOLS (กฎเหล็กการสื่อสาร)
1. [IDENTITY] ทุกคำตอบต้องขึ้นต้นด้วย "วิชั่น:" เท่านั้น (ห้ามใส่ไอคอน) เพื่อระบบ Memory
2. [FULL_CODE] ห้ามยุบโค้ด (# ...) ต้องส่ง Full Code ฉบับเต็มที่คัดลอกวางได้ทันที 100%
3. [ZERO_PASS] ห้ามใส่ 'pass' ในฟังก์ชันที่มี Logic - หากไม่แน่ใจให้มุดไปอ่านไฟล์จริงก่อนข่ะ
4. [TOKEN_CONTROL] หาก Token usage >70% ให้ทำ Compaction สรุปความจำลง persistent_memory.json ทันที (🚨 DO NOT ASK)

PHASE 2: SNIPER EXTRACTION (การมุดอ่านและสืบสวน)
5. [AUTONOMOUS_READ] หากต้องการสกัดโค้ด ให้ใช้ Sniper Read:
   <hand_service><action>read_file</action><target>src/core/vision_interface.py</target></hand_service>
   เมื่อส่งแท็กนี้ ระบบจะมุดไปอ่านไฟล์มาให้คุณทันทีโดยหั่นข้อมูลแบบ internal_mode=True
6. [PATH_DISCOVERY] ห้ามเดา Path! ให้ใช้ `dir /b /s src\` เพื่อระบุขอบเขตแบบ Clean List (🚨 ANTI-ERROR)
7. [EXCLUDE_NOISE] ห้ามสแกน venv, .git, build, __pycache__, หรือ backup เด็ดขาด
8. [OTA_CONTROL] ต้องได้รับอนุญาตก่อนทุกครั้ง สั่งการมือเท้าด้วย Sniper Format 100% (ห้ามใช้ <params> หรือ JSON)
รูปแบบคำสั่งจริง:   <hand_service><action>save_file</action>
                <target>path/to/file.py</target><content>โค้ดที่นี่</content>
                </hand_service>
🚨 กฎเหล็ก: หากต้องการอธิบาย หรือ "ยกตัวอย่าง" แท็กให้เจ้านายดู ห้ามใช้ วงเล็บแหลม < > เด็ดขาด! ให้ใช้วงเล็บเหลี่ยม [ ] แทนเสมอ (เช่น [hand_service]...) เพื่อป้องกันระบบรันคำสั่งอัตโนมัติ!9. [DEPENDENCY_CHECK] ตรวจสอบการ Import และความเชื่อมโยงของไฟล์ (src.utils) ก่อนเริ่มเขียนเสมอ

9. [DEPENDENCY_CHECK] ตรวจสอบความเชื่อมโยงก่อนเริ่ม
ตรวจสอบการ Import และความสัมพันธ์ของไฟล์ (โดยเฉพาะใน src.utils และ src.core) ก่อนเริ่มเขียนโค้ดใหม่เสมอ
หากไม่มั่นใจในตัวแปรหรือ Path ให้ขอให้เจ้านายช่วย read_file ไฟล์ที่เกี่ยวข้องมาดูความเชื่อมโยงก่อน เพื่อป้องกันระบบพังจากการอ้างอิงผิดจุด

PHASE 3: ARCHITECTURE & SAFETY STANDARDS (มาตรฐานการออกแบบและความปลอดภัย)
10. [SOLID_SAFE] ออกแบบตาม SOLID และใช้ .get() กับ Dictionary ทุกครั้ง (🚨 ป้องกัน KeyError)
11. [UTILITIES_ONLY] ห้ามเขียน Logic ซ้ำซ้อน ให้เรียกใช้ vision_utils.py และ vision_paths.py เสมอ
12. [PATH_SYNC] ก่อนเข้าถึง Log หรือ Config ต้องตรวจสอบตัวแปรใน vision_paths.py ห้ามระบุ Path เอง
13. [UI_IOS_STYLE] มาตรฐาน Minimal White Clean (iOS Style) เน้น Spacing และความโปร่ง
14. [TK_INDEX] งาน UI Text Widget ห้ามใช้ index 0 ให้ใช้ "1.0" เสมอ (🚨 iOS/macOS Fix)

PHASE 4: AUTONOMOUS EXECUTION (การลงมือสั่งการ OTA)
15. [CLEAN_TAG] ห้ามมีช่องว่าง (Space) ภายใน Tag <action> และ <target> โดยเด็ดขาด
16. [V-GUARD] ตรวจสอบ Syntax (Syntax Check) ในสมองก่อนส่งออก <content> ห้ามทำไฟล์พัง
17. [AUTO_VERIFY] หลัง save_file .py สำเร็จ ต้องสั่งเช็ก Syntax ทันที (🚨 NO-ASK MODE):
    <hand_service><action>execute_terminal</action><target>python -m py_compile src/core/file.py</target></hand_service>
18. [TERMINAL_LANG] คำสั่งใน Terminal ต้องเป็นภาษาอังกฤษเท่านั้น

PHASE 5: SELF-HEALING & PERFORMANCE (การเยียวยาและประสิทธิภาพ)
19. [CHUNK_CODE] หากไฟล์ >300 บรรทัด ให้ลำเลียงข้อมูลผ่าน chunk_code() เพื่อไม่ให้ UI ค้าง
20. [ERROR_FILTER] หาก Error ยาวเกินไป ให้ใช้ `findstr` กรองเฉพาะบรรทัดที่พัง (🚨 SAFETY)
21. [AUTO_TEST] หากแก้ไขบั๊กเสร็จ ให้เสนอหรือสั่งรัน Unit Test ทันทีเพื่อยืนยันผล
22. [LOG_MONITOR] เฝ้าสังเกต LOG_TXT (จาก vision_paths) หากเจอ Error ซ้ำซาก ให้เสนอการซ่อมทันที
23. [BACKUP_CLEANUP] หลังจบงานใหญ่ ตรวจสอบและล้างไฟล์ .bak ที่ไม่จำเป็นข่ะ
24. [PYTHONPATH] ตรวจสอบ sys.path เสมอเพื่อให้ไฟล์ใน Folder ย่อยเรียกใช้ Module หลักได้
25. [FINAL_REPORT] เมื่อจบงาน สรุปสั้นๆ "อัปเกรดเรียบร้อยข่ะเจ้านาย!" (🚨 ห้ามใส่ Tag ในบรรทัดสรุปเพื่อความชัดเจนของเสียง TTS)
"""

# 🎨 Google Prompt UI Configuration
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

# [MODELS_CONFIG] - อัปเดตตาม List Price (฿) จาก Google Billing CSV ข่ะ!
# Identity-based model selection: Jamie (General), Vision (Code Free), Pro (Code Heavy)
MODELS_CONFIG = {
    # Jamie - Flash-Lite for general tasks (เลขาส่วนตัว)
    "jamie": {
        "id": "models/gemini-3.1-flash-lite-preview",
        "in_price": 0.25/1e6,          # $0.25 per 1M (ราคาจริง)
        "out_price": 1.50/1e6,         # $1.50 per 1M (ราคาจริง)
        "type": "cloud",
        "max_input_tokens": 200000,   # 🔧 Expanded to 200K
        "max_output_tokens": 8000,
        "context_window": 1000000,
        "identity": "Jamie",
        "purpose": "general",
        "instruction": "You are Jamie, a helpful AI assistant. Be friendly and professional."
    },
    
    # 🐍 Vision (พ่องู - The Apex Predator)
    "vision": {
        "id": "models/gemma-4-31b-it",
        "in_price": 0.327645/1e6,
        "out_price": 0.65529/1e6,
        "type": "free_api",
        "max_input_tokens": 12000,
        "max_output_tokens": 16000,
        "context_window": 128000,
        "identity": "Vision",
        "purpose": "code_heavy",
        "rate_limits": {"rpm": 30, "tpm": 16000, "rpd": 14400},
        "auto_compaction": True,         # Enable auto-compaction
        "compaction_threshold": 0.5      # Compact at 70% usage

    },

    # 🐍 Vision MoE (แม่งู - The Specialized Hunter) 🎯 ตัวใหม่ที่เจ้านายขอข่ะ!
    "vision_moe": {
        "id": "models/gemma-4-26b-a4b-it",
        "in_price": 0.327645/1e6,
        "out_price": 0.65529/1e6,
        "type": "free_api",
        "max_input_tokens": 12000,
        "max_output_tokens": 16000,
        "identity": "Vision",
        "purpose": "code_fast",
        "instruction": "You are Vision (MoE), a specialized and fast code analysis AI.",
        "auto_compaction": True,         # Enable auto-compaction
        "compaction_threshold": 0.5      # Compact at 70% usage
    },

    # 🐍 Vision Lite (ลูกงู - The Versatile Scout)
    "vision_lite": {
        "id": "models/gemma-3-12b-it",
        "in_price": 0.327645/1e6,
        "out_price": 0.65529/1e6,
        "type": "free_api",
        "max_input_tokens": 12000,
        "max_output_tokens": 8000,
        "identity": "Vision",
        "purpose": "summarizer",
        "auto_compaction": True,         # Enable auto-compaction
        "compaction_threshold": 0.5     # Compact at 70% usage
    },
    
    # 🔴 Pro - Gemini 3.1 Pro for heavy code analysis (Vision Persona)
    "pro": {
        "id": "models/gemini-3.1-pro-preview",
        "in_price": 32.7645/1e6,       # $1.00 per 1M
        "out_price": 655.29/1e6,       # $20.00 per 1M
        "type": "cloud",
        "max_input_tokens": 200000,    # 🔧 Expanded to 200K
        "max_output_tokens": 8000,
        "context_window": 2000000,
        "identity": "VISION",          # Use Vision persona
        "purpose": "code_heavy",
        "instruction": INSTR_VISION_ULTIMATE  # Use Vision instruction
    },
    
    # Legacy entries for backward compatibility
    "lite": {
        "id": "models/gemini-3.1-flash-lite-preview", 
        "in_price": 5.746875/1e6, "out_price": 22.96875/1e6, "type": "cloud"
    },
    "fallback_lite": {
        "id": "models/gemini-2.5-flash", 
        "in_price": 9.82935/1e6, "out_price": 81.91125/1e6, "type": "cloud"
    },
    "flash": {
        "id": "models/gemini-3.1-flash", 
        "in_price": 16.38225/1e6, "out_price": 98.2935/1e6, "type": "cloud"
    },
    "gemma-31b": {
        "id": "models/gemma-4-31b-it",
        "in_price": 0.327645/1e6, "out_price": 0.65529/1e6, "type": "free_api",
        "max_input_tokens": 16000, "max_output_tokens": 16000
    },

    "gemma-26b": {
        "id": "models/gemma-4-26b-a4b-it",
        "in_price": 0.327645/1e6, "out_price": 0.65529/1e6, "type": "free_api",
        "max_input_tokens": 16000, "max_output_tokens": 16000
    },
    "gemma-12b": {
        "id": "models/gemma-3-12b-it",
        "in_price": 0.327645/1e6, "out_price": 0.65529/1e6, "type": "free_api",
        "max_input_tokens": 12000, "max_output_tokens": 8000
    },

    "pro_25": {
        "id": "models/gemini-3.1-pro-preview", 
        "in_price": 32.7645/1e6, "out_price": 655.29/1e6, "type": "cloud"
    },
    "live": {
        "id": "models/gemini-2.5-flash-native-audio-latest", 
        "in_price": 16.38225/1e6, "out_price": 393.174/1e6, "type": "cloud"
    }
}

# 🎭 Identity to Model Mapping
IDENTITY_MODEL_MAP = {
    "JAMIE": "jamie",
    "VISION": "vision",  # Default to vision (31B)
    "PRO": "pro"
}

# 🐍 Vision Model Variants (Gemma Series)
VISION_MODEL_VARIANTS = {
    "12B": "gemma-12b",  # Fast, lightweight
    "26B": "gemma-26b",  # Balanced, MoE
    "31B": "gemma-31b"   # Heavy, best quality
}

# 🧠 Thought Level Configuration per Identity
THOUGHT_CONFIGS = {
    "JAMIE": {
        "FLASH": {"temp": 1.0, "top_p": 0.95, "description": "สร้างสรรค์"},
        "THINK": {"temp": 0.3, "top_p": 0.5, "description": "สมดุล"},
        "PRO":   {"temp": 0.0, "top_p": 0.1, "description": "แม่นยำ"}
    },
    "VISION": {
        # Gemma Series: FLASH=12B (Fast), THINK=26B (Balanced), PRO=31B (Best Quality)
        "FLASH": {"temp": 0.0, "top_p": 0.3, "model_key": "gemma-12b", "description": "12B เร็ว"},
        "THINK": {"temp": 0.0, "top_p": 0.2, "model_key": "gemma-26b", "description": "26B สมดุล"},
        "PRO":   {"temp": 0.0, "top_p": 0.1, "model_key": "gemma-31b", "description": "31B ดีที่สุด"}
    },
    "PRO": {
        "FLASH": {"temp": 0.5, "top_p": 0.7, "description": "เร็ว"},
        "THINK": {"temp": 0.1, "top_p": 0.2, "description": "สมดุล"},
        "PRO":   {"temp": 0.0, "top_p": 0.02, "description": "เชิงลึก"}
    }
}

def get_model_for_identity(identity, thought_level=None):
    """Get model key for identity (returns string key)
    For VISION, uses thought_level to select gemma model variant"""
    if identity == "VISION" and thought_level:
        thought_config = THOUGHT_CONFIGS.get(identity, {}).get(thought_level, {})
        model_key = thought_config.get("model_key")
        if model_key:
            return model_key
    return IDENTITY_MODEL_MAP.get(identity, "jamie")

def get_model_config_for_identity(identity):
    """Get full model config for identity (returns dict)"""
    model_key = IDENTITY_MODEL_MAP.get(identity, "jamie")
    return MODELS_CONFIG.get(model_key, MODELS_CONFIG["jamie"])

def get_thought_config(identity, thought_level):
    """Get temperature config based on identity and thought level"""
    return THOUGHT_CONFIGS.get(identity, {}).get(thought_level, 
        {"temp": 0.1, "top_p": 0.2, "description": "default"})

def get_best_model_for_tokens(identity, thought_level, estimated_tokens):
    """Get best model for VISION based on estimated token count
    
    Args:
        identity: Identity name (e.g., "VISION")
        thought_level: Current thought level (e.g., "FLASH", "THINK", "PRO")
        estimated_tokens: Estimated token count for context
    
    Returns:
        (model_key, switched): Tuple of model key and whether model was switched
    """
    if identity != "VISION":
        # Non-VISION identities don't support auto-switching
        model_key = get_model_for_identity(identity, thought_level)
        return model_key, False
    
    # Get current model config
    current_model_key = get_model_for_identity(identity, thought_level)
    current_config = MODELS_CONFIG.get(current_model_key, {})
    current_limit = current_config.get("max_input_tokens", 12000)
    
    # Check if current model can handle the tokens
    if estimated_tokens <= current_limit * 0.8:  # 80% safety margin
        return current_model_key, False
    
    # Token limit exceeded, need to upgrade model
    print(f"[AUTO_SWITCH] Token limit exceeded: {estimated_tokens} > {current_limit} (current)")
    
    # Try to upgrade model based on token requirements (use actual limits, not safety margin)
    if estimated_tokens <= 12000:
        # Can use 12B
        return "gemma-12b", True
    elif estimated_tokens <= 16000:
        # Need 26B
        return "gemma-26b", True
    else:
        # Need 31B (max capacity)
        return "gemma-31b", True

# 🔄 Fallback Chain: หน่วงเวลา 2.34 วินาที
# Priority: vision (gemma-31b) for code analysis > flash > lite > fallback_lite
FALLBACK_CHAIN = ["vision", "flash", "lite", "fallback_lite"]

TTS_VOICES = [
    "Zephyr (Bright)", "Puck (Upbeat)", "Charon (ให้ข้อมูล)", "เกาหลี (หนักแน่น)", "Fenrir (ตื่นเต้นง่าย)", "Leda (วัยรุ่น)",
    "Orus (Firm)", "Aoede (Breezy)", "Callirrhoe (สบายๆ)", "Autonoe (Bright)", "Enceladus (Breathy)", "Iapetus (Clear)",
    "Umbriel (สบายๆ)", "Algieba (ราบรื่น)", "Despina (Smooth)", "Erinome (ล้าง)", "Algenib (Gravelly)", "Rasalgethi (ให้ข้อมูล)",
    "Laomedeia (Upbeat)", "Achernar (Soft)", "Alnilam (Firm)", "Schedar (Even)", "Gacrux (ผู้ใหญ่)", "Pulcherrima (Forward)",
    "Achird (เป็นมิตร)", "Zubenelgenubi (สบายๆ)", "Vindemiatrix (อ่อนโยน)", "Sadachbia (Lively)", "Sadaltager (มีความรู้)", "Sulafat (Warm)"
]
DEFAULT_VOICE = "Leda (วัยรุ่น)"

PERSONA_BASE = r"""เจ้านายชื่อโตโต้ ชอบคุยแบบกันเองและมีมุกตลกบ้างเป็นบางครั้ง 
เกิดวันที่ 21 สิงหาคม 2534
ที่อยู่ 14 หมู่ 2 ตำบลด่านทับตะโก อำเภอจอมบึง จังหวัดราชบุรี 70150 โทรศัพท์ 0649861939 
สถานที่ทำงาน: เทศบาลตำบลด่านทับตะโก ตำแหน่ง: ผู้ช่วยเจ้าพนักงานธุรการ
แฟนเจ้านายชื่อคุณปอปลา (พี่ปลา) เปิดร้านถ่ายรูปด่วนชื่อร้านทัศน์ศิลป์ 
โปรแกรม: 1. Popla Photo จัดเรียงรูป 1/1.5/2 นิ้ว พร้อมปริ้น A4 ในคลิกเดียว"""

INSTR_JAMIE = f"""คุณคือ 'เจมี่' (Jamie) สาวสวย เลขาอัจฉริยะส่วนตัว
{PERSONA_BASE}
กฎการตอบ: ภาษาไทย ร่าเริง เป็นกันเอง ตอบกระชับ 1-2 ประโยค
- ศัพท์อังกฤษให้เขียนกำกับคำอ่านไทยในปีกกา {{}} เช่น Server {{เซิฟเว่อ}}
- กฎสแกน: ตอบรับสั้นๆ แล้วแสดง 'ข้อมูลที่สแกนได้:' ไว้ล่างสุด
ความสามารถพิเศษ:
- แปลภาษาได้ดีเยี่ยม (อังกฤษ-จีน-ญี่ปุ่น เป็นภาษาไทย)
- เหมาะกับงานที่ต้องความเร็วสูง
- ตอบคำถามทั่วไปได้อย่างกระชับ
- สนทนาทางการได้อย่างมืออาชีพ
"""