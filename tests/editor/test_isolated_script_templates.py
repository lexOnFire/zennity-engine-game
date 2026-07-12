from pathlib import Path

from editor.script_templates import build_isolated_script_template, inspect_script_contract


def test_created_script_has_complete_runtime_contract(tmp_path: Path) -> None:
    path = tmp_path / "movement.py"
    path.write_text(build_isolated_script_template("movement"), encoding="utf-8")

    compatible, reason = inspect_script_contract(path)
    namespace: dict = {}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)

    assert compatible, reason
    assert callable(namespace["isolated_start"])
    assert callable(namespace["isolated_update"])
    assert callable(namespace["isolated_on_instruction"])
    assert callable(namespace["isolated_stop"])


def test_contract_accepts_legacy_update_and_rejects_empty_script(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.py"
    legacy.write_text("def update(obj, dt):\n    pass\n", encoding="utf-8")
    empty = tmp_path / "empty.py"
    empty.write_text("VALUE = 1\n", encoding="utf-8")

    assert inspect_script_contract(legacy)[0]
    compatible, reason = inspect_script_contract(empty)
    assert not compatible
    assert "isolated_update" in reason
