from src.config.models import MODELS_CONFIG

MODEL_PRICING = {
    key: {
        "in_price": value.get("in_price"),
        "out_price": value.get("out_price"),
    }
    for key, value in MODELS_CONFIG.items()
}
