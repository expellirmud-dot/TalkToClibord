# ==========================================
# seed_vault.py (One-time Memory Injector)
# ==========================================
import json
import os
from datetime import datetime

def seed_memory():
    filepath = "root/vault.json"
    
    # 🧠 คลังข้อมูลความจำระดับ VIP ของกุนซือโตโต้
    vault_data = {
        "project_context": {
            "Workplace": {"value": "เทศบาลตำบลด่านทับตะโก (จ.ราชบุรี)", "timestamp": "2026-04-13"},
            "Position": {"value": "ผู้ช่วยเจ้าพนักงานธุรการ", "timestamp": "2026-04-13"},
            "Smart_Vaccine_DTK": {"value": "ระบบลงทะเบียนวัคซีนสุนัขและแมว ผ่าน LINE API", "timestamp": "2026-04-13"},
            "LUMINA_Project": {"value": "ระบบประมวลผลแสง Batch Processing (L* Extraction)", "timestamp": "2026-04-13"},
            "CurrencyWarAI": {"value": "โปรเจกต์วิเคราะห์หน้าจอเกมด้วย OCR (85 ไฟล์)", "timestamp": "2026-04-13"}
        },
        "learned_logic": {
            "Code_Rule": {"value": "ต้องส่งโค้ดแบบ Full Code/Full Function ที่คัดลอกวางรันได้ทันทีเสมอ", "timestamp": "2026-04-13"},
            "Overwrite_Policy": {"value": "ห้ามเซฟทับไฟล์เดิม ให้ส่งผลลัพธ์ไปที่ outbox_fixed.py เท่านั้น", "timestamp": "2026-04-13"},
            "Skin_Tone_Formula": {"value": "Target Skin 120 / Divisor 70 (สูตรวัดแสงอมตะ)", "timestamp": "2026-04-13"},
            "Double_Pass_Scan": {"value": "แสกนที่ขนาด 300px และ 800px เพื่อความแม่นยำสูงสุด", "timestamp": "2026-04-13"}
        },
        "user_preferences": {
            "UI_Style": {"value": "Minimal White Clean (ขาวโปร่งใส) ฟอนต์ไทยสมัยใหม่", "timestamp": "2026-04-13"},
            "Reporting_Style": {"value": "จดรายงานการประชุมแบบละเอียด (Verbatim / คำต่อคำ)", "timestamp": "2026-04-13"},
            "Developer_Info": {"value": "คุณโตโต้ เกิด 21 ส.ค. 2534 เรียนวิทยาการคอมพิวเตอร์ ม.ปทุมธานี", "timestamp": "2026-04-13"}
        }
    }

    if not os.path.exists("root"):
        os.makedirs("root")

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(vault_data, f, ensure_ascii=False, indent=4)
        print(f"✅ ฉีดความจำลง {filepath} เรียบร้อยแล้วข่ะเจ้านาย!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    seed_memory()