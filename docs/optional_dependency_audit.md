# TASK O — Optional Dependency Lazy Import Audit

Date: 2026-05-13  
Baseline: clean HEAD `05d93fa` (as requested)

## Scope
Production code scanned:
- `main.py`
- `vision_config.py`
- `src/**/*.py`

Optional dependencies audited:
- `keyboard`
- `mss`
- `pyaudio`
- `pygame`
- `speech_recognition`
- `vosk`
- `whisper`

## Audit Summary
This audit checks whether optional dependencies can break baseline startup via top-level imports.

### keyboard
- **Imported where**: `src/core/vision_interface.py` (top-level import list).
- **Safety**: **Unsafe** for baseline startup if `keyboard` is not installed, because import happens when module is imported.
- **Recommended action**: Move `keyboard` import behind feature boundary (e.g., STT hotkey setup path) with graceful fallback/log when unavailable.

### mss
- **Imported where**: `src/core/vision_live_service.py` inside `_screen_loop()`.
- **Safety**: **Safe** (lazy import in feature function).
- **Recommended action**: No change required.

### pyaudio
- **Imported where**: `src/core/vision_live_service.py` top-level import list.
- **Safety**: **Unsafe** for baseline startup if `pyaudio` is absent.
- **Recommended action**: Lazily import in live-audio initialization path, with feature-disable fallback when unavailable.

### pygame
- **Imported where**: `src/utils/vision_audio_core.py` top-level import list.
- **Safety**: **Unsafe** for baseline startup if `pygame` is absent.
- **Recommended action**: Lazily import in audio initialization path or guard module-level import with optional-availability handling.

### speech_recognition
- **Imported where**: `src/core/vision_stt_service.py` top-level import (`import speech_recognition as sr`).
- **Safety**: **Unsafe** for baseline startup if `speech_recognition` is absent.
- **Recommended action**: Import only when STT service is initialized/used; provide clear runtime message when dependency missing.

### vosk
- **Imported where**: `src/core/vision_stt_service.py` in guarded `try/except ImportError` block near module top.
- **Safety**: **Conditionally safe** for import-time failure (does not crash module import due to guard).
- **Recommended action**: Current guard is acceptable; optionally move deeper into engine init for stricter lazy loading consistency.

### whisper
- **Imported where**: `src/core/vision_stt_service.py` in guarded `try/except ImportError` block near module top.
- **Safety**: **Conditionally safe** for import-time failure (does not crash module import due to guard).
- **Recommended action**: Current guard is acceptable; optionally move deeper into engine init for stricter lazy loading consistency.

## Unsafe Import Findings (explicit)
Unsafe top-level imports were found for:
- `keyboard`
- `pyaudio`
- `pygame`
- `speech_recognition`

No runtime changes were made in this task; this document is the audit output only.
