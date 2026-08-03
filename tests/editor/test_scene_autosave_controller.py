from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QWidget

from editor.scene_autosave_controller import SceneAutosaveController


class _Persistence:
    def __init__(self) -> None:
        self.calls = []

    def save(self, path, snapshots, document):
        self.calls.append((path, snapshots, document))
        return {"scene_name": path.stem, "objects": list(snapshots)}


def test_autosave_updates_named_scene_without_opening_dialog(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    host = QWidget()
    persistence = _Persistence()
    scene_path = tmp_path / "Level.zscene"
    host._play_session = SimpleNamespace(is_running=False)
    host._current_scene_path = scene_path
    host._scene_snapshot = [{"name": "Player", "x": 2}]
    host._scene_document = {"scene_name": "Level"}
    host._selected_name = "Player"
    host._scene_persistence = persistence
    host._log = lambda *_args: None
    messages = []
    host.statusBar = lambda: SimpleNamespace(showMessage=messages.append)
    controller = SceneAutosaveController(host, tmp_path, delay_ms=250)

    try:
        assert controller.flush()
        assert persistence.calls[0][0] == scene_path
        assert host._scene_document["objects"] == host._scene_snapshot
        assert messages[-1] == "Autosave: Level.zscene"
    finally:
        controller._manager.clear_recovery()
        host.deleteLater()
        app.processEvents()


def test_autosave_untitled_scene_writes_recovery_only(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    host = QWidget()
    persistence = _Persistence()
    host._play_session = SimpleNamespace(is_running=False)
    host._current_scene_path = None
    host._scene_snapshot = []
    host._scene_document = {"scene_name": "Untitled", "objects": []}
    host._selected_name = None
    host._scene_persistence = persistence
    host._log = lambda *_args: None
    host.statusBar = lambda: SimpleNamespace(showMessage=lambda _message: None)
    controller = SceneAutosaveController(host, tmp_path, delay_ms=250)

    try:
        assert controller.flush()
        assert persistence.calls == []
        assert (tmp_path / ".zennity_autosave.json").is_file()
    finally:
        controller._manager.clear_recovery()
        host.deleteLater()
        app.processEvents()
