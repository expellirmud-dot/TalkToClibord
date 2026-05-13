import ast
from pathlib import Path


MAIN_PY = Path(__file__).resolve().parents[1] / "main.py"

# Drift module names are sourced from docs/ui_module_audit.md.
DRIFT_UI_MODULES = {
    "src.core.vision_interface_corrected",
    "src.core.vision_interface_updated",
    "src.core.vision_interface_optimized",
    "src.core.vision_interface_tpm",
    "src.core.vision_interface_tpm_correct",
    "src.core.vision_interface_tpm_fixed",
    "src.core.vision_interface_memory",
    "src.core.vision_interface_file_preview",
}


def _imported_modules_from_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    return imported


def test_main_imports_canonical_ui_module():
    imported_modules = _imported_modules_from_file(MAIN_PY)

    assert "src.core.vision_interface" in imported_modules


def test_main_does_not_import_drift_ui_modules():
    imported_modules = _imported_modules_from_file(MAIN_PY)

    assert imported_modules.isdisjoint(DRIFT_UI_MODULES), (
        "main.py imports drift UI modules: "
        f"{sorted(imported_modules.intersection(DRIFT_UI_MODULES))}"
    )
