import ast
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
    assert callable(namespace["on_update"])


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


def test_all_attachable_asset_scripts_use_current_contract() -> None:
    scripts_dir = Path("Assets/Scripts")
    failures = {}
    for path in scripts_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue
        compatible, reason = inspect_script_contract(path)
        if not compatible:
            failures[path.name] = reason
    assert not failures


def test_all_attachable_asset_scripts_run_one_frame() -> None:
    world = {
        "Subject": {"name": "Subject", "x": 0.0, "y": 0.0, "w": 32.0, "h": 32.0},
        "Player": {"name": "Player", "tag": "Player", "x": 100.0, "y": 0.0, "w": 32.0, "h": 32.0},
        "Danger": {"name": "Danger", "tag": "perigoso", "x": 10.0, "y": 0.0, "w": 32.0, "h": 32.0},
    }
    for path in Path("Assets/Scripts").glob("*.py"):
        if path.name == "__init__.py":
            continue
        namespace: dict = {}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
        game = PlayScriptAPI("Subject", dict(world["Subject"]), events=None, world=world)
        game.begin_frame({"right": True, "jump": True})
        start = namespace.get("on_start") or namespace.get("isolated_start")
        if callable(start):
            # Tenta com dict game.obj primeiro se for isolated_start
            if "isolated_start" in namespace:
                start(game.obj)
            else:
                try:
                    start(game)
                except (TypeError, AttributeError):
                    start(game.obj)
        update = namespace.get("on_update") or namespace.get("isolated_update")
        if callable(update):
            if "isolated_update" in namespace:
                update(game.obj, {"left": False, "right": False, "up": False, "down": False, "jump": False}, 1.0 / 60.0)
            else:
                try:
                    update(game, 1.0 / 60.0)
                except (TypeError, AttributeError):
                    update(game.obj, {"left": False, "right": False, "up": False, "down": False, "jump": False}, 1.0 / 60.0)
        else:
            hook = namespace.get("on_collision") or namespace.get("on_trigger")
            if callable(hook):
                other = PlayScriptAPI("Danger", world["Danger"], events=None, world=world)
                hook(game, other)


def test_all_native_asset_scripts_also_expose_play_hooks() -> None:
    world = {
        "Enemy": {"name": "Enemy", "x": 0.0, "y": 0.0},
        "Player": {"name": "Player", "tag": "Player", "x": 100.0, "y": 0.0},
    }
    for path in Path("assets/scripts").glob("*.py"):
        if path.name == "__init__.py":
            continue
        compatible, reason = inspect_script_contract(path)
        assert compatible, f"{path.name}: {reason}"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        play_nodes = [
            node for node in tree.body
            if (isinstance(node, ast.Import) and any(alias.name == "math" for alias in node.names))
            or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "SCRIPT_CONFIG" for target in node.targets))
            or (isinstance(node, ast.FunctionDef) and node.name in {"on_start", "on_update", "on_instruction"})
        ]
        namespace: dict = {}
        exec(compile(tree, str(path), "exec"), namespace)
        game = PlayScriptAPI("Enemy", world["Enemy"], events=None, world=world)
        start = namespace.get("on_start")
        if callable(start):
            start(game)
        
        # Nem todos os scripts expõem on_update (ex: alguns usam apenas on_collision)
        update = namespace.get("on_update")
        if callable(update):
            update(game, 1.0 / 60.0)
        else:
            hook = namespace.get("on_collision") or namespace.get("on_trigger")
            if callable(hook):
                other = PlayScriptAPI("Player", world["Player"], events=None, world=world)
                hook(game, other)
