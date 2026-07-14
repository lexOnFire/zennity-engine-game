"""Editor visual básico para assets ``.zanimator``."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from engine.animation.controller_asset import (
    default_animator_controller, load_animator_controller, save_animator_controller,
)


class AnimatorControllerEditorDialog(QDialog):
    """Edita estados, parâmetros e transições sem expor o JSON ao usuário."""

    def __init__(self, project_root: Path, path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.project_root = Path(project_root).resolve()
        self.path = path.resolve() if path else None
        self.data = load_animator_controller(self.path) if self.path else default_animator_controller()
        self.saved_path: Path | None = None
        self.setWindowTitle("Animator Controller")
        self.resize(720, 520)
        self._build_ui()
        self._refresh_all()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        header = QFormLayout()
        self.name_field = QLineEdit(str(self.data["name"]))
        self.initial_combo = QComboBox()
        header.addRow("Nome", self.name_field)
        header.addRow("Estado inicial", self.initial_combo)
        layout.addLayout(header)

        tabs = QTabWidget()
        self.states_tree = self._tree(("Estado", "Animação", "Velocidade"))
        self.states_tree.itemDoubleClicked.connect(self._edit_state)
        tabs.addTab(self._tab(self.states_tree, self._add_state, self._remove_state), "Estados")
        self.parameters_tree = self._tree(("Parâmetro", "Tipo", "Padrão"))
        self.parameters_tree.itemDoubleClicked.connect(self._edit_parameter)
        tabs.addTab(self._tab(self.parameters_tree, self._add_parameter, self._remove_parameter), "Parâmetros")
        self.transitions_tree = self._tree(("Origem", "Destino", "Condição"))
        tabs.addTab(self._tab(self.transitions_tree, self._add_transition, self._remove_transition), "Transições")
        layout.addWidget(tabs, 1)

        hint = QLabel("Dica: use * como origem para uma transição disponível em qualquer estado.")
        hint.setObjectName("PanelHint")
        layout.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _tree(headers: tuple[str, ...]) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderLabels(list(headers))
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        return tree

    @staticmethod
    def _tab(tree: QTreeWidget, add_slot, remove_slot) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(tree, 1)
        row = QHBoxLayout()
        add_button = QPushButton("Adicionar")
        remove_button = QPushButton("Remover")
        add_button.clicked.connect(add_slot)
        remove_button.clicked.connect(remove_slot)
        row.addWidget(add_button)
        row.addWidget(remove_button)
        row.addStretch(1)
        layout.addLayout(row)
        return page

    def _animation_assets(self) -> list[str]:
        return sorted(
            path.relative_to(self.project_root).as_posix()
            for path in self.project_root.rglob("*.zanim")
            if path.is_file()
        )

    def _refresh_all(self) -> None:
        current_initial = str(self.data["initial_state"])
        self.initial_combo.clear()
        self.initial_combo.addItems(list(self.data["states"]))
        self.initial_combo.setCurrentText(current_initial)
        self.states_tree.clear()
        for name, state in self.data["states"].items():
            QTreeWidgetItem(self.states_tree, [name, state["animation"] or "Sem animação", f'{float(state.get("speed", 1.0)):.2f}'])
        self.parameters_tree.clear()
        for name, parameter in self.data["parameters"].items():
            QTreeWidgetItem(self.parameters_tree, [name, parameter["type"], str(parameter["default"])])
        self.transitions_tree.clear()
        for transition in self.data["transitions"]:
            conditions = transition.get("conditions", [])
            text = "Sempre" if not conditions else " e ".join(
                f'{condition["parameter"]} {condition["operator"]} {condition.get("value", "")}' for condition in conditions
            )
            QTreeWidgetItem(self.transitions_tree, [transition["from"], transition["to"], text])

    def _add_state(self) -> None:
        name, ok = QInputDialog.getText(self, "Novo estado", "Nome do estado:")
        name = name.strip()
        if not ok or not name:
            return
        if name in self.data["states"]:
            QMessageBox.warning(self, "Estado existente", "Já existe um estado com esse nome.")
            return
        animations = self._animation_assets()
        animation = ""
        if animations:
            animation, ok = QInputDialog.getItem(self, "Animação do estado", "Animação salva:", animations, 0, False)
            if not ok:
                return
        self.data["states"][name] = {"animation": animation, "speed": 1.0}
        self._refresh_all()

    def _remove_state(self) -> None:
        item = self.states_tree.currentItem()
        if item is None or len(self.data["states"]) <= 1:
            return
        name = item.text(0)
        self.data["states"].pop(name, None)
        self.data["transitions"] = [t for t in self.data["transitions"] if t["from"] != name and t["to"] != name]
        if self.data["initial_state"] == name:
            self.data["initial_state"] = next(iter(self.data["states"]))
        self._refresh_all()

    def _edit_state(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        name = item.text(0)
        state = self.data["states"].get(name)
        if state is None:
            return
        animations = self._animation_assets()
        choices = ["Sem animação"] + animations
        current = str(state.get("animation", ""))
        index = choices.index(current) if current in choices else 0
        animation, ok = QInputDialog.getItem(self, f"Estado {name}", "Animação salva:", choices, index, False)
        if not ok:
            return
        speed, ok = QInputDialog.getDouble(
            self, f"Estado {name}", "Velocidade:", float(state.get("speed", 1.0)), 0.0, 100.0, 2
        )
        if not ok:
            return
        state["animation"] = "" if animation == "Sem animação" else animation
        state["speed"] = speed
        self._refresh_all()

    def _add_parameter(self) -> None:
        name, ok = QInputDialog.getText(self, "Novo parâmetro", "Nome do parâmetro:")
        name = name.strip()
        if not ok or not name or name in self.data["parameters"]:
            return
        kind, ok = QInputDialog.getItem(self, "Tipo", "Tipo do parâmetro:", ["bool", "float", "trigger"], 0, False)
        if not ok:
            return
        default = 0.0 if kind == "float" else False
        self.data["parameters"][name] = {"type": kind, "default": default}
        self._refresh_all()

    def _remove_parameter(self) -> None:
        item = self.parameters_tree.currentItem()
        if item is None:
            return
        name = item.text(0)
        self.data["parameters"].pop(name, None)
        for transition in self.data["transitions"]:
            transition["conditions"] = [c for c in transition["conditions"] if c["parameter"] != name]
        self._refresh_all()

    def _edit_parameter(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        name = item.text(0)
        parameter = self.data["parameters"].get(name)
        if parameter is None or parameter["type"] == "trigger":
            return
        if parameter["type"] == "float":
            value, ok = QInputDialog.getDouble(
                self, f"Parâmetro {name}", "Valor padrão:", float(parameter["default"]), -1000000, 1000000, 3
            )
        else:
            text, ok = QInputDialog.getItem(
                self, f"Parâmetro {name}", "Valor padrão:", ["True", "False"],
                0 if parameter["default"] else 1, False,
            )
            value = text == "True"
        if ok:
            parameter["default"] = value
            self._refresh_all()

    def _add_transition(self) -> None:
        states = list(self.data["states"])
        origin, ok = QInputDialog.getItem(self, "Origem", "Estado de origem:", ["*"] + states, 0, False)
        if not ok:
            return
        target, ok = QInputDialog.getItem(self, "Destino", "Estado de destino:", states, 0, False)
        if not ok:
            return
        conditions = []
        parameters = list(self.data["parameters"])
        if parameters:
            choices = ["Sem condição"] + parameters
            parameter, ok = QInputDialog.getItem(self, "Condição", "Parâmetro:", choices, 0, False)
            if not ok:
                return
            if parameter != "Sem condição":
                kind = self.data["parameters"][parameter]["type"]
                operators = ["trigger"] if kind == "trigger" else ([">", ">=", "<", "<=", "==", "!="] if kind == "float" else ["==", "!="])
                operator, ok = QInputDialog.getItem(self, "Operador", "Comparação:", operators, 0, False)
                if not ok:
                    return
                value = True
                if kind == "float":
                    value, ok = QInputDialog.getDouble(self, "Valor", "Valor:", 0.0, -1000000, 1000000, 3)
                    if not ok:
                        return
                elif kind == "bool":
                    text, ok = QInputDialog.getItem(self, "Valor", "Valor:", ["True", "False"], 0, False)
                    if not ok:
                        return
                    value = text == "True"
                conditions.append({"parameter": parameter, "operator": operator, "value": value})
        self.data["transitions"].append({"from": origin, "to": target, "conditions": conditions})
        self._refresh_all()

    def _remove_transition(self) -> None:
        index = self.transitions_tree.indexOfTopLevelItem(self.transitions_tree.currentItem())
        if index >= 0:
            self.data["transitions"].pop(index)
            self._refresh_all()

    def _save(self) -> None:
        name = self.name_field.text().strip()
        if not name:
            QMessageBox.warning(self, "Nome obrigatório", "Informe um nome para o controller.")
            return
        self.data["name"] = name
        self.data["initial_state"] = self.initial_combo.currentText()
        if self.path is None:
            safe_name = "".join(character if character.isalnum() or character in "-_" else "_" for character in name)
            self.path = self.project_root / "Assets" / "Animations" / f"{safe_name}.zanimator"
        save_animator_controller(self.path, self.data)
        self.saved_path = self.path
        self.accept()
