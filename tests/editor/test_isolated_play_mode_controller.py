from __future__ import annotations

from editor.runtime.isolated_play_mode_controller import IsolatedPlayModeController


def test_new_play_builds_ordered_snapshot_play_and_audio_commands() -> None:
    controller = IsolatedPlayModeController()
    scene = [
        {"id": "player", "name": "Player", "audio": {"path": "play.ogg", "autoplay": True}}
    ]

    plan = controller.plan(
        {"type": "play"},
        scene_objects=scene,
        selected_name="Player",
        scene_blackboard={"score": 7},
    )

    assert plan.starting
    assert [command["type"] for command in plan.commands] == [
        "scene_snapshot",
        "play",
        "start_play_audio",
    ]
    assert plan.commands[1]["scene_blackboard"] == {"score": 7}
    assert plan.commands[1]["audio_sources"]["Player"]["path"] == "play.ogg"


def test_resume_does_not_replace_snapshot_or_restart_audio() -> None:
    controller = IsolatedPlayModeController()
    original = [{"id": "player", "name": "Player", "x": 1.0}]
    controller.plan({"type": "play"}, scene_objects=original, selected_name="Player")
    controller.session.set_runtime_state("pause")

    plan = controller.plan(
        {"type": "play"},
        scene_objects=[{"id": "player", "name": "Player", "x": 99.0}],
        selected_name="Player",
    )

    assert plan.resuming
    assert plan.commands == ({"type": "play"},)
    assert controller.session.finish()[0] == original


def test_stop_always_follows_with_audio_cleanup() -> None:
    controller = IsolatedPlayModeController()

    plan = controller.plan({"type": "stop"}, scene_objects=[], selected_name=None)

    assert [command["type"] for command in plan.commands] == ["stop", "stop_all_audio"]


def test_scene_mutations_are_blocked_only_while_session_runs() -> None:
    controller = IsolatedPlayModeController()
    assert not controller.blocks("new_scene")

    controller.plan({"type": "play"}, scene_objects=[], selected_name=None)

    assert controller.blocks("new_scene")
    assert controller.blocks("move_selected")
    assert not controller.blocks("save_scene")
