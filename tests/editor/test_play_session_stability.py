from copy import deepcopy
import importlib.util
import sys
from pathlib import Path


def _load_runtime_module(name: str):
    path = Path("editor/runtime") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"play_stability_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


set_channels_paused = _load_runtime_module("audio_playback_state").set_channels_paused
EditorPlaySession = _load_runtime_module("play_session").EditorPlaySession


def test_stop_restores_all_nested_components_and_selection() -> None:
    original = [{
        "id": "player-id",
        "name": "Player",
        "x": 10.0,
        "audio": {"path": "theme.ogg", "autoplay": True},
        "animator": {"active_clip": "andar", "clips": {"andar": {"frame": 0}}},
        "scripts": ["Assets/Scripts/player.py"],
        "ui": {"type": "text", "text": "VIDA: 3"},
        "rigidbody": {"velocity_y": 0.0},
    }]
    session = EditorPlaySession()
    runtime = session.begin(original, "Player")
    runtime[0]["x"] = 999.0
    runtime[0]["audio"]["path"] = "changed.ogg"
    runtime[0]["animator"]["clips"]["andar"]["frame"] = 7
    runtime[0]["scripts"].append("runtime_only.py")
    runtime[0]["ui"]["text"] = "VIDA: 0"
    runtime[0]["rigidbody"]["velocity_y"] = 500.0

    session.set_runtime_state("play")
    restored, selected = session.finish()
    final, selected_after_snapshot = session.consume_scene_snapshot(runtime)

    assert restored == original
    assert final == original
    assert selected == "Player"
    assert selected_after_snapshot == "Player"
    assert session.state == "edit"
    assert session.is_running is False


def test_repeated_play_request_does_not_replace_original_edit_snapshot() -> None:
    original = [{"id": "same-id", "name": "Player", "x": 10.0}]
    session = EditorPlaySession()
    first = session.begin(original, "Player")
    changed_editor_reference = deepcopy(original)
    changed_editor_reference[0]["x"] = 500.0

    second = session.begin(changed_editor_reference, "Player")

    assert first == original
    assert second == original


def test_stop_discards_prefabs_spawned_by_visual_logic() -> None:
    original = [{"id": "player", "name": "Player", "x": 0.0}]
    session = EditorPlaySession()
    runtime = session.begin(original, "Player")
    runtime.append({
        "id": "runtime-projectile", "name": "Projectile",
        "spawned_by_logic": True,
        "prefab_path": "Assets/Prefabs/Projectile.zprefab",
        "logic_graphs": [{"path": "Assets/Logic/Projectile.zlogic"}],
    })
    session.set_runtime_state("play")

    restored, selected = session.finish()

    assert restored == original
    assert selected == "Player"
    assert all(item["name"] != "Projectile" for item in restored)


def test_selection_is_recovered_by_stable_id() -> None:
    session = EditorPlaySession()
    session.begin([{"id": "stable", "name": "Player"}], "Player")
    session.set_runtime_state("play")
    restored, selected = session.finish()

    restored[0]["name"] = "PlayerRenamedInRuntime"
    assert selected == "Player"
    assert session.consume_scene_snapshot(restored)[1] == "Player"


class _FakeChannel:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def pause(self) -> None:
        self.calls.append("pause")

    def unpause(self) -> None:
        self.calls.append("unpause")


def test_pause_and_resume_are_forwarded_to_every_audio_channel() -> None:
    channels = {"music": _FakeChannel(), "effect": _FakeChannel()}

    set_channels_paused(channels, True)
    set_channels_paused(channels, False)

    assert channels["music"].calls == ["pause", "unpause"]
    assert channels["effect"].calls == ["pause", "unpause"]


def test_editor_and_viewport_integrate_session_lock_and_audio_pause() -> None:
    editor_source = open("editor/isolated_editor_main.py", encoding="utf-8").read()
    viewport_source = open("editor/isolated_viewport.py", encoding="utf-8").read()

    assert "self._play_controller.plan" in editor_source
    assert "self._play_session.finish" in editor_source
    assert "self._set_play_mode_editing_locked(True)" in editor_source
    assert "set_channels_paused(audio_channels, paused)" in viewport_source
    assert "set_channels_paused(audio_channels, False)" in viewport_source


def test_generic_property_command_captures_old_value_without_invalid_syntax() -> None:
    command_type = _load_runtime_module("property_commands").SetPropertyCommand
    target = type("Target", (), {"value": 3})()
    command = command_type(target, "value", 9)

    command.execute()
    assert target.value == 9
    command.undo()
    assert target.value == 3


def test_runtime_restart_resets_physics_and_restarts_autoplay_audio() -> None:
    viewport_source = Path("editor/isolated_viewport.py").read_text(encoding="utf-8")
    restart_block = viewport_source.split("if restart_requested:", 1)[1].split(
        "physics_steps = physics_scheduler.consume", 1
    )[0]

    assert "stop_audio_sources()" in restart_block
    assert "physics_scheduler.reset()" in restart_block
    assert "start_audio_sources()" in restart_block


def test_viewport_has_one_runtime_lifecycle_and_initializes_spawned_prefabs() -> None:
    viewport_source = Path("editor/isolated_viewport.py").read_text(encoding="utf-8")

    assert viewport_source.count("    def start_scripts()") == 1
    assert viewport_source.count("    def stop_scripts()") == 1
    assert viewport_source.count("    def game_camera()") == 1
    assert "def start_spawned_objects()" in viewport_source
    assert "for hydrator in (hydrate_animation_asset_clips, hydrate_animator_controllers, hydrate_logic_graphs)" in viewport_source
    assert "hydrator({name: obj}, Path.cwd())" in viewport_source
    assert "start_spawned_objects()\n            trace_now" in viewport_source
