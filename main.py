#!/usr/bin/env python3
# main.py - J.A.V.I.S. V6.0.0 Entry Point
# This is the main entry point for the J.A.V.I.S. AI Assistant system

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set GEMINI_API_KEY if not already set (for running directly without .bat)
if not os.getenv('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = 'AIzaSyCCeRF0hjjO7Z1o14ZMTFCApwZ1Zul2kLQ'

def main():
    """Main entry point for J.A.V.I.S. application"""
    try:
        # [V6.0.0] Pre-loading and System Checks
        print("[⚡ J.A.V.I.S. V6.0.0 Initializing...]")
        
        # 1. Ensure directory structure exists
        from src.utils.vision_paths import ensure_dirs, ROOT_DIR
        ensure_dirs()
        print(f"[✓] Directory structure verified at: {ROOT_DIR}")
        
        # 2. Validate API Key
        from vision_config import GEMINI_API_KEY
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
            print("[❌] API Key not configured! Please set GEMINI_API_KEY in vision_config.py")
            sys.exit(1)
        print("[✓] API Key validated")
        
        # 3. Pre-load critical modules into RAM
        print("[⚡] Pre-loading critical modules...")
        from src.core.vision_persistent_memory import PersistentMemory
        from src.core.vision_reference_loader import ReferenceLoader
        from src.core.vision_smart_summarizer import SmartSummarizer
        from src.utils.vision_audio_core import vision_audio
        
        # Initialize pre-loaded services
        preloaded_memory = PersistentMemory(project_dir=ROOT_DIR)
        preloaded_ref_loader = ReferenceLoader()
        preloaded_summarizer = SmartSummarizer()
        
        print(f"[✓] PersistentMemory ready")
        print(f"[✓] ReferenceLoader ready")
        print(f"[✓] SmartSummarizer ready")
        
        # 4. Import and Initialize UI Layer (Vision Interface)
        print("[⚡] Initializing Vision Interface...")
        from src.core.vision_interface import ProjectJAVIS
        
        vision_audio.speak("ต้อนรับข่ะเจ้านาย")
        app = ProjectJAVIS()
        
        #Start Auto-Fixer Heartbeat if needed
        app._start_log_monitor()  # Enable auto-fixer on startup
        
        print("[✓] J.A.V.I.S. is ready! 🚀\n")
        
        # Run the main UI loop
        app.root.mainloop()
        
    except KeyboardInterrupt:
        print("\n[!] Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"[❌ Fatal Error: {e}]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
