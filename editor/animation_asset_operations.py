"""Animation asset, controller, preview and binding operations."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTreeWidgetItem

from editor.runtime.sprite_rendering import assign_sprite_texture
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from engine.animation.clip_asset import animation_asset_from_clip, animation_asset_to_clip, default_animation_asset, load_animation_asset, save_animation_asset
from engine.animation.controller_asset import load_animator_controller


class AnimationAssetOperations:
    def _show_animation_window(self) -> None:
        self._refresh_animation_library()
        self.animation_window.show()
        self.animation_window.raise_()
        self.animation_window.activateWindow()
        self._log("INFO", "Editor de Animação aberto")

    def _toggle_animator_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("animator", {"active_clip": "Idle", "speed": 1.0, "clips": {"Idle": self._default_animation_clip()}})
        else:
            obj.pop("animator", None)
        self._scene_controller.publish_snapshot(self._scene_snapshot)
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
        self._animation_workspace.connect()

    def _animation_assets_directory(self) -> Path:
        return self._animation_workspace.assets_directory()

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
            self._scene_controller.publish_snapshot(self._scene_snapshot)
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
        self._scene_controller.publish_snapshot(self._scene_snapshot)
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
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._scene_controller.select(object_name)
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
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._update_inspector(self._selected_name)

    def _project_relative_path(self, path: Path | None) -> str:
        if path is None:
            return ""
        try:
            return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

