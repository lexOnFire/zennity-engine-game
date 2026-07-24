from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QToolButton, QVBoxLayout, QFrame

class DragScrubLabel(QLabel):
    dragged = Signal(float)

    def __init__(self, text: str):
        super().__init__(text)
        self.setCursor(Qt.SizeHorCursor)
        self._dragging = False
        self._last_x = 0

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_x = event.globalPosition().x()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            x = event.globalPosition().x()
            delta = x - self._last_x
            self._last_x = x
            if delta != 0:
                self.dragged.emit(delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class DragScrubSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(self, label_text: str, value: float = 0.0, step: float = 0.1):
        super().__init__()
        self.step = step
        self._value = value

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.label = DragScrubLabel(label_text)
        self.label.dragged.connect(self._on_drag)
        self.label.setMinimumWidth(15)

        self.input = QLineEdit(f"{self._value:.2f}")
        self.input.editingFinished.connect(self._on_edit)

        layout.addWidget(self.label)
        layout.addWidget(self.input, 1)

    def _on_drag(self, delta: float):
        self._value += delta * self.step
        self._update_ui()
        self.valueChanged.emit(self._value)

    def _on_edit(self):
        try:
            self._value = float(self.input.text())
            self._update_ui()
            self.valueChanged.emit(self._value)
        except ValueError:
            self._update_ui()

    def _update_ui(self):
        self.input.setText(f"{self._value:.2f}")

    def value(self) -> float:
        return self._value

    def setValue(self, val: float):
        self._value = val
        self._update_ui()
        
    def lineEdit(self):
        return self.input

class FoldoutHeader(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

class FoldoutWidget(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header = FoldoutHeader()
        self.header.setObjectName("FoldoutHeader")
        self.header.setStyleSheet("""
            QFrame#FoldoutHeader {
                background-color: #2b2d35;
                border-radius: 4px;
            }
            QFrame#FoldoutHeader:hover {
                background-color: #383b45;
            }
        """)
        self.header.clicked.connect(self.toggle)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        
        self.toggle_btn = QToolButton()
        self.toggle_btn.setArrowType(Qt.DownArrow)
        self.toggle_btn.setObjectName("FoldoutToggle")
        self.toggle_btn.clicked.connect(self.toggle)
        self.toggle_btn.setStyleSheet("QToolButton { border: none; background: transparent; }")
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("FoldoutTitle")
        self.title_label.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        
        self.options_btn = QToolButton()
        self.options_btn.setText("⋮") # 3 vertical dots
        self.options_btn.setToolTip("Opções do Componente (Resetar, etc)")
        self.options_btn.setObjectName("FoldoutOptions")
        self.options_btn.setStyleSheet("""
            QToolButton { 
                border: none; 
                background: transparent; 
                color: #8a8e99;
                font-weight: bold;
                font-size: 14px;
            }
            QToolButton:hover { color: #ffffff; }
        """)
        
        header_layout.addWidget(self.toggle_btn)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.options_btn)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(12, 4, 4, 4)

        self.layout.addWidget(self.header)
        self.layout.addWidget(self.content_area)
        self._is_expanded = True

    def addWidget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def toggle(self):
        self._is_expanded = not self._is_expanded
        self.content_area.setVisible(self._is_expanded)
        self.toggle_btn.setArrowType(Qt.DownArrow if self._is_expanded else Qt.RightArrow)
