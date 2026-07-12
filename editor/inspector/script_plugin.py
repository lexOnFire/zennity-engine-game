from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager

# Pasta padrão onde os scripts do jogo são buscados.
# Pode ser sobrescrita via ScriptInspectorPlugin.scripts_root antes de usar.
_DEFAULT_SCRIPTS_ROOT = Path("game/scripts")


def _discover_scripts(root: Path) -> list[Path]:
    """Retorna todos os .py dentro de *root*, recursivamente."""
    if not root.exists():
        return []
    return sorted(root.rglob("*.py"))


class _ScriptWidget(QWidget):
    """Widget que representa um ScriptComponent no Inspector.

    Estrutura visual (espelha outros componentes do Inspector):
    ┌─ Header ───────────────────────────────────────────┐
    │  [v] ☒ Player (Script)                          [•••]│
    ├─ Body ───────────────────────────────────────────┤
    │  Script  [dropdown: player.py       ▼]           │
    │  Velocidade  [5.00    ]                          │
    │  Pulo        [10.00   ]                          │
    └────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        component: Any,
        scripts_root: Path,
        command_manager: CommandManager | None,
        refresh: callable | None,
        on_remove: callable | None,
    ) -> None:
        super().__init__()
        self._component = component
        self._scripts_root = scripts_root
        self._command_manager = command_manager
        self._refresh = refresh
        self._on_remove = on_remove
        self._collapsed = False

        self.setObjectName("ScriptComponentWidget")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 2)
        root_layout.setSpacing(0)

        # ---- Header ----
        self._header = self._build_header()
        root_layout.addWidget(self._header)

        # ---- Body ----
        self._body = QWidget()
        self._body.setObjectName("ScriptComponentBody")
        self._body_layout = QFormLayout(self._body)
        self._body_layout.setContentsMargins(8, 4, 8, 8)
        self._body_layout.setSpacing(4)
        self._body_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        root_layout.addWidget(self._body)

        self._rebuild_body()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("InspectorSection")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        self._collapse_btn = QToolButton()
        self._collapse_btn.setText("▼")
        self._collapse_btn.setFixedWidth(16)
        self._collapse_btn.setObjectName("CollapseButton")
        self._collapse_btn.clicked.connect(self._toggle_collapse)

        self._enabled_check = QCheckBox()
        self._enabled_check.setChecked(bool(getattr(self._component, "enabled", True)))
        self._enabled_check.setObjectName("InspectorCheckBox")
        self._enabled_check.toggled.connect(self._on_enabled_toggled)

        name = self._component.script_name() or "Script"
        title_label = QLabel(f"📄 {name} (Script)")
        title_label.setObjectName("InspectorSectionTitle")
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        menu_btn = QToolButton()
        menu_btn.setText("•••")
        menu_btn.setObjectName("ComponentMenuButton")
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(menu_btn)
        menu.addAction("Recolher / Expandir", self._toggle_collapse)
        menu.addSeparator()
        menu.addAction("Remover", self._request_remove)
        menu_btn.setMenu(menu)

        layout.addWidget(self._collapse_btn)
        layout.addWidget(self._enabled_check)
        layout.addWidget(title_label)
        layout.addWidget(menu_btn)
        return header

    # ------------------------------------------------------------------
    # Body
    # ------------------------------------------------------------------

    def _rebuild_body(self) -> None:
        """Reconstrói o body com o dropdown de scripts e as propriedades."""
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # -- Dropdown de scripts --
        script_combo = QComboBox()
        script_combo.setObjectName("ScriptComboBox")
        scripts = _discover_scripts(self._scripts_root)
        script_combo.addItem("-- Selecionar script --", None)
        for s in scripts:
            script_combo.addItem(s.name, str(s))

        current_path = getattr(self._component, "script_path", "")
        if current_path:
            for i in range(script_combo.count()):
                if script_combo.itemData(i) == current_path:
                    script_combo.setCurrentIndex(i)
                    break

        script_combo.currentIndexChanged.connect(
            lambda _idx, combo=script_combo: self._on_script_selected(combo)
        )
        self._body_layout.addRow("Script", script_combo)

        # -- Propriedades dinâmicas --
        for prop_name, prop_value in getattr(self._component, "properties", {}).items():
            editor = self._make_editor(prop_name, prop_value)
            if editor is not None:
                self._body_layout.addRow(prop_name.capitalize(), editor)

    def _make_editor(self, name: str, value: Any) -> QWidget | None:
        """Cria o widget editor adequado para o tipo do valor."""
        if isinstance(value, bool):
            w = QCheckBox()
            w.setChecked(value)
            w.toggled.connect(lambda v, n=name: self._set_property(n, v))
            return w
        if isinstance(value, (int, float)):
            w = QDoubleSpinBox()
            w.setDecimals(2)
            w.setRange(-1_000_000.0, 1_000_000.0)
            w.setValue(float(value))
            w.valueChanged.connect(lambda v, n=name: self._set_property(n, v))
            return w
        if isinstance(value, str):
            w = QLineEdit(value)
            w.editingFinished.connect(lambda n=name, widget=w: self._set_property(n, widget.text()))
            return w
        # Tipo desconhecido — exibe como texto somente leitura
        lbl = QLabel(repr(value))
        lbl.setEnabled(False)
        return lbl

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_script_selected(self, combo: QComboBox) -> None:
        path = combo.currentData()
        if path is None:
            return
        old_path = self._component.script_path
        old_props = dict(getattr(self._component, "properties", {}))

        def apply() -> None:
            self._component.script_path = path
            self._component.properties = {}
            self._component._load_defaults()  # noqa: SLF001
            self._rebuild_body()

        def undo() -> None:
            self._component.script_path = old_path
            self._component.properties = old_props
            self._rebuild_body()

        if self._command_manager is not None:
            from editor.runtime.command_manager import FunctionCommand
            self._command_manager.execute(FunctionCommand(f"Set Script {path}", apply, undo))
        else:
            apply()

    def _set_property(self, name: str, value: Any) -> None:
        old = self._component.properties.get(name)

        def apply() -> None:
            self._component.set_property(name, value)

        def undo() -> None:
            self._component.set_property(name, old)

        if self._command_manager is not None:
            from editor.runtime.command_manager import FunctionCommand
            self._command_manager.execute(FunctionCommand(f"Set Script.{name}", apply, undo))
        else:
            apply()

    def _on_enabled_toggled(self, checked: bool) -> None:
        self._component.enabled = checked

    def _toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        self._collapse_btn.setText("▶" if self._collapsed else "▼")

    def _request_remove(self) -> None:
        if self._on_remove is not None:
            self._on_remove(self._component)


class ScriptInspectorPlugin(InspectorPlugin):
    """Plugin do Inspector para ScriptComponent.

    Segue o contrato de InspectorPlugin:
    - component_type identifica o tipo
    - create_widget() devolve o widget completo
    - supports() filtra pelo type_name
    """

    component_type: str = "Script"
    title: str = "Script"

    #: Pasta onde os scripts são descobertos. Pode ser sobrescrita antes
    #: de instanciar o plugin.
    scripts_root: Path = _DEFAULT_SCRIPTS_ROOT

    def supports(self, component: Any) -> bool:
        return getattr(component, "type_name", type(component).__name__) == "Script"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        def on_remove(comp: Any) -> None:
            # Delega ao painel pai (premium_panels.py) via refresh
            # que aciona remove_component_from_selected internamente.
            # Emitimos como request_remove para não criar dependência circular.
            if hasattr(comp, "_remove_request_callback") and comp._remove_request_callback:  # noqa: SLF001
                comp._remove_request_callback()  # noqa: SLF001
            elif refresh is not None:
                refresh()

        return _ScriptWidget(
            component=component,
            scripts_root=self.scripts_root,
            command_manager=command_manager,
            refresh=refresh,
            on_remove=on_remove,
        )

    def refresh_widget(self, widget: QWidget, component: Any) -> None:
        if isinstance(widget, _ScriptWidget):
            widget._rebuild_body()  # noqa: SLF001
