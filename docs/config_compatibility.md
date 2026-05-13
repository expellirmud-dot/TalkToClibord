# Config Compatibility Aliases

This project keeps `vision_config.py` as a compatibility facade to avoid breaking legacy imports while config code is organized under `src/config/*`.

## Legacy aliases kept intentionally

The following legacy names remain supported for backward compatibility:

- `INSTR_VISION` -> `INSTR_VISION_ULTIMATE`
- `get_model_by_identity` -> `get_model_for_identity`
- `get_model_config` -> `get_model_config_for_identity`

## Canonical ownership

Canonical implementations live in the newer config modules under `src/config/*`:

- canonical instruction constants are defined in `src.config.instructions`
- canonical identity-based model lookups are defined in `src.config.models`

`vision_config.py` re-exports compatibility aliases that point to these canonical implementations.

## Import guidance

- **New code**: import directly from `src.config.*` modules.
- **Legacy code**: `vision_config` imports remain supported and are intentionally preserved for compatibility.
