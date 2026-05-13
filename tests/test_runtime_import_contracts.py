import importlib
import sys

import pytest


CRITICAL_MODULES = [
    "vision_config",
    "src.config.settings",
    "src.config.models",
    "src.config.prompts",
    "src.config.pricing",
    "src.utils.vision_paths",
    "src.core.vision_smart_summarizer",
]


@pytest.fixture
def clean_import_cache():
    original_modules = {}
    for name in CRITICAL_MODULES:
        if name in sys.modules:
            original_modules[name] = sys.modules[name]
            del sys.modules[name]
    try:
        yield
    finally:
        for name in CRITICAL_MODULES:
            sys.modules.pop(name, None)
        sys.modules.update(original_modules)


def test_runtime_import_contracts_for_critical_startup_modules(monkeypatch, clean_import_cache):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-import-test-key")

    vision_config = importlib.import_module("vision_config")
    settings = importlib.import_module("src.config.settings")
    models = importlib.import_module("src.config.models")
    prompts = importlib.import_module("src.config.prompts")
    pricing = importlib.import_module("src.config.pricing")
    vision_paths = importlib.import_module("src.utils.vision_paths")
    smart_summarizer = importlib.import_module("src.core.vision_smart_summarizer")

    assert hasattr(vision_config, "GEMINI_API_KEY")
    assert hasattr(settings, "GEMINI_API_KEY")
    assert settings.GEMINI_API_KEY == "dummy-import-test-key"

    assert hasattr(vision_config, "MODELS_CONFIG")
    assert hasattr(models, "MODELS_CONFIG")
    assert models.MODELS_CONFIG

    assert hasattr(prompts, "INSTR_JAMIE")
    assert isinstance(prompts.INSTR_JAMIE, str)

    assert hasattr(pricing, "MODEL_PRICING")
    assert isinstance(pricing.MODEL_PRICING, dict)

    assert hasattr(vision_paths, "ROOT_DIR")
    assert vision_paths.ROOT_DIR

    assert hasattr(smart_summarizer, "SmartSummarizer")
    summarizer = smart_summarizer.SmartSummarizer()
    assert summarizer is not None
