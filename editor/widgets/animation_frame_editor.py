"""Visual sprite-sheet frame picker and animation sequence editor."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class AnimationFrameEditor(QWidget):
    """Builds an ordered animation sequence from frames in a sprite sheet."""

    framesChanged = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AnimationFrameEditor")
        self._pixmap = QPixmap()
        self._frame_width = 1
        self._frame_height = 1
        self._frames: list[int] = [0]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("FRAME BUILDER")
        title.setObjectName("PanelSectionTitle")
        self.summary = QLabel("Selecione um Sprite Sheet")
        self.summary.setObjectName("PanelHint")
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self.summary)
        layout.addLayout(title_row)

        splitter = QSplitter(Qt.Horizontal)
        source_panel = QWidget()
        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addWidget(self._caption("QUADROS DO SPRITE SHEET"))
        self.source_list = self._new_frame_list(multi=True)
        self.source_list.itemDoubleClicked.connect(lambda _item: self.add_selected())
        source_layout.addWidget(self.source_list)

        sequence_panel = QWidget()
        sequence_layout = QVBoxLayout(sequence_panel)
        sequence_layout.setContentsMargins(0, 0, 0, 0)
        sequence_layout.addWidget(self._caption("SEQUÊNCIA DA ANIMAÇÃO"))
        self.sequence_list = self._new_frame_list(multi=True)
        sequence_layout.addWidget(self.sequence_list)

        splitter.addWidget(source_panel)
        splitter.addWidget(sequence_panel)
        splitter.setSizes([420, 420])
        layout.addWidget(splitter, 1)

        actions = QHBoxLayout()
        self.add_button = QPushButton("Adicionar selecionados →")
        self.remove_button = QPushButton("Remover")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        self.clear_button = QPushButton("Limpar")
        self.add_button.clicked.connect(self.add_selected)
        self.remove_button.clicked.connect(self.remove_selected)
        self.left_button.clicked.connect(lambda: self.move_selected(-1))
        self.right_button.clicked.connect(lambda: self.move_selected(1))
        self.clear_button.clicked.connect(self.clear_sequence)
        for button in (
            self.add_button, self.remove_button, self.left_button,
            self.right_button, self.clear_button,
        ):
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)

    @staticmethod
    def _caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("PanelHint")
        return label

    @staticmethod
    def _new_frame_list(*, multi: bool) -> QListWidget:
        widget = QListWidget()
        widget.setViewMode(QListWidget.IconMode)
        widget.setFlow(QListWidget.LeftToRight)
        widget.setWrapping(False)
        widget.setResizeMode(QListWidget.Adjust)
        widget.setIconSize(QSize(48, 48))
        widget.setGridSize(QSize(64, 72))
        widget.setMinimumHeight(92)
        widget.setMaximumHeight(126)
        widget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        widget.setSelectionMode(
            QAbstractItemView.ExtendedSelection if multi
            else QAbstractItemView.SingleSelection
        )
        return widget

    def set_source(
        self,
        texture: str | Path,
        frame_width: int,
        frame_height: int,
        frames: list[int],
    ) -> None:
        self._frame_width = max(1, int(frame_width))
        self._frame_height = max(1, int(frame_height))
        path = Path(texture) if str(texture) else Path()
        self._pixmap = QPixmap(str(path)) if str(texture) else QPixmap()
        self.source_list.clear()
        if self._pixmap.isNull():
            self.summary.setText("Selecione um Sprite Sheet válido")
            self.set_frames(frames)
            return
        columns = self._pixmap.width() // self._frame_width
        rows = self._pixmap.height() // self._frame_height
        total = max(0, columns * rows)
        for index in range(total):
            self.source_list.addItem(self._item_for_frame(index))
        self.summary.setText(
            f"{self._pixmap.width()}×{self._pixmap.height()}  •  "
            f"{self._frame_width}×{self._frame_height}  •  {total} quadros"
        )
        self.set_frames(frames)

    def set_frames(self, frames: list[int]) -> None:
        self._frames = [max(0, int(frame)) for frame in frames] or [0]
        self.sequence_list.clear()
        for frame in self._frames:
            self.sequence_list.addItem(self._item_for_frame(frame))

    def frames(self) -> list[int]:
        return list(self._frames)

    def add_selected(self) -> None:
        selected = sorted(
            (item for item in self.source_list.selectedItems()),
            key=lambda item: self.source_list.row(item),
        )
        if not selected:
            return
        self._frames.extend(int(item.data(Qt.UserRole)) for item in selected)
        if len(self._frames) > len(selected) and self._frames[0] == 0 and self.sequence_list.count() == 1:
            self._frames = self._frames[1:]
        self._commit()

    def remove_selected(self) -> None:
        rows = sorted(
            {self.sequence_list.row(item) for item in self.sequence_list.selectedItems()},
            reverse=True,
        )
        for row in rows:
            if 0 <= row < len(self._frames):
                self._frames.pop(row)
        self._frames = self._frames or [0]
        self._commit()

    def clear_sequence(self) -> None:
        self._frames = [0]
        self._commit()

    def move_selected(self, offset: int) -> None:
        current = self.sequence_list.currentRow()
        target = current + int(offset)
        if current < 0 or target < 0 or target >= len(self._frames):
            return
        self._frames[current], self._frames[target] = self._frames[target], self._frames[current]
        self._commit(selected_row=target)

    def _commit(self, selected_row: int = -1) -> None:
        self.set_frames(self._frames)
        if selected_row >= 0:
            self.sequence_list.setCurrentRow(selected_row)
        self.framesChanged.emit(self.frames())

    def _item_for_frame(self, index: int) -> QListWidgetItem:
        item = QListWidgetItem(str(index))
        item.setData(Qt.UserRole, int(index))
        if not self._pixmap.isNull():
            columns = max(1, self._pixmap.width() // self._frame_width)
            x = (index % columns) * self._frame_width
            y = (index // columns) * self._frame_height
            frame = self._pixmap.copy(x, y, self._frame_width, self._frame_height)
            item.setIcon(QIcon(frame.scaled(
                48, 48, Qt.KeepAspectRatio, Qt.FastTransformation
            )))
        return item
