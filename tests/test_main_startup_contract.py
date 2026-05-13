"""Static startup contract tests for main.py.

These tests rely on AST analysis only to avoid launching UI or making network/API calls.
"""

from __future__ import annotations

import ast
from pathlib import Path


MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"


def _main_source() -> str:
    return MAIN_PATH.read_text(encoding="utf-8")


def _main_tree() -> ast.AST:
    return ast.parse(_main_source(), filename=str(MAIN_PATH))


def _is_name_or_attr(node: ast.AST, target: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == target
    if isinstance(node, ast.Attribute):
        return node.attr == target
    return False


def test_no_literal_assignment_to_gemini_api_key() -> None:
    tree = _main_tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if _is_name_or_attr(target, "GEMINI_API_KEY"):
                    assert not isinstance(
                        node.value, ast.Constant
                    ), "main.py must not assign GEMINI_API_KEY to a literal value."


def test_reads_gemini_api_key_from_environment() -> None:
    tree = _main_tree()
    getenv_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "getenv"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "GEMINI_API_KEY"
    ]

    assert getenv_calls, (
        "main.py must read GEMINI_API_KEY from environment via "
        "os.getenv('GEMINI_API_KEY')."
    )


def test_imports_canonical_ui_module_and_references_projectjavis() -> None:
    tree = _main_tree()

    canonical_import_found = False
    projectjavis_referenced = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.core.vision_interface":
            imported_names = {alias.name for alias in node.names}
            if "ProjectJAVIS" in imported_names:
                canonical_import_found = True

        if isinstance(node, ast.Name) and node.id == "ProjectJAVIS":
            projectjavis_referenced = True

    assert canonical_import_found, (
        "main.py must import ProjectJAVIS from canonical UI module "
        "src.core.vision_interface."
    )
    assert projectjavis_referenced, "main.py must reference ProjectJAVIS."


def test_mainloop_call_is_not_at_module_top_level() -> None:
    tree = _main_tree()

    top_level_mainloop_calls = []
    guarded_main_invocation = False

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "mainloop":
                top_level_mainloop_calls.append(node.lineno)

        if isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                for stmt in node.body:
                    if (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Call)
                        and isinstance(stmt.value.func, ast.Name)
                        and stmt.value.func.id == "main"
                    ):
                        guarded_main_invocation = True

    assert not top_level_mainloop_calls, (
        "main.py must not call mainloop at module top level; keep it in startup "
        "execution path only."
    )
    assert guarded_main_invocation, (
        "main.py should invoke main() under if __name__ == '__main__' startup guard."
    )
