import importlib
import sys

import pytest


CONFIG_MODULES = [
    "vision_config",
    "src.config.settings",
    "src.config.models",
    "src.config.prompts",
    "src.config.pricing",
]


@pytest.fixture
def fresh_config_imports(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-contract-key")

    for name in CONFIG_MODULES:
        sys.modules.pop(name, None)

    modules = {name: importlib.import_module(name) for name in CONFIG_MODULES}
    return modules


def test_legacy_facade_exports_runtime_symbols(fresh_config_imports):
    vision_config = fresh_config_imports["vision_config"]

    expected_symbols = [
        "GEMINI_API_KEY",
        "MODELS_CONFIG",
        "INSTR_JAMIE",
        "INSTR_VISION",
        "get_model_by_identity",
        "get_model_config",
    ]

    for symbol in expected_symbols:
        assert hasattr(vision_config, symbol), f"vision_config missing legacy export: {symbol}"


def test_config_module_ownership_is_stable(fresh_config_imports):
    settings = fresh_config_imports["src.config.settings"]
    models = fresh_config_imports["src.config.models"]
    prompts = fresh_config_imports["src.config.prompts"]
    pricing = fresh_config_imports["src.config.pricing"]

    assert hasattr(prompts, "INSTR_JAMIE")
    assert hasattr(prompts, "INSTR_VISION_ULTIMATE")

    assert hasattr(models, "MODELS_CONFIG")
    assert hasattr(models, "IDENTITY_MODEL_MAP")
    assert hasattr(models, "get_model_for_identity")
    assert hasattr(models, "get_model_config_for_identity")

    assert hasattr(pricing, "MODEL_PRICING")

    assert hasattr(settings, "GEMINI_API_KEY")
    assert hasattr(settings, "FALLBACK_CHAIN")
    assert hasattr(settings, "UI_STYLE")


def test_facade_symbols_map_to_owning_modules(fresh_config_imports):
    vision_config = fresh_config_imports["vision_config"]
    settings = fresh_config_imports["src.config.settings"]
    models = fresh_config_imports["src.config.models"]
    prompts = fresh_config_imports["src.config.prompts"]

    assert vision_config.GEMINI_API_KEY == settings.GEMINI_API_KEY
    assert vision_config.MODELS_CONFIG is models.MODELS_CONFIG
    assert vision_config.INSTR_JAMIE == prompts.INSTR_JAMIE
    assert vision_config.INSTR_VISION == prompts.INSTR_VISION_ULTIMATE
    assert vision_config.get_model_by_identity is models.get_model_for_identity
    assert vision_config.get_model_config is models.get_model_config_for_identity
