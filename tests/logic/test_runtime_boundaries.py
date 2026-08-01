import ast
from pathlib import Path


def test_logic_runtime_core_has_no_large_methods() -> None:
    source = Path("engine/logic/runtime/core.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    runtime = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LogicGraphRuntime"
    )
    sizes = {
        node.name: node.end_lineno - node.lineno + 1
        for node in runtime.body if isinstance(node, ast.FunctionDef)
    }

    assert sizes["_evaluate_output"] < 15
    assert max(sizes.values()) < 100


def test_output_evaluation_is_isolated_from_runtime_orchestration() -> None:
    source = Path("engine/logic/runtime/output_evaluator.py").read_text(encoding="utf-8")
    assert "def evaluate_output(" in source
    assert "Ciclo de dados detectado" in source
    assert "Divisão por zero" in source
