"""EditorBridgeOrchestrator — ponto central de inicialização de todos os bridges.

Responsabilidade:
  Inicializa e conecta todos os bridges do Editor Framework 2.0
  em ordem correta, injetando dependências entre eles.

Uso (na MainWindow ou IsolatedEditorWindow):
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator

    orchestrator = EditorBridgeOrchestrator(editor_context)
    orchestrator.setup(
        hierarchy=self.dock_hierarchy,
        inspector=self.dock_inspector,
        viewport=self.viewport,
        viewmodel=self.scene_viewmodel,
        animation_dock=self.dock_animation,
        visual_scripting_dock=self.dock_vs,
        behavior_tree_dock=self.dock_bt,
        dialogue_dock=self.dock_dlg,
        material_dock=self.dock_mat,
    )
"""
from __future__ import annotations

from typing import Any


class EditorBridgeOrchestrator:
    """Inicializa todos os bridges do Editor Framework 2.0 em sequência.

    Ordem de inicialização:
      1. ReactiveEditorBridge  (base: Hierarchy + Inspector + Viewport)
      2. AnimationStudioBridge (Animation.* Events)
      3. VisualScriptingBridge (Graph.vs.* Events)
      4. BehaviorTreeBridge    (Graph.bt.* Events)   ← Sprint 4c
      5. DialogueBridge        (Graph.dlg.* Events)  ← Sprint 4c
      6. MaterialGraphBridge   (Graph.mat.* Events)  ← Sprint 4c
    """

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self.reactive: Any = None
        self.animation: Any = None
        self.visual_scripting: Any = None
        self.behavior_tree: Any = None
        self.dialogue: Any = None
        self.material_graph: Any = None

    def setup(
        self,
        hierarchy: Any = None,
        inspector: Any = None,
        viewport: Any = None,
        viewmodel: Any = None,
        animation_dock: Any = None,
        visual_scripting_dock: Any = None,
        behavior_tree_dock: Any = None,
        dialogue_dock: Any = None,
        material_dock: Any = None,
    ) -> None:
        """Configura todos os bridges. Argumentos None são silenciosamente ignorados."""

        # 1. Bridge base (Hierarchy → Inspector → Viewport)
        from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge
        self.reactive = ReactiveEditorBridge(self._ctx)
        if hierarchy:
            self.reactive.attach_hierarchy(hierarchy)
        if inspector:
            self.reactive.attach_inspector(inspector)
        if viewport:
            self.reactive.attach_viewport(viewport)
        if viewmodel:
            self.reactive.attach_viewmodel(viewmodel)

        # 2. Animation Studio Bridge
        from editor.runtime.animation_studio_bridge import AnimationStudioBridge
        self.animation = AnimationStudioBridge(self._ctx)
        self.animation.attach_reactive_bridge(self.reactive)
        if animation_dock:
            self.animation.attach_dock(animation_dock)

        # 3. Visual Scripting Bridge
        from editor.runtime.visual_scripting_bridge import VisualScriptingBridge
        self.visual_scripting = VisualScriptingBridge(self._ctx)
        self.visual_scripting.attach_reactive_bridge(self.reactive)
        if visual_scripting_dock:
            self.visual_scripting.attach_dock(visual_scripting_dock)

        # 4. Behavior Tree Bridge (Sprint 4c)
        from editor.runtime.graph_bridges import BehaviorTreeBridge
        self.behavior_tree = BehaviorTreeBridge(self._ctx)
        if behavior_tree_dock:
            self.behavior_tree.attach_dock(behavior_tree_dock)

        # 5. Dialogue Bridge (Sprint 4c)
        from editor.runtime.graph_bridges import DialogueBridge
        self.dialogue = DialogueBridge(self._ctx)
        if dialogue_dock:
            self.dialogue.attach_dock(dialogue_dock)

        # 6. Material Graph Bridge (Sprint 4c)
        from editor.runtime.graph_bridges import MaterialGraphBridge
        self.material_graph = MaterialGraphBridge(self._ctx)
        if material_dock:
            self.material_graph.attach_dock(material_dock)

    # ── Convenience API ───────────────────────────────────────────────────────

    def select(self, obj: Any, context: str = "scene") -> None:
        """Seleciona um objeto propagando para todos os painéis."""
        if self.reactive:
            self.reactive.select(obj, context=context)

    def open_animation(self, path: str | None = None, data: Any = None) -> Any:
        if self.animation:
            return self.animation.open_animation_document(path=path, data=data)
        return None

    def open_visual_script(self, path: str | None = None, data: Any = None) -> Any:
        if self.visual_scripting:
            return self.visual_scripting.open_script_document(path=path, data=data)
        return None

    def open_behavior_tree(self, path: str | None = None, data: Any = None) -> Any:
        if self.behavior_tree:
            return self.behavior_tree.open_document(path=path, data=data)
        return None

    def open_dialogue(self, path: str | None = None, data: Any = None) -> Any:
        if self.dialogue:
            return self.dialogue.open_document(path=path, data=data)
        return None

    def open_material(self, path: str | None = None, data: Any = None) -> Any:
        if self.material_graph:
            return self.material_graph.open_document(path=path, data=data)
        return None

    def activate(self, tool_id: str) -> None:
        """Ativa qualquer ferramenta pelo ID via ToolRegistry."""
        try:
            from editor.workspace.tool_registry import ToolRegistry
            ToolRegistry.instance().activate(tool_id)
        except Exception:
            pass

    def activate_animation_studio(self) -> None:
        self.activate("animation.studio")

    def activate_visual_scripting(self) -> None:
        self.activate("visual_scripting.editor")

    def activate_behavior_tree(self) -> None:
        self.activate("behavior_tree")

    def activate_dialogue(self) -> None:
        self.activate("dialogue")

    def activate_material_graph(self) -> None:
        self.activate("material_graph")
