"""Smoke tests to keep dependency declarations aligned with import contracts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _declared_requirements(filename: str) -> set[str]:
    requirements_path = ROOT / filename
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


CORE_DEPENDENCY_TO_IMPORT = {
    "google-genai": "google.genai",
    "edge-tts": "edge_tts",
    "websocket-client": "websocket",
    "pillow": "PIL",
    "numpy": "numpy",
    "pyperclip": "pyperclip",
    "sumy": "sumy",
}


OPTIONAL_DEPENDENCY_TO_IMPORT = {
    "keyboard": "keyboard",
    "mss": "mss",
    "pyaudio": "pyaudio",
    "pygame": "pygame",
    "speechrecognition": "speech_recognition",
    "vosk": "vosk",
    "openai-whisper": "whisper",
}


@pytest.mark.parametrize("dependency,import_name", CORE_DEPENDENCY_TO_IMPORT.items())
def test_core_dependencies_are_declared_and_importable(
    dependency: str, import_name: str
) -> None:
    declared = _declared_requirements("requirements.txt")
    assert dependency in declared, f"{dependency} must be declared in requirements.txt"

    if importlib.util.find_spec(import_name) is None:
        pytest.skip(
            f"Core dependency is not installed in this environment: {dependency} -> {import_name}"
        )


@pytest.mark.parametrize("dependency,import_name", OPTIONAL_DEPENDENCY_TO_IMPORT.items())
def test_optional_dependencies_are_declared_and_importable_when_installed(
    dependency: str, import_name: str
) -> None:
    declared = _declared_requirements("requirements-optional.txt")
    assert dependency in declared, (
        f"{dependency} must be declared in requirements-optional.txt"
    )

    if importlib.util.find_spec(import_name) is None:
        pytest.skip(
            f"Optional dependency is not installed in this environment: {dependency} -> {import_name}"
        )
