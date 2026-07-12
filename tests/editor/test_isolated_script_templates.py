from pathlib import Path

from editor.script_templates import build_isolated_script_template, inspect_script_contract
from editor.isolated_viewport import PlayScriptAPI


def test_created_script_has_complete_runtime_contract(tmp_path: Path) -> None:
    path = tmp_path / "movement.py"
    path.write_text(build_isolated_script_template("movement"), encoding="utf-8")

    compatible, reason = inspect_script_contract(path)
    namespace: dict = {}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)

    assert compatible, reason
    assert callable(namespace["on_start"])
    assert callable(namespace["on_update"])
    assert callable(namespace["on_instruction"])
    assert callable(namespace["on_stop"])


def test_contract_accepts_legacy_update_and_rejects_empty_script(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.py"
    legacy.write_text("def update(obj, dt):\n    pass\n", encoding="utf-8")
    empty = tmp_path / "empty.py"
    empty.write_text("VALUE = 1\n", encoding="utf-8")

    assert inspect_script_contract(legacy)[0]
    compatible, reason = inspect_script_contract(empty)
    assert not compatible
    assert "on_update" in reason


def test_simple_play_api_moves_reads_edges_and_requests_jump() -> None:
    obj = {"x": 10.0, "y": 20.0}
    game = PlayScriptAPI("Player", obj, events=None)

    game.begin_frame({"right": True, "jump": True})
    assert game.axis("left", "right") == 1
    assert game.key_pressed("space")
    game.move(5.0, -2.0)
    game.jump(500.0)
    game.end_frame()

    assert (obj["x"], obj["y"]) == (15.0, 18.0)
    assert obj["_jump_force"] == 500.0
    game.begin_frame({"right": True, "jump": True})
    assert not game.key_pressed("space")
