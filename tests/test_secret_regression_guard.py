from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".ini"}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
ALLOWLIST_VALUES = {"dummy-import-test-key", "test-key", "example-key"}

GEMINI_ASSIGNMENT_RE = re.compile(
    r"\bGEMINI_API_KEY\b\s*=\s*(['\"])(?P<value>[^'\"\n]+)\1"
)
GOOGLE_API_KEY_RE = re.compile(r"(?P<value>AIza[0-9A-Za-z_\-]{20,})")
GENERIC_SECRET_ASSIGNMENT_RE = re.compile(
    r"\b(?:api[_-]?key|secret|token|password|passwd|auth[_-]?token)\b"
    r"\s*=\s*(['\"])(?P<value>[^'\"\n]{16,})\1",
    flags=re.IGNORECASE,
)


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    files: list[Path] = []
    for rel in result.stdout.splitlines():
        candidate = Path(rel)
        if candidate.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in candidate.parts):
            continue
        files.append(REPO_ROOT / candidate)
    return files


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _is_allowlisted(value: str) -> bool:
    return value.strip().lower() in ALLOWLIST_VALUES


def _find_violations(text: str, rel_path: str) -> list[str]:
    violations: list[str] = []
    rules = [
        ("hardcoded GEMINI_API_KEY", GEMINI_ASSIGNMENT_RE),
        ("Google/Gemini API key-looking value", GOOGLE_API_KEY_RE),
        ("generic secret assignment", GENERIC_SECRET_ASSIGNMENT_RE),
    ]

    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern_name, regex in rules:
            for match in regex.finditer(line):
                value = match.group("value")
                if _is_allowlisted(value):
                    continue
                violations.append(
                    f"{rel_path}:{lineno}: {pattern_name} -> {_mask(value)}"
                )
    return violations


def test_repository_has_no_hardcoded_secrets() -> None:
    violations: list[str] = []
    for file_path in _tracked_files():
        rel_path = str(file_path.relative_to(REPO_ROOT))
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        violations.extend(_find_violations(text, rel_path))

    assert not violations, (
        "Potential hardcoded secrets detected. Replace with environment variables "
        "or allowlisted dummy values.\n" + "\n".join(violations)
    )
