import ast
from pathlib import Path


VIEWPORT_SOURCE = Path("editor/widgets/phase1_viewport.py")
EXPECTED_PASS_ORDER = [
    "BackgroundPass",
    "LegacyScenePass",
    "GizmoPass",
    "FramebufferPresentPass",
    "SpriteOverlayPass",
    "GridPass",
    "OverlayPass",
    "TransformGizmoPass",
]


def _phase1_class() -> ast.ClassDef:
    tree = ast.parse(VIEWPORT_SOURCE.read_text(encoding="utf-8"))
    return next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Phase1ViewportWidget"
    )


def _method(name: str) -> ast.FunctionDef:
    return next(
        node for node in _phase1_class().body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_phase1_pipeline_keeps_official_visual_order() -> None:
    method = _method("_build_render_pipeline")
    return_node = next(node for node in ast.walk(method) if isinstance(node, ast.Return))
    pass_list = return_node.value.args[0]
    names = [item.func.id for item in pass_list.elts]

    assert names == EXPECTED_PASS_ORDER


def test_paint_gl_only_prepares_renders_and_finishes() -> None:
    method = _method("paintGL")
    called_attributes = [
        node.func.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]

    assert called_attributes == ["create_context", "render", "finish"]
    assert any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(method))


def test_viewport_has_no_private_render_pass_callbacks() -> None:
    private_callbacks = [
        node.name for node in _phase1_class().body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_render_")
    ]

    assert private_callbacks == []

