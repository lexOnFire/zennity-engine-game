import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from editor.widgets.animation_frame_editor import AnimationFrameEditor


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_frame_builder_creates_sequence_from_sprite_sheet(tmp_path) -> None:
    _app()
    sheet = QPixmap(64, 32)
    sheet.fill(QColor("#6b4bda"))
    path = tmp_path / "sheet.png"
    assert sheet.save(str(path))

    editor = AnimationFrameEditor()
    editor.set_source(path, 32, 32, [0])
    assert editor.source_list.count() == 2

    editor.source_list.item(0).setSelected(True)
    editor.source_list.item(1).setSelected(True)
    editor.add_selected()

    assert editor.frames() == [0, 1]
    assert editor.sequence_list.count() == 2


def test_frame_builder_removes_and_reorders_frames() -> None:
    _app()
    editor = AnimationFrameEditor()
    editor.set_frames([0, 2, 1])
    editor.sequence_list.setCurrentRow(1)

    editor.move_selected(-1)
    assert editor.frames() == [2, 0, 1]

    editor.sequence_list.clearSelection()
    editor.sequence_list.item(2).setSelected(True)
    editor.remove_selected()
    assert editor.frames() == [2, 0]


def test_frame_builder_emits_canonical_frame_list() -> None:
    _app()
    editor = AnimationFrameEditor()
    captured: list[list[int]] = []
    editor.framesChanged.connect(captured.append)
    editor.set_frames([4, 2])
    editor.sequence_list.setCurrentRow(0)

    editor.move_selected(1)

    assert captured[-1] == [2, 4]
