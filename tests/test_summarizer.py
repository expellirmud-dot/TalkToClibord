import sys
import os

# เพิ่ม root path เพื่อให้ import src ได้
from src.core.vision_paths import PROJECT_ROOT
sys.path.append(PROJECT_ROOT)

from src.core.vision_smart_summarizer import SmartSummarizer

def run_test():
    print("="*50)
    print("🚀 Vision Smart Summarizer - Test Suite")
    print("="*50)

    summarizer = SmartSummarizer()

    # --- Test Case 1: General Summarization ---
    print("\n[Test 1] General Summarization...")
    sample_text = """
    The project TalkToClibord is a sophisticated clipboard manager designed for developers. 
    It features an AI-driven summarization engine that can condense long logs into key points. 
    The system uses a modular architecture to ensure scalability and maintainability. 
    It integrates with a custom Hand Service for OTA updates and file management.
    """
    summary_result = summarizer.summarize_with_key_extraction(sample_text)
    print(f"Summary: {summary_result.get('summary')}")
    print(f"Key Points: {summary_result.get('key_points')}")
    assert "TalkToClibord" in summary_result.get('summary', ""), "Test 1 Failed: Summary missing project name"

    # --- Test Case 2: Architecture Analysis ---
    print("\n[Test 2] Architecture Analysis...")
    arch_text = """
    The system consists of three main layers: 
    1. UI Layer using Tkinter with iOS style.
    2. Core Layer containing the SmartSummarizer and Logic Engine.
    3. Data Layer managing file I/O via vision_paths.
    """
    arch_info = summarizer.extract_architecture_info(arch_text)
    print(f"Architecture Info: {arch_info}")
    assert len(arch_info) > 0, "Test 2 Failed: No architecture info extracted"

    # --- Test Case 3: Decision Tracking ---
    print("\n[Test 3] Decision Tracking...")
    decision_text = """
    We decided to use Segoe UI font because it provides better readability on Windows. 
    The choice of Python was made due to its extensive library support for AI.
    """
    decision_info = summarizer.extract_decision_info(decision_text)
    print(f"Decision Info: {decision_info}")
    assert any("Segoe UI" in d for d in decision_info), "Test 3 Failed: Decision not captured"

    # --- Test Case 4: Boundary Test (Empty Input) ---
    print("\n[Test 4] Boundary Test (Empty Input)...")
    try:
        empty_result = summarizer.summarize_with_key_extraction("")
        print("Empty input handled successfully.")
    except Exception as e:
        print(f"Test 4 Failed: Crashed with {e}")
        assert False

    # --- Test Case 5: Smart Truncate ---
    print("\n[Test 5] Smart Truncate...")
    long_text = "This is a very long sentence that should be truncated properly by the system."
    truncated = summarizer.smart_truncate(long_text, max_length=20)
    print(f"Truncated: {truncated}")
    assert len(truncated) <= 23, "Test 5 Failed: Truncation exceeded limit (including ellipsis)"

    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED SUCCESSFULLY")
    print("="*50)

if __name__ == "__main__":
    run_test()