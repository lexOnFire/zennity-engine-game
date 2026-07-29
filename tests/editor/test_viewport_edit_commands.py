from editor.runtime.viewport_edit_commands import ViewportEditCommandHandler


def _handler(objects):
    emitted = []
    handler = ViewportEditCommandHandler(
        objects,
        emitted.append,
        lambda x, y: (x, y),
        lambda x, y: (x + 10.0, y + 20.0),
        lambda: 1.0,
    )
    return handler, emitted


def test_edit_handler_updates_transform_and_selection() -> None:
    objects = {"Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 10.0, "h": 20.0, "rotation": 0.0}}
    handler, emitted = _handler(objects)

    handled, selected = handler.handle({"type": "select_object", "name": "Player"}, playing=False, selected_name=None)
    assert handled and selected == "Player"
    handled, selected = handler.handle({"type": "move_selected", "dx": 3, "dy": -2}, playing=False, selected_name=selected)

    assert handled and objects["Player"]["x"] == 3.0 and objects["Player"]["y"] == -2.0
    assert emitted[-1] == {"type": "transform", "name": "Player", "x": 3.0, "y": -2.0}


def test_edit_handler_blocks_editor_mutation_during_play() -> None:
    objects = {"Player": {"name": "Player", "x": 0.0, "y": 0.0, "w": 10.0, "h": 20.0, "rotation": 0.0}}
    handler, emitted = _handler(objects)

    handled, selected = handler.handle(
        {"type": "set_transform", "name": "Player", "x": 99},
        playing=True,
        selected_name="Player",
    )

    assert handled and selected == "Player"
    assert objects["Player"]["x"] == 0.0
    assert emitted == []


def test_edit_handler_blocks_creation_during_play() -> None:
    objects = {"Player": {"name": "Player"}}
    handler, emitted = _handler(objects)

    handled, selected = handler.handle(
        {"type": "create_object_at", "kind": "Enemy", "screen_x": 10, "screen_y": 20},
        playing=True,
        selected_name="Player",
    )

    assert handled and selected == "Player"
    assert list(objects) == ["Player"]
    assert emitted == []


def test_edit_handler_creates_unique_sprite_and_emits_snapshot() -> None:
    objects = {"hero": {"name": "hero"}}
    handler, emitted = _handler(objects)

    handled, selected = handler.handle(
        {"type": "create_sprite_at", "texture": "Assets/hero.png", "screen_x": 5, "screen_y": 7},
        playing=False,
        selected_name=None,
    )

    assert handled and selected == "hero_2"
    assert objects["hero_2"]["x"] == 15.0 and objects["hero_2"]["y"] == 27.0
    assert [event["type"] for event in emitted] == ["scene_snapshot", "selected"]


def test_edit_handler_ignores_commands_owned_by_other_subsystems() -> None:
    handler, emitted = _handler({})
    assert handler.handle({"type": "play"}, playing=False, selected_name=None) == (False, None)
    assert emitted == []

