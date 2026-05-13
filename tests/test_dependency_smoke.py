"""Smoke tests to keep runtime dependency declarations aligned with import contracts.

TODO: If production code starts importing third-party modules that are not declared in
requirements.txt, document them here first before changing dependencies.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _declared_requirements() -> set[str]:
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    declared: set[str] = set()
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        normalized = line.lower().replace("_", "-")
        for marker in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if marker in normalized:
                normalized = normalized.split(marker, 1)[0].strip()
                break

        if normalized:
            declared.add(normalized)

    return declared


DEPENDENCY_TO_IMPORT = {
    "google-genai": "google.genai",
    "edge-tts": "edge_tts",
    "websocket-client": "websocket",
    "pillow": "PIL",
    "keyboard": "keyboard",
    "mss": "mss",
    "numpy": "numpy",
    "pyaudio": "pyaudio",
    "pygame": "pygame",
    "pyperclip": "pyperclip",
    "speechrecognition": "speech_recognition",
    "sumy": "sumy",
    "vosk": "vosk",
    "openai-whisper": "whisper",
}


@pytest.mark.parametrize("dependency,import_name", DEPENDENCY_TO_IMPORT.items())
def test_declared_runtime_dependencies_are_importable(dependency: str, import_name: str) -> None:
    """Validate expected import modules for direct runtime dependencies."""
    declared = _declared_requirements()
    assert dependency in declared, f"{dependency} must be declared in requirements.txt"

    if importlib.util.find_spec(import_name) is None:
        pytest.skip(
            f"Declared dependency is not installed in this environment: {dependency} -> {import_name}"
        )
