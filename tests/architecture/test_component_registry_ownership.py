"""Built-in component registration has one dependency direction."""
from pathlib import Path

SELF_REGISTERED = (
    "engine/animation/animator.py",
    "engine/ui/runtime_components.py",
    "engine/physics/collider.py",
)


def test_registry_bootstrapped_components_do_not_import_registry() -> None:
    offenders = [
        path for path in SELF_REGISTERED
        if "engine.core.component_registry" in Path(path).read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_registry_owns_builtin_registration() -> None:
    source = Path("engine/core/component_registry.py").read_text(encoding="utf-8")
    for component in ("Animator", "Canvas", "BoxCollider", "CircleCollider"):
        assert f"component_registry.register({component}" in source
