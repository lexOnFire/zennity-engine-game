"""Production UI layout authoring dock for canonical ``.zui`` assets."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDockWidget, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QTabWidget, QTextBrowser,
)

from engine.ui.runtime import (
    UIButton, UICanvas, UIContainer, UIImage, UIInput, UILabel, UIPanel,
    UIScrollView, UIWidget, widget_from_dict,
)
from editor.widgets.logic_asset_picker import LogicAssetPickerDialog


class UICanvasPreviewWidget(QWidget):
    """Interactive WYSIWYG preview with selection and drag positioning."""

    selection_changed = Signal(object)
    widget_moved = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.canvas_runtime = UICanvas("MainCanvas")
        self.selected_widget: UIWidget | None = None
        self._drag_origin: QPoint | None = None
        self._widget_origin = (0.0, 0.0)
        self.setMinimumSize(520, 320)

    def canvas_rect(self) -> QRectF:
        margin = 24
        width = max(1, self.width() - margin * 2)
        height = min(max(1, self.height() - margin * 2), width * 9 / 16)
        width = height * 16 / 9
        return QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)

    def _scale(self) -> tuple[float, float]:
        rect = self.canvas_rect()
        return rect.width() / self.canvas_runtime.width, rect.height() / self.canvas_runtime.height

    def _walk(self, parent: UIWidget | None = None):
        root = parent or self.canvas_runtime
        for child in root.children:
            yield child
            yield from self._walk(child)

    def _widget_rect(self, widget: UIWidget) -> QRectF:
        canvas = self.canvas_rect()
        sx, sy = self._scale()
        return QRectF(
            canvas.left() + widget.x * sx, canvas.top() + widget.y * sy,
            widget.width * sx, widget.height * sy,
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#10141d"))
        canvas = self.canvas_rect()
        painter.fillRect(canvas, QColor("#1c2330"))
        painter.setPen(QPen(QColor("#46536b"), 1))
        painter.drawRect(canvas)
        for widget in self._walk():
            if not widget.visible:
                continue
            rect = self._widget_rect(widget)
            if isinstance(widget, (UIPanel, UIContainer, UIScrollView)):
                painter.fillRect(rect, QColor(getattr(widget, "bg_color", "#263246")))
            elif isinstance(widget, UIButton):
                painter.fillRect(rect, QColor("#3478d4"))
                painter.setPen(QColor("#ffffff"))
                painter.drawText(rect, Qt.AlignCenter, widget.text)
            elif isinstance(widget, UILabel):
                painter.setPen(QColor(widget.text_color))
                painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, widget.text)
            elif isinstance(widget, UIInput):
                painter.fillRect(rect, QColor("#151b26"))
                painter.setPen(QColor("#8d9ab0"))
                painter.drawRect(rect)
                painter.drawText(rect.adjusted(6, 0, -4, 0), Qt.AlignVCenter, widget.placeholder)
            elif isinstance(widget, UIImage):
                painter.fillRect(rect, QColor("#332d48"))
                painter.setPen(QColor("#b79cff"))
                painter.drawText(rect, Qt.AlignCenter, Path(widget.texture_path).name or "Image")
            if widget is self.selected_widget:
                painter.setPen(QPen(QColor("#61d7ff"), 2, Qt.DashLine))
                painter.drawRect(rect.adjusted(-2, -2, 2, 2))

    def mousePressEvent(self, event) -> None:
        position = event.position()
        selected = next(
            (widget for widget in reversed(list(self._walk())) if self._widget_rect(widget).contains(position)),
            None,
        )
        self.selected_widget = selected
        self.selection_changed.emit(selected)
        if selected is not None:
            self._drag_origin = event.position().toPoint()
            self._widget_origin = (selected.x, selected.y)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.selected_widget is None or self._drag_origin is None:
            return
        sx, sy = self._scale()
        delta = event.position().toPoint() - self._drag_origin
        self.selected_widget.x = max(0.0, self._widget_origin[0] + delta.x() / sx)
        self.selected_widget.y = max(0.0, self._widget_origin[1] + delta.y() / sy)
        self.widget_moved.emit(self.selected_widget)
        self.update()

    def mouseReleaseEvent(self, _event) -> None:
        self._drag_origin = None


class UIBuilderDock(QDockWidget):
    """Complete editor for creating, editing and persisting UI layouts."""

    document_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None, project_root: str | Path | None = None) -> None:
        super().__init__("🎨 UI Builder", parent)
        self.setObjectName("UIBuilderDock")
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.current_path: Path | None = None
        self.is_dirty = False
        self._updating_inspector = False
        self._name_counter: dict[str, int] = {}

        container = QWidget(self)
        root = QVBoxLayout(container)
        root.setContentsMargins(6, 6, 6, 6)
        toolbar = QHBoxLayout()
        for label, callback in (
            ("Novo", self.new_document), ("Abrir", self.open_dialog), ("Salvar", self.save),
            ("Panel", lambda: self.add_widget(UIPanel(self._next_name("Panel")))),
            ("Button", lambda: self.add_widget(UIButton(self._next_name("Button")))),
            ("Label", lambda: self.add_widget(UILabel(self._next_name("Label")))),
            ("Image", lambda: self.add_widget(UIImage(self._next_name("Image")))),
            ("Input", lambda: self.add_widget(UIInput(self._next_name("Input")))),
            ("Container", lambda: self.add_widget(UIContainer(self._next_name("Container")))),
        ):
            button = QPushButton(label, self)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        self.btn_duplicate = QPushButton("Duplicar", self)
        self.btn_delete = QPushButton("Excluir", self)
        self.btn_duplicate.clicked.connect(self.duplicate_selected)
        self.btn_delete.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.btn_duplicate)
        toolbar.addWidget(self.btn_delete)
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal, container)
        self.tree_hierarchy = QTreeWidget(splitter)
        self.tree_hierarchy.setHeaderLabel("Hierarquia de UI")
        self.preview_canvas = UICanvasPreviewWidget(splitter)
        self.inspector_tabs = QTabWidget(splitter)
        self.inspector_panel = QWidget(self.inspector_tabs)
        form = QFormLayout(self.inspector_panel)
        self.txt_name = QLineEdit(self)
        self.spin_x, self.spin_y = QSpinBox(self), QSpinBox(self)
        self.spin_width, self.spin_height = QSpinBox(self), QSpinBox(self)
        for spin in (self.spin_x, self.spin_y, self.spin_width, self.spin_height):
            spin.setRange(0, 8192)
        self.txt_text = QLineEdit(self)
        self.txt_asset = QLineEdit(self)
        self.txt_asset.setReadOnly(True)
        self.txt_asset.setPlaceholderText("Nenhuma imagem selecionada")
        self.btn_asset = QPushButton("Selecionar...", self)
        self.btn_asset.clicked.connect(self.choose_image_asset)
        asset_row = QWidget(self)
        asset_layout = QHBoxLayout(asset_row)
        asset_layout.setContentsMargins(0, 0, 0, 0)
        asset_layout.addWidget(self.txt_asset, 1)
        asset_layout.addWidget(self.btn_asset)
        self.check_visible = QCheckBox("Visível", self)
        self.check_visible.setChecked(True)
        self.combo_layout = QComboBox(self)
        self.combo_layout.addItems(["Vertical", "Horizontal", "Free"])
        self.combo_render_mode = QComboBox(self)
        self.combo_render_mode.addItems(["Screen Space", "World Space"])
        self.combo_render_mode.currentTextChanged.connect(lambda _val: self.apply_inspector())
        form.addRow("Nome", self.txt_name)
        form.addRow("X", self.spin_x)
        form.addRow("Y", self.spin_y)
        form.addRow("Largura", self.spin_width)
        form.addRow("Altura", self.spin_height)
        form.addRow("Render Mode", self.combo_render_mode)
        form.addRow("Texto", self.txt_text)
        form.addRow("Imagem", asset_row)
        form.addRow("Layout", self.combo_layout)
        form.addRow(self.check_visible)
        splitter.addWidget(self.tree_hierarchy)
        splitter.addWidget(self.preview_canvas)
        self.help_browser = QTextBrowser(self.inspector_tabs)
        self.inspector_tabs.addTab(self.inspector_panel, "Propriedades")
        self.inspector_tabs.addTab(self.help_browser, "Ajuda")
        splitter.addWidget(self.inspector_tabs)
        splitter.setSizes([220, 700, 250])
        root.addWidget(splitter, 1)
        self.setWidget(container)

        self.tree_hierarchy.itemSelectionChanged.connect(self._tree_selection_changed)
        self.preview_canvas.selection_changed.connect(self.select_widget)
        self.preview_canvas.widget_moved.connect(self._widget_moved)
        for target in (self.tree_hierarchy, self.preview_canvas):
            shortcut = QShortcut(QKeySequence(Qt.Key_Delete), target)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self.delete_selected)
        self.txt_name.editingFinished.connect(self.apply_inspector)
        self.txt_text.editingFinished.connect(self.apply_inspector)
        self.txt_asset.editingFinished.connect(self.apply_inspector)
        self.combo_layout.currentTextChanged.connect(lambda _value: self.apply_inspector())
        self.check_visible.toggled.connect(lambda _value: self.apply_inspector())
        for spin in (self.spin_x, self.spin_y, self.spin_width, self.spin_height):
            spin.valueChanged.connect(lambda _value: self.apply_inspector())
        self.rebuild_hierarchy_tree()
        self.select_widget(None)
        self._auto_load_last_file()

    def _last_ui_cache_path(self) -> Path:
        cache_dir = self.project_root / ".zennity"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "last_ui.json"

    def _auto_load_last_file(self) -> None:
        cache_file = self._last_ui_cache_path()
        if cache_file.exists():
            try:
                info = json.loads(cache_file.read_text(encoding="utf-8"))
                last_path = Path(info.get("last_path", ""))
                if last_path.exists():
                    self.load_document(last_path)
            except Exception:
                pass

    def _next_name(self, prefix: str) -> str:
        self._name_counter[prefix] = self._name_counter.get(prefix, 0) + 1
        return f"{prefix}_{self._name_counter[prefix]}"

    def _tree_items(self, parent_item, parent_widget: UIWidget) -> None:
        for child in parent_widget.children:
            item = QTreeWidgetItem(parent_item, [child.name])
            item.setData(0, Qt.UserRole, child)
            self._tree_items(item, child)

    def rebuild_hierarchy_tree(self) -> None:
        selected_widget = self.preview_canvas.selected_widget
        self.tree_hierarchy.blockSignals(True)
        self.tree_hierarchy.clear()
        canvas = self.preview_canvas.canvas_runtime
        root_item = QTreeWidgetItem(self.tree_hierarchy, [canvas.name])
        root_item.setData(0, Qt.UserRole, canvas)
        self._tree_items(root_item, canvas)
        self.tree_hierarchy.expandAll()
        
        # Restaurar a seleção do item sem disparar eventos em loop
        if selected_widget is not None:
            self._select_tree_item_for_widget(root_item, selected_widget)
        self.tree_hierarchy.blockSignals(False)

    def _select_tree_item_for_widget(self, parent_item: QTreeWidgetItem, widget: UIWidget) -> bool:
        if parent_item.data(0, Qt.UserRole) is widget:
            self.tree_hierarchy.setCurrentItem(parent_item)
            return True
        for i in range(parent_item.childCount()):
            if self._select_tree_item_for_widget(parent_item.child(i), widget):
                return True
        return False

    def add_widget(self, widget: UIWidget) -> None:
        parent = self.preview_canvas.selected_widget
        if not isinstance(parent, (UICanvas, UIPanel, UIContainer, UIScrollView)):
            parent = self.preview_canvas.canvas_runtime
        widget.x = 40.0 + len(parent.children) * 24.0
        widget.y = 40.0 + len(parent.children) * 24.0
        parent.add_child(widget)
        self._changed()
        self.rebuild_hierarchy_tree()
        self.select_widget(widget)
        try:
            from editor.core.event_bus import EventBus
            EventBus.emit("UI.widget_added", widget=widget)
        except Exception:
            pass

    def select_widget(self, widget: UIWidget | None) -> None:
        self.preview_canvas.selected_widget = widget
        self._updating_inspector = True
        enabled = widget is not None and widget is not self.preview_canvas.canvas_runtime
        for control in (
            self.txt_name, self.spin_x, self.spin_y, self.spin_width, self.spin_height,
            self.txt_text, self.txt_asset, self.combo_layout, self.check_visible,
            self.btn_asset, self.btn_duplicate, self.btn_delete,
        ):
            control.setEnabled(enabled)
        image_enabled = isinstance(widget, UIImage)
        self.txt_asset.setEnabled(image_enabled)
        self.btn_asset.setEnabled(image_enabled)
        is_canvas = isinstance(widget, UICanvas)
        self.combo_render_mode.setEnabled(is_canvas or enabled)
        if widget is not None:
            self.txt_name.setText(widget.name)
            self.spin_x.setValue(int(widget.x))
            self.spin_y.setValue(int(widget.y))
            self.spin_width.setValue(int(widget.width))
            self.spin_height.setValue(int(widget.height))
            self.txt_text.setText(str(getattr(widget, "text", getattr(widget, "placeholder", ""))))
            self.txt_asset.setText(str(getattr(widget, "texture_path", "")))
            self.check_visible.setChecked(widget.visible)
            self.combo_layout.setCurrentText(str(getattr(widget, "layout_mode", "Free")))
            self.combo_render_mode.setCurrentText(str(getattr(widget, "render_mode", "Screen Space")))
        self._updating_inspector = False
        self._update_help(widget)
        self.preview_canvas.update()

    def _update_help(self, widget: UIWidget | None) -> None:
        guides = {
            UIButton: ("Button", "Botão interativo para confirmar ações, abrir menus ou executar lógica."),
            UILabel: ("Label", "Texto informativo para HUD, placar, títulos e mensagens."),
            UIImage: ("Image", "Imagem do projeto para ícones, retratos, fundos e barras personalizadas."),
            UIInput: ("Input", "Campo para entrada de texto do jogador."),
            UIPanel: ("Panel", "Área visual que agrupa e destaca outros elementos."),
            UIScrollView: ("Scroll View", "Contêiner rolável para listas maiores que a tela."),
            UIContainer: ("Container", "Agrupa elementos e controla sua organização."),
            UICanvas: ("Canvas", "Raiz da interface e referência para posicionamento em tela."),
        }
        title, description = guides.get(type(widget), ("UI & HUD", "Selecione um elemento na hierarquia ou na prévia."))
        self.help_browser.setHtml(
            f"<h2>{title}</h2><p>{description}</p>"
            "<h3>Como editar</h3><p>Arraste na prévia para posicionar e use Propriedades para tamanho, texto e visibilidade.</p>"
            "<p><b>Delete</b> remove o elemento selecionado. Duplicar cria uma cópia deslocada.</p>"
        )

    def choose_image_asset(self) -> None:
        widget = self.preview_canvas.selected_widget
        if not isinstance(widget, UIImage):
            return
        picker = LogicAssetPickerDialog(self.project_root, "image", self)
        if picker.exec() and picker.selected_path:
            self.txt_asset.setText(picker.selected_path)
            self.apply_inspector()

    def _tree_selection_changed(self) -> None:
        items = self.tree_hierarchy.selectedItems()
        self.select_widget(items[0].data(0, Qt.UserRole) if items else None)

    def _widget_moved(self, widget: UIWidget) -> None:
        self._updating_inspector = True
        self.spin_x.setValue(int(widget.x))
        self.spin_y.setValue(int(widget.y))
        self._updating_inspector = False
        self._changed()

    def apply_inspector(self) -> None:
        widget = self.preview_canvas.selected_widget
        if self._updating_inspector or widget is None:
            return
        widget.name = self.txt_name.text().strip() or widget.name
        widget.x, widget.y = float(self.spin_x.value()), float(self.spin_y.value())
        widget.width, widget.height = float(self.spin_width.value()), float(self.spin_height.value())
        widget.visible = self.check_visible.isChecked()
        if hasattr(widget, "text"):
            widget.text = self.txt_text.text()
        if hasattr(widget, "placeholder"):
            widget.placeholder = self.txt_text.text()
        if hasattr(widget, "texture_path"):
            widget.texture_path = self.txt_asset.text().strip()
        if hasattr(widget, "layout_mode"):
            widget.layout_mode = self.combo_layout.currentText()
        widget.render_mode = self.combo_render_mode.currentText()
        self._changed()
        # Atualizar o rótulo do item na árvore sem rebuild/limpeza completa
        items = self.tree_hierarchy.selectedItems()
        if items and items[0].data(0, Qt.UserRole) is widget:
            items[0].setText(0, widget.name)

    def delete_selected(self) -> None:
        widget = self.preview_canvas.selected_widget
        if widget is None or widget.parent is None:
            return
        widget.parent.remove_child(widget)
        self.select_widget(None)
        self.rebuild_hierarchy_tree()
        self._changed()

    def duplicate_selected(self) -> None:
        widget = self.preview_canvas.selected_widget
        if widget is None or widget.parent is None:
            return
        clone = widget_from_dict(deepcopy(widget.serialize()))
        clone.name = f"{widget.name}_Copy"
        clone.x += 24.0
        clone.y += 24.0
        widget.parent.add_child(clone)
        self.rebuild_hierarchy_tree()
        self.select_widget(clone)
        self._changed()

    def new_document(self) -> None:
        if not self._confirm_discard():
            return
        self.preview_canvas.canvas_runtime = UICanvas("MainCanvas")
        self.current_path = None
        self.is_dirty = False
        self.rebuild_hierarchy_tree()
        self.select_widget(None)
        self.document_changed.emit(None)

    def open_dialog(self) -> None:
        if not self._confirm_discard():
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir UI Layout", str(self.project_root / "Assets"), "Zennity UI (*.zui)"
        )
        if filename:
            self.load_document(filename)

    def load_document(self, path: str | Path) -> bool:
        try:
            source = Path(path).resolve()
            data = json.loads(source.read_text(encoding="utf-8"))
            canvas = widget_from_dict(data.get("canvas", data))
            if not isinstance(canvas, UICanvas):
                raise ValueError("O documento não possui um UICanvas válido.")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "UI inválida", str(exc))
            return False
        self.preview_canvas.canvas_runtime = canvas
        self.current_path = source
        self.is_dirty = False
        self.rebuild_hierarchy_tree()
        self.select_widget(None)
        self.document_changed.emit(source)
        try:
            self._last_ui_cache_path().write_text(json.dumps({"last_path": str(source)}), encoding="utf-8")
        except Exception:
            pass
        return True

    def document_data(self) -> dict:
        return {"format": "zennity.ui", "version": 1, "canvas": self.preview_canvas.canvas_runtime.serialize()}

    def save(self) -> bool:
        path = self.current_path
        if path is None:
            directory = self.project_root / "Assets" / "UI"
            directory.mkdir(parents=True, exist_ok=True)
            filename, _ = QFileDialog.getSaveFileName(
                self, "Salvar UI Layout", str(directory / "MainUI.zui"), "Zennity UI (*.zui)"
            )
            if not filename:
                return False
            path = Path(filename)
        if path.suffix.lower() != ".zui":
            path = path.with_suffix(".zui")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".zui.tmp")
        temporary.write_text(json.dumps(self.document_data(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        self.current_path = path.resolve()
        self.is_dirty = False
        self.document_changed.emit(self.current_path)
        try:
            self._last_ui_cache_path().write_text(json.dumps({"last_path": str(self.current_path)}), encoding="utf-8")
        except Exception:
            pass
        return True

    def _changed(self) -> None:
        self.is_dirty = True
        self.preview_canvas.update()

    def _confirm_discard(self) -> bool:
        if not self.is_dirty:
            return True
        answer = QMessageBox.question(
            self, "Descartar alterações?", "O layout possui alterações não salvas.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        return answer == QMessageBox.Yes
