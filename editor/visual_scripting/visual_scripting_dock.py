"""Visual Scripting Editor Dock (Production Suite — Visual Scripting 2.0).

Implementa o layout profissional completo de 4 áreas + Mini Live Viewport:
  - Toolbar Superior: Play/Pause/Stop, Auto-Layout, Validate, Search, DebugGER, Settings.
  - Paleta de Nós com Busca & Categorias (Esquerda).
  - Graph Canvas com Bézier Animado, Zoom/Pan, CommentFrames & Minimap (Centro).
  - Node Inspector de Propriedades & Documentação (Direita).
  - Painel Inferior com Mini Live Viewport (Preview de Runtime em Tempo Real) & Watch Variables.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QSplitter, QTabWidget, QTextEdit,
)

from editor.widgets.logic_graph_editor import LogicGraphEditor
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from editor.ui_builder.ui_builder_dock import UIBuilderDock
from editor.visual_scripting.mini_live_viewport import (
    MiniLiveViewportWidget,
    ViewportMode,
)
from editor.visual_scripting.modern_theme import apply_visual_scripting_theme
from editor.visual_scripting.dock_workspace_sync import (
    GraphToolAdapter as _GraphToolAdapter,
    sync_scene_workspace,
)


class VisualScriptingEditorDock(QMainWindow):
    """Independent dedicated tool window for Visual Scripting 2.0."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("⚡ Visual Scripting Editor 2.0 — Zennity Engine")
        self.setObjectName("VisualScriptingEditorDock")
        self._host = parent
        self.resize(1400, 860)
        self.setMinimumSize(960, 640)
        self._scene_workspace_signature: tuple = ()

        # Container Principal
        self.main_container = QWidget(self)
        self.main_container.setObjectName("VisualScriptingSurface")
        self.setCentralWidget(self.main_container)

        root_layout = QVBoxLayout(self.main_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        shared_editor = getattr(parent, "logic_workspace", None)
        self.graph_editor = shared_editor or LogicGraphEditor(parent=self.main_container)
        # Reparent the shared workspace without briefly drawing its old shell;
        # this window then promotes the same widget to the full modern surface.
        self.graph_editor.set_embedded_mode(True)
        self.graph_editor.set_embedded_mode(False)

        # A janela continua sendo o único hub oficial. Cada domínio possui uma
        # aba editável, sem abrir janelas ou runtimes paralelos.
        self.graph_mode_tabs = QTabWidget(self.main_container)
        self.graph_mode_tabs.setObjectName("GraphModeTabs")
        self.graph_mode_tabs.addTab(self.graph_editor, "Logic Graph")
        self.behavior_tree_editor = self._new_specialized_graph("Behavior Tree")
        self.dialogue_graph_editor = self._new_specialized_graph("Dialogue")
        self.material_graph_editor = self._new_specialized_graph("Material")
        self.animator_graph_editor = AnimatorControllerEditorDialog(
            Path.cwd(), parent=self, embedded=True
        )
        self.ui_builder = UIBuilderDock(self, project_root=Path.cwd())
        self.ui_builder.setFeatures(UIBuilderDock.NoDockWidgetFeatures)
        self.graph_mode_tabs.addTab(self.behavior_tree_editor, "Behavior Tree")
        self.graph_mode_tabs.addTab(self.dialogue_graph_editor, "Dialogue")
        self.graph_mode_tabs.addTab(self.material_graph_editor, "Material")
        self.graph_mode_tabs.addTab(self.animator_graph_editor, "Animator Graph")
        self.graph_mode_tabs.addTab(self.ui_builder, "UI & HUD")
        root_layout.addWidget(self.graph_mode_tabs)
        self._graph_tool_adapters = {
            "behavior_tree": _GraphToolAdapter(self, "behavior_tree", self.behavior_tree_editor),
            "dialogue": _GraphToolAdapter(self, "dialogue", self.dialogue_graph_editor),
            "material_graph": _GraphToolAdapter(self, "material_graph", self.material_graph_editor),
            "animator_graph": _GraphToolAdapter(self, "animator_graph", self.animator_graph_editor),
            "ui": _GraphToolAdapter(self, "ui", self.ui_builder),
        }
        self.graph_mode_tabs.currentChanged.connect(self._on_graph_mode_changed)

        # Mapeamento de propriedades e botões mantendo compatibilidade total
        self.toolbar_widget = self.graph_editor.header_widget
        self.btn_play = self.graph_editor.play_button
        self.btn_pause = self.graph_editor.pause_button
        self.btn_stop = self.graph_editor.stop_button
        self.btn_save = self.graph_editor.save_button
        self.btn_new = self.graph_editor.new_button
        self.btn_open = self.graph_editor.open_button
        self.btn_auto_layout = self.graph_editor.organize_button
        self.btn_validate = self.graph_editor.compile_button
        self.btn_hot_reload = self.graph_editor.save_button
        self.btn_debug = self.graph_editor.breakpoint_button
        self.btn_explain = self.graph_editor.help_button
        self.search_bar = self.graph_editor.node_search
        self.document_label = self.graph_editor.asset_label
        self.object_context_label = self.graph_editor.validation_label
        self.vertical_splitter = self.graph_editor.content_splitter
        self.horizontal_splitter = self.graph_editor.content_splitter
        self.mini_viewport = getattr(self.graph_editor, "mini_live_viewport", None)
        if self.mini_viewport is None:
            self.mini_viewport = MiniLiveViewportWidget(self.main_container)
        self.mini_viewport.set_transport_controls_visible(False)
        self.runtime_logs_text = getattr(self.graph_editor, "trace_console", None)
        if self.runtime_logs_text is None:
            self.runtime_logs_text = QTextEdit()

        self._apply_modern_theme()
        self._connect_signals()
        self._open_initial_document()
        self.sync_from_host()
        
        self._sync_timer = QTimer(self)
        self._sync_timer.timeout.connect(self._tick_sync)

    def _tick_sync(self) -> None:
        self.sync_from_host()

    @staticmethod
    def _new_specialized_graph(category: str) -> GenericGraphEditorWidget:
        """Create a metadata-backed graph editor inside the unified hub."""
        try:
            from engine.core.context import EngineContext
            if EngineContext.current() is None:
                from engine.core.bootstrap import EngineBootstrap
                EngineBootstrap.boot()
        except Exception:
            pass
        return GenericGraphEditorWidget(graph_category_filter=category)

    def _on_graph_mode_changed(self, index: int) -> None:
        labels = (
            "LOGIC GRAPH", "BEHAVIOR TREE", "DIALOGUE", "MATERIAL",
            "ANIMATOR GRAPH", "UI & HUD",
        )
        logic_mode = index == 0
        for button in (self.btn_play, self.btn_pause, self.btn_stop):
            button.setVisible(logic_mode)
        self.document_label.setText(
            labels[index] if 0 <= index < len(labels) else "VISUAL LOGIC"
        )

    def open_graph_tool(self, tool_id: str) -> None:
        """Open this single window directly on a requested graph domain."""
        indexes = {
            "visual_scripting": 0, "logic_graph": 0, "behavior_tree": 1,
            "dialogue": 2, "material_graph": 3, "animator_graph": 4,
            "ui": 5,
        }
        self.graph_mode_tabs.setCurrentIndex(indexes.get(tool_id, 0))
        self.show()
        self.raise_()
        self.activateWindow()

    def graph_tool_adapter(self, tool_id: str):
        return getattr(self, "_graph_tool_adapters", {}).get(tool_id)

    def _apply_modern_theme(self) -> None:
        apply_visual_scripting_theme(self)

    def configure_independent_window(self) -> None:
        """Configures independent tool window size and flags."""
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
        self.resize(1400, 860)
        self.setMinimumSize(960, 640)

    def closeEvent(self, event) -> None:
        """Hide the editor so reopening preserves the active graph and layout."""
        event.ignore()
        self.hide()

    def _connect_signals(self) -> None:
        self.graph_editor.asset_changed.connect(self.sync_from_host)
        self.graph_editor.pause_button.clicked.connect(self._pause)

    def _active_graph_editor(self):
        index = self.graph_mode_tabs.currentIndex()
        if index == 0:
            return self.graph_editor
        if 1 <= index <= 5:
            return self.graph_mode_tabs.widget(index)
        return None

    def _auto_layout_active(self) -> None:
        editor = self._active_graph_editor()
        if editor is None:
            return
        callback = getattr(editor, "organize_graph", None) or getattr(
            editor, "auto_layout", None
        )
        if callback is not None:
            callback()

    def _validate_active(self) -> None:
        editor = self._active_graph_editor()
        if editor is self.graph_editor:
            self._validate()
        elif editor is not None:
            editor.validate_graph()

    def update_runtime_stats(
        self, *, fps: float, object_count: int, frame_ms: float | None = None
    ) -> None:
        """Display live measurements using the new profiler widget."""
        milliseconds = (
            float(frame_ms) if frame_ms is not None
            else (1000.0 / fps if fps > 0 else 0.0)
        )
        budget = "OK" if milliseconds <= 16.67 else "ACIMA"
        summary = f"FPS: {fps:.1f} | Frame: {milliseconds:.2f} ms ({budget}) | Obj: {object_count}"
        fps_badge = getattr(getattr(self, "graph_editor", None), "fps_badge", None)
        if fps_badge is not None:
            fps_badge.setText(f"{fps:.0f} FPS")
        profiler_widget = getattr(self, "profiler_widget", None)
        if profiler_widget is not None:
            profiler_widget.fps_label.setText(summary)
        profiler_text = getattr(self, "profiler_text", None)
        if callable(getattr(profiler_text, "setPlainText", None)):
            profiler_text.setPlainText(summary)

    def _new_for_active_object(self) -> None:
        """Create a blank graph already bound to the selected scene object."""
        host = self.parent()
        controller = getattr(host, "_logic_workspace_controller", None)
        selected = getattr(host, "_selected_name", None)
        objects = getattr(host, "_objects_by_name", {})
        if controller is not None and selected in objects:
            controller.create_blank_for_selected()
            return
        self.graph_editor.new_graph()

    def _open_initial_document(self) -> None:
        """Open the selected object's graph, or the most useful project graph."""
        if self.graph_editor.current_path is not None:
            return
        host = self._host
        repository = getattr(host, "_logic_assets_repository", None)
        if repository is None:
            return
        selected = getattr(host, "_selected_name", None)
        objects = getattr(host, "_objects_by_name", {})
        assets = repository.for_object(selected, objects.get(selected, {})) if selected else []
        if not assets:
            assets = repository.assets()
        if not assets:
            return
        path, _graph = max(
            assets,
            key=lambda entry: (
                str(entry[1].get("target", {}).get("value", "")) in objects,
                len(entry[1].get("nodes", [])),
            ),
        )
        self.graph_editor.open_asset(path)
        self.document_label.setText(path.name.upper())

    def _dispatch(self, command: str) -> None:
        dispatcher = getattr(self._host, "_editor_commands", None)
        if dispatcher is not None:
            dispatcher.dispatch({"type": command})

    def _play(self) -> None:
        # request_play saves the graph and emits the single official Play command.
        self.graph_editor.request_play()

    def _pause(self) -> None:
        self._dispatch("pause")

    def _stop(self) -> None:
        # stop_requested is wired to the same command controller as the main toolbar.
        self.graph_editor.stop_requested.emit()

    def _trigger_hot_reload(self) -> None:
        """Salva o documento atual e dispara notificação de hot reload para o runtime."""
        if hasattr(self.graph_editor, "is_dirty") and self.graph_editor.is_dirty:
            self.graph_editor.save()
        elif hasattr(self.graph_editor, "save"):
            # Sempre salva para ter certeza que as modificações estão no disco
            self.graph_editor.save()
        self._dispatch("logic_hot_reload")
        self.runtime_logs_text.append("[HOT RELOAD] Sinal enviado para atualizar grafo em tempo de execução.")

    def set_play_state(self, state: str) -> None:
        """Mirror the state confirmed by the real viewport process."""
        modes = {
            "play": ViewportMode.GAME,
            "pause": ViewportMode.DEBUG,
            "edit": ViewportMode.EDITOR,
        }
        mode = modes.get(str(state))
        if mode is None:
            return
        self.mini_viewport.set_viewport_mode(mode)
        graph_editor = getattr(self, "graph_editor", None)
        title = getattr(graph_editor, "mini_viewport_title", None)
        if title is not None:
            title.setText({
                "play": "● Mini Viewport — Play Mode",
                "pause": "● Mini Viewport — Pausado",
                "edit": "● Mini Viewport — Editor",
            }[state])
            color = "#22c55e" if state == "play" else "#e6b85c" if state == "pause" else "#60a5fa"
            title.setStyleSheet(
                f"color: {color}; font-weight: bold; font-size: 11px;"
            )
        running = state in {"play", "pause"}
        if graph_editor is not None:
            graph_editor.set_play_state(running)
        self.btn_play.setEnabled(state != "play")
        self.btn_pause.setEnabled(running)
        self.btn_stop.setEnabled(running)
        hot_reload = getattr(self, "btn_hot_reload", None)
        if hot_reload is not None:
            hot_reload.setEnabled(running)
        if running:
            self._sync_timer.start(33)
        else:
            self._sync_timer.stop()
        self.sync_from_host()

    def _validate(self) -> None:
        issues = self.graph_editor.validate_graph()
        errors = [item for item in issues if item.get("level") == "error"]
        self.runtime_logs_text.append(
            f"[VALIDATE] {len(issues)} aviso(s), {len(errors)} erro(s)."
        )

    def sync_from_host(self) -> None:
        """Mirror the active editor/runtime scene in the integrated Game View."""
        host = self._host
        if self.graph_editor.current_path is not None:
            self.document_label.setText(
                self.graph_editor.current_path.name.upper()
            )
        runtime = getattr(host, "_runtime_objects_by_name", {})
        source = list(runtime.values()) if runtime else list(
            getattr(host, "_scene_snapshot", [])
        )
        self.mini_viewport.unified_viewport.apply_snapshot({
            "objects": source,
            "object_count": len(source),
        })
        selected = getattr(host, "_selected_name", None)
        objects = getattr(host, "_objects_by_name", {})
        repository = getattr(host, "_logic_assets_repository", None)
        graph_count = len(
            repository.for_object(selected, objects.get(selected, {}))
        ) if repository is not None and selected in objects else 0
        self.set_object_context(selected, graph_count)
        active_objects = runtime or objects
        if selected in active_objects:
            self.mini_viewport.set_target_object(active_objects[selected])
            self.mini_viewport.unified_viewport.selected_object_id = str(
                active_objects[selected].get("id", "")
            )
        else:
            self.mini_viewport.unified_viewport.selected_object_id = ""
        self._sync_scene_workspace()

    def _sync_scene_workspace(self) -> None:
        """Preload all visual documents declared by the active scene."""
        sync_scene_workspace(self)

    def set_object_context(
        self, object_name: str | None, graph_count: int = 0
    ) -> None:
        if object_name:
            suffix = "grafo" if graph_count == 1 else "grafos"
            self.object_context_label.setText(
                f"OBJETO ATIVO: {object_name}  •  {graph_count} {suffix}"
            )
        else:
            self.object_context_label.setText("OBJETO ATIVO: NENHUM")

    def apply_runtime_trace(self, message: dict) -> None:
        if message.get("type") != "logic_trace":
            return
        node_id = str(message.get("node_id") or message.get("current_node") or "")
        node_name = str(message.get("node_name") or message.get("title") or node_id)
        if node_id:
            self.highlight_node_execution(node_id, node_name)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.sync_from_host()

    def trigger_explain_mode(self) -> None:
        """Dispara a explicação causa-raiz no Runtime Explain Mode."""
        from editor.visual_scripting.runtime_explain_mode import RuntimeExplainMode
        exp = RuntimeExplainMode.instance().explain_object_behavior(self.mini_viewport.target_object or "Player", "Move")
        self.runtime_logs_text.append(f"[EXPLAIN] {exp['cause_summary']}")
        self.runtime_logs_text.append(f"[EXPLAIN] Cadeia: {' ➔ '.join(exp['execution_chain'])}")

    def highlight_node_execution(self, node_id: str, node_name: str) -> None:
        """Sincroniza execução de um nó com a Mini Live Viewport."""
        self.mini_viewport.highlight_execution_node(node_id, node_name)
        self.runtime_logs_text.append(f"[EXEC] Nó '{node_name}' ({node_id}) executado.")
