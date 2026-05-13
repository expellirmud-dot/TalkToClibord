# UI Module Drift Audit

## Scope
Audit date baseline: commit `fc2c8c6`.

This audit identifies which UI module is used at runtime and classifies similarly named `src/core/vision_interface*` files as canonical, helper/mixin-style, or likely drifted duplicates.

## Canonical runtime UI module

- **Canonical module used by app startup:** `src/core/vision_interface.py`
- **Reason:** `main.py` imports `ProjectJAVIS` directly from `src.core.vision_interface` before entering the Tk mainloop.

## Runtime import path evidence

- `main.py` contains:
  - `from src.core.vision_interface import ProjectJAVIS`

No runtime imports were found for `_corrected.py`, `_updated.py`, `_optimized.py`, `_fixed.py`, or `_tpm_*` variants.

## UI-related file inventory and classification

| File | Seen imported by runtime path | Notes | Recommendation |
|---|---|---|---|
| `src/core/vision_interface.py` | **Yes** | Canonical class/module for `ProjectJAVIS` used by startup. | **Keep** |
| `src/core/vision_interface_corrected.py` | No | Suffix suggests patch/prototype variant; no active import references found. | **Needs manual diff** |
| `src/core/vision_interface_updated.py` | No | Suffix suggests iterative variant; no active import references found. | **Needs manual diff** |
| `src/core/vision_interface_optimized.py` | No | Suffix suggests performance-focused branch artifact; no active import references found. | **Needs manual diff** |
| `src/core/vision_interface_tpm.py` | No | Appears as support snippet/partial implementation, not startup target. | **Candidate for archive** |
| `src/core/vision_interface_tpm_correct.py` | No | Patch-style TPM variant, not imported by startup path. | **Candidate for archive** |
| `src/core/vision_interface_tpm_fixed.py` | No | Patch-style TPM variant, not imported by startup path. | **Candidate for archive** |
| `src/core/vision_interface_memory.py` | No | Helper-like module for memory behavior; currently not imported by startup path. | **Needs manual diff** |
| `src/core/vision_interface_file_preview.py` | No | Helper-like module for file token preview behavior; currently not imported by startup path. | **Needs manual diff** |

## Minimal next-step recommendation

1. Keep `vision_interface.py` as runtime source of truth.
2. For each non-runtime variant, perform a targeted diff against canonical module to identify unique logic worth merging.
3. After merge decisions are documented, move true duplicates to an archive folder in a separate cleanup task.

## Deterministic method used

- Import-reference scan for `vision_interface` symbols and module names.
- File inventory scan under `src/core` for `vision_interface*` files.
