"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import json
import shutil
import uuid
from copy import deepcopy
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QColorDialog, QFileDialog, QInputDialog, QMenu, QToolBar,
    QHBoxLayout, QFormLayout,
    QCheckBox, QLabel, QComboBox, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox,
)
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.isolated_viewport import run_viewport
from editor.runtime.native_ui import normalize_ui, scene_item_to_ui, ui_to_scene_item
from editor.runtime.play_session import EditorPlaySession
from editor.runtime.sprite_rendering import assign_sprite_texture
from editor.script_templates import build_isolated_script_template, inspect_script_contract
from editor.widgets.component_picker import ComponentPickerDialog
from editor.widgets.animation_picker import AnimationPickerDialog
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from editor.ui.icons import component_title, editor_icon
from editor.ui.tokens import DEFAULT_TOKENS
from engine.animation.clip_asset import (
    animation_asset_from_clip,
    animation_asset_to_clip,
    default_animation_asset,
    load_animation_asset,
    save_animation_asset,
)
from engine.animation.controller_asset import load_animator_controller
from editor.widgets.build_report_dialog import BuildReportDialog
from editor.widgets.project_validation_dialog import ProjectValidationDialog
from engine.build import (
    BuildReport, ProjectValidationReport,
    export_development_project_with_report, validate_project,
)


