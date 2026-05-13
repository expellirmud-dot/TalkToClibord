# UI Module Drift Audit

## Scope
Audit performed on working tree rooted at `main.py`, using deterministic import/reference scanning only.

## Canonical runtime UI module

- **Canonical runtime module:** `src/core/vision_interface.py`
- **Runtime import path in startup:** `main.py` -> `from src.core.vision_interface import ProjectJAVIS`
- **Why this is canonical:** `main.py` constructs `ProjectJAVIS()` from that import path during startup.

## Reference scanning method (grep/import scan)

Commands used:

- `rg -n "from src\.core\.vision_interface import ProjectJAVIS|ProjectJAVIS|vision_interface" main.py src`
- `rg --files src/core | rg '^src/core/vision_interface.*\.py$'`

Interpretation rule:

- **Imported by runtime code = Yes** only when referenced by startup/runtime path rooted at `main.py`.

## Duplicate/drifted UI-related files

| File | Imported by runtime code? | Classification | Recommendation |
|---|---:|---|---|
| `src/core/vision_interface.py` | Yes | Canonical runtime UI module | **Keep** |
| `src/core/vision_interface_corrected.py` | No | Drifted variant (patch/prototype naming) | **Needs manual diff** |
| `src/core/vision_interface_updated.py` | No | Drifted variant (iterative naming) | **Needs manual diff** |
| `src/core/vision_interface_optimized.py` | No | Drifted variant (optimization branch naming) | **Needs manual diff** |
| `src/core/vision_interface_tpm.py` | No | Duplicate/drifted side variant | **Candidate for archive** |
| `src/core/vision_interface_tpm_correct.py` | No | Duplicate/drifted side variant | **Candidate for archive** |
| `src/core/vision_interface_tpm_fixed.py` | No | Duplicate/drifted side variant | **Candidate for archive** |
| `src/core/vision_interface_memory.py` | No | Drifted helper-style variant | **Needs manual diff** |
| `src/core/vision_interface_file_preview.py` | No | Drifted helper-style variant | **Needs manual diff** |

## Notes

- No runtime code deletion/rename/modification was performed in this task.
- This audit is documentation-only; no dependency changes were introduced.
