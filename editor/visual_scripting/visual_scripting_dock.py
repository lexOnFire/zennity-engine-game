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


class _GraphToolAdapter:
    """Expose one hub tab through the bridge/tool contracts."""

    def __init__(self, hub: "VisualScriptingEditorDock", tool_id: str, graph_editor) -> None:
        self.hub = hub
        self.tool_id = tool_id
        self.graph_editor = graph_editor

    def show(self) -> None:
        self.hub.open_graph_tool(self.tool_id)

    def raise_(self) -> None:
        self.hub.raise_()

    def activateWindow(self) -> None:
        self.hub.activateWindow()


class VisualScriptingEditorDock(QMainWindow):
    """Independent native window for Visual Scripting 2.0."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("⚡ Visual Scripting Editor 2.0")
        self.setObjectName("VisualScriptingEditorDock")
        self._host = parent
        self._scene_workspace_signature: tuple[tuple[str, str], ...] = ()

        # Container Principal
        self.main_container = QWidget(self)
        self.main_container.setObjectName("VisualScriptingSurface")
        self.setCentralWidget(self.main_container)

        root_layout = QVBoxLayout(self.main_container)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        # 1. TOOLBAR SUPERIOR (Sprint 1)
        self.toolbar_widget = QWidget(self.main_container)
        self.toolbar_widget.setObjectName("VisualCommandBar")
        self.toolbar_widget.setFixedHeight(58)
        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(12, 6, 12, 6)
        toolbar_layout.setSpacing(6)

        brand_box = QWidget(self.toolbar_widget)
        brand_box.setObjectName("VisualBrand")
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(0, 0, 12, 0)
        brand_layout.setSpacing(0)
        brand_title = QLabel("ZENNITY  /  VISUAL LOGIC", brand_box)
        brand_title.setObjectName("VisualBrandTitle")
        self.document_label = QLabel("NO GRAPH", brand_box)
        self.document_label.setObjectName("VisualDocumentLabel")
        self.object_context_label = QLabel("OBJETO ATIVO: NENHUM", brand_box)
        self.object_context_label.setObjectName("VisualObjectContext")
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(self.document_label)
        brand_layout.addWidget(self.object_context_label)
        toolbar_layout.addWidget(brand_box)
        toolbar_layout.addSpacing(8)

        self.btn_play = QPushButton("▶ Play", self.toolbar_widget)
        self.btn_play.setObjectName("VisualPlayButton")
        self.btn_pause = QPushButton("⏸ Pause", self.toolbar_widget)
        self.btn_stop = QPushButton("⏹ Stop", self.toolbar_widget)
        self.btn_stop.setObjectName("VisualStopButton")
        
        self.btn_hot_reload = QPushButton("🔥 Hot Reload", self.toolbar_widget)
        self.btn_hot_reload.setEnabled(False)

        self.btn_auto_layout = QPushButton("✨ Auto Layout", self.toolbar_widget)
        self.btn_validate = QPushButton("✔️ Validar Grafo", self.toolbar_widget)
        self.btn_new = QPushButton("＋ Novo", self.toolbar_widget)
        self.btn_open = QPushButton("📂 Abrir", self.toolbar_widget)
        self.btn_save = QPushButton("💾 Salvar", self.toolbar_widget)
        self.btn_debug = QPushButton("🐞 Debugger", self.toolbar_widget)
        self.btn_explain = QPushButton("💡 Explain Mode", self.toolbar_widget)
        self.btn_explain.setObjectName("VisualExplainButton")

        self.search_bar = QLineEdit(self.toolbar_widget)
        self.search_bar.setPlaceholderText("🔍 Pesquisar Nós... (Ctrl+F)")
        self.search_bar.setMinimumWidth(210)
        self.search_bar.setMaximumWidth(280)

        toolbar_layout.addWidget(self.btn_play)
        toolbar_layout.addWidget(self.btn_pause)
        toolbar_layout.addWidget(self.btn_stop)
        toolbar_layout.addWidget(self.btn_hot_reload)
        toolbar_layout.addSpacing(12)
        toolbar_layout.addWidget(self.btn_new)
        toolbar_layout.addWidget(self.btn_open)
        toolbar_layout.addWidget(self.btn_save)
        toolbar_layout.addSpacing(12)
        toolbar_layout.addWidget(self.btn_auto_layout)
        toolbar_layout.addWidget(self.btn_validate)
        toolbar_layout.addWidget(self.btn_debug)
        toolbar_layout.addWidget(self.btn_explain)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.search_bar)

        root_layout.addWidget(self.toolbar_widget)

        # 2. SPLITTER VERTICAL (Divisão Superior Graph / Divisão Inferior Mini Viewport & Logs)
        self.vertical_splitter = QSplitter(Qt.Vertical, self.main_container)

        # 3. SPLITTER HORIZONTAL (Paleta | Graph Canvas | Node Inspector)
        self.horizontal_splitter = QSplitter(Qt.Horizontal, self.vertical_splitter)

        # O VS 2.0 hospeda o editor .zlogic oficial. Isso preserva os assets,
        # o runtime e a biblioteca completa de nós em uma única implementação.
        shared_editor = getattr(parent, "logic_workspace", None)
        self.graph_editor = shared_editor or LogicGraphEditor(parent=self.horizontal_splitter)
        self.graph_editor.set_embedded_mode(True)
        self.horizontal_splitter.addWidget(self.graph_editor)
        self.horizontal_splitter.setSizes([1000])
        self.vertical_splitter.addWidget(self.horizontal_splitter)

        # 4. PAINEL INFERIOR (Sprint 7: Mini Live Viewport & Runtime Watches)
        self.bottom_panel = QSplitter(Qt.Horizontal, self.vertical_splitter)

        # Mini Live Viewport
        self.mini_viewport = MiniLiveViewportWidget(self.bottom_panel)
        self.mini_viewport.set_transport_controls_visible(False)
        self.bottom_panel.addWidget(self.mini_viewport)

        # Painel de Watches / Runtime Logs & Timeline (Sprint 13)
        from editor.visual_scripting.runtime_timeline import RuntimeTimelineWidget
        self.watches_tabs = QTabWidget(self.bottom_panel)
        self.runtime_logs_text = QTextEdit(self.watches_tabs)
        self.runtime_logs_text.setReadOnly(True)
        self.runtime_logs_text.append("[Runtime] Visual Scripting 2.0 inicializado.")
        self.watches_tabs.addTab(self.runtime_logs_text, "📜 Runtime Logs & Watches")

        self.runtime_timeline = RuntimeTimelineWidget(self.watches_tabs)
        self.watches_tabs.addTab(self.runtime_timeline, "⏱️ Runtime Timeline")

        # Visual Profiler Tab (Fase 9)
        from editor.visual_scripting.visual_profiler_widget import VisualProfilerWidget
        self.profiler_widget = VisualProfilerWidget(self.watches_tabs)
        self.watches_tabs.addTab(self.profiler_widget, "📊 Visual Profiler")

        self.bottom_panel.addWidget(self.watches_tabs)

        self.bottom_panel.setSizes([560, 640])
        self.vertical_splitter.addWidget(self.bottom_panel)

        self.vertical_splitter.setSizes([650, 260])

        # Central única para todos os sistemas baseados em grafo. Modos
        # especializadas não criam mais janelas concorrentes no editor.
        self.graph_mode_tabs = QTabWidget(self.main_container)
        self.graph_mode_tabs.setObjectName("GraphModeTabs")
        self.graph_mode_tabs.addTab(self.vertical_splitter, "Logic Graph")
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
        self._graph_tool_adapters = {
            "behavior_tree": _GraphToolAdapter(self, "behavior_tree", self.behavior_tree_editor),
            "dialogue": _GraphToolAdapter(self, "dialogue", self.dialogue_graph_editor),
            "material_graph": _GraphToolAdapter(self, "material_graph", self.material_graph_editor),
            "animator_graph": _GraphToolAdapter(self, "animator_graph", self.animator_graph_editor),
        }
        self.graph_mode_tabs.currentChanged.connect(self._on_graph_mode_changed)
        root_layout.addWidget(self.graph_mode_tabs)

        self._apply_modern_theme()
        # Conexões de Sinais da Toolbar
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
        logic_mode = index == 0
        for button in (
            self.btn_play, self.btn_pause, self.btn_stop, self.btn_hot_reload, self.btn_new,
            self.btn_open, self.btn_save, self.btn_debug, self.btn_explain,
        ):
            button.setEnabled(logic_mode)
        self.search_bar.setEnabled(logic_mode)
        self.btn_auto_layout.setEnabled(index != 5)
        self.btn_validate.setEnabled(index != 5)
        labels = (
            "LOGIC GRAPH", "BEHAVIOR TREE", "DIALOGUE", "MATERIAL",
            "ANIMATOR GRAPH", "UI & HUD",
        )
        self.document_label.setText(labels[index] if 0 <= index < len(labels) else "GRAPH")

    def open_graph_tool(self, tool_id: str) -> None:
        """Open this single window directly on a requested graph domain."""
        indexes = {
            "visual_scripting": 0,
            "logic_graph": 0,
            "behavior_tree": 1,
            "dialogue": 2,
            "material_graph": 3,
            "animator_graph": 4,
            "ui": 5,
        }
        self.graph_mode_tabs.setCurrentIndex(indexes.get(tool_id, 0))
        self.show()
        self.raise_()
        self.activateWindow()

    def graph_tool_adapter(self, tool_id: str):
        return self._graph_tool_adapters.get(tool_id)

    def _apply_modern_theme(self) -> None:
        apply_visual_scripting_theme(self)


    def configure_independent_window(self) -> None:
        """Turn this tool into a native, independent editor window."""
        host = self._host
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
        self.btn_play.clicked.connect(self._play)
        self.btn_pause.clicked.connect(self._pause)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_hot_reload.clicked.connect(self._trigger_hot_reload)
        self.btn_new.clicked.connect(self._new_for_active_object)
        self.btn_open.clicked.connect(self.graph_editor.open_dialog)
        self.btn_save.clicked.connect(self.graph_editor.save)
        self.btn_auto_layout.clicked.connect(self._auto_layout_active)
        self.btn_validate.clicked.connect(self._validate_active)
        self.btn_explain.clicked.connect(self.trigger_explain_mode)
        self.search_bar.textChanged.connect(self.graph_editor.node_search.setText)
        self.graph_editor.asset_changed.connect(self.sync_from_host)

    def _active_graph_editor(self):
        index = self.graph_mode_tabs.currentIndex()
        if index == 0:
            return self.graph_editor
        if 1 <= index <= 4:
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
        profiler_widget = getattr(self, "profiler_widget", None)
        if profiler_widget is not None:
            profiler_widget.fps_label.setText(summary)
        profiler_text = getattr(self, "profiler_text", None)
        if profiler_text is not None:
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
        running = state in {"play", "pause"}
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
        from engine.logic.graph_asset import validate_logic_graph
        issues = validate_logic_graph(self.graph_editor.graph_data())
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
        document = getattr(self._host, "_scene_document", None)
        workspace = (
            document.get("visual_logic_workspace", {})
            if isinstance(document, dict) else {}
        )
        if not isinstance(workspace, dict):
            return
        signature = tuple(
            sorted((str(key), str(value)) for key, value in workspace.items())
        )
        if not signature or signature == self._scene_workspace_signature:
            return
        # Set before opening: LogicGraphEditor emits asset_changed synchronously.
        self._scene_workspace_signature = signature
        editors = {
            "logic": self.graph_editor,
            "behavior_tree": self.behavior_tree_editor,
            "dialogue": self.dialogue_graph_editor,
            "material": self.material_graph_editor,
            "animator": self.animator_graph_editor,
            "ui": self.ui_builder,
        }
        opened = 0
        for key, editor in editors.items():
            asset_value = workspace.get(key)
            if not asset_value:
                continue
            path = Path(str(asset_value))
            path = path if path.is_absolute() else Path.cwd() / path
            callback = (
                getattr(editor, "open_asset", None)
                or getattr(editor, "load_document", None)
            )
            if callback is not None and path.is_file() and callback(path):
                opened += 1
        if opened:
            self.runtime_logs_text.append(
                f"[Workspace] {opened} documento(s) da cena carregado(s)."
            )

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
