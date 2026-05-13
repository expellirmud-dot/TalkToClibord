import sys

from src.utils.vision_paths import ROOT_DIR

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.core.vision_smart_summarizer import SmartSummarizer


def test_basic_summarization_returns_non_empty_string():
    summarizer = SmartSummarizer(max_tokens=200)
    sample_text = (
        "TalkToClibord summarizes long content. "
        "Added tests and Fixed edge cases for summaries."
    )

    result = summarizer.summarize_with_key_extraction(sample_text)

    assert isinstance(result, str)
    assert result.strip() != ""


def test_keyword_extraction_works():
    summarizer = SmartSummarizer()
    text = "Added unit tests.\nNeutral sentence.\nFixed truncation bug."

    key_points = summarizer.extract_key_points(text)

    assert any("Added" in point for point in key_points)
    assert any("Fixed" in point for point in key_points)


def test_smart_truncate_respects_max_chars():
    summarizer = SmartSummarizer()
    text = "This is a very long sentence that should be truncated properly."

    truncated = summarizer.smart_truncate(text, max_chars=20)

    assert len(truncated) <= 20 + len("\n... [truncated]")


def test_empty_input_handled_safely():
    summarizer = SmartSummarizer()

    result = summarizer.summarize_with_key_extraction("")

    assert result == ""
