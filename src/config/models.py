from src.config.prompts import INSTR_VISION_ULTIMATE

MODELS_CONFIG = {
    "jamie": {
        "id": "models/gemini-3.1-flash-lite-preview",
        "in_price": 0.25/1e6,
        "out_price": 1.50/1e6,
        "type": "cloud",
        "max_input_tokens": 200000,
        "max_output_tokens": 8000,
        "context_window": 1000000,
        "identity": "Jamie",
        "purpose": "general",
        "instruction": "You are Jamie, a helpful AI assistant. Be friendly and professional."
    },
    "vision": {
        "id": "models/gemma-4-31b-it",
        "in_price": 0.327645/1e6,
        "out_price": 0.65529/1e6,
        "type": "free_api",
        "max_input_tokens": 12000,
        "max_output_tokens": 16000,
        "context_window": 128000,
        "identity": "Vision",
        "purpose": "code_heavy",
        "rate_limits": {"rpm": 30, "tpm": 16000, "rpd": 14400},
        "auto_compaction": True,
        "compaction_threshold": 0.5
    },
    "vision_moe": {
        "id": "models/gemma-4-26b-a4b-it",
        "in_price": 0.327645/1e6,
        "out_price": 0.65529/1e6,
        "type": "free_api",
        "max_input_tokens": 12000,
        "max_output_tokens": 16000,
        "identity": "Vision",
        "purpose": "code_fast",
        "instruction": "You are Vision (MoE), a specialized and fast code analysis AI.",
        "auto_compaction": True,
        "compaction_threshold": 0.5
    },
    "vision_lite": {
        "id": "models/gemma-3-12b-it",
        "in_price": 0.327645/1e6,
        "out_price": 0.65529/1e6,
        "type": "free_api",
        "max_input_tokens": 12000,
        "max_output_tokens": 8000,
        "identity": "Vision",
        "purpose": "summarizer",
        "auto_compaction": True,
        "compaction_threshold": 0.5
    },
    "pro": {
        "id": "models/gemini-3.1-pro-preview",
        "in_price": 32.7645/1e6,
        "out_price": 655.29/1e6,
        "type": "cloud",
        "max_input_tokens": 200000,
        "max_output_tokens": 8000,
        "context_window": 2000000,
        "identity": "VISION",
        "purpose": "code_heavy",
        "instruction": INSTR_VISION_ULTIMATE
    },
    "lite": {"id": "models/gemini-3.1-flash-lite-preview", "in_price": 5.746875/1e6, "out_price": 22.96875/1e6, "type": "cloud"},
    "fallback_lite": {"id": "models/gemini-2.5-flash", "in_price": 9.82935/1e6, "out_price": 81.91125/1e6, "type": "cloud"},
    "flash": {"id": "models/gemini-3.1-flash", "in_price": 16.38225/1e6, "out_price": 98.2935/1e6, "type": "cloud"},
    "gemma-31b": {"id": "models/gemma-4-31b-it", "in_price": 0.327645/1e6, "out_price": 0.65529/1e6, "type": "free_api", "max_input_tokens": 16000, "max_output_tokens": 16000},
    "gemma-26b": {"id": "models/gemma-4-26b-a4b-it", "in_price": 0.327645/1e6, "out_price": 0.65529/1e6, "type": "free_api", "max_input_tokens": 16000, "max_output_tokens": 16000},
    "gemma-12b": {"id": "models/gemma-3-12b-it", "in_price": 0.327645/1e6, "out_price": 0.65529/1e6, "type": "free_api", "max_input_tokens": 12000, "max_output_tokens": 8000},
    "pro_25": {"id": "models/gemini-3.1-pro-preview", "in_price": 32.7645/1e6, "out_price": 655.29/1e6, "type": "cloud"},
    "live": {"id": "models/gemini-2.5-flash-native-audio-latest", "in_price": 16.38225/1e6, "out_price": 393.174/1e6, "type": "cloud"}
}

IDENTITY_MODEL_MAP = {"JAMIE": "jamie", "VISION": "vision", "PRO": "pro"}
VISION_MODEL_VARIANTS = {"12B": "gemma-12b", "26B": "gemma-26b", "31B": "gemma-31b"}
THOUGHT_CONFIGS = {
    "JAMIE": {
        "FLASH": {"temp": 1.0, "top_p": 0.95, "description": "สร้างสรรค์"},
        "THINK": {"temp": 0.3, "top_p": 0.5, "description": "สมดุล"},
        "PRO": {"temp": 0.0, "top_p": 0.1, "description": "แม่นยำ"},
    },
    "VISION": {
        "FLASH": {"temp": 0.0, "top_p": 0.3, "model_key": "gemma-12b", "description": "12B เร็ว"},
        "THINK": {"temp": 0.0, "top_p": 0.2, "model_key": "gemma-26b", "description": "26B สมดุล"},
        "PRO": {"temp": 0.0, "top_p": 0.1, "model_key": "gemma-31b", "description": "31B ดีที่สุด"},
    },
    "PRO": {
        "FLASH": {"temp": 0.5, "top_p": 0.7, "description": "เร็ว"},
        "THINK": {"temp": 0.1, "top_p": 0.2, "description": "สมดุล"},
        "PRO": {"temp": 0.0, "top_p": 0.02, "description": "เชิงลึก"},
    },
}


def get_model_for_identity(identity, thought_level=None):
    if identity == "VISION" and thought_level:
        thought_config = THOUGHT_CONFIGS.get(identity, {}).get(thought_level, {})
        model_key = thought_config.get("model_key")
        if model_key:
            return model_key
    return IDENTITY_MODEL_MAP.get(identity, "jamie")


def get_model_config_for_identity(identity):
    model_key = IDENTITY_MODEL_MAP.get(identity, "jamie")
    return MODELS_CONFIG.get(model_key, MODELS_CONFIG["jamie"])


def get_thought_config(identity, thought_level):
    return THOUGHT_CONFIGS.get(identity, {}).get(thought_level, {"temp": 0.1, "top_p": 0.2, "description": "default"})


def get_best_model_for_tokens(identity, thought_level, estimated_tokens):
    if identity != "VISION":
        model_key = get_model_for_identity(identity, thought_level)
        return model_key, False

    current_model_key = get_model_for_identity(identity, thought_level)
    current_config = MODELS_CONFIG.get(current_model_key, {})
    current_limit = current_config.get("max_input_tokens", 12000)

    if estimated_tokens <= current_limit * 0.8:
        return current_model_key, False

    print(f"[AUTO_SWITCH] Token limit exceeded: {estimated_tokens} > {current_limit} (current)")

    if estimated_tokens <= 12000:
        return "gemma-12b", True
    elif estimated_tokens <= 16000:
        return "gemma-26b", True
    else:
        return "gemma-31b", True
