"""Seletor de assets ``.zanim`` ao adicionar Animator 2D."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from engine.animation.clip_asset import load_animation_asset


class AnimationPickerDialog(QDialog):
    """Escolhe uma animação salva sem abrir o seletor de arquivos do Windows."""

    def __init__(self, project_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AnimationPickerDialog")
        self.setWindowTitle("Escolher Animação")
        self.setModal(True)
        self.resize(680, 470)
        self.setMinimumSize(560, 400)
        self.project_root = Path(project_root).resolve()
        self.selected_path: Path | None = None
        self.requested_action: str | None = None
        self._assets: list[tuple[Path, dict | None, str]] = []
        self._build_ui()
        self._discover_assets()
        self._rebuild("")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        title = QLabel("Escolha a animação do objeto")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        intro = QLabel("A animação escolhida será anexada ao Animator 2D e ficará ativa no Play Mode.")
        intro.setObjectName("DialogDescription")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.search = QLineEdit()
        self.search.setObjectName("AnimationPickerSearch")
        self.search.setPlaceholderText("Pesquisar animação...")
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)

        content = QHBoxLayout()
        content.setSpacing(10)
        self.list = QListWidget()
        self.list.setObjectName("AnimationPickerList")
        self.list.setMinimumWidth(230)
        content.addWidget(self.list, 2)

        details_panel = QWidget()
        details_panel.setObjectName("AnimationPickerDetailsPanel")
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(12, 12, 12, 12)
        self.preview = QLabel("Selecione uma animação")
        self.preview.setObjectName("AnimationPickerPreview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(150)
        details_layout.addWidget(self.preview)
        self.details = QLabel("Nome, frames e Sprite Sheet aparecerão aqui.")
        self.details.setObjectName("AnimationPickerDetails")
        self.details.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details.setWordWrap(True)
        details_layout.addWidget(self.details, 1)
        content.addWidget(details_panel, 3)
        layout.addLayout(content, 1)

        actions = QHBoxLayout()
        self.create_button = QPushButton("Criar nova")
        self.empty_button = QPushButton("Adicionar vazio")
        self.empty_button.setToolTip("Modo avançado: adiciona o Animator sem escolher um clip")
        self.cancel_button = QPushButton("Cancelar")
        self.use_button = QPushButton("Usar animação")
        self.use_button.setProperty("uiRole", "primary")
        self.use_button.setEnabled(False)
        actions.addWidget(self.create_button)
        actions.addWidget(self.empty_button)
        actions.addStretch(1)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.use_button)
        layout.addLayout(actions)

        self.search.textChanged.connect(self._rebuild)
        self.list.currentItemChanged.connect(self._selection_changed)
        self.list.itemDoubleClicked.connect(lambda _item: self._accept_selected())
        self.create_button.clicked.connect(lambda: self._finish("create"))
        self.empty_button.clicked.connect(lambda: self._finish("empty"))
        self.cancel_button.clicked.connect(self.reject)
        self.use_button.clicked.connect(self._accept_selected)

    def _discover_assets(self) -> None:
        directory = self.project_root / "Assets" / "Animations"
        paths = sorted(directory.rglob("*.zanim"), key=lambda item: str(item).casefold()) if directory.exists() else []
        for path in paths:
            try:
                asset = load_animation_asset(path)
                error = self._asset_error(asset)
            except (OSError, ValueError) as exc:
                asset = None
                error = str(exc)
            self._assets.append((path.resolve(), asset, error))

    def _rebuild(self, query: str) -> None:
        normalized = query.strip().casefold()
        self.list.clear()
        for path, asset, error in self._assets:
            searchable = f"{path.stem} {(asset or {}).get('name', '')} {path.parent.name}".casefold()
            if normalized and normalized not in searchable:
                continue
            label = str((asset or {}).get("name") or path.stem)
            item = QListWidgetItem(label + ("  — incompleta" if error else ""))
            item.setData(Qt.UserRole, str(path))
            item.setToolTip(self._relative(path) if not error else f"Asset inválido: {error}")
            if error:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.list.addItem(item)
        if self.list.count() == 0:
            empty = QListWidgetItem("Nenhuma animação encontrada")
            empty.setFlags(empty.flags() & ~Qt.ItemIsEnabled)
            self.list.addItem(empty)
            self.preview.clear()
            self.preview.setText("Nenhum asset .zanim")
            self.details.setText("Crie uma animação nova ou salve um clip na aba Animation.")
        else:
            first = next((self.list.item(i) for i in range(self.list.count()) if self.list.item(i).data(Qt.UserRole)), None)
            if first is not None:
                self.list.setCurrentItem(first)

    def _asset_error(self, asset: dict) -> str:
        texture = str(asset.get("texture", "")).strip()
        if not texture:
            return "Sprite Sheet não definido"
        texture_path = Path(texture)
        if not texture_path.is_absolute():
            texture_path = self.project_root / texture_path
        pixmap = QPixmap(str(texture_path))
        if pixmap.isNull():
            return f"Sprite Sheet não encontrado: {texture}"
        width = max(1, int(asset.get("frame_width", 1)))
        height = max(1, int(asset.get("frame_height", 1)))
        if width > pixmap.width() or height > pixmap.height():
            return "O frame é maior que o Sprite Sheet"
        columns = max(1, pixmap.width() // width)
        rows = max(1, pixmap.height() // height)
        frames = list(asset.get("frames") or [0])
        if max(int(frame) for frame in frames) >= columns * rows:
            return "Há frames fora do Sprite Sheet"
        return ""

    def _selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        path_value = current.data(Qt.UserRole) if current is not None else None
        self.use_button.setEnabled(bool(path_value))
        if not path_value:
            return
        path = Path(str(path_value))
        record = next((entry for entry in self._assets if entry[0] == path), None)
        if record is None or record[1] is None:
            return
        asset = record[1]
        frames = list(asset.get("frames", [0]))
        texture = str(asset.get("texture", ""))
        self.details.setText(
            f"<b>{asset['name']}</b><br><br>"
            f"Frames: {len(frames)}<br>FPS: {float(asset['fps']):g}<br>"
            f"Repetir: {'Sim' if asset['loop'] else 'Não'}<br>"
            f"Sprite Sheet: {Path(texture).name if texture else 'Não definido'}<br><br>"
            f"{self._relative(path)}"
        )
        self._update_preview(asset)

    def _update_preview(self, asset: dict) -> None:
        texture = str(asset.get("texture", ""))
        texture_path = Path(texture)
        if texture and not texture_path.is_absolute():
            texture_path = self.project_root / texture_path
        pixmap = QPixmap(str(texture_path)) if texture else QPixmap()
        width = max(1, int(asset.get("frame_width", 1)))
        height = max(1, int(asset.get("frame_height", 1)))
        frame = max(0, int((asset.get("frames") or [0])[0]))
        columns = max(1, pixmap.width() // width) if not pixmap.isNull() else 1
        x, y = (frame % columns) * width, (frame // columns) * height
        if pixmap.isNull() or x + width > pixmap.width() or y + height > pixmap.height():
            self.preview.clear()
            self.preview.setText("Prévia indisponível")
            return
        frame_pixmap = pixmap.copy(x, y, width, height)
        self.preview.setPixmap(frame_pixmap.scaled(150, 130, Qt.KeepAspectRatio, Qt.FastTransformation))

    def _accept_selected(self) -> None:
        item = self.list.currentItem()
        path_value = item.data(Qt.UserRole) if item is not None else None
        if not path_value:
            return
        self.selected_path = Path(str(path_value))
        self.requested_action = "select"
        self.accept()

    def _finish(self, action: str) -> None:
        self.requested_action = action
        self.accept()

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project_root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
