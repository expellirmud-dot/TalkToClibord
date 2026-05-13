# ==========================================
# vision_processor.py (V2.8.5 - The Full Eternal Edition)
# ==========================================

import re
import time

class VisionProcessor:
    def __init__(self):

        # 🧠 คลังแก้ไขคำอ่านผิดจาก STT (ห้ามลบแม้แต่คำเดียว!)
        self.stt_correction_map = {
            "วิเคราะห์โค้ช": "วิเคราะห์โค้ด", "วิเคราะห์คน": "วิเคราะห์โค้ด",
            "วิเคราะห์โค้ต": "วิเคราะห์โค้ด", "วิเคราะโค้ต": "วิเคราะห์โค้ด",
            "วิเคราะโค้ช": "วิเคราะห์โค้ด", "ทุบคนให้หน่อย": "ทุบโค้ด",
            "ทุบโค้ช": "ทุบโค้ด", "ทุบโค้ต": "ทุบโค้ด", "ทุบโก้ด": "ทุบโค้ด",
            "ทุกโพสต์": "ทุบโค้ด", "ทุกโค้ด": "ทุบโค้ด", "ทุบโพสต์": "ทุบโค้ด", 
            "ทุก code": "ทุบโค้ด", "ทุบโพส": "ทุบโค้ด", "ทุบโค้ด": "ทุบโค้ด",
            "โค๊ต": "โค้ด", "โค๊ด": "โค้ด", 
            "หลอกไฟล์": "Log ไฟล์", "ล็อกไฟล์": "Log ไฟล์", "หลอคไฟล์": "Log ไฟล์",
            "เจนรุป": "เจนรูป", "เจนลูก": "เจนรูป", "เจนรูป": "เจนรูป",
            "สแกน": "สแกน", "สะแกน": "สแกน", "สแก้น": "สแกน",
            "เซฟไฟล์": "บันทึกไฟล์", "เซฟ": "บันทึก", "เซฟไฟล์นี้": "บันทึกไฟล์นี้",
            "เจมีนาย": "Gemini", "เจมีนัย": "Gemini", "จะมีนาย": "Gemini",
            "เจมีไน": "Gemini", "เจมิไน": "Gemini", "เจมินาย": "Gemini",
            "เจนนี่": "เจมี่", "เจนี่": "เจมี่", "เอมมี่": "เจมี่", "เอมี่": "เจมี่", "เจมมี่": "เจมี่","เจม" : "เจมี่","แซมมี่": "เจมี่",
            "วิชาการ": "Vision", "พี่ช่าง": "Vision", "วิชัน": "Vision", "วิชัญ": "Vision",
            "วิซัน": "Vision", "วิสัน": "Vision", "วิชั่น": "Vision",
            "ซิงเกอร์": "Thinking", "สิงเกอร์": "Thinking", "ซิงกิ้ง": "Thinking",
            "คอนโทรลชิพ": "Ctrl+Shift+", "คอนโทรลกิ๊ฟ": "Ctrl+Shift+", 
            "Control Gib": "Ctrl+Shift+", "Control Gib z": "Ctrl+Shift+z", "Control Gib Z": "Ctrl+Shift+Z",
            "ยูไอ": "UI", "ui": "UI", "โค้ต": "โค้ด", "เนียม": "เนี่ยม", "เมียม": "เมี่ยม",
            "พิมเขียว": "พิมพ์เขียว", "พริ้นเขียว": "พิมพ์เขียว",
            "ปอปลา": "Popla", "ป๊อปปลา": "Popla", "ปอ-ปลา": "Popla", "ป๊อปลา": "Popla",
            "ปอปลา โฟโต้": "Popla Photo", "ป๊อปปลา โฟโต้": "Popla Photo",
            "ร้านทัศน์ศิลป์": "ร้านทัศน์ศิลป์", "ทัศนะศิลป์": "ร้านทัศน์ศิลป์",
            "เจมี่ี่": "เจมี่",
            "รันโค้ช": "รันโค้ด", "รันโค้ต": "รันโค้ด", "รันคอต": "รันโค้ด",
            "บัค": "บั๊ก", "เออเรอ": "Error", "เออเลอร์": "Error", "เออร่อ": "Error",
            # [NEW] STT terms เพิ่มเติม
            "ดีบัค": "Debug", "ดีบัก": "Debug", "ดีบั๊ก": "Debug",
            "โฟลเดอร์": "Folder", "โฟลเด้อ": "Folder", "โฟลเดอ": "Folder",
            "ไฟล์": "File", "ฟาย": "File",
            "เทอร์มินัล": "Terminal", "เทอมินอล": "Terminal", "เทอมิน่อน": "Terminal",
            "คอมพิวเตอร์": "Computer", "คอม": "Computer", "คอมพิวเต้อ": "Computer",
            "โปรแกรม": "Program", "โปรแกรมมิ่ง": "Programming",
            "อินเทอร์เน็ต": "Internet", "อินเทอร์เน็ต": "Internet", "เน็ต": "Internet",
            "เซิร์ฟเวอร์": "Server", "เซิฟเว่อ": "Server", "เซิฟเวอร์": "Server",
            "เว็บไซต์": "Website", "เว็บ": "Web",
            "ดาต้าเบส": "Database", "ดาต้าเบท": "Database", "เดต้าเบส": "Database",
            "แอพ": "App", "แอพพลิเคชั่น": "Application", "แอป": "App",
            "ซอฟต์แวร์": "Software", "ซอฟแวร์": "Software",
            "ฮาร์ดแวร์": "Hardware", "ฮาร์ดแวร์": "Hardware",
            "เน็ตเวิร์ก": "Network", "เน็ตเวอร์ค": "Network", "เน็ตเวิร์ค": "Network",
            "ไอพี": "IP", "ไอพีแอดเดรส": "IP Address",
            "พอร์ต": "Port", "พอด": "Port",
            "โปรโตคอล": "Protocol", "โพรโทคอล": "Protocol",
            "ดาเมน": "Domain", "โดเมน": "Domain", "โดเมนต์": "Domain",
            "ยูอาร์แอล": "URL", "ยูอาร์แอล": "URL",
            "เอชทีทีพี": "HTTP", "เอชทีทีพีเอส": "HTTPS",
            "เอสเอสเอช": "SSH", "เอสเอสเอช": "SSH",
            "เอฟทีพี": "FTP",
            "เอพีไอ": "API", "เอพีไอ้": "API",
            "จีซีพี": "GCP", "เอดับบลิวเอส": "AWS", "อะเมซอน": "Amazon",
            "ด็อกเกอร์": "Docker", "ดอคเคอร์": "Docker",
            "คูเบอร์เนตส": "Kubernetes", "คูเบอร์เนตีส": "Kubernetes",
            "กิท": "Git", "กิต": "Git", "กิ๊ท": "Git",
            "กิทฮับ": "GitHub", "กิทหับ": "GitHub", "กิตฮับ": "GitHub",
            "บรานช์": "Branch", "แบรนช์": "Branch", "แบรนซ์": "Branch",
            "คอมมิต": "Commit", "คอมมิด": "Commit",
            "พูลรีเควสต์": "Pull Request", "พีอาร์": "PR",
            "เมิร์จ": "Merge", "เช็คเอาท์": "Checkout",
            "พูช": "Push", "พลูล": "Pull", "โคลน": "Clone",
            "สเตจ": "Stage", "สเตจจิ้ง": "Staging",
            "รีโพสิทอรี่": "Repository", "รีโป": "Repo",
            "เวอร์ชั่น": "Version", "เวอร์ชัน": "Version",
            "รีลีส": "Release", "รีลีซ": "Release",
            "ดีพลอย": "Deploy", "ดีพลอร์ย": "Deploy",
            "บิลด์": "Build", "คอมไพล์": "Compile",
            "เทส": "Test", "เทสติ้ง": "Testing", "เทสต์": "Test",
            "ม็อก": "Mock", "สตับ": "Stub",
            "ดียูไอ": "GUI", "ยูไอ": "UI", "ยูเอ็กซ์": "UX",
            "อีดิเตอร์": "Editor", "ไอดีอี": "IDE",
            "เวอร์ช่วล": "Virtual", "เวอร์ช่วลสตูดิโอ": "Virtual Studio",
            "คอนเทนเนอร์": "Container", "คอนเทนเนอ": "Container",
            "อิมเมจ": "Image", "อิมเมจ": "Image",
            "โวลุ่ม": "Volume", "โวลุม": "Volume",
            "มิร์เรอร์": "Mirror", "มิเรอร์": "Mirror",
            "รีจิสทรี": "Registry", "รีจิสตรี": "Registry",
            "เนมสเปซ": "Namespace", "เนมสเปส": "Namespace",
            "พอด": "Pod",
            "เซอร์วิส": "Service", "เซอร์วิซ": "Service",
            "อิงเกรส": "Ingress", "อิงเกรซ": "Ingress",
            "อีเวนต์": "Event", "อีเวนท์": "Event",
            "แทรฟฟิก": "Traffic", "แทรฟฟิค": "Traffic",
            "โหลด": "Load", "โหลดบาลานซ์": "Load Balance",
            "สเกล": "Scale", "สเกลลิ่ง": "Scaling",
            "รีซอร์ซ": "Resource", "รีซอร์ส": "Resource",
            "โควต้า": "Quota", "โควตา": "Quota",
            "ลิมิต": "Limit", "ลิมิต": "Limit",
            "แคช": "Cache", "แคส": "Cache",
            "เซสชั่น": "Session", "เซสชัน": "Session",
            "คุกกี้": "Cookie",
            "โทเคน": "Token", "โทเค่น": "Token",
            "จาวาสคริปต์": "JavaScript", "จาวาสคริป": "JavaScript", "เจเอส": "JS",
            "พายธอน": "Python", "ไพธอน": "Python",
            "จาวา": "Java",
            "ซีชาร์ป": "C#", "ซีพลัสพลัส": "C++", "ซี": "C",
            "ก็อป": "Go", "โก": "Go",
            "รูสต์": "Rust",
            "สวิฟต์": "Swift",
            "คอตลิน": "Kotlin",
            "สเกล่า": "Scala",
            "เอสคิวแอล": "SQL", "เอสเคิวแอล": "SQL",
            "โนเอสคิวแอล": "NoSQL",
            "มายเอสคิวแอล": "MySQL",
            "โปสต์เกรส": "Postgres",
            "มองโกดีบี": "MongoDB", "มองโก้ดีบี": "MongoDB",
            "เรดิส": "Redis",
            "เอลาสติก": "Elastic",
            "คาซซานดรา": "Cassandra", "คาซานดรา": "Cassandra",
            "รีแอคท์": "React", "รีแอค": "React",
            "วิว": "Vue",
            "แองกูลาร์": "Angular",
            "เอสเวีเจ": "Svelte",
            "เน็กซ์เจเอส": "Next.js", "เนกซ์เจเอส": "Next.js",
            "เนสต์เจเอส": "NestJS",
            "เอ็กซ์เพรส": "Express", "เอ็กซ์เพรส": "Express",
            "ดิจองโก": "Django",
            "แฟลสก์": "Flask",
            "สปริง": "Spring",
            "ลาราเวล": "Laravel",
            "เรลส์": "Rails", "รูบี้ออนเรลส์": "Ruby on Rails",
            "เทลวินด์": "Tailwind", "เทลวินด์ซีเอสเอส": "Tailwind CSS",
            "บูตสแตรป": "Bootstrap",
            "แมททีเรียลยูไอ": "Material UI",
            "แอนด์ดีไซน์": "Ant Design",
            "ชาคร่า": "Chakra",
            "เรเดียกซ์": "Redux", "รีดักซ์": "Redux",
            "โมบเอ็ก": "MobX",
            "รีคอยล์": "Recoil",
            "โกรธ": "Growth",
            "สตอรี่บุ๊ค": "Storybook",
            "เจเอสเอ็กซ์": "JSX", "เจเอสเอ็ก": "JSX",
            "ทีเอสเอ็กซ์": "TSX", "ทีเอสเอ็ก": "TSX",
            "เอชทีเอ็มแอล": "HTML", "เอชทีเอ็มแอล": "HTML",
            "ซีเอสเอส": "CSS", "ซีเอสเอส": "CSS",
            "เอสซีเอสเอส": "SCSS", "ซาส": "Sass",
            "เลส": "Less",
            "สไตล์ดคอมโพเนนต์": "Styled Components",
            "ซีเอสเอสอินเจเอส": "CSS-in-JS",
            "เว็บแพ็ค": "Webpack", "เว็บแพค": "Webpack",
            "วีที": "Vite",
            "พาร์เซล": "Parcel",
            "โรลอัพ": "Rollup",
            "สโนว์แพ็ค": "Snowpack",
            "สวาน": "SWR",
            "รีแอคคิวรี่": "React Query",
            "แทนแสต็ก": "TanStack",
            "อัพโหลด": "Upload", "อัพโหลด": "Upload",
            "ดาวน์โหลด": "Download", "ดาวโหลด": "Download",
            "คลาวด์": "Cloud",
            "บัคเก็ต": "Bucket",
            "โฟลเดอร์": "Folder",
            "ไดเร็กทอรี่": "Directory", "ไดเรกทอรี่": "Directory",
            "อ็อบเจกต์": "Object", "อ๊อบเจ็ก": "Object",
            "อาเรย์": "Array", "อาร์เรย์": "Array",
            "สตริง": "String",
            "อินทิเจอร์": "Integer", "อินทิเจอ": "Integer",
            "ฟล็อต": "Float",
            "บูลีน": "Boolean", "บูลีอัน": "Boolean",
            "นัล": "Null", "นัลล์": "Null",
            "อันเดฟายน์": "Undefined", "อันเดฟาย": "Undefined",
            "ฟังก์ชั่น": "Function", "ฟังก์ชัน": "Function",
            "เมท็อด": "Method", "เมธอด": "Method",
            "คลาส": "Class", "คลาส": "Class",
            "อินเทอร์เฟซ": "Interface", "อินเตอร์เฟส": "Interface",
            "เนมสเปซ": "Namespace",
            "อีนัม": "Enum",
            "เจเนอริก": "Generic",
            "เทมเพลต": "Template",
            "ไทป์": "Type",
            "อินเทอร์เซปชั่น": "Intersection",
            "ยูเนี่ยน": "Union",
            "ออปชั่นแนล": "Optional", "ออปชั่นนอล": "Optional",
            "เรดโอนลี่": "Readonly", "รีดโอนลี่": "Readonly",
            "พริเวท": "Private",
            "พับลิก": "Public",
            "โปรเทคเต็ด": "Protected",
            "สตาติก": "Static", "สแตติก": "Static",
            "แอสซิง": "Async", "อะซิง": "Async",
            "อะวอิท": "Await", "อะเวท": "Await",
            "พรอมิส": "Promise", "พรอมิส": "Promise",
            "รีโซลว์": "Resolve", "รีเซอล์ฟ": "Resolve",
            "รีเจ็กต์": "Reject",
            "เทรายแคช": "Try-Catch", "ทรายแคตช์": "Try-Catch",
            "ฟินนัลลี่": "Finally", "ฟินอลลี่": "Finally",
            "ธราว": "Throw",
            "เออเร่อ": "Error", "เออเรอร์": "Error",
            "เอ็กเซ็ปชั่น": "Exception", "เอ็กเซพชั่น": "Exception",
            "สแต็ก": "Stack",
            "คิว": "Queue",
            "ดีคิว": "Deque",
            "ลิสต์": "List",
            "ลิงค์ลิสต์": "Linked List",
            "แฮช": "Hash",
            "แมป": "Map",
            "เซต": "Set",
            "ทรี": "Tree",
            "บินารี่ทรี": "Binary Tree",
            "กราฟ": "Graph",
            "ฮีป": "Heap",
            "สตั๊ก": "Stack",
            "รีเคอร์ชั่น": "Recursion", "รีเคอร์ชัน": "Recursion",
            "อิเทอเรเตอร์": "Iterator",
            "เจเนอเรเตอร์": "Generator",
            "เดคอเรเตอร์": "Decorator",
            "โพรกซี่": "Proxy",
            "โอเวอร์โหลด": "Overload",
            "โอเวอร์ไรด์": "Override",
            "อิมพลิเมนต์": "Implement", "อิมพลีเมนต์": "Implement",
            "เอ็กซ์เท็นด์": "Extend", "เอ็กซ์เทนด์": "Extend",
            "อินเฮอริท": "Inherit", "อินเฮอร์ริท": "Inherit",
            "อินสแตนซ์": "Instance", "อินสแตนซ์": "Instance",
            "คอนสตรัคเตอร์": "Constructor", "คอนสตรัคเตอร์": "Constructor",
            "ดีสตรัคเตอร์": "Destructor",
            "เก็ตเตอร์": "Getter",
            "เซ็ตเตอร์": "Setter",
            "โพรพเพอร์ตี้": "Property", "โพรพเพอร์ตี้": "Property",
            "แอททริบิวต์": "Attribute", "แอททริบิ้ว": "Attribute",
            "พารามิเตอร์": "Parameter", "พารามิเตอร์": "Parameter",
            "อาร์กิวเมนต์": "Argument", "อาร์กิวเม้นต์": "Argument",
            "รีเทิร์น": "Return", "รีเทิร์น": "Return",
            "เบรก": "Break",
            "คอนทินิว": "Continue",
            "พาส": "Pass",
            "เยลด์": "Yield",
            "เวย์ท": "Wait",
            "สลีป": "Sleep",
            "พอส": "Pause",
            "รีซูม": "Resume",
            "อินิเชียลไลซ์": "Initialize", "อินิเชอไลซ์": "Initialize",
            "เซ็ตอัพ": "Setup", "เซ็ตอัป": "Setup",
            "เทียร์ดาวน์": "Teardown", "เทียร์ดาว": "Teardown",
            "เอ็กซิคิวต์": "Execute",
            "รัน": "Run",
            "สตาร์ท": "Start",
            "สต๊อป": "Stop", "สต้อป": "Stop",
            "รีสตาร์ท": "Restart", "รีสตาร์ท": "Restart",
            "รีเซ็ต": "Reset",
            "รีเฟรช": "Refresh",
            "รีโหลด": "Reload",
            "คลีน": "Clean",
            "เคลียร์": "Clear",
            "ลบ": "Delete", "ดีลีท": "Delete", "ดีลีต": "Delete",
            "เรมูฟ": "Remove", "รีมูฟ": "Remove",
            "เคลียร์": "Clear",
            "รีเซ็ต": "Reset",
            "อัพเดท": "Update", "อัปเดต": "Update",
            "อัพเกรด": "Upgrade", "อัปเกรด": "Upgrade",
            "ดาวน์เกรด": "Downgrade",
            "อินสตอล": "Install", "อินสตอล": "Install",
            "อันินสตอล": "Uninstall",
            "ซิงค์": "Sync", "ซิง": "Sync",
            "แบ็กอัป": "Backup", "แบกอัพ": "Backup",
            "รีสโตร์": "Restore", "รีสตอร์": "Restore",
            "มิกเกรต": "Migrate", "ไมเกรต": "Migrate",
            "รีเวิว": "Review", "รีวิว": "Review",
            "อนุมัติ": "Approve",
            "ปฏิเสธ": "Reject",
            "เมิร์จ": "Merge",
            "คอนฟลิกต์": "Conflict",
            "รีโซลว์": "Resolve",
            "อิกนอร์": "Ignore",
            "สกิป": "Skip",
            "แพส": "Pass",
            "เฟล": "Fail",
            "ซักเซส": "Success", "ซัคเซส": "Success",
            "ดัน": "Done",
            "โอเค": "OK",
            "เยส": "Yes",
            "โน": "No",
            "ออฟ": "Off", "ออน": "On",
            "เอนเบิล": "Enable", "ดิสเอเบิล": "Disable",
            "โชว์": "Show", "ซ่อน": "Hide",
            "แสดง": "Display",
            "เปิด": "Open", "ปิด": "Close",
            "สร้าง": "Create", "นิว": "New",
            "เอดิต": "Edit", "แก้ไข": "Edit",
            "เซฟ": "Save", "บันทึก": "Save",
            "คัดลอก": "Copy", "ก๊อปปี้": "Copy",
            "วาง": "Paste", "เพสต์": "Paste",
            "ตัด": "Cut",
            "เลือก": "Select", "ซีเล็กต์": "Select",
            "ยกเลิก": "Cancel",
            "อันโด": "Undo", "รีโด": "Redo",
            "หาด": "Find", "ค้นหา": "Search",
            "รีเพลส": "Replace", "แทนที่": "Replace",
            "จัดเรียง": "Sort", "ซอร์ต": "Sort",
            "กรอง": "Filter", "ฟิลเตอร์": "Filter",
            "กลุ่ม": "Group", "แยก": "Split",
            "รวม": "Merge",
            "แตก": "Extract",
            "แปลง": "Convert", "คอนเวิร์ต": "Convert",
            "ฟอร์แมต": "Format",
            "พาร์ส": "Parse",
            "ซีเรียลไลซ์": "Serialize", "ซีเรียไลซ์": "Serialize",
            "ดีซีเรียลไลซ์": "Deserialize",
            "อีนโค้ด": "Encode", "ดีโค้ด": "Decode",
            "คอมเพรส": "Compress", "คอมเพรส": "Compress",
            "ดีคอมเพรส": "Decompress",
            "เอนคริปต์": "Encrypt",
            "ดีคริปต์": "Decrypt",
            "แฮช": "Hash",
            "เอนคอด": "Encode",
            "ดีคอด": "Decode",
            "เอสเคป": "Escape",
            "ทริม": "Trim",
            "สแปลท": "Split",
            "จอยน์": "Join",
            "แพด": "Pad",
            "รีพีต": "Repeat", "รีพีท": "Repeat",
            "รีเวิร์ส": "Reverse", "รีเวอร์ส": "Reverse",
            "เชัฟเฟิล": "Shuffle",
            "สแวป": "Swap",
            "โรเทท": "Rotate",
            "สเกล": "Scale",
            "รีไซซ์": "Resize",
            "ครอป": "Crop",
            "ซูม": "Zoom",
            "พัน": "Pan",
            "โฟกัส": "Focus",
            "เบลอร์": "Blur",
            "ชาร์ปเพ็น": "Sharpen",
            "อินเวอร์ต": "Invert",
            "กรายสเกล": "Grayscale",
            "ซีเปีย": "Sepia",
            "คอนทราสต์": "Contrast",
            "ไฮไลท์": "Highlight",
            "ชาโดว์": "Shadow",
            "เฟด": "Fade",
            "ทรานซิชั่น": "Transition",
            "แอนิเมชั่น": "Animation", "แอนิเมชั่น": "Animation",
            "ทวีน": "Tween",
            "คีย์เฟรม": "Keyframe",
            "ไทม์ไลน์": "Timeline",
            "เฟรม": "Frame",
            "เลเยอร์": "Layer", "เลเย่อ": "Layer",
            "มาสก์": "Mask",
            "คลิปปิ้ง": "Clipping",
            "แมททีเรียล": "Material",
            "เท็กเซอร์": "Texture",
            "เมช": "Mesh",
            "เวอร์เท็กซ์": "Vertex", "เวอร์เทอซ์": "Vertex",
            "เฟซ": "Face",
            "เอดจ์": "Edge",
            "โพลิกอน": "Polygon",
            "สเปรย์": "Sprite",
            "ริก": "Rig",
            "โมเดล": "Model", "โมเดล": "Model",
            "รีโทพอลยี": "Retopology",
            "ยูวี": "UV",
            "นอร์มอล": "Normal",
            "แทนเจนต์": "Tangent",
            "บินอร์มอล": "Binormal",
            "โลคัล": "Local", "โลคอล": "Local",
            "โกลบอล": "Global",
            "เวิลด์": "World",
            "ออบเจ็กต์": "Object",
            "พาเรนต์": "Parent",
            "ชายล์ด": "Child",
            "รูท": "Root",
            "ลีฟ": "Leaf",
            "โหนด": "Node", "โหนด": "Node",
            "เอดจ์": "Edge",
            "คอนเนคชั่น": "Connection",
            "พอร์ต": "Port",
            "ซ็อกเก็ต": "Socket",
            "สตรีม": "Stream", "สตรีม": "Stream",
            "ไซนัล": "Signal",
            "สลอต": "Slot",
            "อีเวนต์": "Event", "อีเวนท์": "Event",
            "แอคชั่น": "Action",
            "คอลแบ็ค": "Callback", "คอลแบค": "Callback",
            "ลิสเซอร์": "Listener",
            "ดีลีเกต": "Delegate",
            "อ็อบเซอร์เวอร์": "Observer",
            "ซับเจ็กต์": "Subject",
            "อ็อพเซอร์เวเบิล": "Observable",
            "สับสคริปชั่น": "Subscription",
            "ดิสโพส": "Dispose",
            "ฟินาไลซ์": "Finalize",
            "คลีนอัป": "Cleanup",
            "รีเฟอเรนซ์": "Reference", "รีเฟอร์เรนซ์": "Reference",
            "พอยเตอร์": "Pointer",
            "แอดเดรส": "Address", "แอดเดรส": "Address",
            "เมมโมรี่": "Memory", "เมมอรี่": "Memory",
            "แคช": "Cache",
            "บัฟเฟอร์": "Buffer",
            "รีจิสเตอร์": "Register",
            "ไลบรารี่": "Library", "ไลบรารี่": "Library",
            "พัคเกจ": "Package", "แพ็กเกจ": "Package",
            "โมดูล": "Module",
            "คอมโพเนนต์": "Component", "คอมโพเน้นท์": "Component",
            "พลั๊กอิน": "Plugin",
            "เอ็กซ์เท็นชั่น": "Extension", "เอ็กซ์เทนชั่น": "Extension",
            "แอดออน": "Add-on", "แอดออน": "Add-on",
            "เซอร์วิส": "Service", "เซอร์วิซ": "Service",
            "ยูทิลิตี้": "Utility",
            "เฮลเปอร์": "Helper",
            "แมเนเจอร์": "Manager", "แมเนเจอร์": "Manager",
            "คอนโทรลเลอร์": "Controller",
            "แฮนเดอร์": "Handler",
            "โปรไวเดอร์": "Provider",
            "คอนซูเมอร์": "Consumer",
            "โพรดิวเซอร์": "Producer",
            "ฟาซาด": "Facade",
            "อดัปเตอร์": "Adapter",
            "สเตราทิจี": "Strategy",
            "ฟักตอรี่": "Factory",
            "บิลเดอร์": "Builder",
            "ซิงเกิลตัน": "Singleton",
            "โพรโตไทป์": "Prototype",
            "เอ็กซ์เท็นชั่น": "Extension",
            "มิกซิน": "Mixin",
            "เทรท": "Trait",
            "อินเทอร์เฟซ": "Interface", "อินเทอร์เฟส": "Interface",
            "อับสแตรกต์": "Abstract",
            "คอนกรีต": "Concrete",
            "เซอริไลซ์เบิล": "Serializable",
            "คลโลนเบิล": "Clonable",
            "คอมพาเรเบิล": "Comparable",
            "อิเทอเรเบิล": "Iterable",
            "อิเทอเรเตอร์": "Iterator"
        }
        
        # 🗣️ คลังคำอ่านออกเสียงสำหรับ TTS (ห้ามลบแม้แต่คำเดียว!)
        self.pronunciation_map = {
            "การ์ดจอ": "ก๊าดจอ", "การ์ด": "ก๊าด", 
            "บอร์ด": "บอด", "เมนบอร์ด": "เมนบอด", "คีย์บอร์ด": "คีบอด", 
            "สมาร์ท": "สะม้าด", "สตาร์ท": "สะต๊าด", "มาร์เก็ต": "ม๊าเกต",
            "พาร์ท": "พาท", "พอร์ต": "พอด", "ชาร์จ": "ช้าด", "มาร์ค": "ม้าก", 
            "กราฟิก": "กร๊าฟฟิก", "3D": "ทีดี", "AMD": "เอเอมดี", "AI": "เอไอ",
            "NVIDIA": "เอ็นวิเดีย", "GeForce": "จีฟ้อด", "Radeon": "เรเดียน",
            "RTX": "อาทีเอก", "GTX": "จีทีเอ๊ก", "RX": "อาเอ๊ก", "GT": "จีที", "Ti": "ทีไอ",
            "GPU": "จีพียู", "CPU": "ซีพียู", "SSD": "เอสเอสดี", "HDD": "เอชดีดี",
            "Core": "คอ", "GHz": "จิกะเฮิด", "MB": "เมกะไบ", "GB": "กิกะไบ",
            "Ada Lovelace": "อาด้าเลิฟเลต",
            "Google": "กูเกิ้น", "Update": "อับเดด", "Download": "ดาวโหลด",
            "Upload": "อับโหลด", "Server": "เซิฟเว่อ", "Error": "เออเร่อ",
            "Script": "สะคริบ", "Code": "โค้ด", "Debug": "ดีบั๊ก", "Prompt": "พร้อม",
            "Gemini": "เจมิไน", "Vision": "วิชั่น", "Jamie": "เจมี่","vision": "วิชั่น", "jamie": "เจมี่", "เจ-มี่": "เจมี่","วิ-ชั่น":"วิชั่น",
            "Log": "ล็อก", "API": "เอพีไอ", "Check": "เช็ก", "เช็ค": "เช็ก",
            "Config": "คอนฟิก", "Setup": "เซ็ตอับ", "Install": "อินสตอล", 
            "System": "ซิสเต้ม", "Database": "ดาต้าเบต", 
            "Application": "แอบพิเคชั่น", "Interface": "อินเตอเฟส", "Deep": "ดี๊บ", "Learning": "เลินนิ่ง",
            "Save": "เซฟ", "Edit": "เอดดิด", "Cancel": "แคนเซิ่น", "Delete": "ดีลี๊ท",
            "รีนเดอร์": "เรนเดอร์", "Render": "เรนเดอร์", "เรน เดอร์": "เรนเดอร์",  
            "Bug": "บั๊ก", "Fix": "ฟิกซ์", "Run": "รัน", "Compile": "คอมพาย",
            "Folder": "โฟลเด่อ", "File": "ไฟล์", "Directory": "ไดเร็กเทอรี่",
            "Python": "ไพธ่อน", "JavaScript": "จาวาสะคริบ", "HTML": "เอชทีเอ็มแอล", 
            "CSS": "ซีเอสเอส", "React": "รีแอก", "Node": "โหนด", 
            "Function": "ฟังชั่น", 
            "Parameter": "พารามิเต้อ", "Variable": "วาริเอเบิ้ล", "String": "สตริง", 
            "Integer": "อินทิกเจ้อ", "Array": "อาเรย์", "Object": "อ๊อบเจ็ก", 
            "Class": "คลาส", "Method": "เมทตอด", "Loop": "ลูพ",
            "Terminal": "เทอมิน่อน", "Console": "คอนโซล", "Syntax": "ซินแท็ก",
            "Photoshop": "โฟโต้ช็อป", "Lightroom": "ไล้รูม", "Illustrator": "อิลลาสสเตเต้อ",
            "Adobe": "อะโดบี้", "Export": "เอ็กพอด", "Import": "อิมพอด",
            "Resolution": "เรโซลูชั่น", "Pixel": "พิกเซล", "Layer": "เลเย่อ",
            "Filter": "ฟิวเต้อ", "Crop": "ครอป", "Print": "ปริ๊น", "Printer": "ปริ๊นเต้อ",
            "A4": "เอสี่", "Photo": "โฟโต้", "Camera": "คาเมร่า", "Format": "ฟอแมต",
            "JPEG": "เจเป็ก", "PNG": "พีเอ็นจี", "Layout": "เลย์เอาท์",
            "Popla Photo": "ปอปลาโฟโต้",
            "Popla": "ปอปลา",
            "พจนานุกรม": "พดจะนานุกรม", "ไทเทเนียม": "ไทเทเนี่ยม",
            "พอยท์": "พ้อย", "บูลเล็ต": "บูนเล็ด", "ๆๆ": "", 
            "Morning": "ม้อนิ่ง", "Welcome": "เวลคั่ม", "Beautiful": "บิ้วตี้ฟลู",
            "Special": "สะเปเชี่ยล", "Message": "แมสเสจ", "Information": "อินฟอเมชั่น",
            "Summary": "ซัมมารี่", "Example": "อิกแซมเปิ้น", "Detail": "ดีเทล",
            "History": "ฮิสทอรี่", "Important": "อิมพ้อเท่น", "Battery": "แบตเตอรี่",
            "Surprise": "เซอร์ไพร้", "Happy": "แฮปปี้", "Dinner": "ดินเน่อ", 
            "Ready": "เรดดี้", "Schedule": "สเก็ดจูล",
            "Monitor": "มอนิเท่อ", "Desktop": "เด็ดท็อป", "Icon": "ไอค่อน",
            "Button": "บัทเทิ่น", "Mouse": "เมาส์", "Mouse mat": "เมาส์แมต",
            "Modem": "โมเด็ม", "Connect": "คะเน็ก", "Search": "เซริช",
            "Sign up": "ไซน์อับ", "Log in": "ล็อกอิน", "Log out": "ล็อกเอา",
            "Password": "พาสเวิด", "E-mail": "อีเมล", "Email": "อีเมล", "Click": "คลิก",
            "Internet": "อินเท้อเน็ด", "Social network": "โซเชี่ยลเน็ตเวิด",
            "Scanner": "สแกนเน่อ", "Speaker": "สปีคเก้อ", "Headphones": "เฮดโฟน",
            "Flash drive": "แฟลชไดร้", "Memory card": "เม็มโมรี่ก๊าด",
            "Card reader": "ก๊าดรีดเด๊อ", "Plug": "พลัก", "Socket": "ซ็อกเก็ด",
            "Copy": "ก๊อปปี้", "Paste": "เพสต", "Default": "ดีฟ้อล", "Version": "เวอชั่น",
            "เจมี่ี่": "เจมี่",
            "รันโค้ช": "รันโค้ด", "รันโค้ต": "รันโค้ด", "บัค": "บั๊ก", "เออเรอ": "Error",
            # เพิ่มศัพท์อังกฤษที่พบบ่อยใน AI responses
            "Analysis": "อะนาลิซิส", "Analyze": "อะนาไลซ์", "Data": "ดาต้า",
            "Information": "อินฟอร์เมชั่น", "Technology": "เทคโนโลยี", "Computer": "คอมพิวเตอร์",
            "Software": "ซอฟต์แวร์", "Hardware": "ฮาร์ดแวร์", "Network": "เน็ตเวิร์ก",
            "Security": "ซิคิวริตี้", "Performance": "เพอร์ฟอร์มานซ์", "Quality": "ควอลิตี้",
            "Service": "เซอร์วิส", "Support": "ซัพพอร์ต", "Solution": "โซลูชั่น",
            "Development": "ดีเวลอปเมนต์", "Programming": "โปรแกรมมิ่ง", "Framework": "เฟรมเวิร์ก",
            "Library": "ไลบรารี", "Package": "แพ็กเกจ", "Module": "โมดูล",
            "Project": "โปรเจกต์", "Task": "ทาสก์", "Feature": "ฟีเจอร์",
            "User": "ยูสเซอร์", "Client": "ไคลเอนต์", "Server": "เซิร์ฟเวอร์",
            "Database": "เดต้าเบส", "Storage": "สตอเรจ", "Memory": "เมมโมรี่",
            "Process": "โพรเซส", "Thread": "เทรด", "Async": "อะซิงค์",
            "Stream": "สตรีม", "Buffer": "บัฟเฟอร์", "Queue": "คิว",
            "Response": "รีสปอนส์", "Request": "รีเควสต์", "Message": "เมสเสจ",
            "Success": "ซัคเซส", "Failure": "เฟลเยอร์", "Warning": "วอร์นิ่ง",
            "Status": "สเตตัส", "Exception": "เอกเซ็ปชั่น",
            "Method": "เมท็อด", "Class": "คลาส",
            "List": "ลิสต์",
            "Dictionary": "ดิกชันนารี", "Tuple": "ทูเปิล", "Set": "เซ็ต",
            "String": "สตริง", "Number": "นัมเบอร์", "Boolean": "บูลเลียน",
            "True": "ทรู", "False": "ฟอลส์", "None": "นัน",
            "Import": "อิมพอร์ต", "Export": "เอ็กซพอร์ต", "Return": "รีเทิร์น",
            "Print": "พริ้นต์", "Input": "อินพุต", "Output": "เอาต์พุต",
            "Path": "แพธ",
            "Create": "ครีเอต", "Read": "รีด", "Write": "ไรท์",
            "Delete": "ดีลีท", "Update": "อัปเดต", "Insert": "อินเซิร์ต",
            "Select": "เซเล็กต์", "From": "ฟรอม", "Where": "แวร์",
            "Join": "จอยน์", "Group": "กรุ๊ป", "Order": "ออร์เดอร์",
            "Limit": "ลิมิต", "Offset": "ออฟเซ็ต", "Index": "อินเด็กซ์",
            "Key": "คีย์", "Value": "วาลู", "Type": "ไทป์",
            "Length": "เลงธ์", "Size": "ไซส์", "Count": "เคานต์",
            "Sum": "ซัม", "Average": "เอเวอเรจ", "Max": "แม็กซ์",
            "Min": "มิน", "Sort": "ซอร์ต",
            "Map": "แม็ป", "Reduce": "รีดิวซ์",
            "Lambda": "แลมดา", "Yield": "ยีลด์", "Await": "อะเวท",
            "Sync": "ซิงค์", "Lock": "ล็อก",
            "Semaphore": "เซมาฟอร์", "Event": "อีเวนต์", "Condition": "คอนดิชัน"
        }
        self._compile_patterns()

    def _compile_patterns(self):
       
        # ใช้ Raw Strings (r'...') เพื่อความแม่นยำของ Backslash ข่ะ
        self.code_fixed_tag_pattern = re.compile(r'\[Code Fixed\].*?\[Code Fixed\]', re.DOTALL)
        self.vowel_pattern = re.compile(r'([ิีึืุูเแโใไ็่้๊๋])\1+')
        self.code_pattern = re.compile(r'```.*?```', re.DOTALL)
        self.header_pattern = re.compile(r'^\s*\*\*(?:เจมี่|วิชั่น)\*\*\s*:\s*')
        self.emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf]')
        self.pronunc_pattern = re.compile(r'([a-zA-Z0-9_]+)\s*{([^}]+)}')
        self.floating_braces_pattern = re.compile(r'{([^}]+)}')

    def fix_stt_text(self, text):
        if not text: return ""
        text = text.replace("เจมี่ี่", "เจมี่")
       
        # คืนค่า \1 ให้กับ Regex sub
        text = self.vowel_pattern.sub(r'\1', text)
        for wrong, right in self.stt_correction_map.items():
            text = re.sub(wrong, right, text, flags=re.IGNORECASE)
        return text.strip()

    def clean_for_display(self, text):
        if not text: return ""
        
        start_time = time.time()
        
        # Show text as-is without pronunciation processing
        result = text.strip()
        
        processing_time = time.time() - start_time
        if processing_time > 0.01:  # Log if processing takes more than 10ms
            print(f"[PERF] clean_for_display: {processing_time:.3f}s")
        
        return result

    def clean_for_speech(self, text):
        if not text: return ""
        
        start_time = time.time()
        original_text = text
        
        markers = ["ข้อมูลที่สแกนได้:", "เนื้อหาที่สแกนได้:", "Extracted Data:", "ผลลัพธ์:"]
        for marker in markers:
            if marker in text:
                text = text.split(marker)[0]
                break
        
        text = self.code_pattern.sub('', text)
        text = self.code_fixed_tag_pattern.sub('', text)
        text = self.header_pattern.sub('', text)
        text = self.emoji_pattern.sub('', text)
        
        # คืนค่าการแทนที่ Group \1 และ \2 ให้สมบูรณ์ข่ะ!
        text = self.pronunc_pattern.sub(r' \2 ', text)
        text = self.floating_braces_pattern.sub(r' \1 ', text)
        
        text = text.replace('**', '')
        
        sorted_keys = sorted(self.pronunciation_map.keys(), key=len, reverse=True)
        for key in sorted_keys:
            val = self.pronunciation_map[key]
            if any('\u0e00' <= c <= '\u0e7f' for c in key):
                text = text.replace(key, val)
            else:
                text = re.sub(r'\b' + re.escape(key) + r'\b', val, text, flags=re.IGNORECASE)
        
        final_text = text.strip()
        if not final_text and original_text.strip():
            final_text = "ขออภัยค่ะ เจมี่ไม่สามารถอ่านข้อความนี้ได้"
        
        processing_time = time.time() - start_time
        if processing_time > 0.05:  # Log if processing takes more than 50ms
            print(f"[PERF] clean_for_speech: {processing_time:.3f}s")
        
        return final_text

    def chunk_code(self, code: str, max_lines: int = 300):
        """หั่นโค้ดเป็นส่วนๆ เพื่อให้ AI ประมวลผลได้แม่นยำขึ้นข่ะ"""
        lines = code.splitlines()
        return ["\n".join(lines[i:i + max_lines]) for i in range(0, len(lines), max_lines)]

    def clean_code_for_ai(self, code: str):
        """ลบคอมเมนต์ขยะหรือบรรทัดว่างที่เยอะเกินไปเพื่อประหยัด Token ข่ะ"""
        # ลบบรรทัดว่างที่ติดกันเกิน 2 บรรทัด
        code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
        return code.strip()

    def process_voice_command(self, text, identity="VISION"):
        """Process voice command for AI tasks - สำหรับงานโค้ดและงานทั่วไป"""
        if not text:
            return ""
        
        # Fix STT errors first
        text = self.fix_stt_text(text)
        
        # Voice command patterns for code tasks
        code_commands = {
            r'วิเคราะห์.*โค้ด|วิเคราะห์นี้|วิเคราะห์.*ไฟล์': 'วิเคราะห์โค้ดนี้',
            r'แก้ไข.*โค้ด|แก้.*โค้ด|ทุบ.*โค้ด': 'แก้ไขโค้ดให้ถูกต้อง',
            r'วิเคราะห์.*บั๊ก|หา.*บั๊ก|ดีบั๊ก': 'วิเคราะห์และแก้ไขบั๊ก',
            r'อธิบาย.*ฟังก์ชัน|อธิบาย.*โค้ด': 'อธิบายการทำงานของโค้ด',
            r'สแกน.*โค้ด|ดีป.*สแกน': 'deep scan โค้ดนี้',
            r'รัน.*โค้ด|ทดสอบ.*โค้ด': 'ทดสอบการทำงานของโค้ด',
        }
        
        # Voice command patterns for general tasks
        general_commands = {
            r'สวิตช์.*โมเดล|สลับ.*โมเดล|เปลี่ยน.*โมเดล': 'สลับโมเดล AI',
            r'เปิด.*ไมค์|เปิด.*เสียง': 'เปิดรับเสียง',
            r'ปิด.*ไมค์|ปิด.*เสียง': 'ปิดรับเสียง',
            r'เคลียร์.*ไฟล์|ล้าง.*ไฟล์': 'ล้างไฟล์แนบทั้งหมด',
            r'ส่ง.*คำสั่ง|ทำงาน': 'ส่งคำสั่ง',
            r'วาง.*คลิปบอร์ด': 'วางจากคลิปบอร์ด',
            r'แนบ.*ไฟล์|เพิ่ม.*ไฟล์': 'แนบไฟล์',
        }
        
        # Check for code commands (priority for Vision identity)
        if identity == "VISION":
            for pattern, replacement in code_commands.items():
                if re.search(pattern, text, re.IGNORECASE):
                    return replacement
        
        # Check for general commands
        for pattern, replacement in general_commands.items():
            if re.search(pattern, text, re.IGNORECASE):
                return replacement
        
        # If no command pattern matched, return original text (for natural language queries)
        return text