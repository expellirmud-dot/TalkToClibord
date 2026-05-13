# Config Compatibility Aliases

`vision_config.py` remains in place as a compatibility facade so legacy imports continue to work while canonical config code lives in `src/config/*`.

## Legacy aliases (intentional)

The following aliases introduced in TASK M are intentionally preserved:

- `INSTR_VISION` -> `INSTR_VISION_ULTIMATE`
- `get_model_by_identity` -> `get_model_for_identity`
- `get_model_config` -> `get_model_config_for_identity`

## Canonical implementations

- Instruction constants: `src.config.instructions`
- Identity/model lookup functions: `src.config.models`

`vision_config.py` re-exports these symbols and aliases for backward compatibility.

## Import guidance

- New code should import from `src.config.*` where possible.
- Legacy code can continue importing from `vision_config`; those imports remain supported.
