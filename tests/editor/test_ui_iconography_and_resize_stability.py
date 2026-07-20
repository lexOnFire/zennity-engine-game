from pathlib import Path
import xml.etree.ElementTree as ET

from editor.ui.icons import TOOLBAR_ICONS, icon_path


ROOT = Path(__file__).resolve().parents[2]


def test_toolbar_has_a_valid_svg_for_every_action() -> None:
    assert set(TOOLBAR_ICONS) == {
        "Novo", "Abrir", "Salvar", "Desfazer", "Refazer", "Select",
        "Move", "Rotate", "Scale", "Snap: OFF", "Play", "Pause", "Stop",
    }
    for name in TOOLBAR_ICONS.values():
        path = icon_path(name)
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        assert root.tag.endswith("svg")
        assert root.attrib["viewBox"] == "0 0 24 24"
        assert root.attrib["stroke"] == "#b9c2d0"


def test_animation_actions_use_the_same_svg_package() -> None:
    source = (ROOT / "editor" / "interface_smoke_test.py").read_text(encoding="utf-8")
    required = {
        "new", "open", "save", "duplicate", "delete", "apply", "play",
        "first", "previous", "pause", "next", "last",
    }
    for name in required:
        assert icon_path(name).is_file()
        assert f'"{name}"' in source
    assert "action = QAction(editor_icon(icon_name), label, self)" in source


def test_viewport_resize_events_are_coalesced_and_deduplicated() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")
    event_filter = (ROOT / "editor" / "runtime" / "editor_event_router.py").read_text(encoding="utf-8")
    flush = source[source.index("def _flush_viewport_resize"):source.index("def _dragged_asset_path")]

    assert "self._viewport_resize_timer.setSingleShot(True)" in source
    assert "self._viewport_resize_timer.setInterval(24)" in source
    assert "editor._pending_viewport_size = editor.native_viewport_size()" in event_filter
    assert "editor._viewport_resize_timer.start()" in event_filter
    assert 'self._commands.put({"type": "viewport_size"' not in event_filter
    assert "size == self._last_viewport_size_sent" in flush
    assert 'self._commands.put({"type": "viewport_size", "w": size[0], "h": size[1]})' in flush
