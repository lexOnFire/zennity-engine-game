"""Compatibility adapters between the editor shell and focused controllers."""
from __future__ import annotations

import multiprocessing as mp
import sys
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QComboBox, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox,
)
from PySide6.QtWidgets import QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.controllers.logic_assets import LogicAssetRepository
from editor.isolated_viewport import run_viewport
from editor.runtime.viewport_process_controller import ViewportProcessController
from editor.editor_bootstrap_controller import EditorBootstrapController
from editor.animation_workspace_operations import AnimationWorkspaceOperations
from editor.widgets.component_picker import ComponentPickerDialog
from editor.widgets.animation_picker import AnimationPickerDialog
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from editor.ui.icons import component_title, editor_icon
from engine.animation.clip_asset import (
    animation_asset_from_clip,
    animation_asset_to_clip,
    default_animation_asset,
    save_animation_asset,
)

class EditorIntegrationAdapters:
    def _change_attached_script(self, old_path: str, new_path: str) -> None:
        self._script_workspace.change(old_path, new_path)

    def _remove_single_script(self, script_path: str) -> None:
        self._script_workspace.remove(script_path)

    def _update_script_config_val(self, script_path: str, key: str, value: float | bool | str) -> None:
        self._script_workspace.update_property(script_path, key, value)

    def _remove_all_scripts(self) -> None:
        self._script_workspace.remove_all()

    def _create_script_asset(self) -> None:
        self._script_workspace.create_asset()

    def _edit_selected_script(self) -> None:
        self._script_workspace.edit_selected()

    def _edit_script_path(self, path: Path) -> None:
        self._script_workspace.edit_path(path)

    def _change_view_mode(self, index: int) -> None:
        mode = "scene" if index == 0 else "game"
        self._commands.put({"type": "set_view_mode", "mode": mode})
        self._log("INFO", f"Aba alterada para: {mode.upper()}")

    def _build_viewport_link_toolbar(self) -> None:
        self._editor_commands.build_viewport_toolbar()

    def _save_selected_as_prefab(self) -> None:
        self._prefab_workspace.save_selected()

    def _create_prefab_variant(self, base_path: Path) -> None:
        self._prefab_workspace.create_variant(base_path)

