from __future__ import annotations

import builtins
import importlib
import sys

import pytest


OPTIONAL_IMPORTS = {"keyboard", "pyaudio", "pygame", "speech_recognition"}
MODULES_UNDER_TEST = [
    "src.core.vision_live_service",
    "src.core.vision_stt_service",
    "src.utils.vision_audio_core",
    "src.core.vision_interface",
]


def _blocking_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".", 1)[0]
    if root in OPTIONAL_IMPORTS:
        raise ImportError(f"blocked optional dependency: {name}")
    return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


_ORIGINAL_IMPORT = builtins.__import__


@pytest.mark.parametrize("module_name", MODULES_UNDER_TEST)
def test_module_import_does_not_require_optional_dependencies(module_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(builtins, "__import__", _blocking_import)
    sys.modules.pop(module_name, None)
    importlib.import_module(module_name)
