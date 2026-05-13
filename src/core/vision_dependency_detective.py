# vision_dependency_detective.py (V5.0.6 - Deep Scan Enabled)
import os, re, ast
from src.utils.vision_utils import sys_log
import time

class DependencyDetective:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        # Cache สำหรับเก็บผลการสแกนล่าสุด
        self.scan_cache = {}
        self.cache_ttl = 300  # 5 นาที

    def extract_parts(self, file_path, keywords):
        try:
            # Check cache ก่อน
            cache_key = f"{file_path}:{hash(tuple(sorted(keywords)))}"
            current_time = time.time()
            
            if cache_key in self.scan_cache:
                cached_data = self.scan_cache[cache_key]
                if current_time - cached_data['timestamp'] < self.cache_ttl:
                    return cached_data['result']
            
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # ถ้าไม่ใช่ไฟล์ Python ให้ดึงมาแค่ส่วนหัวเพื่อประหยัด Token ข่ะ
            if not file_path.endswith('.py'):
                result = source[:3000] if len(source) > 3000 else source
                # Cache ผลลัพธ์
                self.scan_cache[cache_key] = {'result': result, 'timestamp': current_time}
                return result

            # ให้ Python อ่านโค้ดและแยกแยะโครงสร้าง (AST)
            tree = ast.parse(source)
            extracted = list()
            signatures = list()
            imports = list()
            
            # เก็บ imports ไว้ด้วย
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
                
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # ถ้าชื่อคลาสหรือฟังก์ชัน ถูกพูดถึงในคำถาม/คลิปบอร์ด ของเจ้านาย
                    if any(keyword.lower() in node.name.lower() for keyword in keywords):
                        try:
                            extracted.append(ast.get_source_segment(source, node))
                        except:
                            # Fallback: สร้าง source segment เอง
                            lines = source.split('\n')
                            start_line = node.lineno - 1
                            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
                            extracted.append('\n'.join(lines[start_line:end_line]))
                    
                    # ถ้าไม่ถูกพูดถึง ให้เก็บแค่ 'โครงสร้างเปล่า' (Signature) 
                    elif isinstance(node, ast.ClassDef): 
                        signatures.append(f"class {node.name}:")
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): 
                        args = [arg.arg for arg in node.args.args]
                        signatures.append(f"def {node.name}({', '.join(args[:3])}{'...' if len(args) > 3 else ''}):")
            
            # 1. ถ้าเจอส่วนที่เจ้านายสั่ง ให้ส่งเฉพาะส่วนนั้นแบบ Full Code
            if extracted and all(item is not None for item in extracted):
                result = "\n\n".join(extracted)
            else:
                # 2. ถ้าไม่ได้เจาะจง ให้ส่งแค่ "โครงสร้าง" ประหยัด Token ไปได้มหาศาล!
                try:
                    if imports and signatures and all(item is not None for item in imports) and all(item is not None for item in signatures):
                        result = f"# เจ้านายไม่ได้ระบุฟังก์ชันที่เจาะจง เจมี่เลยดึงมาเฉพาะโครงสร้าง (Signatures) ข่ะ:\n" + "\n".join(imports[:5]) + "\n\n" + "\n".join(signatures[:10])
                    elif imports and all(item is not None for item in imports):
                        result = f"# เจ้านายไม่ได้ระบุฟังก์ชันที่เจาะจง เจมี่เลยดึงมาเฉพาะโครงสร้าง (Signatures) ข่ะ:\n" + "\n".join(imports[:5])
                    elif signatures and all(item is not None for item in signatures):
                        result = f"# เจ้านายไม่ได้ระบุฟังก์ชันที่เจาะจง เจมี่เลยดึงมาเฉพาะโครงสร้าง (Signatures) ข่ะ:\n" + "\n".join(signatures[:10])
                    else:
                        result = "# ไม่พบโครงสร้างที่เกี่ยวข้องในไฟล์นี้"
                except:
                    result = "# ไม่สามารถวิเคราะห์โครงสร้างไฟล์นี้ได้"
            
            # Cache ผลลัพธ์
            self.scan_cache[cache_key] = {'result': result, 'timestamp': current_time}
            return result

        except Exception as e:
            error_msg = f"# Error reading {os.path.basename(file_path)}: {str(e)}"
            return error_msg

    def scan_local_dependencies(self, text_content):
        import time
        
        # 1. หาชื่อไฟล์ทั้งหมดที่เกี่ยวข้อง (รองรับ path แบบเต็มด้วย)
        file_patterns = [
            r'[\w\-]+\.py',
            r'[\w\-]+\.json', 
            r'[\w\-]+\.md',
            r'[\w\-]+\.txt',
            r'[\w\-]+\.yml',
            r'[\w\-]+\.yaml'
        ]
        
        detected_files = set()
        for pattern in file_patterns:
            detected_files.update(re.findall(pattern, text_content))
        
        if not detected_files: 
            return ""

        # 2. แกะคำทั้งหมดออกมาเป็น Keywords เพื่อเอาไปค้นหาฟังก์ชัน
        keywords = set(re.findall(r'[a-zA-Z_]\w*', text_content))
        # เพิ่มคำสำคัญจากชื่อไฟล์ด้วย
        for fname in detected_files:
            base_name = os.path.splitext(fname)[0]
            keywords.add(base_name)
        
        context_blocks = list()
        processed_files = []
        
        # ตรวจสอบโหมด Deep Scan
        is_deep_scan = any(k in text_content.lower() for k in [
            "deep scan", "แสกนลึก", "สแกนลึก", "scan all", "ทั้งหมด"
        ])
        
        # จำกัดจำนวนไฟล์ตามโหมด
        limit = 10 if is_deep_scan else 3
        
        # จัดลำดับความสำคัญของไฟล์ (.py ก่อน อื่นทีหลัง)
        py_files = [f for f in detected_files if f.endswith('.py')]
        other_files = [f for f in detected_files if not f.endswith('.py')]
        sorted_files = py_files + other_files
        
        # Show detective scanning status
        sys_log("Detective", "[🔍 สแกนไฟล์...] เริ่มวิเคราะห์ไฟล์ที่เกี่ยวข้อง\n")
        
        for fname in sorted_files[:limit]:
            target_path = os.path.join(self.base_dir, fname)
            if os.path.exists(target_path) and os.path.isfile(target_path):
                try:
                    sys_log("Detective", f" สแกนไฟล์: {fname} (Deep Scan: {is_deep_scan})")
                    snippet = self.extract_parts(target_path, keywords)
                    
                    # ตรวจสอบว่า snippet ไม่ใช่ None ก่อนนำไปใช้
                    if snippet is not None and snippet != "":
                        # จัดรูปแบบ output ให้สวยงาม
                        context_blocks.append(
                            f"--- [FILE: {fname}] ---\n"
                            f"{snippet}\n"
                            f"--- [END: {fname}] ---"
                        )
                        processed_files.append(fname)
                    else:
                        # ถ้า snippet เป็น None หรือว่าง ให้ข้ามไฟล์นี้
                        sys_log("Detective", f"  ข้ามไฟล์ {fname}: ไม่พบข้อมูลที่เกี่ยวข้อง")
                except Exception as e:
                    sys_log("Detective", f" ไม่สามารถอ่าน {fname}: {e}")
                    context_blocks.append(
                        f"--- [ERROR: {fname}] ---\n"
                        f"# Error: {str(e)}\n"
                        f"--- [END: {fname}] ---"
                    )
        
        # ลบ cache เก่าๆ บางครั้ง
        if len(self.scan_cache) > 50:
            # เก็บไว้ 20 ล่าสุด
            sorted_items = sorted(self.scan_cache.items(), key=lambda x: x[1]['timestamp'], reverse=True)
            self.scan_cache = dict(sorted_items[:20])
        
        if context_blocks:
            header = f"[SMART DETECTIVE] {'(Deep Scan)' if is_deep_scan else '(Quick Scan)'}\n"
            header += f"Files analyzed: {len(processed_files)}/{len(detected_files)}\n"
            header += f"Keywords found: {len(keywords)}\n"
            header += "-" * 50 + "\n"
            
            # Ensure context_blocks is not empty and all elements are strings
            if context_blocks and all(isinstance(block, str) for block in context_blocks):
                return header + "\n\n".join(context_blocks)
            else:
                return header + "\n[!] ไม่พบข้อมูลที่เกี่ยวข้อง"
        
        return ""