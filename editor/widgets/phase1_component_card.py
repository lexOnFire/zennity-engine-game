from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QCheckBox
)

class Phase1ComponentCard(QFrame):
    _collapsed_states = {}

    def __init__(self, key: str, display_name: str, has_enable: bool = True, removable: bool = True, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("Phase1ComponentCard")
        # Styles are now handled by the global theme system (editor/ui/theme.py)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("CardHeader")
        header.setCursor(Qt.PointingHandCursor)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(6, 4, 4, 4)
        h_layout.setSpacing(4)

        self._collapsed = Phase1ComponentCard._collapsed_states.get(key, False)

        self._arrow = QLabel("▶" if self._collapsed else "▼")
        self._arrow.setFixedWidth(12)

        self.chk_enabled = QCheckBox()
        self.chk_enabled.setFixedWidth(16)
        self.chk_enabled.setVisible(has_enable)

        self._lbl_name = QLabel(display_name)
        self._lbl_name.setProperty("uiRole", "bold")

        self.btn_remove = QPushButton("×")
        self.btn_remove.setObjectName("CardRemoveBtn")
        self.btn_remove.setVisible(removable)
        self.btn_remove.setToolTip(f"Remover {display_name}")

        h_layout.addWidget(self._arrow)
        h_layout.addWidget(self.chk_enabled)
        h_layout.addWidget(self._lbl_name, 1)
        h_layout.addWidget(self.btn_remove)

        header.mousePressEvent = self._toggle_collapse
        outer.addWidget(header)

        self.body_wrapper = QWidget()
        self.body_layout = QVBoxLayout(self.body_wrapper)
        self.body_layout.setContentsMargins(8, 6, 8, 8)
        self.body_layout.setSpacing(4)
        self.body_wrapper.setVisible(not self._collapsed)
        outer.addWidget(self.body_wrapper)

    def _toggle_collapse(self, event=None):
        self._collapsed = not self._collapsed
        Phase1ComponentCard._collapsed_states[self.key] = self._collapsed
        self._arrow.setText("▶" if self._collapsed else "▼")
        self.body_wrapper.setVisible(not self._collapsed)
