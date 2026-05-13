# vision_config.py (compatibility facade)
from google.genai import types

from src.config.settings import GEMINI_API_KEY, UI_STYLE, FALLBACK_CHAIN, TTS_VOICES, DEFAULT_VOICE
from src.config.prompts import INSTR_VISION_ULTIMATE, PERSONA_BASE, INSTR_JAMIE
from src.config.models import (
    MODELS_CONFIG,
    IDENTITY_MODEL_MAP,
    VISION_MODEL_VARIANTS,
    THOUGHT_CONFIGS,
    get_model_for_identity,
    get_model_config_for_identity,
    get_thought_config,
    get_best_model_for_tokens,
)
from src.config.pricing import MODEL_PRICING