class IsolatedEditorWindow(InterfaceSmokeTest):
    def __init__(self, viewport_process: mp.Process | None, commands, events) -> None:
        self._console_records: list[tuple[str, str]] = []
        self._last_build_report: BuildReport | None = None
        self._last_validation_report: ProjectValidationReport | None = None
        super().__init__()
        self._current_animation_asset_path: Path | None = None
        self._animation_draft_name = "NewAnimation"
        self._animation_events: list[dict] = []
        self._animation_asset_dirty = False
        self._animation_preview_playing = True
        self._animation_bound_key: tuple[str, str] | None = None
        # A workspace usa este índice durante sua configuração inicial.
        self._animator_preview_index = 0
        self._animator_controller_dialog: AnimatorControllerEditorDialog | None = None
        self._runtime_animator_states: dict[str, dict] = {}
        self._component_expanded = {
            "transform": True,
            "sprite": True,
            "audio": False,
            "rigidbody": False,
            "collider": False,
            "camera": False,
            "ui": True,
        }
        self._viewport_process = viewport_process
        self._commands = commands
        self._events = events
        self._pending_viewport_size: tuple[int, int] | None = None
        self._last_viewport_size_sent: tuple[int, int] | None = None
        self._viewport_resize_timer = QTimer(self)
        self._viewport_resize_timer.setSingleShot(True)
        self._viewport_resize_timer.setInterval(24)
        self._viewport_resize_timer.timeout.connect(self._flush_viewport_resize)
        self._initial_scene_snapshot = [
            {"id": "floor", "name": "Chao", "x": 0.0, "y": 150.0, "w": 600.0, "h": 32.0, "rotation": 0.0, "color": (91, 194, 100), "rigidbody": {"is_kinematic": True, "use_gravity": False}, "collider": {"type": "box"}},
            {"id": "player", "name": "Player", "x": 0.0, "y": 0.0, "w": 36.0, "h": 48.0, "rotation": 0.0, "color": (88, 117, 255), "rigidbody": {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}, "collider": {"type": "box"}, "scripts": ["Assets/Scripts/player_controller_2d.py"]},
        ]
        self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
        self._scene_document: dict | None = None
        self._current_scene_path: Path | None = None
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._selected_name: str | None = None
        self._updating_inspector = False
        self._undo_stack: list[list[dict]] = []
        self._redo_stack: list[list[dict]] = []
        self._drag_history_snapshot: list[dict] | None = None
        self._snap_enabled = False
        self._runtime_playing = False
        self._play_session = EditorPlaySession()
        self._runtime_keys = {
            key: False for key in ("left", "right", "up", "down", "jump", "restart")
        }
        self.setWindowTitle("Zennity Engine Editor — Phase 1")
        self.statusBar().showMessage(
            "Zennity Phase 1 pronto — Viewport em processo dedicado."
        )
        self._connect_existing_toolbar_actions()
        self._configure_main_menus()
        self._configure_tool_actions()
        self._configure_create_menu()
        self._connect_create_panel()
        self._configure_edit_menu()
        self._refresh_assets()
        self._refresh_prefabs()
        self.prefab_tree.itemDoubleClicked.connect(self._instantiate_prefab_item)
        for check in self.console_level_checks.values():
            check.toggled.connect(self._refresh_console)
        self.console_clear_button.clicked.connect(self._clear_console)
        self.assets_tree.itemClicked.connect(self._preview_asset)
        self._connect_hierarchy_to_viewport()
        self._refresh_hierarchy()
        self._connect_inspector_to_viewport()
        self._configure_animation_workspace()
        self.script_containers = []
        self._clear_inspector_view()
        self.add_component_button.clicked.connect(self._open_add_component_menu)
        self.viewport_tabs.currentChanged.connect(self._change_view_mode)

        # Habilita Drag & Drop na árvore de assets e viewport_host
        self.assets_tree.setDragEnabled(True)
        self.viewport_host.setAcceptDrops(True)
        self.viewport_host.installEventFilter(self)
        self._hierarchy_drop_targets = {self.hierarchy_tree, self.hierarchy_tree.viewport()}
        self._inspector_drop_targets = {self.inspector_panel, *self.inspector_panel.findChildren(QWidget)}
        self._scene_drop_targets = {self.viewport_tabs, self.viewport_tabs.tabBar(), self.viewport_host}
        self._script_drop_targets = self._hierarchy_drop_targets | self._inspector_drop_targets | self._scene_drop_targets
        for target in self._script_drop_targets:
            target.setAcceptDrops(True)
            target.installEventFilter(self)
        QApplication.instance().installEventFilter(self)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self._read_viewport_events)
        self._event_timer.start(33)
        self._animator_preview_timer = QTimer(self)
        self._animator_preview_timer.timeout.connect(self._tick_animation_preview)
        self._animator_preview_timer.start(125)
        self._log("INFO", "Zennity Phase 1 iniciado com Viewport em processo separado")

    def _log(self, level: str, message: str) -> None:
        normalized = str(level).upper()
        self._console_records.append((normalized, str(message)))
        self._console_records = self._console_records[-2000:]
        if self.console_level_checks.get(normalized) is None or self.console_level_checks[normalized].isChecked():
            self.console_output.appendPlainText(f"[{normalized}] {message}")

    def _refresh_console(self) -> None:
        visible = {level for level, check in self.console_level_checks.items() if check.isChecked()}
        self.console_output.setPlainText("\n".join(f"[{level}] {message}" for level, message in self._console_records if level in visible))

    def _clear_console(self) -> None:
        self._console_records.clear()
        self.console_output.clear()

    def _connect_create_panel(self) -> None:
        for kind, button in self.create_buttons.items():
            button.clicked.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))

    def _preview_asset(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if not path_value:
            return
        path = Path(path_value)
        self._set_asset_preview_state("content")
        if not path.exists() or path.is_dir():
            self.preview_label.clear()
            self.preview_label.setText("📁 Folder")
            self.preview_details_label.setText(f"<b>{path.name}</b><br><br>Tipo: Diretório do Projeto<br>Caminho: {path}")
            return

        import os
        from datetime import datetime

        size_bytes = os.path.getsize(path)
        size_kb = size_bytes / 1024.0
        size_str = f"{size_kb:.2f} KB" if size_kb < 1024.0 else f"{size_kb/1024.0:.2f} MB"
        mtime = os.path.getmtime(path)
        date_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        ext = path.suffix.lower()

        if ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(self.preview_label.width(), self.preview_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                meta = (
                    f"<b>{path.name}</b><br><br>"
                    f"Tipo: Textura 2D<br>"
                    f"Tamanho: {pixmap.width()} x {pixmap.height()} px<br>"
                    f"Formato: {ext[1:].upper()}<br>"
                    f"Tamanho Físico: {size_str}<br>"
                    f"Importado: {date_str}"
                )
                self.preview_details_label.setText(meta)
                return

        elif ext in {".wav", ".ogg", ".mp3"}:
            self.preview_label.clear()
            self.preview_label.setText("🔊 Audio")
            meta = (
                f"<b>{path.name}</b><br><br>"
                f"Tipo: Clipe de Áudio (AudioClip)<br>"
                f"Formato: {ext[1:].upper()}<br>"
                f"Tamanho: {size_str}<br>"
                f"Importado: {date_str}<br>"
                f"<i>Dica: Arraste para o Inspector para criar um AudioSource</i>"
            )
            self.preview_details_label.setText(meta)
            return

        elif ext == ".py":
            self.preview_label.clear()
            self.preview_label.setText("🐍 Script")
            meta = (
                f"<b>{path.name}</b><br><br>"
                f"Tipo: Script de Comportamento<br>"
                f"Tamanho: {size_str}<br>"
                f"Linguagem: Python 3<br>"
                f"Modificado: {date_str}"
            )
            self.preview_details_label.setText(meta)
            return

        elif ext == ".zanim":
            self.preview_label.clear()
            self.preview_label.setText("🎞 Animation")
            try:
                animation = load_animation_asset(path)
                details = (
                    f"Nome: {animation['name']}<br>"
                    f"Quadros: {len(animation['frames'])}<br>"
                    f"FPS: {animation['fps']:g}<br>"
                    f"Repetir: {'Sim' if animation['loop'] else 'Não'}<br>"
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                details = f"<span style='color:{DEFAULT_TOKENS.danger}'>Asset inválido: {exc}</span><br>"
            self.preview_details_label.setText(
                f"<b>{path.name}</b><br><br>Tipo: Clip de Animação 2D<br>{details}Tamanho: {size_str}<br>Modificado: {date_str}"
            )
            return

        elif ext == ".zanimator":
            self.preview_label.clear()
            self.preview_label.setText("◉ Animator Controller")
            try:
                controller = load_animator_controller(path)
                details = (
                    f"Nome: {controller['name']}<br>"
                    f"Estado inicial: {controller['initial_state']}<br>"
                    f"Estados: {len(controller['states'])}<br>"
                    f"Transições: {len(controller['transitions'])}<br>"
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                details = f"<span style='color:{DEFAULT_TOKENS.danger}'>Asset inválido: {exc}</span><br>"
            self.preview_details_label.setText(
                f"<b>{path.name}</b><br><br>Tipo: Animator Controller<br>{details}Tamanho: {size_str}<br>Modificado: {date_str}"
            )
            return

        elif ext in {".zscene", ".json"}:
            self.preview_label.clear()
            self.preview_label.setText("🎬 Scene")
            meta = (
                f"<b>{path.name}</b><br><br>"
                f"Tipo: Cena de Jogo<br>"
                f"Formato: Zennity JSON<br>"
                f"Tamanho: {size_str}<br>"
                f"Modificado: {date_str}"
            )
            self.preview_details_label.setText(meta)
            return

        # Fallback
        self.preview_label.clear()
        self.preview_label.setText("📄 File")
        meta = (
            f"<b>{path.name}</b><br><br>"
            f"Tipo: Recurso Genérico<br>"
            f"Formato: {ext.upper() or 'N/A'}<br>"
            f"Tamanho: {size_str}<br>"
            f"Modificado: {date_str}"
        )
        self.preview_details_label.setText(meta)

    def _set_asset_preview_state(self, state: str) -> None:
        """Atualiza somente o estado visual, preservando o conteúdo da prévia."""
        self.preview_label.setProperty("uiState", state)
        self.preview_label.style().unpolish(self.preview_label)
        self.preview_label.style().polish(self.preview_label)

    def attach_viewport_process(self, process: mp.Process) -> None:
        self._viewport_process = process

    def native_viewport_size(self) -> tuple[int, int]:
        """Return physical pixels expected by the native Pygame child window."""
        scale = max(1.0, float(self.viewport_host.devicePixelRatioF()))
        return (
            max(32, round(self.viewport_host.width() * scale)),
            max(32, round(self.viewport_host.height() * scale)),
        )

    def eventFilter(self, watched, event) -> bool:
        key_map = {
            Qt.Key_A: "left", Qt.Key_Left: "left",
            Qt.Key_D: "right", Qt.Key_Right: "right",
            Qt.Key_W: "up", Qt.Key_Up: "up",
            Qt.Key_S: "down", Qt.Key_Down: "down",
            Qt.Key_Space: "jump",
            Qt.Key_R: "restart",
        }
        if self._runtime_playing and event.type() == QEvent.ShortcutOverride and event.key() in key_map:
            event.accept()
            return True
        if self._runtime_playing and event.type() in (QEvent.KeyPress, QEvent.KeyRelease) and event.key() in key_map:
            if not event.isAutoRepeat():
                self._runtime_keys[key_map[event.key()]] = event.type() == QEvent.KeyPress
                self._commands.put({"type": "runtime_input", "keys": dict(self._runtime_keys)})
                self.statusBar().showMessage(f"Play Input: {key_map[event.key()]} {'ON' if event.type() == QEvent.KeyPress else 'OFF'}")
            return True
        if watched is self.viewport_host and event.type() == QEvent.Resize:
            self._pending_viewport_size = self.native_viewport_size()
            self._viewport_resize_timer.start()
        if watched in self._script_drop_targets:
            if self._play_session.is_running and event.type() in {
                QEvent.DragEnter, QEvent.DragMove, QEvent.Drop
            }:
                event.ignore()
                return True
            if event.type() == QEvent.DragEnter:
                if event.source() is not self.assets_tree:
                    return super().eventFilter(watched, event)
                path = self._dragged_asset_path()
                if path is not None and path.suffix.lower() in {".py", ".zanim", ".zanimator", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.DragMove:
                if event.source() is not self.assets_tree:
                    return super().eventFilter(watched, event)
                event.acceptProposedAction()
                return True
            elif event.type() == QEvent.Drop:
                if event.source() is not self.assets_tree:
                    return super().eventFilter(watched, event)
                path = self._dragged_asset_path()
                if path is not None and path.suffix.lower() == ".py":
                    if watched is self.viewport_host:
                        pos = event.position()
                        scale = max(1.0, float(self.viewport_host.devicePixelRatioF()))
                        self._commands.put({"type": "script_drop_at", "path": str(path.resolve()), "screen_x": float(pos.x()) * scale, "screen_y": float(pos.y()) * scale})
                        event.acceptProposedAction()
                        return True
                    target_name = self._selected_name
                    if watched in self._hierarchy_drop_targets:
                        local_position = self.hierarchy_tree.viewport().mapFromGlobal(event.globalPosition().toPoint())
                        item = self.hierarchy_tree.itemAt(local_position)
                        item_name = self._hierarchy_item_name(item)
                        if item_name in self._objects_by_name:
                            target_name = item_name
                    if target_name in self._objects_by_name:
                        self._attach_script(target_name, path)
                        event.acceptProposedAction()
                        return True
                elif path is not None and path.suffix.lower() == ".zanim":
                    target_name = self._selected_name
                    if watched in self._hierarchy_drop_targets:
                        local_position = self.hierarchy_tree.viewport().mapFromGlobal(event.globalPosition().toPoint())
                        item = self.hierarchy_tree.itemAt(local_position)
                        item_name = self._hierarchy_item_name(item)
                        if item_name in self._objects_by_name:
                            target_name = item_name
                    if target_name in self._objects_by_name:
                        self._apply_animation_asset_path_to_object(path, target_name)
                        event.acceptProposedAction()
                        return True
                elif path is not None and path.suffix.lower() == ".zanimator":
                    target_name = self._selected_name
                    if watched in self._hierarchy_drop_targets:
                        local_position = self.hierarchy_tree.viewport().mapFromGlobal(event.globalPosition().toPoint())
                        item = self.hierarchy_tree.itemAt(local_position)
                        item_name = self._hierarchy_item_name(item)
                        if item_name in self._objects_by_name:
                            target_name = item_name
                    if target_name in self._objects_by_name:
                        self._apply_animator_controller_path(path, target_name)
                        event.acceptProposedAction()
                        return True
                elif path is not None and watched is self.viewport_host and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                    pos = event.position()
                    scale = max(1.0, float(self.viewport_host.devicePixelRatioF()))
                    self._create_sprite_at(path, float(pos.x()) * scale, float(pos.y()) * scale)
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(watched, event)

    def _flush_viewport_resize(self) -> None:
        """Agrupa a rajada de Resize do Qt e envia sempre o último tamanho."""
        size = self._pending_viewport_size
        self._pending_viewport_size = None
        if size is None or size == self._last_viewport_size_sent:
            return
        self._last_viewport_size_sent = size
        self._commands.put({"type": "viewport_size", "w": size[0], "h": size[1]})

    def _dragged_asset_path(self) -> Path | None:
        selected_items = self.assets_tree.selectedItems()
        if not selected_items:
            return None
        path_value = selected_items[0].toolTip(0)
        return Path(path_value) if path_value else None

    def _attach_script(self, object_name: str, path: Path) -> None:
        if self._play_session.is_running:
            return
        if object_name not in self._objects_by_name or path.suffix.lower() != ".py":
            return
        try:
            script_path = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            script_path = str(path.resolve())
        obj = self._objects_by_name[object_name]
        if script_path in obj.get("scripts", []):
            self.statusBar().showMessage(f"Script já anexado: {path.name}")
            return
        compatible, reason = inspect_script_contract(path)
        if not compatible:
            self._log("WARNING", f"Script anexado, mas incompatível com Play isolado: {path.name}: {reason}")
        self._record_history()
        scripts = obj.setdefault("scripts", [])
        scripts.append(script_path)
        self._component_expanded[f"script:{script_path}"] = True
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": object_name})
        self._selected_name = object_name
        self._update_inspector(object_name)
        self._log("INFO", f"Script anexado em {object_name}: {script_path}")

    def _get_available_scripts(self) -> list[Path]:
        scripts_dir = Path.cwd() / "Assets" / "Scripts"
        if scripts_dir.exists():
            return sorted([p for p in scripts_dir.glob("*.py") if p.name != "__init__.py"])
        return []

    def _change_attached_script(self, old_path: str, new_path: str) -> None:
        if self._selected_name not in self._objects_by_name or not new_path:
            return
        if old_path == new_path:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        scripts = obj.get("scripts", [])
        if old_path in scripts:
            idx = scripts.index(old_path)
            scripts[idx] = new_path
        else:
            scripts.append(new_path)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Script alterado de {Path(old_path).name} para {Path(new_path).name}")

    def _remove_single_script(self, script_path: str) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        scripts = obj.get("scripts", [])
        if script_path in scripts:
            scripts.remove(script_path)
        if not scripts:
            obj.pop("scripts", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Script removido: {Path(script_path).name}")

    def _update_script_config_val(self, script_path: str, key: str, value: float | bool | str) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        properties = obj.setdefault("script_properties", {}).setdefault(script_path, {})
        if properties.get(key) == value:
            return
        self._record_history()
        properties[key] = value
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._log("INFO", f"{self._selected_name}: '{key}' = {value} em {Path(script_path).name}")

    def _remove_all_scripts(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        obj.pop("scripts", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Todos os scripts removidos de {self._selected_name}")

    def _create_script_asset(self) -> None:
        if self._selected_name not in self._objects_by_name:
            self.statusBar().showMessage("Selecione um objeto antes de criar o script")
            return
        default_path = Path.cwd() / "Assets" / "Scripts" / "new_script.py"
        filename, _ = QFileDialog.getSaveFileName(self, "Criar Script", str(default_path), "Python Script (*.py)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".py":
            path = path.with_suffix(".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(build_isolated_script_template(path.stem), encoding="utf-8")
        self._refresh_assets()
        self._attach_script(self._selected_name, path)
        self._edit_script_path(path)

    def _edit_selected_script(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        scripts = obj.get("scripts", [])
        if not scripts:
            self.statusBar().showMessage("Nenhum script anexado para editar")
            return
        self._edit_script_path(Path(scripts[0]))

    def _edit_script_path(self, path: Path) -> None:
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            self.statusBar().showMessage(f"Script não encontrado: {path}")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve()))):
            self.statusBar().showMessage(f"Não foi possível abrir o editor para {path.name}")

    def _change_view_mode(self, index: int) -> None:
        animation_mode = index == 2
        self.animation_workspace.setVisible(animation_mode)
        self.viewport_host.setVisible(not animation_mode)
        if animation_mode:
            self._refresh_animation_library()
            self._log("INFO", "Aba alterada para: ANIMATION")
            if self._selected_name in self._objects_by_name:
                self._update_inspector(self._selected_name)
            return
        mode = "scene" if index == 0 else "game"
        self._commands.put({"type": "set_view_mode", "mode": mode})
        self._log("INFO", f"Aba alterada para: {mode.upper()}")

    def _build_viewport_link_toolbar(self) -> None:
        toolbar = QToolBar("Ligação com Viewport")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, payload in (
            ("Selecionar Player", {"type": "select_object", "name": "Player"}),
            ("Mover ←", {"type": "move_selected", "dx": -16}),
            ("Mover →", {"type": "move_selected", "dx": 16}),
            ("Reset", {"type": "reset_from_interface"}),
        ):
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, message=payload: self._send_toolbar_command(message))
            toolbar.addAction(action)

    def _configure_main_menus(self) -> None:
        for label in ("Novo", "Abrir", "Salvar"):
            self.editor_menus["Arquivo"].addAction(self.toolbar_actions[label])
        for label in ("Select", "Move", "Rotate", "Scale", "Snap: OFF"):
            self.editor_menus["Ferramentas"].addAction(self.toolbar_actions[label])
        for label in ("Play", "Pause", "Stop"):
            self.editor_menus["Executar"].addAction(self.toolbar_actions[label])
        validate_action = self.editor_menus["Build"].addAction("Validar projeto...")
        validate_action.triggered.connect(self._validate_current_project)
        self.editor_menus["Build"].addSeparator()
        export_action = self.editor_menus["Build"].addAction("Exportar projeto...")
        export_action.triggered.connect(self._export_project)
        report_action = self.editor_menus["Build"].addAction("Último relatório...")
        report_action.setEnabled(False)
        report_action.triggered.connect(self._show_last_build_report)
        self._build_report_action = report_action
        self.toolbar_actions["Pause"].setEnabled(False)
        self.toolbar_actions["Stop"].setEnabled(False)
        snap_action = self.toolbar_actions["Snap: OFF"]
        snap_action.setCheckable(True)
        snap_action.toggled.connect(self._toggle_snap)

    def _toggle_snap(self, enabled: bool) -> None:
        self._snap_enabled = bool(enabled)
        action = self.toolbar_actions["Snap: OFF"]
        action.setText("Snap: ON" if enabled else "Snap: OFF")
        self._commands.put({"type": "set_snap", "enabled": bool(enabled), "size": 16.0, "angle": 15.0})
        self.statusBar().showMessage("Snap ativado" if enabled else "Snap desativado")

    def _refresh_assets(self) -> None:
        self.assets_tree.clear()
        root_path = Path.cwd() / "Assets"
        if not root_path.exists():
            root_path = Path.cwd() / "assets"
        root_item = QTreeWidgetItem(["📁 " + (root_path.name if root_path.exists() else "Assets")])
        self.assets_tree.addTopLevelItem(root_item)

        def add_directory(parent_item: QTreeWidgetItem, directory: Path) -> None:
            for child in sorted(directory.iterdir(), key=lambda path: (path.is_file(), path.name.lower())):
                if child.name.startswith(".") or child.suffix == ".meta":
                    continue
                if child.is_dir():
                    icon = "📁 "
                elif child.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    icon = "🖼️ "
                elif child.suffix.lower() in (".ogg", ".wav", ".mp3"):
                    icon = "🔊 "
                elif child.suffix.lower() == ".zanim":
                    icon = "🎞 "
                elif child.suffix.lower() == ".zanimator":
                    icon = "◉ "
                else:
                    icon = "📄 "
                item = QTreeWidgetItem([icon + child.name])
                item.setToolTip(0, str(child))
                parent_item.addChild(item)
                if child.is_dir():
                    add_directory(item, child)

        if root_path.exists():
            add_directory(root_item, root_path)
        root_item.setExpanded(True)

    def _refresh_prefabs(self) -> None:
        self.prefab_tree.clear()
        root = QTreeWidgetItem(["📦 Prefabs"])
        self.prefab_tree.addTopLevelItem(root)
        directory = Path.cwd() / "Assets" / "Prefabs"
        directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(directory.glob("*.zprefab"), key=lambda item: item.name.lower()):
            item = QTreeWidgetItem(["🧩 " + path.stem])
            item.setToolTip(0, str(path))
            root.addChild(item)
        root.setExpanded(True)

    def _save_selected_as_prefab(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        default_name = self._selected_name
        name, accepted = QInputDialog.getText(self, "Criar Prefab", "Nome do Prefab:", text=default_name)
        name = "".join(char for char in name.strip() if char.isalnum() or char in "-_ ")
        if not accepted or not name:
            return
        path = Path.cwd() / "Assets" / "Prefabs" / f"{name}.zprefab"
        prefab_object = deepcopy(self._objects_by_name[self._selected_name])
        prefab_object.pop("id", None)
        payload = {"format_version": 1, "prefab_name": name, "object": prefab_object}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self._refresh_prefabs()
        self._refresh_assets()
        self._log("INFO", f"Prefab criado: {path.name}")

    def _instantiate_prefab_item(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if not path_value:
            return
        try:
            payload = json.loads(Path(path_value).read_text(encoding="utf-8"))
            prefab_object = payload.get("object")
            if not isinstance(prefab_object, dict):
                raise ValueError("objeto do Prefab inválido")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._log("ERROR", f"Falha ao abrir Prefab: {exc}")
            return
        self._record_history()
        obj = deepcopy(prefab_object)
        obj["id"] = str(uuid.uuid4())
        obj["name"] = self._unique_name(str(obj.get("name") or payload.get("prefab_name") or "Prefab"))
        obj["x"] = float(obj.get("x", 0.0)) + 16.0
        obj["y"] = float(obj.get("y", 0.0)) + 16.0
        self._scene_snapshot.append(obj)
        self._objects_by_name[obj["name"]] = obj
        self._selected_name = obj["name"]
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._commands.put({"type": "select_object", "name": obj["name"]})
        self._update_inspector(obj["name"])
        self._log("INFO", f"Prefab adicionado: {obj['name']}")

    def _export_project(self) -> None:
        self._save_scene_snapshot()
        if self._current_scene_path is None:
            return
        validation = validate_project(Path.cwd(), self._current_scene_path)
        self._last_validation_report = validation
        if not validation.valid:
            self._log("ERROR", f"Exportação bloqueada por {len(validation.errors)} erro(s) de validação")
            self.statusBar().showMessage("Corrija os erros de validação antes de exportar")
            ProjectValidationDialog(validation, self).exec()
            return
        output = QFileDialog.getExistingDirectory(self, "Pasta para exportar", str(Path.cwd() / "Builds"))
        if not output:
            return
        default_name = str((self._scene_document or {}).get("scene_name", "ZennityGame"))
        project_name, accepted = QInputDialog.getText(self, "Exportar projeto", "Nome do jogo:", text=default_name)
        if not accepted or not project_name.strip():
            return
        report = export_development_project_with_report(
            Path.cwd(), self._current_scene_path, Path(output), project_name
        )
        self._last_build_report = report
        self._build_report_action.setEnabled(True)
        if report.success:
            self._log(
                "INFO",
                f"Projeto exportado: {report.destination} "
                f"({report.file_count} arquivos, {len(report.warnings)} aviso(s))",
            )
            self.statusBar().showMessage(f"Build criado em {report.destination}")
        else:
            self._log("ERROR", f"Build não concluído: {len(report.errors)} erro(s)")
            self.statusBar().showMessage("Build não concluído — consulte o relatório")
        self._show_last_build_report()

    def _validate_current_project(self) -> None:
        self._save_scene_snapshot()
        if self._current_scene_path is None:
            return
        report = validate_project(Path.cwd(), self._current_scene_path)
        self._last_validation_report = report
        if report.valid:
            self._log("INFO", f"Projeto validado: {len(report.warnings)} aviso(s), nenhum erro")
            self.statusBar().showMessage("Projeto pronto para exportar")
        else:
            self._log("ERROR", f"Validação encontrou {len(report.errors)} erro(s) e {len(report.warnings)} aviso(s)")
            self.statusBar().showMessage("Projeto precisa de correções antes da exportação")
        ProjectValidationDialog(report, self).exec()

    def _show_last_build_report(self) -> None:
        if self._last_build_report is None:
            return
        BuildReportDialog(self._last_build_report, self).exec()

    def _connect_existing_toolbar_actions(self) -> None:
        commands = {
            "Novo": {"type": "new_scene"},
            "Abrir": {"type": "load_scene"},
            "Salvar": {"type": "save_scene"},
            "Play": {"type": "play"},
            "Pause": {"type": "pause"},
            "Stop": {"type": "stop"},
        }
        for action in self.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            payload = commands.get(label)
            if payload is not None:
                action.triggered.connect(
                    lambda checked=False, message=payload: self._send_toolbar_command(message)
                )

    def _configure_tool_actions(self) -> None:
        group = QActionGroup(self)
        group.setExclusive(True)
        shortcuts = {"select": "Q", "move": "W", "rotate": "E", "scale": "R"}
        for action in self.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            tool = label.lower()
            if tool not in {"select", "move", "rotate", "scale"}:
                continue
            action.setCheckable(True)
            action.setShortcut(shortcuts[tool])
            action.setChecked(tool == "select")
            group.addAction(action)
            action.triggered.connect(lambda checked=False, name=tool: checked and self._commands.put({"type": "set_tool", "tool": name}))
        self._tool_action_group = group

    def _send_toolbar_command(self, message: dict) -> None:
        starting_play = False
        if self._play_session.is_running and message.get("type") in {
            "new_scene", "load_scene", "reset_from_interface", "move_selected"
        }:
            self.statusBar().showMessage("Pare o Play Mode antes de alterar a cena")
            return
        if message.get("type") == "new_scene":
            self._new_scene()
            return
        if message.get("type") == "save_scene":
            self._save_scene_snapshot()
            return
        if message.get("type") == "load_scene":
            self._load_scene_snapshot()
            return
        if message.get("type") == "reset_from_interface":
            self._record_history()
            self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
            self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
            self._refresh_hierarchy()
            self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
            if self._selected_name in self._objects_by_name:
                self._update_inspector(self._selected_name)
            return
        if message.get("type") == "play":
            resuming_play = self._play_session.state == "pause"
            play_snapshot = self._play_session.begin(self._scene_snapshot, self._selected_name)
            self._runtime_playing = True
            self._set_play_mode_editing_locked(True)
            self.toolbar_actions["Play"].setEnabled(False)
            self.toolbar_actions["Pause"].setEnabled(False)
            self.toolbar_actions["Stop"].setEnabled(True)
            self.viewport_tabs.setCurrentIndex(1)
            if resuming_play:
                self._log("INFO", "Retomando Play pausado")
            else:
                starting_play = True
                attached = [(obj["name"], path) for obj in play_snapshot for path in obj.get("scripts", [])]
                self._log("INFO", f"Play solicitado com {len(attached)} script(s) anexado(s)")
                for object_name, path in attached:
                    self._log("INFO", f"  {object_name} → {path}")
                self._commands.put({"type": "scene_snapshot", "objects": deepcopy(play_snapshot)})
                audio_sources = {
                    obj["name"]: deepcopy(obj["audio"])
                    for obj in play_snapshot
                    if isinstance(obj.get("audio"), dict)
                }
                enabled_audio = [name for name, audio in audio_sources.items() if audio.get("autoplay") and audio.get("path")]
                self._log("INFO", f"Play enviando {len(audio_sources)} Audio Source(s); {len(enabled_audio)} configurado(s) para iniciar")
                message = {**message, "audio_sources": audio_sources}
        elif message.get("type") == "stop":
            self.viewport_tabs.setCurrentIndex(0)
        if message.get("type") == "move_selected" and self._selected_name is not None:
            self._record_history()
        self._commands.put(message)
        if message.get("type") == "play" and starting_play:
            # Comando separado: não depende do carregamento ou da presença de scripts.
            self._commands.put({"type": "start_play_audio", "audio_sources": audio_sources})
        elif message.get("type") == "stop":
            # Garante a interrupção mesmo que o estado de scripts já tenha mudado.
            self._commands.put({"type": "stop_all_audio"})

    def _set_play_mode_editing_locked(self, locked: bool) -> None:
        """Mantém a inspeção visível, mas impede alterações na cena em execução."""
        self.inspector_panel.setEnabled(not locked)
        self.hierarchy_tree.setDragEnabled(not locked)
        for label in ("Desfazer", "Refazer", "Move", "Rotate", "Scale", "Snap: OFF"):
            action = self.toolbar_actions.get(label)
            if action is not None:
                action.setEnabled(not locked)
        create_menu = self.editor_menus.get("Criar")
        if create_menu is not None:
            for action in create_menu.actions():
                action.setEnabled(not locked)

    def _configure_create_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Criar":
                continue
            menu.clear()
            for label, kind in (
                ("Empty Object", "Empty"), ("Sprite 2D", "Sprite"),
                ("Player 2D", "Player"), ("Platform 2D", "Platform"),
                ("Enemy 2D", "Enemy"), ("Trigger 2D", "Trigger"),
                ("Camera 2D", "Camera"),
            ):
                action = menu.addAction(label)
                action.triggered.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))
            break

    def _configure_edit_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Editar":
                continue
            menu.clear()
            undo_action = self.toolbar_actions["Desfazer"]
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(self._undo)
            menu.addAction(undo_action)
            redo_action = self.toolbar_actions["Refazer"]
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(self._redo)
            menu.addAction(redo_action)
            menu.addSeparator()
            duplicate_action = menu.addAction("Duplicar")
            duplicate_action.setShortcut("Ctrl+D")
            duplicate_action.triggered.connect(self._duplicate_selected)
            delete_action = menu.addAction("Excluir")
            delete_action.setShortcut("Delete")
            delete_action.triggered.connect(
                lambda _checked=False: self._selected_name is not None and self._delete_object(self._selected_name)
            )
            break

    def _record_history(self, snapshot: list[dict] | None = None) -> None:
        state = deepcopy(snapshot if snapshot is not None else self._scene_snapshot)
        if not self._undo_stack or self._undo_stack[-1] != state:
            self._undo_stack.append(state)
            self._undo_stack = self._undo_stack[-100:]
        self._redo_stack.clear()

    def _restore_history(self, snapshot: list[dict]) -> None:
        self._scene_snapshot = deepcopy(snapshot)
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        if self._selected_name not in self._objects_by_name:
            self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        if self._selected_name is not None:
            self._commands.put({"type": "select_object", "name": self._selected_name})
            self._update_inspector(self._selected_name)

    def _undo(self) -> None:
        if self._undo_stack:
            self._redo_stack.append(deepcopy(self._scene_snapshot))
            self._restore_history(self._undo_stack.pop())

    def _redo(self) -> None:
        if self._redo_stack:
            self._undo_stack.append(deepcopy(self._scene_snapshot))
            self._restore_history(self._redo_stack.pop())

    def _new_scene(self) -> None:
        self._record_history()
        self._scene_snapshot = []
        self._objects_by_name = {}
        self._scene_document = {"format_version": 1, "scene_name": "Untitled", "engine_version": "Zennity 0.1.0", "objects": []}
        self._current_scene_path = None
        self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": []})
        self.statusBar().showMessage("Nova cena criada")
        self._log("INFO", "Nova cena criada")

    def _unique_name(self, base: str) -> str:
        if base not in self._objects_by_name:
            return base
        index = 2
        while f"{base}_{index}" in self._objects_by_name:
            index += 1
        return f"{base}_{index}"

    def _create_object(self, kind: str) -> None:
        if self._play_session.is_running:
            return
        self._record_history()
        presets = {
            "Empty": ("GameObject", 40.0, 40.0, (160, 164, 174), None),
            "Sprite": ("Sprite", 64.0, 64.0, (180, 180, 190), None),
            "Player": ("Player", 36.0, 48.0, (88, 117, 255), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Platform": ("Platform", 160.0, 32.0, (91, 194, 100), {"is_kinematic": True, "use_gravity": False}),
            "Enemy": ("Enemy", 40.0, 40.0, (220, 88, 88), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Trigger": ("Trigger", 80.0, 80.0, (222, 178, 72), {"is_kinematic": True, "use_gravity": False}),
            "Camera": ("Camera2D", 96.0, 54.0, (110, 190, 210), None),
        }
        base, width, height, color, rigidbody = presets[kind]
        name = self._unique_name(base)
        obj = {"id": str(uuid.uuid4()), "name": name, "x": 450.0, "y": 250.0, "w": width, "h": height, "rotation": 0.0, "color": color, "mesh_type": kind}
        if rigidbody is not None:
            obj["rigidbody"] = rigidbody
            obj["collider"] = {"type": "box"}
        if kind == "Trigger":
            obj["collider"]["is_trigger"] = True
        if kind == "Player":
            obj["scripts"] = ["Assets/Scripts/player_controller_2d.py"]
        if kind == "Camera":
            obj["component_names"] = ["Camera2D"]
            obj["camera"] = {"active": True, "zoom": 1.0}
        self._scene_snapshot.append(obj)
        self._objects_by_name[name] = obj
        self._selected_name = name
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": name})
        self._update_inspector(name)
        self._log("INFO", f"Objeto criado: {name}")

    def _create_object_at(self, kind: str, screen_x: float, screen_y: float) -> None:
        self._record_history()
        self._commands.put({
            "type": "create_object_at",
            "kind": kind,
            "screen_x": screen_x,
            "screen_y": screen_y
        })

    def _create_sprite_at(self, texture_path: Path, screen_x: float, screen_y: float) -> None:
        try:
            relative = str(texture_path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            relative = str(texture_path.resolve())
        pixmap = QPixmap(str(texture_path))
        width = float(pixmap.width()) if not pixmap.isNull() else 64.0
        height = float(pixmap.height()) if not pixmap.isNull() else 64.0
        self._record_history()
        self._commands.put({
            "type": "create_sprite_at", "texture": relative,
            "screen_x": screen_x, "screen_y": screen_y,
            "width": max(1.0, width), "height": max(1.0, height),
        })

    def _save_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar cena", str(self._current_scene_path or "Untitled.zscene"),
            "Zennity Scene (*.zscene);;Cena JSON (*.json)"
        )
        if not filename:
            return
        path = Path(filename)
        payload = deepcopy(self._scene_document) if self._scene_document else {
            "format_version": 2, "scene_name": path.stem, "engine_version": "Zennity 0.1.0", "objects": []
        }
        payload["format_version"] = max(2, int(payload.get("format_version", 1)))
        payload["scene_name"] = str(payload.get("scene_name") or path.stem)
        existing_by_id = {str(item.get("id")): item for item in payload.get("objects", []) if item.get("id") is not None}
        existing_by_name = {str(item.get("name")): item for item in payload.get("objects", [])}
        scene_objects = []
        for snapshot in self._scene_snapshot:
            source = deepcopy(existing_by_id.get(str(snapshot.get("id"))) or existing_by_name.get(snapshot["name"], {}))
            source.update({"name": snapshot["name"], "active": bool(snapshot.get("active", True)), "enabled": bool(snapshot.get("active", True)), "static": bool(snapshot.get("static", False)), "tag": str(snapshot.get("tag", "Untagged")), "layer": str(snapshot.get("layer", "Default"))})
            source.setdefault("id", snapshot.get("id", snapshot["name"]))
            source["transform"] = {
                "position": [snapshot["x"], snapshot["y"], 0.0],
                "rotation": [0.0, 0.0, float(snapshot.get("rotation", 0.0))],
                "rz": float(snapshot.get("rotation", 0.0)),
                "scale": [snapshot["w"], snapshot["h"], 1.0],
            }
            source.setdefault("visual", {"mesh_type": snapshot.get("mesh_type"), "color": snapshot.get("color")})
            if not isinstance(source.get("visual"), dict):
                source["visual"] = {"mesh_type": snapshot.get("mesh_type"), "color": snapshot.get("color")}
            source["visual"]["enabled"] = bool(snapshot.get("renderer_enabled", True))
            source["visual"]["material"] = str(snapshot.get("material", "Default_Material"))
            source["visual"]["mesh_type"] = snapshot.get("mesh_type")
            source["visual"]["color"] = snapshot.get("color", (255, 255, 255))
            source["visual"]["texture"] = str(snapshot.get("texture", ""))
            source["visual"]["layer"] = str(snapshot.get("render_layer", "Default"))
            source["visual"]["order"] = int(snapshot.get("sort_order", 0))
            components = source.get("components")
            if not isinstance(components, dict):
                components = {}
                source["components"] = components
            components.pop("controller", None)
            for key in ("rigidbody", "collider", "camera", "audio", "scripts"):
                components.pop(key, None)
            if snapshot.get("rigidbody") is not None:
                components["rigidbody"] = deepcopy(snapshot["rigidbody"])
            if snapshot.get("collider") is not None:
                collider = deepcopy(snapshot["collider"])
                collider.setdefault("width", snapshot["w"])
                collider.setdefault("height", snapshot["h"])
                components["collider"] = collider
            if snapshot.get("camera") is not None or "Camera2D" in snapshot.get("component_names", []):
                components["camera"] = deepcopy(snapshot.get("camera") or {"active": True, "zoom": 1.0})
            if snapshot.get("scripts"):
                components["scripts"] = list(dict.fromkeys(str(path) for path in snapshot["scripts"]))
            if isinstance(snapshot.get("audio"), dict):
                components["audio"] = deepcopy(snapshot["audio"])
            existing_items = components.get("items") if isinstance(components.get("items"), list) else []
            components["items"] = [
                deepcopy(item) for item in existing_items
                if scene_item_to_ui(item) is None
            ]
            ui_item = ui_to_scene_item(snapshot.get("ui"))
            if ui_item is not None:
                components["items"].append(ui_item)
            if not components["items"]:
                components.pop("items", None)
            known_keys = {
                "id", "name", "x", "y", "w", "h", "rotation", "color", "mesh_type",
                "renderer_enabled", "material", "texture", "render_layer", "sort_order", "active", "static", "tag", "layer",
                "rigidbody", "collider", "camera", "audio", "scripts", "component_names", "ui",
            }
            editor_data = {
                key: deepcopy(value) for key, value in snapshot.items()
                if key not in known_keys and not str(key).startswith("_")
            }
            if editor_data:
                source["editor_data"] = editor_data
            else:
                source.pop("editor_data", None)
            scene_objects.append(source)
        payload["objects"] = scene_objects
        temporary_path = path.with_name(path.name + ".tmp")
        temporary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary_path.replace(path)
        self._scene_document = payload
        self._current_scene_path = path
        self.statusBar().showMessage(f"Cena salva: {filename}")
        self._log("INFO", f"Cena salva: {filename}")

    def _load_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir cena", "", "Zennity Scene (*.zscene);;Cena JSON (*.json)"
        )
        if not filename:
            return
        try:
            payload = json.loads(Path(filename).read_text(encoding="utf-8"))
            objects = payload.get("objects", [])
            if not isinstance(objects, list):
                raise ValueError("arquivo de cena inválido")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.statusBar().showMessage(f"Falha ao abrir cena: {exc}")
            return
        snapshots = []
        for item in objects:
            if not isinstance(item, dict) or "name" not in item:
                continue
            if "transform" in item:
                transform = item.get("transform", {})
                position = list(transform.get("position", [0.0, 0.0, 0.0]))
                scale = list(transform.get("scale", [32.0, 32.0, 1.0]))
                visual = item.get("visual", {}) or {}
                components = item.get("components", {}) or {}
                color = visual.get("color") or ((91, 194, 100) if item["name"].lower() in {"chao", "floor"} else (88, 117, 255))
                rotation = transform.get("rz", (transform.get("rotation") or [0.0, 0.0, 0.0])[2])
                snapshot = {"id": item.get("id", item["name"]), "name": item["name"], "x": float(position[0]), "y": float(position[1]), "w": abs(float(scale[0])), "h": abs(float(scale[1])), "rotation": float(rotation), "color": color, "mesh_type": visual.get("mesh_type"), "renderer_enabled": bool(visual.get("enabled", True)), "material": str(visual.get("material", "Default_Material")), "texture": str(visual.get("texture", "")), "render_layer": str(visual.get("layer", "Default")), "sort_order": int(visual.get("order", 0)), "active": bool(item.get("active", item.get("enabled", True))), "static": bool(item.get("static", False)), "tag": str(item.get("tag", "Untagged")), "layer": str(item.get("layer", "Default"))}
                if isinstance(item.get("editor_data"), dict):
                    snapshot.update(deepcopy(item["editor_data"]))
                if isinstance(components.get("rigidbody"), dict):
                    snapshot["rigidbody"] = deepcopy(components["rigidbody"])
                if isinstance(components.get("collider"), dict):
                    snapshot["collider"] = deepcopy(components["collider"])
                if isinstance(components.get("camera"), dict):
                    snapshot["camera"] = deepcopy(components["camera"])
                if isinstance(components.get("audio"), dict):
                    snapshot["audio"] = deepcopy(components["audio"])
                component_names = ["Camera2D"] if isinstance(components.get("camera"), dict) else []
                for component in components.get("items", []):
                    if isinstance(component, dict):
                        component_names.append(str(component.get("type") or component.get("component_type") or "Component"))
                        parsed_ui = scene_item_to_ui(component)
                        if parsed_ui is not None:
                            snapshot["ui"] = parsed_ui
                if components.get("scripts"):
                    snapshot["scripts"] = [str(script) for script in components["scripts"]]
                    component_names.extend(f"Script: {script}" for script in components["scripts"])
                if component_names:
                    snapshot["component_names"] = component_names
                snapshots.append(snapshot)
            elif {"x", "y", "w", "h"}.issubset(item):
                snapshots.append(dict(item))
        if not snapshots and objects:
            self.statusBar().showMessage("Falha ao abrir cena: nenhum objeto compatível")
            return
        names = [str(item["name"]) for item in snapshots]
        if len(names) != len(set(names)):
            self.statusBar().showMessage("Falha ao abrir cena: existem objetos com nomes duplicados")
            return
        self._record_history()
        self._scene_snapshot = snapshots
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._scene_document = payload if any("transform" in item for item in objects if isinstance(item, dict)) else None
        self._current_scene_path = Path(filename)
        self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self.statusBar().showMessage(f"Cena aberta: {filename}")
        self._log("INFO", f"Cena aberta: {filename}")

    def _connect_hierarchy_to_viewport(self) -> None:
        self.hierarchy_tree.setDragEnabled(True)
        self.hierarchy_tree.setAcceptDrops(True)
        self.hierarchy_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.hierarchy_tree.itemClicked.connect(self._select_hierarchy_item)
        self.hierarchy_tree.itemDoubleClicked.connect(lambda item: self._rename_object(self._hierarchy_item_name(item)))
        self.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hierarchy_tree.customContextMenuRequested.connect(self._open_hierarchy_menu)

    def _open_hierarchy_menu(self, position) -> None:
        item = self.hierarchy_tree.itemAt(position)
        item_name = self._hierarchy_item_name(item)
        if item is None or item_name not in self._objects_by_name:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Renomear")
        duplicate_action = menu.addAction("Duplicar")
        prefab_action = menu.addAction("Criar Prefab")
        delete_action = menu.addAction("Excluir")
        rename_action.triggered.connect(lambda _checked=False: self._rename_object(item_name))
        duplicate_action.triggered.connect(lambda _checked=False: self._select_and_duplicate(item_name))
        prefab_action.triggered.connect(lambda _checked=False: self._select_and_save_prefab(item_name))
        delete_action.triggered.connect(lambda _checked=False: self._delete_object(item_name))
        menu.exec(self.hierarchy_tree.viewport().mapToGlobal(position))

    def _select_and_duplicate(self, name: str) -> None:
        self._selected_name = name
        self._duplicate_selected()

    def _select_and_save_prefab(self, name: str) -> None:
        self._selected_name = name
        self._save_selected_as_prefab()

    def _rename_object(self, old_name: str) -> None:
        if self._play_session.is_running:
            return
        new_name, accepted = QInputDialog.getText(self, "Renomear objeto", "Nome:", text=old_name)
        new_name = new_name.strip()
        if not accepted or not new_name or (new_name != old_name and new_name in self._objects_by_name):
            return
        self._record_history()
        obj = self._objects_by_name.pop(old_name)
        obj["name"] = new_name
        self._objects_by_name[new_name] = obj
        if self._selected_name == old_name:
            self._selected_name = new_name
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": new_name})
        self._update_inspector(new_name)

    def _delete_object(self, name: str) -> None:
        if self._play_session.is_running:
            return
        self._record_history()
        self._scene_snapshot = [obj for obj in self._scene_snapshot if obj["name"] != name]
        self._objects_by_name.pop(name, None)
        if self._selected_name == name:
            self._selected_name = None
            for header, body in self.script_containers:
                self.inspector_layout.removeWidget(header)
                self.inspector_layout.removeWidget(body)
                header.deleteLater()
                body.deleteLater()
            self.script_containers.clear()
            self._clear_inspector_view()
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})

    def _duplicate_selected(self) -> None:
        if self._play_session.is_running:
            return
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        duplicate = deepcopy(self._objects_by_name[self._selected_name])
        duplicate["id"] = str(uuid.uuid4())
        duplicate["name"] = self._unique_name(f"{self._selected_name}_copy")
        duplicate["x"] = float(duplicate.get("x", 0.0)) + 16.0
        duplicate["y"] = float(duplicate.get("y", 0.0)) + 16.0
        self._scene_snapshot.append(duplicate)
        self._objects_by_name[duplicate["name"]] = duplicate
        self._selected_name = duplicate["name"]
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": self._selected_name})
        self._update_inspector(self._selected_name)

    def _refresh_hierarchy(self) -> None:
        self.hierarchy_tree.clear()
        scene_name = self._scene_document.get("scene_name", "MainScene") if self._scene_document else "MainScene"
        root = QTreeWidgetItem(["🟢 " + str(scene_name)])
        root.setExpanded(True)
        for obj in self._scene_snapshot:
            name = str(obj["name"])
            if "player" in name.lower():
                icon = "👤 "
            elif "chao" in name.lower() or "floor" in name.lower():
                icon = "🏔️ "
            else:
                icon = "📦 "
            item = QTreeWidgetItem([icon + name])
            item.setData(0, Qt.UserRole, name)
            root.addChild(item)
        self.hierarchy_tree.addTopLevelItem(root)

    @staticmethod
    def _hierarchy_item_name(item: QTreeWidgetItem | None) -> str:
        if item is None:
            return ""
        stored_name = item.data(0, Qt.UserRole)
        if stored_name:
            return str(stored_name)
        return item.text(0).lstrip("🟢🔴🟡🔵🟣⚫⚪📁🏔️☀️☁️📷🔶💡👤📦 ").strip()

    def _connect_inspector_to_viewport(self) -> None:
        for field in self.inspector_fields.values():
            field.valueChanged.connect(lambda _value: self._send_inspector_transform())
        for field in self.physics_fields.values():
            field.toggled.connect(lambda _checked: self._send_inspector_physics())
        for field in self.collider_fields.values():
            field.valueChanged.connect(lambda _value: self._send_inspector_collider())
        self.collider_trigger_field.toggled.connect(lambda _checked: self._send_inspector_collider())

        self.show_rigidbody_chk.toggled.connect(self._toggle_rigidbody_component)
        self.show_collider_chk.toggled.connect(self._toggle_collider_component)
        self.show_animator_chk.toggled.connect(self._toggle_animator_component)
        self.btn_del_rb.clicked.connect(lambda: self.show_rigidbody_chk.setChecked(False))
        self.btn_del_col.clicked.connect(lambda: self.show_collider_chk.setChecked(False))
        self.btn_del_anim.clicked.connect(lambda: self.show_animator_chk.setChecked(False))
        self.show_renderer_chk.toggled.connect(self._toggle_renderer_component)
        self.sprite_texture_button.clicked.connect(self._choose_sprite_texture)
        self.sprite_color_button.clicked.connect(self._choose_sprite_color)
        self.sprite_layer_combo.currentTextChanged.connect(lambda _text: self._send_inspector_renderer())
        self.sprite_order_field.valueChanged.connect(lambda _value: self._send_inspector_renderer())
        self.btn_collapse_transform.clicked.connect(lambda: self._toggle_inspector_card("transform"))
        self.btn_collapse_renderer.clicked.connect(lambda: self._toggle_inspector_card("sprite"))
        self.btn_delete_renderer.clicked.connect(lambda: self.show_renderer_chk.setChecked(False))
        self.show_audio_chk.toggled.connect(self._toggle_audio_component)
        self.btn_collapse_audio.clicked.connect(lambda: self._toggle_inspector_card("audio"))
        self.btn_delete_audio.clicked.connect(lambda: self.show_audio_chk.setChecked(False))
        self.audio_path_combo.activated.connect(lambda _idx: self._send_inspector_audio())
        self.audio_volume_field.valueChanged.connect(lambda _value: self._send_inspector_audio())
        self.audio_loop_field.toggled.connect(lambda _value: self._send_inspector_audio())
        self.audio_autoplay_field.toggled.connect(lambda _value: self._send_inspector_audio())
        self.audio_test_button.clicked.connect(self._test_selected_audio)
        self.audio_stop_button.clicked.connect(lambda: self._commands.put({"type": "stop_audio_preview"}))
        self.animator_clip_combo.currentTextChanged.connect(lambda _text: self._send_inspector_animator())
        self.animator_speed_field.valueChanged.connect(lambda _value: self._send_inspector_animator())
        self.animator_sheet_combo.currentIndexChanged.connect(lambda _value: self._send_inspector_animator())
        for field in (self.animator_frame_width, self.animator_frame_height, self.animator_start_frame, self.animator_frame_count, self.animator_fps_field):
            field.valueChanged.connect(lambda _value: self._send_inspector_animator())
        self.animator_loop_field.toggled.connect(lambda _value: self._send_inspector_animator())
        self.animator_add_clip_button.clicked.connect(self._add_animation_clip)
        self.animator_remove_clip_button.clicked.connect(self._remove_animation_clip)
        self.show_camera_chk.toggled.connect(self._toggle_camera_component)
        self.btn_collapse_rigidbody.clicked.connect(lambda: self._toggle_inspector_card("rigidbody"))
        self.btn_collapse_collider.clicked.connect(lambda: self._toggle_inspector_card("collider"))
        self.btn_collapse_camera.clicked.connect(lambda: self._toggle_inspector_card("camera"))
        self.btn_delete_camera.clicked.connect(lambda: self.show_camera_chk.setChecked(False))
        self.camera_active_field.toggled.connect(lambda _value: self._send_inspector_camera())
        self.camera_width_field.valueChanged.connect(lambda _value: self._send_inspector_camera())
        self.camera_height_field.valueChanged.connect(lambda _value: self._send_inspector_camera())
        self.camera_zoom_field.valueChanged.connect(lambda _value: self._send_inspector_camera())
        self.camera_follow_combo.currentTextChanged.connect(lambda _value: self._send_inspector_camera())
        self.camera_color_button.clicked.connect(self._choose_camera_color)
        self.show_ui_chk.toggled.connect(self._toggle_ui_visibility)
        self.btn_collapse_ui.clicked.connect(lambda: self._toggle_inspector_card("ui"))
        self.btn_delete_ui.clicked.connect(self._delete_ui_component)
        self.ui_text_field.editingFinished.connect(self._send_inspector_ui)
        for field in self.ui_position_fields.values():
            field.valueChanged.connect(lambda _value: self._send_inspector_ui())
        self.ui_color_button.clicked.connect(self._choose_ui_color)
        self.ui_image_button.clicked.connect(self._choose_ui_image)
        self.ui_interactable_field.toggled.connect(lambda _value: self._send_inspector_ui())
        self.ui_event_field.editingFinished.connect(self._send_inspector_ui)
        self.ui_target_combo.currentTextChanged.connect(lambda _value: self._send_inspector_ui())

    def _inspector_card(self, key: str):
        return {
            "transform": (self.transform_header, self.transform_body, self.btn_collapse_transform),
            "sprite": (self.sprite_renderer_header, self.sprite_renderer_body, self.btn_collapse_renderer),
            "audio": (self.audio_source_header, self.audio_source_body, self.btn_collapse_audio),
            "rigidbody": (self.rigidbody_header, self.rigidbody_body, self.btn_collapse_rigidbody),
            "collider": (self.collider_header, self.collider_body, self.btn_collapse_collider),
            "camera": (self.camera_header, self.camera_body, self.btn_collapse_camera),
            "ui": (self.ui_component_header, self.ui_component_body, self.btn_collapse_ui),
        }[key]

    def _set_inspector_card_present(self, key: str, present: bool) -> None:
        header, body, button = self._inspector_card(key)
        header.setVisible(bool(present))
        expanded = bool(self._component_expanded.get(key, False))
        body.setVisible(bool(present) and expanded)
        button.setText("▼" if expanded else "▶")

    def _toggle_inspector_card(self, key: str) -> None:
        header, body, button = self._inspector_card(key)
        expanded = not bool(self._component_expanded.get(key, False))
        self._component_expanded[key] = expanded
        body.setVisible(header.isVisible() and expanded)
        button.setText("▼" if expanded else "▶")

    def _toggle_dynamic_inspector_card(self, key: str, body: QWidget, button) -> None:
        expanded = not bool(self._component_expanded.get(key, False))
        self._component_expanded[key] = expanded
        body.setVisible(expanded)
        button.setText("▼" if expanded else "▶")

    def _clear_inspector_view(self) -> None:
        self.inspector_name_label.setText("Nenhum objeto selecionado")
        self.animation_object_label.setText("Nenhum objeto selecionado")
        for key in self._component_expanded:
            self._set_inspector_card_present(key, False)
        self.add_component_button.setEnabled(False)

    def _toggle_renderer_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        self._objects_by_name[self._selected_name]["renderer_enabled"] = bool(checked)
        self._send_inspector_renderer(record_history=False)
        self._update_inspector(self._selected_name)

    def _choose_sprite_texture(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar textura", str(Path.cwd() / "Assets"), "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not filename:
            return
        path = Path(filename)
        try:
            texture = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            textures_dir = Path.cwd() / "Assets" / "Textures"
            textures_dir.mkdir(parents=True, exist_ok=True)
            destination = textures_dir / path.name
            index = 1
            while destination.exists() and destination.read_bytes() != path.read_bytes():
                destination = textures_dir / f"{path.stem}_{index}{path.suffix}"
                index += 1
            if not destination.exists():
                shutil.copy2(path, destination)
            texture = str(destination.relative_to(Path.cwd())).replace("\\", "/")
            self._refresh_assets()
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        assign_sprite_texture(obj, texture)
        self.sprite_texture_field.setText(texture)
        self.sprite_color_button.setStyleSheet("background: rgb(255, 255, 255);")
        self._send_inspector_renderer(record_history=False)
        self._log("INFO", f"Textura aplicada sem tint: {Path(texture).name}")

    def _choose_sprite_color(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        current = self._objects_by_name[self._selected_name].get("color", (255, 255, 255))
        color = QColorDialog.getColor(QColor(*current[:3]), self, "Cor do Sprite")
        if not color.isValid():
            return
        self._record_history()
        self._objects_by_name[self._selected_name]["color"] = (color.red(), color.green(), color.blue())
        self.sprite_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self._send_inspector_renderer(record_history=False)

    def _send_inspector_renderer(self, record_history: bool = True) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        if record_history:
            self._record_history()
        obj = self._objects_by_name[self._selected_name]
        obj["renderer_enabled"] = self.show_renderer_chk.isChecked()
        obj["texture"] = self.sprite_texture_field.text().strip()
        obj["render_layer"] = self.sprite_layer_combo.currentText()
        obj["sort_order"] = int(self.sprite_order_field.value())
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _toggle_audio_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("audio", {"path": "", "volume": 1.0, "loop": False, "autoplay": False})
        else:
            obj.pop("audio", None)
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._update_inspector(self._selected_name)

    def _get_available_audio_files(self) -> list[str]:
        audio_dir = Path.cwd() / "Assets" / "Audio"
        if not audio_dir.exists():
            return []
        audio_files = []
        for file in audio_dir.rglob("*"):
            if file.is_file() and file.suffix.lower() in {".wav", ".ogg", ".mp3"}:
                try:
                    rel_p = str(file.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
                except ValueError:
                    rel_p = str(file).replace("\\", "/")
                audio_files.append(rel_p)
        return sorted(audio_files, key=str.lower)

    def _send_inspector_audio(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        if not isinstance(obj.get("audio"), dict):
            return
        self._record_history()
        chosen = self.audio_path_combo.currentData() or self.audio_path_combo.currentText()
        if chosen == "Nenhum":
            chosen = ""
        obj["audio"].update({
            "path": chosen,
            "volume": float(self.audio_volume_field.value()),
            "loop": self.audio_loop_field.isChecked(),
            "autoplay": self.audio_autoplay_field.isChecked(),
        })
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _test_selected_audio(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        audio = self._objects_by_name[self._selected_name].get("audio")
        if not isinstance(audio, dict) or not audio.get("path"):
            self._log("WARNING", "Selecione um arquivo no Audio Source antes de testar")
            return
        self._commands.put({
            "type": "preview_audio", "name": self._selected_name,
            "path": str(audio["path"]), "volume": float(audio.get("volume", 1.0)),
            "loop": bool(audio.get("loop", False)),
        })

    def _toggle_rigidbody_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("rigidbody", {"mass": 1.0, "gravity_scale": 1.0, "use_gravity": True, "is_kinematic": False})
        else:
            obj.pop("rigidbody", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)

    def _toggle_collider_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("collider", {"type": "box", "is_trigger": False})
        else:
            obj.pop("collider", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)

    def _toggle_animator_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("animator", {"active_clip": "Idle", "speed": 1.0, "clips": {"Idle": self._default_animation_clip()}})
        else:
            obj.pop("animator", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)

    @staticmethod
    def _default_animation_clip() -> dict:
        return {"texture": "", "frame_width": 32, "frame_height": 32, "start_frame": 0, "frame_count": 1, "fps": 8.0, "loop": True}

    def _animation_clips(self, animator: dict) -> dict[str, dict]:
        clips = animator.get("clips")
        if isinstance(clips, list):
            clips = {str(name): self._default_animation_clip() for name in clips}
            animator["clips"] = clips
        elif not isinstance(clips, dict):
            clips = {"Idle": self._default_animation_clip()}
            animator["clips"] = clips
        return clips

    def _available_sprite_sheets(self) -> list[str]:
        root = Path.cwd() / "Assets"
        result = []
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                    result.append(str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/"))
        return sorted(result, key=str.lower)

    def _configure_animation_workspace(self) -> None:
        """Conecta a biblioteca de clips sem interferir no runtime existente."""
        self.animation_new_button.clicked.connect(self._new_animation_asset)
        self.animation_open_button.clicked.connect(self._open_animation_asset_dialog)
        self.animation_save_button.clicked.connect(self._save_animation_asset)
        self.animation_save_as_button.clicked.connect(lambda: self._save_animation_asset(save_as=True))
        self.animation_duplicate_button.clicked.connect(self._duplicate_animation_asset)
        self.animation_delete_button.clicked.connect(self._delete_animation_asset)
        self.animation_apply_button.clicked.connect(self._apply_current_animation_to_selected)
        self.animation_demo_button.clicked.connect(self._run_walk_animation_demo)
        self.animation_library_tree.itemDoubleClicked.connect(self._open_animation_library_item)
        self.animation_controller_combo.currentIndexChanged.connect(self._select_animation_controller)
        self.animation_new_controller_button.clicked.connect(self._new_animator_controller)
        self.animation_edit_controller_button.clicked.connect(self._edit_animator_controller)

        self.animation_play_button.clicked.connect(self._toggle_animation_preview_playback)
        self.animation_first_frame_button.clicked.connect(lambda: self._set_animation_preview_frame(0))
        self.animation_previous_frame_button.clicked.connect(lambda: self._set_animation_preview_frame(self._animator_preview_index - 1))
        self.animation_next_frame_button.clicked.connect(lambda: self._set_animation_preview_frame(self._animator_preview_index + 1))
        self.animation_last_frame_button.clicked.connect(lambda: self._set_animation_preview_frame(self._animation_frame_count() - 1))
        self.animation_timeline.valueChanged.connect(self._set_animation_preview_frame)
        self.animation_add_event_button.clicked.connect(self._add_animation_event)
        self.animation_remove_event_button.clicked.connect(self._remove_animation_event)

        for field_signal in (
            self.animator_clip_combo.currentTextChanged,
            self.animator_sheet_combo.currentIndexChanged,
            self.animator_frame_width.valueChanged,
            self.animator_frame_height.valueChanged,
            self.animator_start_frame.valueChanged,
            self.animator_frame_count.valueChanged,
            self.animator_fps_field.valueChanged,
            self.animator_loop_field.toggled,
        ):
            field_signal.connect(self._mark_animation_asset_dirty)
        self._refresh_animation_library()
        self._refresh_animator_controllers()
        self._refresh_animation_timeline(self._default_animation_clip())
        self._update_animation_asset_status()

    def _animation_assets_directory(self) -> Path:
        return Path.cwd() / "Assets" / "Animations"

    def _refresh_animator_controllers(self, selected_path: str = "") -> None:
        combo = self.animation_controller_combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Nenhum", "")
        directory = self._animation_assets_directory()
        for path in sorted(directory.rglob("*.zanimator"), key=lambda item: str(item).lower()) if directory.exists() else []:
            relative = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
            combo.addItem(path.stem, relative)
        index = combo.findData(str(selected_path).replace("\\", "/"))
        combo.setCurrentIndex(max(0, index))
        combo.blockSignals(False)
        self._update_animator_controller_summary()

    def _select_animation_controller(self, _index: int = -1) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        controller_path = str(self.animation_controller_combo.currentData() or "")
        if controller_path:
            self._apply_animator_controller_path(Path.cwd() / controller_path, self._selected_name)
        else:
            obj = self._objects_by_name[self._selected_name]
            animator = obj.get("animator")
            if not isinstance(animator, dict):
                return
            self._record_history()
            animator.pop("controller_path", None)
            animator.pop("controller", None)
            animator.pop("parameters", None)
            self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
            self._update_animator_controller_summary()

    def _apply_animator_controller_path(self, path: Path, target_name: str) -> None:
        try:
            resolved = path.resolve()
            relative = resolved.relative_to(Path.cwd().resolve()).as_posix()
            controller = load_animator_controller(resolved)
        except (OSError, ValueError) as exc:
            self._log("ERROR", f"Não foi possível aplicar o controller: {exc}")
            return
        self._record_history()
        obj = self._objects_by_name[target_name]
        animator = obj.setdefault("animator", {"active_clip": controller["initial_state"], "speed": 1.0, "clips": {}})
        animator["controller_path"] = relative
        animator["controller"] = controller
        animator["active_clip"] = controller["initial_state"]
        animator["parameters"] = {
            name: parameter["default"] for name, parameter in controller["parameters"].items()
        }
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        if target_name == self._selected_name:
            self._refresh_animator_controllers(relative)
            self._update_inspector(target_name)
        self._log("INFO", f"Controller aplicado em {target_name}: {resolved.name}")

    def _new_animator_controller(self) -> None:
        dialog = AnimatorControllerEditorDialog(Path.cwd(), parent=self)
        self._animator_controller_dialog = dialog
        result = dialog.exec()
        self._animator_controller_dialog = None
        if result and dialog.saved_path:
            relative = dialog.saved_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
            self._refresh_animator_controllers(relative)
            self._select_animation_controller()
            self._refresh_assets()
            self._log("INFO", f"Animator Controller criado: {relative}")

    def _edit_animator_controller(self) -> None:
        controller_path = str(self.animation_controller_combo.currentData() or "")
        if not controller_path:
            QMessageBox.information(self, "Animator Controller", "Selecione um controller para editar.")
            return
        dialog = AnimatorControllerEditorDialog(Path.cwd(), Path.cwd() / controller_path, self)
        runtime = self._runtime_animator_states.get(self._selected_name or "")
        if runtime:
            dialog.set_runtime_state(str(runtime.get("state", "")), runtime.get("parameters"))
        self._animator_controller_dialog = dialog
        result = dialog.exec()
        self._animator_controller_dialog = None
        if result and dialog.saved_path:
            self._refresh_animator_controllers(controller_path)
            self._select_animation_controller()
            self._log("INFO", f"Animator Controller atualizado: {controller_path}")

    def _update_animator_controller_summary(self) -> None:
        path_value = str(self.animation_controller_combo.currentData() or "")
        if not path_value:
            self.animation_controller_summary.setText("Use um controller para criar estados e transições.")
            self.animation_edit_controller_button.setEnabled(False)
            return
        self.animation_edit_controller_button.setEnabled(True)
        try:
            controller = load_animator_controller(Path.cwd() / path_value)
            self.animation_controller_summary.setText(
                f'Inicial: {controller["initial_state"]} · {len(controller["states"])} estado(s) · '
                f'{len(controller["transitions"])} transição(ões)'
            )
        except (OSError, ValueError):
            self.animation_controller_summary.setText("Controller inválido ou não encontrado.")

    def _refresh_animation_library(self) -> None:
        selected = self._current_animation_asset_path
        self.animation_library_tree.clear()
        directory = self._animation_assets_directory()
        for path in sorted(directory.rglob("*.zanim"), key=lambda item: str(item).lower()) if directory.exists() else []:
            item = QTreeWidgetItem([path.stem])
            item.setData(0, Qt.UserRole, str(path))
            item.setToolTip(0, str(path.relative_to(Path.cwd())).replace("\\", "/"))
            self.animation_library_tree.addTopLevelItem(item)
            if selected and path.resolve() == selected.resolve():
                self.animation_library_tree.setCurrentItem(item)
        if self.animation_library_tree.topLevelItemCount() == 0:
            empty = QTreeWidgetItem(["Nenhuma animação salva"])
            empty.setDisabled(True)
            self.animation_library_tree.addTopLevelItem(empty)

    def _new_animation_asset(self) -> None:
        name, accepted = QInputDialog.getText(self, "Nova Animação", "Nome da animação:", text="NewAnimation")
        name = name.strip()
        if not accepted or not name:
            return
        self._current_animation_asset_path = None
        self._animation_draft_name = name
        self._apply_animation_asset_to_editor(default_animation_asset(name), attach_to_object=False)
        self._animation_asset_dirty = True
        self._update_animation_asset_status()
        self._log("INFO", f"Nova animação preparada: {name}")

    def _open_animation_asset_dialog(self) -> None:
        start = self._animation_assets_directory()
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir Animação", str(start), "Animação Zennity (*.zanim)")
        if filename:
            self._load_animation_asset_path(Path(filename))

    def _open_animation_library_item(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        path = item.data(0, Qt.UserRole)
        if path:
            self._load_animation_asset_path(Path(str(path)))

    def _load_animation_asset_path(self, path: Path) -> None:
        try:
            asset = load_animation_asset(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Animação inválida", f"Não foi possível abrir o arquivo.\n\n{exc}")
            self._log("ERROR", f"Falha ao abrir animação {path.name}: {exc}")
            return
        self._current_animation_asset_path = path.resolve()
        self._animation_draft_name = str(asset["name"])
        self._apply_animation_asset_to_editor(asset, attach_to_object=False)
        self._animation_asset_dirty = False
        self._update_animation_asset_status()
        self._refresh_animation_library()
        self._log("INFO", f"Animação aberta: {path.name}")

    def _current_animation_asset(self) -> tuple[dict, Path | None]:
        path = self._current_animation_asset_path
        if path is not None and path.is_file():
            return load_animation_asset(path), path
        return self._animation_asset_from_editor(), path

    def _animation_play_error(self, asset: dict) -> str:
        texture = str(asset.get("texture", "")).strip()
        if not texture:
            return "selecione um Sprite Sheet nas propriedades da animação e salve novamente"
        texture_path = Path(texture)
        if not texture_path.is_absolute():
            texture_path = Path.cwd() / texture_path
        if not texture_path.is_file():
            return f"Sprite Sheet não encontrado: {texture}"
        pixmap = QPixmap(str(texture_path))
        if pixmap.isNull():
            return f"não foi possível abrir o Sprite Sheet: {texture}"
        frame_width = max(1, int(asset.get("frame_width", 1)))
        frame_height = max(1, int(asset.get("frame_height", 1)))
        if frame_width > pixmap.width() or frame_height > pixmap.height():
            return "o tamanho do quadro é maior que o Sprite Sheet"
        columns = max(1, pixmap.width() // frame_width)
        rows = max(1, pixmap.height() // frame_height)
        frames = asset.get("frames", [0])
        if not isinstance(frames, list) or not frames:
            return "a animação não possui quadros"
        if max(int(frame) for frame in frames) >= columns * rows:
            return f"o quadro {max(int(frame) for frame in frames)} está fora do Sprite Sheet ({columns * rows} disponíveis)"
        return ""

    def _apply_animation_asset_path_to_object(self, path: Path, object_name: str) -> bool:
        try:
            asset = load_animation_asset(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._log("ERROR", f"Não foi possível aplicar {path.name}: {exc}")
            QMessageBox.warning(self, "Animação inválida", str(exc))
            return False
        return self._apply_animation_asset_to_object(asset, path, object_name)

    def _apply_animation_asset_to_object(self, asset: dict, path: Path | None, object_name: str) -> bool:
        if self._play_session.is_running:
            self.statusBar().showMessage("Pare o Play Mode antes de aplicar uma animação")
            return False
        if object_name not in self._objects_by_name:
            return False
        error = self._animation_play_error(asset)
        if error:
            message = f"A animação '{asset.get('name', 'Animation')}' não pode ser reproduzida: {error}."
            self._log("ERROR", message)
            QMessageBox.warning(self, "Animação incompleta", message)
            return False

        self._selected_name = object_name
        self._record_history()
        obj = self._objects_by_name[object_name]
        animator = obj.setdefault("animator", {"active_clip": str(asset["name"]), "speed": 1.0, "clips": {}})
        clips = self._animation_clips(animator)
        clips[str(asset["name"])] = animation_asset_to_clip(asset, self._project_relative_path(path))
        animator["active_clip"] = str(asset["name"])
        assign_sprite_texture(obj, str(asset["texture"]))
        obj["renderer_enabled"] = True
        self._current_animation_asset_path = path.resolve() if path is not None else None
        self._animation_draft_name = str(asset["name"])
        self._animation_asset_dirty = False
        self._animation_bound_key = (str(obj.get("id", object_name)), str(asset["name"]))
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._commands.put({"type": "select_object", "name": object_name})
        self._update_inspector(object_name)
        self._update_animation_asset_status()
        self._log("INFO", f"Animação '{asset['name']}' aplicada em {object_name}")
        return True

    def _apply_current_animation_to_selected(self) -> None:
        if self._selected_name not in self._objects_by_name:
            QMessageBox.information(self, "Aplicar Animação", "Selecione primeiro um objeto na Hierarchy.")
            return
        try:
            asset, path = self._current_animation_asset()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Animação inválida", str(exc))
            return
        self._apply_animation_asset_to_object(asset, path, self._selected_name)

    def _run_walk_animation_demo(self) -> None:
        path = self._current_animation_asset_path
        if path is None or not path.is_file():
            directory = self._animation_assets_directory()
            candidates = [item for item in directory.glob("*.zanim") if item.stem.casefold() == "andar"] if directory.exists() else []
            path = candidates[0] if candidates else None
        if path is None:
            message = "Salve a animação como Assets/Animations/andar.zanim antes de iniciar a demo."
            self._log("ERROR", message)
            QMessageBox.information(self, "Demo andar", message)
            return
        player_name = next(
            (name for name, obj in self._objects_by_name.items() if name.casefold() == "player" or str(obj.get("tag", "")).casefold() == "player"),
            None,
        )
        if player_name is None:
            message = "A demo precisa de um objeto chamado Player ou com Tag Player."
            self._log("ERROR", message)
            QMessageBox.information(self, "Demo andar", message)
            return
        if not self._apply_animation_asset_path_to_object(path, player_name):
            return
        self._log("INFO", f"Demo iniciada: '{path.stem}' está ativa em {player_name}")
        self.statusBar().showMessage("Demo iniciada — a animação está tocando no Player")
        self._send_toolbar_command({"type": "play"})

    def _save_animation_asset(self, _checked: bool = False, save_as: bool = False) -> None:
        path = self._current_animation_asset_path
        if save_as or path is None:
            default_path = self._animation_assets_directory() / f"{self._animation_draft_name}.zanim"
            filename, _ = QFileDialog.getSaveFileName(self, "Salvar Animação", str(default_path), "Animação Zennity (*.zanim)")
            if not filename:
                return
            path = Path(filename)
        if path.suffix.lower() != ".zanim":
            path = path.with_suffix(".zanim")

        asset = self._animation_asset_from_editor(path.stem)
        try:
            saved = save_animation_asset(path, asset)
        except OSError as exc:
            QMessageBox.warning(self, "Erro ao salvar", f"Não foi possível salvar a animação.\n\n{exc}")
            self._log("ERROR", f"Falha ao salvar animação {path.name}: {exc}")
            return
        self._current_animation_asset_path = path.resolve()
        self._animation_draft_name = str(saved["name"])
        self._animation_asset_dirty = False
        self._update_animation_asset_status()
        self._refresh_animation_library()
        self._refresh_assets()
        self._log("INFO", f"Animação salva: {self._project_relative_path(path)} — use 'Aplicar ao selecionado' para anexá-la")

    def _duplicate_animation_asset(self) -> None:
        original_path = self._current_animation_asset_path
        original_name = self._animation_draft_name
        self._current_animation_asset_path = None
        self._animation_draft_name = f"{original_name}_copy"
        self._save_animation_asset(save_as=True)
        if self._current_animation_asset_path is None:
            self._current_animation_asset_path = original_path
            self._animation_draft_name = original_name
            self._update_animation_asset_status()

    def _delete_animation_asset(self) -> None:
        path = self._current_animation_asset_path
        if path is None or not path.exists():
            return
        answer = QMessageBox.question(
            self, "Excluir Animação",
            f"Excluir '{path.name}' da biblioteca?\n\nObjetos que já usam o clip manterão uma cópia compatível.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            path.unlink()
        except OSError as exc:
            QMessageBox.warning(self, "Erro ao excluir", str(exc))
            return
        self._current_animation_asset_path = None
        self._animation_asset_dirty = True
        self._update_animation_asset_status()
        self._refresh_animation_library()
        self._refresh_assets()
        self._log("INFO", f"Animação excluída da biblioteca: {path.name}")

    def _animation_asset_from_editor(self, name: str | None = None) -> dict:
        clip_name = name or self._animation_draft_name or self.animator_clip_combo.currentText() or "NewAnimation"
        clip = {
            "texture": self.animator_sheet_combo.currentData() or "",
            "frame_width": int(self.animator_frame_width.value()),
            "frame_height": int(self.animator_frame_height.value()),
            "start_frame": int(self.animator_start_frame.value()),
            "frame_count": int(self.animator_frame_count.value()),
            "fps": float(self.animator_fps_field.value()),
            "loop": self.animator_loop_field.isChecked(),
            "events": deepcopy(self._animation_events),
        }
        return animation_asset_from_clip(str(clip_name), clip)

    def _apply_animation_asset_to_editor(self, asset: dict, attach_to_object: bool) -> None:
        clip = animation_asset_to_clip(asset)
        previous_updating = self._updating_inspector
        self._updating_inspector = True
        try:
            self.animator_sheet_combo.clear()
            self.animator_sheet_combo.addItem("Nenhum", "")
            for sheet in self._available_sprite_sheets():
                self.animator_sheet_combo.addItem(Path(sheet).name, sheet)
            sheet_index = self.animator_sheet_combo.findData(str(clip.get("texture", "")))
            self.animator_sheet_combo.setCurrentIndex(max(0, sheet_index))
            self.animator_frame_width.setValue(float(clip["frame_width"]))
            self.animator_frame_height.setValue(float(clip["frame_height"]))
            self.animator_start_frame.setValue(float(clip["start_frame"]))
            self.animator_frame_count.setValue(float(clip["frame_count"]))
            self.animator_fps_field.setValue(float(clip["fps"]))
            self.animator_loop_field.setChecked(bool(clip["loop"]))
            self.animator_current_lbl.setText(str(asset["name"]))
            self._animation_events = deepcopy(asset.get("events", []))
            self._refresh_animation_events()
        finally:
            self._updating_inspector = previous_updating
        self._animator_preview_index = 0
        self._refresh_animation_timeline(clip)
        self._update_animation_preview(clip, 0)
        if attach_to_object:
            self._attach_animation_asset_to_selected_object(asset, self._current_animation_asset_path)

    def _attach_animation_asset_to_selected_object(self, asset: dict, path: Path | None) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        animator = obj.setdefault("animator", {"active_clip": str(asset["name"]), "speed": 1.0, "clips": {}})
        clips = self._animation_clips(animator)
        relative_path = self._project_relative_path(path) if path else ""
        clips[str(asset["name"])] = animation_asset_to_clip(asset, relative_path)
        animator["active_clip"] = str(asset["name"])
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._update_inspector(self._selected_name)

    def _project_relative_path(self, path: Path | None) -> str:
        if path is None:
            return ""
        try:
            return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _mark_animation_asset_dirty(self, *_args) -> None:
        if self._updating_inspector:
            return
        self._animation_asset_dirty = True
        self._update_animation_asset_status()

    def _update_animation_asset_status(self) -> None:
        name = self._current_animation_asset_path.name if self._current_animation_asset_path else self._animation_draft_name
        if self._current_animation_asset_path is None:
            suffix = "  •  ainda não salvo"
        elif self._animation_asset_dirty:
            suffix = "  •  alterações não salvas"
        else:
            suffix = "  •  salvo"
        self.animation_asset_label.setText(name + suffix)
        state = "dirty" if self._animation_asset_dirty or self._current_animation_asset_path is None else "saved"
        if self.animation_asset_label.property("uiState") != state:
            self.animation_asset_label.setProperty("uiState", state)
            self.animation_asset_label.style().unpolish(self.animation_asset_label)
            self.animation_asset_label.style().polish(self.animation_asset_label)

    def _animation_frame_count(self) -> int:
        return max(1, int(self.animator_frame_count.value()))

    def _refresh_animation_timeline(self, clip: dict) -> None:
        frames = clip.get("frames")
        count = max(1, len(frames) if isinstance(frames, list) and frames else int(clip.get("frame_count", 1)))
        self.animation_timeline.blockSignals(True)
        self.animation_timeline.setRange(0, count - 1)
        self.animation_timeline.setValue(min(self._animator_preview_index, count - 1))
        self.animation_timeline.blockSignals(False)
        self.animation_frame_label.setText(f"Frame {min(self._animator_preview_index, count - 1) + 1} / {count}")

    def _set_animation_preview_frame(self, index: int) -> None:
        count = self._animation_frame_count()
        self._animator_preview_index = max(0, min(int(index), count - 1))
        self.animation_timeline.blockSignals(True)
        self.animation_timeline.setValue(self._animator_preview_index)
        self.animation_timeline.blockSignals(False)
        self.animation_frame_label.setText(f"Frame {self._animator_preview_index + 1} / {count}")
        self._update_animation_preview(animation_asset_to_clip(self._animation_asset_from_editor()), self._animator_preview_index)

    def _refresh_animation_events(self) -> None:
        self.animation_events_tree.clear()
        ordered = sorted(self._animation_events, key=lambda item: (int(item.get("frame", 0)), str(item.get("name", ""))))
        for event in ordered:
            payload = event.get("payload")
            QTreeWidgetItem(self.animation_events_tree, [str(int(event.get("frame", 0)) + 1), str(event.get("name", "")), "" if payload is None else str(payload)])
        markers = ", ".join(f'F{int(event.get("frame", 0)) + 1}:{event.get("name", "")}' for event in ordered)
        self.animation_timeline.setToolTip("Arraste para visualizar qualquer quadro" + (f"\nEventos: {markers}" if markers else "\nSem eventos"))

    def _add_animation_event(self) -> None:
        name, ok = QInputDialog.getText(self, "Evento de Animação", "Nome do evento:", text="evento")
        name = name.strip()
        if not ok or not name:
            return
        payload, ok = QInputDialog.getText(self, "Evento de Animação", "Payload opcional:")
        if not ok:
            return
        self._animation_events.append({
            "frame": int(self._animator_preview_index), "name": name,
            "payload": payload if payload else None,
        })
        self._animation_asset_dirty = True
        self._refresh_animation_events()
        self._update_animation_asset_status()

    def _remove_animation_event(self) -> None:
        index = self.animation_events_tree.indexOfTopLevelItem(self.animation_events_tree.currentItem())
        if index < 0:
            return
        ordered = sorted(range(len(self._animation_events)), key=lambda item: (int(self._animation_events[item].get("frame", 0)), str(self._animation_events[item].get("name", ""))))
        self._animation_events.pop(ordered[index])
        self._animation_asset_dirty = True
        self._refresh_animation_events()
        self._update_animation_asset_status()

    def _toggle_animation_preview_playback(self) -> None:
        self._animation_preview_playing = not self._animation_preview_playing
        self.animation_play_button.setIcon(editor_icon(
            "pause" if self._animation_preview_playing else "play"
        ))

    def _add_animation_clip(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        animator = self._objects_by_name[self._selected_name].get("animator")
        if not isinstance(animator, dict):
            return
        name, accepted = QInputDialog.getText(self, "Novo Clip", "Nome do clip:", text="NewClip")
        name = name.strip()
        clips = self._animation_clips(animator)
        if not accepted or not name or name in clips:
            return
        self._record_history()
        clips[name] = self._default_animation_clip()
        animator["active_clip"] = name
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._update_inspector(self._selected_name)

    def _remove_animation_clip(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        animator = self._objects_by_name[self._selected_name].get("animator")
        if not isinstance(animator, dict):
            return
        clips = self._animation_clips(animator)
        name = self.animator_clip_combo.currentText()
        if name not in clips or len(clips) <= 1:
            return
        self._record_history()
        clips.pop(name)
        animator["active_clip"] = next(iter(clips))
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._update_inspector(self._selected_name)

    def _tick_animation_preview(self) -> None:
        if not self._animation_preview_playing or self.viewport_tabs.currentIndex() != 2:
            return
        animator = None
        clip = None
        if self._selected_name in self._objects_by_name:
            animator = self._objects_by_name[self._selected_name].get("animator")
            if isinstance(animator, dict):
                clips = self._animation_clips(animator)
                clip = clips.get(self.animator_clip_combo.currentText())
        if not isinstance(clip, dict):
            clip = animation_asset_to_clip(self._animation_asset_from_editor())
        frames = clip.get("frames")
        count = max(1, len(frames) if isinstance(frames, list) and frames else int(clip.get("frame_count", 1)))
        if clip.get("loop", True):
            self._animator_preview_index = (self._animator_preview_index + 1) % count
        else:
            self._animator_preview_index = min(count - 1, self._animator_preview_index + 1)
        speed = float(animator.get("speed", 1.0)) if isinstance(animator, dict) else 1.0
        fps = max(0.1, float(clip.get("fps", 8.0))) * max(0.01, speed)
        self._animator_preview_timer.setInterval(max(16, int(1000.0 / fps)))
        self._update_animation_preview(clip, self._animator_preview_index)
        self.animation_timeline.blockSignals(True)
        self.animation_timeline.setValue(self._animator_preview_index)
        self.animation_timeline.blockSignals(False)
        self.animation_frame_label.setText(f"Frame {self._animator_preview_index + 1} / {count}")

    def _update_animation_preview(self, clip: dict, frame_offset: int = 0) -> None:
        texture = str(clip.get("texture", ""))
        path = Path(texture)
        if texture and not path.is_absolute():
            path = Path.cwd() / path
        pixmap = QPixmap(str(path)) if texture else QPixmap()
        width = max(1, int(clip.get("frame_width", 32)))
        height = max(1, int(clip.get("frame_height", 32)))
        if pixmap.isNull() or width > pixmap.width() or height > pixmap.height():
            self.animator_preview.clear()
            self._set_animation_preview_state("empty" if not texture else "error")
            self.animator_preview.setText(
                "Selecione um Sprite Sheet nas propriedades"
                if not texture else "Sprite Sheet inválido ou frame maior que a imagem"
            )
            return
        columns = max(1, pixmap.width() // width)
        frames = clip.get("frames")
        if isinstance(frames, list) and frames:
            frame = max(0, int(frames[min(max(0, int(frame_offset)), len(frames) - 1)]))
        else:
            frame = max(0, int(clip.get("start_frame", 0))) + max(0, int(frame_offset))
        x = (frame % columns) * width
        y = (frame // columns) * height
        if x + width > pixmap.width() or y + height > pixmap.height():
            self.animator_preview.clear()
            self._set_animation_preview_state("error")
            self.animator_preview.setText("Quadro fora da imagem")
            return
        preview = pixmap.copy(x, y, width, height)
        self._set_animation_preview_state("content")
        self.animator_preview.setPixmap(preview.scaled(120, 90, Qt.KeepAspectRatio, Qt.FastTransformation))

    def _set_animation_preview_state(self, state: str) -> None:
        if self.animator_preview.property("uiState") == state:
            return
        self.animator_preview.setProperty("uiState", state)
        self.animator_preview.style().unpolish(self.animator_preview)
        self.animator_preview.style().polish(self.animator_preview)

    def _send_inspector_animator(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        anim = obj.get("animator")
        if anim is None:
            return
        self._record_history()
        clip_name = self.animator_clip_combo.currentText() or "Idle"
        clips = self._animation_clips(anim)
        clip = clips.setdefault(clip_name, self._default_animation_clip())
        anim["active_clip"] = clip_name
        anim["speed"] = float(self.animator_speed_field.value())
        texture = self.animator_sheet_combo.currentData() or ""
        clip.update({
            "texture": str(texture),
            "frame_width": int(self.animator_frame_width.value()),
            "frame_height": int(self.animator_frame_height.value()),
            "start_frame": int(self.animator_start_frame.value()),
            "frame_count": int(self.animator_frame_count.value()),
            "fps": float(self.animator_fps_field.value()),
            "loop": self.animator_loop_field.isChecked(),
        })
        clip["frames"] = list(range(clip["start_frame"], clip["start_frame"] + clip["frame_count"]))
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)

    def _toggle_camera_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("camera", {"active": True, "zoom": 1.0, "width": 1280.0, "height": 720.0, "background_color": [22, 24, 31], "follow_target": ""})
            names = obj.setdefault("component_names", [])
            if "Camera2D" not in names:
                names.append("Camera2D")
        else:
            obj.pop("camera", None)
            obj["component_names"] = [name for name in obj.get("component_names", []) if name != "Camera2D"]
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._update_inspector(self._selected_name)

    def _send_inspector_camera(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        camera = obj.get("camera")
        if not isinstance(camera, dict):
            return
        self._record_history()
        follow = self.camera_follow_combo.currentText()
        camera.update({
            "active": self.camera_active_field.isChecked(),
            "width": float(self.camera_width_field.value()),
            "height": float(self.camera_height_field.value()),
            "zoom": float(self.camera_zoom_field.value()),
            "follow_target": "" if follow == "Nenhum" else follow,
        })
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _choose_camera_color(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        camera = self._objects_by_name[self._selected_name].get("camera")
        if not isinstance(camera, dict):
            return
        current = camera.get("background_color", [22, 24, 31])
        color = QColorDialog.getColor(QColor(*current[:3]), self, "Cor de fundo da câmera")
        if not color.isValid():
            return
        self._record_history()
        camera["background_color"] = [color.red(), color.green(), color.blue()]
        self.camera_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _toggle_ui_visibility(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        ui = self._objects_by_name[self._selected_name].get("ui")
        if not isinstance(ui, dict):
            return
        self._record_history()
        ui["visible"] = bool(checked)
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _delete_ui_component(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        if "ui" not in obj:
            return
        self._record_history()
        obj.pop("ui", None)
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
        self._update_inspector(self._selected_name)

    def _choose_ui_color(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        ui = normalize_ui(self._objects_by_name[self._selected_name].get("ui"))
        if ui is None:
            return
        current = tuple(ui.get("color", (255, 255, 255)))[:3]
        color = QColorDialog.getColor(QColor(*current), self, "Cor da UI")
        if not color.isValid():
            return
        self._record_history()
        self._objects_by_name[self._selected_name]["ui"]["color"] = [color.red(), color.green(), color.blue()]
        self.ui_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _choose_ui_image(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Selecionar imagem da UI", str(Path.cwd() / "Assets"),
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            value = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            value = str(path.resolve())
        self.ui_image_path_field.setText(value)
        self._send_inspector_ui()

    def _send_inspector_ui(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        ui = normalize_ui(obj.get("ui"))
        if ui is None:
            return
        self._record_history()
        ui.update({key: float(field.value()) for key, field in self.ui_position_fields.items()})
        ui.update({
            "visible": self.show_ui_chk.isChecked(),
            "text": self.ui_text_field.text(),
            "path": self.ui_image_path_field.text(),
            "interactable": self.ui_interactable_field.isChecked(),
            "event": self.ui_event_field.text().strip() or "click",
            "target": "" if self.ui_target_combo.currentText() == "Este objeto" else self.ui_target_combo.currentText(),
        })
        obj["ui"] = ui
        self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})

    def _ensure_canvas(self) -> None:
        if any((normalize_ui(obj.get("ui")) or {}).get("type") == "canvas" for obj in self._scene_snapshot):
            return
        name = self._unique_name("Canvas")
        canvas = {
            "id": str(uuid.uuid4()), "name": name, "x": 0.0, "y": 0.0,
            "w": 1.0, "h": 1.0, "rotation": 0.0, "color": (255, 255, 255),
            "mesh_type": "UI", "renderer_enabled": False,
            "ui": normalize_ui({"type": "canvas"}),
        }
        self._scene_snapshot.append(canvas)
        self._objects_by_name[name] = canvas
        self._log("INFO", "Canvas criado automaticamente para a interface do jogo")

    def _open_add_component_menu(self) -> None:
        if self._play_session.is_running:
            return
        if self._selected_name not in self._objects_by_name:
            return
        picker = ComponentPickerDialog(self)
        if picker.exec() and picker.selected_component:
            self._add_component(picker.selected_component)

    def _add_component(self, component: str) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        if component == "script":
            available = self._get_available_scripts()
            if not available:
                self.statusBar().showMessage("Nenhum script encontrado em Assets/Scripts")
                return
            attached = set(self._objects_by_name[self._selected_name].get("scripts", []))
            preferred = next((path for path in available if path.name == "player_controller_2d.py"), None)
            ordered = ([preferred] if preferred is not None else []) + [path for path in available if path != preferred]
            chosen = None
            for path in ordered:
                try:
                    relative = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
                except ValueError:
                    relative = str(path.resolve())
                if relative not in attached:
                    chosen = path
                    break
            if chosen is None:
                self.statusBar().showMessage("Todos os scripts disponíveis já estão anexados")
                return
            self._attach_script(self._selected_name, chosen)
            return
        if component == "animator":
            self._choose_animation_component()
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if component == "sprite":
            obj["renderer_enabled"] = True
        elif component == "audio":
            obj.setdefault("audio", {"path": "", "volume": 1.0, "loop": False, "autoplay": False})
        elif component == "rigidbody":
            obj.setdefault("rigidbody", {"mass": 1.0, "gravity_scale": 1.0, "use_gravity": True, "is_kinematic": False})
        elif component in {"box", "circle"}:
            obj["collider"] = {"type": component, "is_trigger": False}
        elif component == "camera":
            obj["camera"] = {"active": True, "zoom": 1.0, "width": 1280.0, "height": 720.0, "background_color": [22, 24, 31], "follow_target": ""}
            names = obj.setdefault("component_names", [])
            if "Camera2D" not in names:
                names.append("Camera2D")
        elif component.startswith("ui_"):
            kind = component.removeprefix("ui_")
            if kind != "canvas":
                self._ensure_canvas()
            obj["ui"] = normalize_ui({"type": kind})
            obj["renderer_enabled"] = False
            obj["mesh_type"] = "UI"
            self._refresh_hierarchy()
        card_key = {
            "sprite": "sprite", "audio": "audio", "rigidbody": "rigidbody",
            "box": "collider", "circle": "collider", "camera": "camera",
        }.get(component, "ui" if component.startswith("ui_") else None)
        if card_key is not None:
            self._component_expanded[card_key] = True
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": self._selected_name})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Componente adicionado em {self._selected_name}: {component}")

    def _choose_animation_component(self) -> None:
        """Escolhe um ``.zanim`` antes de criar o Animator no objeto."""
        object_name = self._selected_name
        if object_name not in self._objects_by_name:
            return
        picker = AnimationPickerDialog(Path.cwd(), self)
        if not picker.exec():
            return
        if picker.requested_action == "create":
            self.viewport_tabs.setCurrentIndex(2)
            self._new_animation_asset()
            return
        if picker.requested_action == "empty":
            if isinstance(self._objects_by_name[object_name].get("animator"), dict):
                self.statusBar().showMessage(f"{object_name} já possui um Animator 2D")
                return
            self._record_history()
            self._objects_by_name[object_name]["animator"] = {
                "active_clip": "Idle", "speed": 1.0,
                "clips": {"Idle": self._default_animation_clip()},
            }
            self._commands.put({"type": "scene_snapshot", "objects": deepcopy(self._scene_snapshot)})
            self._update_inspector(object_name)
            self._log("INFO", f"Animator vazio adicionado em {object_name}")
            return
        if picker.requested_action == "select" and picker.selected_path is not None:
            if self._apply_animation_asset_path_to_object(picker.selected_path, object_name):
                self._log("INFO", f"Animator adicionado em {object_name} com {picker.selected_path.name}")

    def _send_inspector_physics(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        rigidbody = obj.get("rigidbody")
        if rigidbody is None:
            return
        self._record_history()
        rigidbody["use_gravity"] = self.physics_fields["use_gravity"].isChecked()
        rigidbody["is_kinematic"] = self.physics_fields["is_kinematic"].isChecked()
        self._commands.put({"type": "set_physics", "name": self._selected_name, "rigidbody": rigidbody})

    def _send_inspector_transform(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        self._record_history()
        for key, field in self.inspector_fields.items():
            obj[key] = float(field.value())
        self._commands.put({"type": "set_transform", "name": self._selected_name, **{k: obj[k] for k in ("x", "y", "w", "h", "rotation")}})

    def _send_inspector_collider(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        collider = obj.get("collider")
        if not isinstance(collider, dict):
            return
        self._record_history()
        collider_type = str(collider.get("type", "box")).lower()
        keys = ("radius", "offset_x", "offset_y") if collider_type == "circle" else ("width", "height", "offset_x", "offset_y")
        for key in keys:
            collider[key] = float(self.collider_fields[key].value())
        collider["is_trigger"] = self.collider_trigger_field.isChecked()
        self._commands.put({"type": "set_collider", "name": self._selected_name, "collider": deepcopy(collider)})

    def _select_hierarchy_item(self, item: QTreeWidgetItem) -> None:
        name = self._hierarchy_item_name(item)
        if name in self._objects_by_name:
            self._commands.put({"type": "select_object", "name": name})
            self._selected_name = name
            self._update_inspector(name)
            self.statusBar().showMessage(f"Interface: {name} selecionado")

    def _update_inspector(self, name: str) -> None:
        obj = self._objects_by_name.get(name)
        if obj is None:
            return
        self._updating_inspector = True
        try:
            self.inspector_name_label.setText(name)
            self.animation_object_label.setText(name)
            self.add_component_button.setEnabled(True)
            self._set_inspector_card_present("transform", True)
            for key in ("x", "y", "w", "h", "rotation"):
                self.inspector_fields[key].setValue(float(obj[key]))
            renderer_enabled = bool(obj.get("renderer_enabled", True))
            renderer_present = renderer_enabled and obj.get("mesh_type") != "UI" and not isinstance(obj.get("camera"), dict)
            self._set_inspector_card_present("sprite", renderer_present)
            self.show_renderer_chk.setChecked(renderer_enabled)
            self.sprite_renderer_body.setEnabled(renderer_enabled)
            self.sprite_texture_field.setText(str(obj.get("texture", "")))
            color = tuple(obj.get("color", (255, 255, 255)))
            self.sprite_color_button.setStyleSheet(f"background: rgb({int(color[0])}, {int(color[1])}, {int(color[2])});")
            layer = str(obj.get("render_layer", "Default"))
            if self.sprite_layer_combo.findText(layer) < 0:
                self.sprite_layer_combo.addItem(layer)
            self.sprite_layer_combo.setCurrentText(layer)
            self.sprite_order_field.setValue(float(obj.get("sort_order", 0)))
            audio = obj.get("audio") if isinstance(obj.get("audio"), dict) else None
            self._set_inspector_card_present("audio", audio is not None)
            self.show_audio_chk.setChecked(audio is not None)
            self.audio_source_body.setEnabled(audio is not None)
            # Popula e seleciona o áudio do QComboBox
            self.audio_path_combo.clear()
            self.audio_path_combo.addItem("Nenhum", "")
            current_path = str((audio or {}).get("path", ""))
            audio_files = self._get_available_audio_files()
            for path in audio_files:
                name_file = Path(path).name
                self.audio_path_combo.addItem(name_file, path)
            if audio:
                idx = self.audio_path_combo.findData(current_path)
                if idx >= 0:
                    self.audio_path_combo.setCurrentIndex(idx)
                else:
                    self.audio_path_combo.setCurrentIndex(0)
            self.audio_volume_field.setValue(float((audio or {}).get("volume", 1.0)))
            self.audio_loop_field.setChecked(bool((audio or {}).get("loop", False)))
            self.audio_autoplay_field.setChecked(bool((audio or {}).get("autoplay", False)))
            rigidbody = obj.get("rigidbody")
            self._set_inspector_card_present("rigidbody", rigidbody is not None)
            self.show_rigidbody_chk.setChecked(rigidbody is not None)
            for key, field in self.physics_fields.items():
                field.setEnabled(rigidbody is not None)
                field.setChecked(bool((rigidbody or {}).get(key, False)))
            collider = obj.get("collider") if isinstance(obj.get("collider"), dict) else None
            self._set_inspector_card_present("collider", collider is not None)
            self.show_collider_chk.setChecked(collider is not None)
            collider_type = str((collider or {}).get("type", "box")).lower()
            collider_defaults = {
                "width": float(obj["w"]), "height": float(obj["h"]),
                "radius": min(float(obj["w"]), float(obj["h"])) / 2.0,
                "offset_x": 0.0, "offset_y": 0.0,
            }
            for key, field in self.collider_fields.items():
                relevant = collider is not None and (key not in ("width", "height") or collider_type == "box") and (key != "radius" or collider_type == "circle")
                field.setEnabled(relevant)
                field.setValue(float((collider or {}).get(key, collider_defaults[key])))
            self.collider_trigger_field.setEnabled(collider is not None)
            self.collider_trigger_field.setChecked(bool((collider or {}).get("is_trigger", False)))

            # Atualiza valores do Animator 2D
            anim = obj.get("animator")
            self.show_animator_chk.setChecked(anim is not None)
            self.animator_body.setEnabled(True)
            self._refresh_animator_controllers(str((anim or {}).get("controller_path", "")))
            if anim:
                clips = self._animation_clips(anim)
                active_clip = str(anim.get("active_clip", next(iter(clips))))
                if active_clip not in clips:
                    active_clip = next(iter(clips))
                self.animator_clip_combo.clear()
                self.animator_clip_combo.addItems(list(clips))
                self.animator_clip_combo.setCurrentText(active_clip)
                self.animator_speed_field.setValue(float(anim.get("speed", 1.0)))
                clip = clips[active_clip]
                bound_key = (str(obj.get("id", name)), active_clip)
                if bound_key != self._animation_bound_key:
                    self._animation_bound_key = bound_key
                    asset_path = str(clip.get("asset_path", ""))
                    self._current_animation_asset_path = (Path.cwd() / asset_path).resolve() if asset_path else None
                    self._animation_draft_name = active_clip
                    self._animation_asset_dirty = False
                    self._animation_events = deepcopy(clip.get("events", []))
                    self._refresh_animation_events()
                    self._update_animation_asset_status()
                self.animator_sheet_combo.clear()
                self.animator_sheet_combo.addItem("Nenhum", "")
                for sheet in self._available_sprite_sheets():
                    self.animator_sheet_combo.addItem(Path(sheet).name, sheet)
                sheet_index = self.animator_sheet_combo.findData(str(clip.get("texture", "")))
                self.animator_sheet_combo.setCurrentIndex(max(0, sheet_index))
                self.animator_frame_width.setValue(float(clip.get("frame_width", 32)))
                self.animator_frame_height.setValue(float(clip.get("frame_height", 32)))
                self.animator_start_frame.setValue(float(clip.get("start_frame", 0)))
                self.animator_frame_count.setValue(float(clip.get("frame_count", 1)))
                self.animator_fps_field.setValue(float(clip.get("fps", 8.0)))
                self.animator_loop_field.setChecked(bool(clip.get("loop", True)))
                # Mostra o clip que está tocando no runtime (ou o ativo do inspector se parado)
                self.animator_current_lbl.setText(str(obj.get("_current_animation_name", anim.get("active_clip", "Idle"))))
                self._animator_preview_index = min(self._animator_preview_index, max(0, int(clip.get("frame_count", 1)) - 1))
                self._refresh_animation_timeline(clip)
                self._update_animation_preview(clip)
            else:
                self._animation_bound_key = None
                self.animator_current_lbl.setText("Nenhum")
                self.animator_preview.setText("Sem Animator")

            camera = obj.get("camera") if isinstance(obj.get("camera"), dict) else None
            self._set_inspector_card_present("camera", camera is not None)
            self.show_camera_chk.setChecked(camera is not None)
            self.camera_body.setEnabled(camera is not None)
            self.camera_active_field.setChecked(bool((camera or {}).get("active", True)))
            self.camera_width_field.setValue(float((camera or {}).get("width", 1280.0)))
            self.camera_height_field.setValue(float((camera or {}).get("height", 720.0)))
            self.camera_zoom_field.setValue(float((camera or {}).get("zoom", 1.0)))
            follow_target = str((camera or {}).get("follow_target", ""))
            self.camera_follow_combo.clear()
            self.camera_follow_combo.addItem("Nenhum")
            for object_name in self._objects_by_name:
                if object_name != name:
                    self.camera_follow_combo.addItem(object_name)
            self.camera_follow_combo.setCurrentText(follow_target if follow_target in self._objects_by_name else "Nenhum")
            bg = (camera or {}).get("background_color", [22, 24, 31])
            self.camera_color_button.setStyleSheet(f"background: rgb({int(bg[0])}, {int(bg[1])}, {int(bg[2])});")

            ui = normalize_ui(obj.get("ui"))
            self._set_inspector_card_present("ui", ui is not None)
            if ui is not None:
                kind = str(ui["type"])
                labels = {"canvas": "🖥 Canvas", "text": "🔤 UI Text", "image": "🖼 UI Image", "button": "🔘 UI Button"}
                self.show_ui_chk.setText(labels[kind])
                self.show_ui_chk.setChecked(bool(ui.get("visible", True)))
                self.ui_type_field.setText({"canvas": "Canvas", "text": "Texto", "image": "Imagem", "button": "Botão"}[kind])
                self.ui_text_field.setText(str(ui.get("text", "")))
                self.ui_text_field.setEnabled(kind in {"text", "button"})
                for key, field in self.ui_position_fields.items():
                    field.setValue(float(ui.get(key, 0)))
                    field.setEnabled(kind != "canvas" and (key != "font_size" or kind in {"text", "button"}) and (key != "alpha" or kind == "image"))
                color = tuple(ui.get("color", (255, 255, 255)))[:3]
                self.ui_color_button.setEnabled(kind in {"text", "image", "button"})
                self.ui_color_button.setStyleSheet(f"background: rgb({int(color[0])}, {int(color[1])}, {int(color[2])});")
                self.ui_image_path_field.setText(str(ui.get("path", "")))
                self.ui_image_path_field.setEnabled(kind == "image")
                self.ui_image_button.setEnabled(kind == "image")
                self.ui_interactable_field.setChecked(bool(ui.get("interactable", True)))
                self.ui_interactable_field.setEnabled(kind == "button")
                self.ui_event_field.setText(str(ui.get("event", "click")))
                self.ui_event_field.setEnabled(kind == "button")
                self.ui_target_combo.clear()
                self.ui_target_combo.addItem("Este objeto")
                self.ui_target_combo.addItems([object_name for object_name in self._objects_by_name if object_name != name])
                target = str(ui.get("target", ""))
                self.ui_target_combo.setCurrentText(target if target in self._objects_by_name else "Este objeto")
                self.ui_target_combo.setEnabled(kind == "button")

            # Limpa widgets de scripts anteriores
            for h_w, b_w in self.script_containers:
                self.inspector_layout.removeWidget(h_w)
                self.inspector_layout.removeWidget(b_w)
                h_w.deleteLater()
                b_w.deleteLater()
            self.script_containers.clear()

            scripts_list = obj.get("scripts", [])
            for s_path in scripts_list:
                s_name = Path(s_path).name

                from PySide6.QtWidgets import QToolButton, QFrame
                h_widget = QWidget()
                h_widget.setObjectName("InspectorComponentHeader")
                h_lay = QHBoxLayout(h_widget)
                h_lay.setContentsMargins(6, 4, 6, 4)

                title_text = s_name.removesuffix(".py").capitalize()
                lbl_title = QLabel(component_title("script", f"{title_text} (Script)"))
                lbl_title.setObjectName("InspectorComponentTitle")
                h_lay.addWidget(lbl_title)
                h_lay.addStretch()

                btn_collapse = QToolButton()
                script_card_key = f"script:{s_path}"
                script_expanded = bool(self._component_expanded.setdefault(script_card_key, False))
                btn_collapse.setText("▼" if script_expanded else "▶")
                btn_collapse.setFixedSize(18, 18)
                btn_collapse.setObjectName("InspectorFoldoutButton")
                btn_collapse.setProperty("uiRole", "icon")
                h_lay.addWidget(btn_collapse)

                btn_del = QToolButton()
                btn_del.setText("✕")
                btn_del.setFixedSize(18, 18)
                btn_del.setObjectName("InspectorDangerButton")
                btn_del.setProperty("uiRole", "danger")
                btn_del.clicked.connect(lambda checked=False, p=s_path: self._remove_single_script(p))
                h_lay.addWidget(btn_del)

                b_widget = QWidget()
                b_widget.setObjectName("InspectorComponentBody")
                b_lay = QFormLayout(b_widget)
                b_lay.setContentsMargins(4, 4, 4, 4)
                b_lay.setSpacing(6)
                b_lay.setLabelAlignment(Qt.AlignLeft)
                b_lay.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

                b_widget.setVisible(script_expanded)
                btn_collapse.clicked.connect(
                    lambda checked=False, key=script_card_key, target=b_widget, button=btn_collapse:
                    self._toggle_dynamic_inspector_card(key, target, button)
                )

                script_sel_combo = QComboBox()
                script_sel_combo.setObjectName("InspectorScriptSelector")
                script_sel_combo.setFixedHeight(22)

                available = self._get_available_scripts()
                for p in available:
                    try:
                        rel_p = str(p.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
                    except ValueError:
                        rel_p = str(p).replace("\\", "/")
                    script_sel_combo.addItem(p.name, rel_p)

                try:
                    current_rel = str(Path(s_path).resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
                except ValueError:
                    current_rel = str(s_path).replace("\\", "/")
                idx_found = script_sel_combo.findData(current_rel)
                if idx_found >= 0:
                    script_sel_combo.setCurrentIndex(idx_found)
                else:
                    idx_found = script_sel_combo.findText(Path(s_path).name)
                    if idx_found >= 0:
                        script_sel_combo.setCurrentIndex(idx_found)

                script_sel_combo.currentIndexChanged.connect(
                    lambda index, old_p=s_path, combo=script_sel_combo: self._change_attached_script(old_p, combo.itemData(index))
                )

                lbl_key = QLabel("Script")
                lbl_key.setStyleSheet("color: #aaaaaa; font-size: 11px;")
                lbl_key.setFixedWidth(50)
                b_lay.addRow(lbl_key, script_sel_combo)

                actions_panel = QWidget()
                act_lay = QHBoxLayout(actions_panel)
                act_lay.setContentsMargins(50, 0, 0, 0)
                act_lay.setSpacing(6)

                btn_create = QPushButton("Criar")
                btn_create.setFixedHeight(20)
                btn_create.setStyleSheet("font-size: 10px; background-color: #2b2b2b; color: #ffffff; border: 1px solid #444;")
                btn_create.clicked.connect(self._create_script_asset)

                btn_edit = QPushButton("Editar")
                btn_edit.setFixedHeight(20)
                btn_edit.setStyleSheet("font-size: 10px; background-color: #2b2b2b; color: #ffffff; border: 1px solid #444;")
                btn_edit.clicked.connect(lambda checked=False, p_edit=s_path: self._edit_script_path(Path(p_edit)))

                act_lay.addWidget(btn_create)
                act_lay.addWidget(btn_edit)
                b_lay.addRow("", actions_panel)

                try:
                    full_p = Path.cwd() / s_path
                    if full_p.exists():
                        import ast
                        tree = ast.parse(full_p.read_text(encoding="utf-8"))
                        editable_properties = []
                        overrides = self._objects_by_name[name].get("script_properties", {}).get(s_path, {})
                        for node in tree.body:
                            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                                target = node.targets[0]
                                if isinstance(target, ast.Name) and target.id == "CONFIG" and isinstance(node.value, ast.Dict):
                                    for k_node, v_node in zip(node.value.keys, node.value.values):
                                        if isinstance(k_node, ast.Constant) and isinstance(v_node, ast.Constant):
                                            editable_properties.append((str(k_node.value), v_node.value))
                                elif isinstance(target, ast.Name) and target.id.isupper() and isinstance(node.value, ast.Constant):
                                    editable_properties.append((target.id, node.value.value))

                        for key_name, default_val in editable_properties:
                            val = overrides.get(key_name, default_val)
                            label_name = key_name.replace("_", " ").capitalize()
                            lbl_prop = QLabel(label_name)
                            lbl_prop.setStyleSheet("color: #aaaaaa; font-size: 11px;")
                            lbl_prop.setFixedWidth(72)

                            if isinstance(val, bool):
                                cb = QCheckBox()
                                cb.setObjectName("InspectorCheckBox")
                                cb.setChecked(val)
                                cb.toggled.connect(lambda checked_new, p_script=s_path, k_prop=key_name: self._update_script_config_val(p_script, k_prop, checked_new))
                                b_lay.addRow(lbl_prop, cb)
                            elif isinstance(val, (int, float)):
                                sb = QDoubleSpinBox()
                                sb.setObjectName("InspectorNumberField")
                                sb.setDecimals(2)
                                sb.setRange(-100000.0, 100000.0)
                                sb.setValue(float(val))
                                sb.setFixedHeight(22)
                                sb.valueChanged.connect(lambda val_new, p_script=s_path, k_prop=key_name: self._update_script_config_val(p_script, k_prop, val_new))
                                b_lay.addRow(lbl_prop, sb)
                            elif isinstance(val, str):
                                text_field = QLineEdit(val)
                                text_field.setObjectName("InspectorTextField")
                                text_field.setFixedHeight(22)
                                text_field.editingFinished.connect(lambda field=text_field, p_script=s_path, k_prop=key_name: self._update_script_config_val(p_script, k_prop, field.text()))
                                b_lay.addRow(lbl_prop, text_field)
                except Exception as e:
                    self._log("WARNING", f"Erro ao ler propriedades de {s_name}: {e}")

                idx = self.inspector_layout.indexOf(self.add_component_button)
                self.inspector_layout.insertWidget(idx, h_widget)
                self.inspector_layout.insertWidget(idx + 1, b_widget)
                self.script_containers.append((h_widget, b_widget))
        finally:
            self._updating_inspector = False

    def _read_viewport_events(self) -> None:
        while True:
            try:
                message = self._events.get_nowait()
            except Exception:
                return
            if message.get("type") == "selected":
                self._selected_name = message["name"]
                self._update_inspector(self._selected_name)
                self.statusBar().showMessage(f"Viewport: {self._selected_name} selecionado")
            elif message.get("type") == "transform_begin":
                self._drag_history_snapshot = deepcopy(self._scene_snapshot)
            elif message.get("type") == "transform_end":
                if self._drag_history_snapshot is not None and self._drag_history_snapshot != self._scene_snapshot:
                    self._record_history(self._drag_history_snapshot)
                self._drag_history_snapshot = None
            elif message.get("type") == "transform":
                obj = self._objects_by_name.get(message["name"])
                if obj is not None and not self._runtime_playing:
                    obj["x"] = float(message["x"])
                    obj["y"] = float(message["y"])
                    if "w" in message:
                        obj["w"] = float(message["w"])
                    if "h" in message:
                        obj["h"] = float(message["h"])
                    if "rotation" in message:
                        obj["rotation"] = float(message["rotation"])
                    if message["name"] == self._selected_name:
                        self._update_inspector(self._selected_name)
                self.statusBar().showMessage(
                    f"Viewport: {message['name']} em X={message['x']:.1f}, Y={message['y']:.1f}"
                )
            elif message.get("type") == "play_state":
                state = message["state"]
                if state in {"play", "pause"}:
                    self._play_session.set_runtime_state(state)
                if state == "edit":
                    self._runtime_animator_states.clear()
                    if self._animator_controller_dialog is not None:
                        self._animator_controller_dialog.set_runtime_state(None, {})
                    self._scene_snapshot, self._selected_name = self._play_session.finish()
                    self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
                    self._runtime_keys = {key: False for key in self._runtime_keys}
                    self._commands.put({"type": "runtime_input", "keys": dict(self._runtime_keys)})
                    self._refresh_hierarchy()
                    if self._selected_name in self._objects_by_name:
                        self._commands.put({"type": "select_object", "name": self._selected_name})
                        self._update_inspector(self._selected_name)
                self._runtime_playing = self._play_session.is_running
                self._set_play_mode_editing_locked(state in {"play", "pause"})
                self.toolbar_actions["Play"].setEnabled(state != "play")
                self.toolbar_actions["Pause"].setEnabled(state in {"play", "pause"})
                self.toolbar_actions["Stop"].setEnabled(state in {"play", "pause"})
                self.statusBar().showMessage(
                    {"play": "Viewport: PLAY", "pause": "Viewport: PAUSE", "edit": "Viewport: EDIT — cena restaurada"}[state]
                )
                self._log("INFO", {"play": "Play iniciado/retomado", "pause": "Play pausado", "edit": "Play finalizado; cena restaurada"}[state])
            elif message.get("type") == "scene_snapshot":
                self._scene_snapshot, restored_selection = self._play_session.consume_scene_snapshot(
                    [deepcopy(item) for item in message.get("objects", [])]
                )
                if restored_selection is not None:
                    self._selected_name = restored_selection
                self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
                self._refresh_hierarchy()
                if self._selected_name in self._objects_by_name:
                    self._update_inspector(self._selected_name)
            elif message.get("type") == "viewport_mode":
                state = "embutida" if message.get("embedded") else "em janela separada (fallback)"
                self.statusBar().showMessage(f"Viewport {state}")
            elif message.get("type") == "script_log":
                self._log(str(message.get("level", "INFO")), str(message.get("message", "")))
            elif message.get("type") == "animator_state":
                object_name = str(message.get("name", ""))
                self._runtime_animator_states[object_name] = dict(message)
                if object_name == self._selected_name:
                    state = str(message.get("state", "Nenhum"))
                    self.animator_current_lbl.setText(state)
                    dialog = self._animator_controller_dialog
                    if dialog is not None:
                        dialog.set_runtime_state(state, message.get("parameters"))
            elif message.get("type") == "animation_event":
                self._log(
                    "INFO",
                    f"Evento de animação: {message.get('name')} → {message.get('event')} "
                    f"(frame {int(message.get('frame', 0)) + 1})",
                )
            elif message.get("type") == "attach_script":
                self._attach_script(str(message.get("name", "")), Path(str(message.get("path", ""))))
            elif message.get("type") == "stats":
                self.profiler_label.setText(
                    f"FPS: {message.get('fps', 0):.0f}\n"
                    f"Objetos: {message.get('objects', 0)}\n"
                    f"Modo: {message.get('mode', 'EDIT')} / {message.get('view', 'SCENE')}\n"
                    f"Câmera: {message.get('camera', 'Editor')}\n"
                    f"Jogador: {message.get('player') or '—'}\n"
                    f"Zoom: {message.get('zoom', 1.0):.2f}"
                )

    def closeEvent(self, event) -> None:
        try:
            self._commands.put_nowait({"type": "shutdown"})
        except Exception:
            pass
        if self._viewport_process is not None and self._viewport_process.is_alive():
            self._viewport_process.terminate()
            self._viewport_process.join(timeout=2)
        super().closeEvent(event)


def main() -> None:
    context = mp.get_context("spawn")
    commands = context.Queue()
    events = context.Queue()
    app = QApplication.instance() or QApplication(sys.argv)
    from editor.ui import apply_editor_theme
    apply_editor_theme(app)
    window = IsolatedEditorWindow(None, commands, events)
    window.show()
    app.processEvents()

    host_id = int(window.viewport_host.winId())
    host_size = window.native_viewport_size()
    viewport_process = context.Process(
        target=run_viewport,
        args=(commands, events, host_id, host_size),
        name="ZennityViewport",
    )
    window.attach_viewport_process(viewport_process)
    viewport_process.start()
    exit_code = app.exec()

    if viewport_process.is_alive():
        viewport_process.terminate()
        viewport_process.join(timeout=2)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
