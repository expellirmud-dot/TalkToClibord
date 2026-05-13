import importlib
import os


def _load_vision_config(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    if "vision_config" in importlib.sys.modules:
        del importlib.sys.modules["vision_config"]
    return importlib.import_module("vision_config")


def test_legacy_imports_still_available(monkeypatch):
    vc = _load_vision_config(monkeypatch)

    assert hasattr(vc, "GEMINI_API_KEY")
    assert hasattr(vc, "MODELS_CONFIG")
    assert hasattr(vc, "INSTR_VISION_ULTIMATE")
    assert hasattr(vc, "INSTR_JAMIE")
    assert hasattr(vc, "get_model_for_identity")
    assert hasattr(vc, "get_best_model_for_tokens")


def test_model_routing_unchanged(monkeypatch):
    vc = _load_vision_config(monkeypatch)

    assert vc.get_model_for_identity("JAMIE") == "jamie"
    assert vc.get_model_for_identity("VISION", "PRO") == "gemma-31b"
    assert vc.get_model_for_identity("PRO") == "pro"


def test_core_config_values_unchanged(monkeypatch):
    vc = _load_vision_config(monkeypatch)

    assert vc.MODELS_CONFIG["vision"]["id"] == "models/gemma-4-31b-it"
    assert vc.MODELS_CONFIG["pro"]["id"] == "models/gemini-3.1-pro-preview"
    assert vc.MODELS_CONFIG["jamie"]["in_price"] == 0.25 / 1e6
    assert vc.FALLBACK_CHAIN == ["vision", "flash", "lite", "fallback_lite"]


def test_best_model_switching_behavior_unchanged(monkeypatch):
    vc = _load_vision_config(monkeypatch)

    assert vc.get_best_model_for_tokens("JAMIE", "FLASH", 5000) == ("jamie", False)
    assert vc.get_best_model_for_tokens("VISION", "FLASH", 9000) == ("gemma-12b", False)
    assert vc.get_best_model_for_tokens("VISION", "FLASH", 13000) == ("gemma-26b", True)


def test_jamie_scan_rule_not_duplicated(monkeypatch):
    vc = _load_vision_config(monkeypatch)

    rule = "กฎสแกน: ตอบรับสั้นๆ แล้วแสดง 'ข้อมูลที่สแกนได้:' ไว้ล่างสุด"
    assert vc.INSTR_JAMIE.count(rule) == 1
