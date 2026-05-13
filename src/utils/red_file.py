import os

# โฟลเดอร์ที่ต้องการสแกน
FOLDER_PATH = "./"

# นามสกุลไฟล์ที่สนใจ
TARGET_EXTENSIONS = [".py", ".js", ".ts", ".json", ".md"]

print("\n===== PROJECT FILE SUMMARY =====\n")

for root, dirs, files in os.walk(FOLDER_PATH):
    for filename in files:

        # กรองเฉพาะไฟล์ที่ต้องการ
        if any(filename.endswith(ext) for ext in TARGET_EXTENSIONS):

            file_path = os.path.join(root, filename)

            print(f"\n📄 FILE: {file_path}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:

                    # อ่านแค่ช่วงต้นไฟล์
                    lines = []

                    for _ in range(20):
                        line = f.readline()
                        if not line:
                            break

                        line = line.strip()

                        # เอาเฉพาะบรรทัดที่น่าจะอธิบายหน้าที่
                        if (
                            line.startswith("#")
                            or line.startswith("//")
                            or line.startswith("/*")
                            or '"""' in line
                            or "class " in line
                            or "def " in line
                        ):
                            lines.append(line)

                    if lines:
                        print("📝 SUMMARY:")
                        for l in lines[:10]:
                            print("   ", l)

                    else:
                        print("📝 No obvious summary found.")

            except Exception as e:
                print(f"❌ อ่านไม่ได้: {e}")
