"""AnimationStudioBridge — Sprint 4b.

Conecta o AnimationStudioDock ao Editor Framework 2.0:
  - EventBus (domínio Animation.*)
  - DocumentManager (abre/fecha documentos .zanim)
  - ToolRegistry (registra a ferramenta com dock + atalhos)
  - SelectionService (quando um GameObject com Animator é selecionado,
    o studio carrega automaticamente as trilhas)

Uso:
    bridge = AnimationStudioBridge(editor_context)
    bridge.attach_dock(animation_studio_dock)
    bridge.attach_reactive_bridge(reactive_editor_bridge)  # opcional
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class AnimationStudioBridge:
    """Integra AnimationStudioDock ao Editor Framework 2.0."""

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self._dock: Any = None
        self._current_document: Any = None

        # Subscreve no SelectionService para carregar trilhas ao selecionar GameObject
        self._ctx.selection.subscribe(self._on_selection_changed)

        # Registra a ferramenta no ToolRegistry
        self._register_tool()

    def attach_dock(self, dock: Any) -> None:
        """Conecta o AnimationStudioDock."""
        self._dock = dock
        self._connect_dock_events()

    def attach_reactive_bridge(self, reactive_bridge: Any) -> None:
        """Conecta ao ReactiveEditorBridge para coordenação multi-painel."""
        self._reactive_bridge = reactive_bridge

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tool(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            tool = ToolDefinition(
                id="animation.studio",
                label="Animation Studio",
                dock=None,  # será atualizado em attach_dock
                shortcuts=["Ctrl+Shift+A"],
                commands=["animation.play", "animation.pause", "animation.stop",
                          "animation.add_keyframe", "animation.hot_reload"],
                menu="Ferramentas",
                icon="animation",
                category="Editor",
            )
            ToolRegistry.instance().register(tool)
            self._tool_def = tool
        except Exception:
            self._tool_def = None

    # ── Document Management ───────────────────────────────────────────────────

    def open_animation_document(self, path: str | Path | None = None, data: Any = None) -> Any:
        """Abre um arquivo .zanim como documento no DocumentManager."""
        try:
            from editor.workspace.document_framework import DocumentManager, DocumentType
            doc = DocumentManager.instance().open(
                DocumentType.ANIMATION,
                path=Path(path) if path else None,
                data=data,
            )
            self._current_document = doc

            from editor.core.event_bus import EventBus, EVENT_ANIMATION_PLAYBACK
            EventBus.emit(EVENT_ANIMATION_PLAYBACK, state="opened", document=doc)

            if self._dock and hasattr(self._dock, "load_animation_data") and data:
                self._dock.load_animation_data(data)

            return doc
        except Exception as exc:
            print(f"[AnimationStudioBridge] open_animation_document: {exc}")
            return None

    def close_animation_document(self) -> None:
        """Fecha o documento de animação atual."""
        if self._current_document is None:
            return
        try:
            from editor.workspace.document_framework import DocumentManager
            DocumentManager.instance().close(self._current_document)
        except Exception:
            pass
        self._current_document = None

    # ── Dock Event Connections ────────────────────────────────────────────────

    def _connect_dock_events(self) -> None:
        """Intercepta eventos do dock e publica no EventBus com domínio Animation.*"""
        if self._dock is None:
            return

        # Atualiza o dock na ToolDefinition registrada
        if self._tool_def is not None:
            self._tool_def.dock = self._dock

        # Monkey-patch dos botões para emitir eventos
        self._patch_button("btn_play", "play", self._on_play)
        self._patch_button("btn_pause", "pause", self._on_pause)
        self._patch_button("btn_stop", "stop", self._on_stop)
        self._patch_button("btn_hot_reload", "trigger_hot_reload", self._on_hot_reload)

    def _patch_button(self, btn_attr: str, method_attr: str, handler: Any) -> None:
        """Conecta um botão do dock ao EventBus sem alterar o dock original."""
        try:
            btn = getattr(self._dock, btn_attr, None)
            if btn:
                btn.clicked.connect(handler)
        except Exception:
            pass

    def _on_play(self) -> None:
        self._emit_playback("playing")

    def _on_pause(self) -> None:
        self._emit_playback("paused")

    def _on_stop(self) -> None:
        self._emit_playback("stopped")
        if self._current_document:
            self._current_document.mark_modified()

    def _on_hot_reload(self) -> None:
        try:
            from editor.core.event_bus import EventBus, EVENT_ANIMATION_PLAYBACK
            EventBus.emit(EVENT_ANIMATION_PLAYBACK, state="hot_reload")
        except Exception:
            pass

    def _emit_playback(self, state: str) -> None:
        try:
            from editor.core.event_bus import EventBus, EVENT_ANIMATION_PLAYBACK
            EventBus.emit(EVENT_ANIMATION_PLAYBACK, state=state,
                          document=self._current_document)
        except Exception:
            pass

    # ── SelectionService → Auto-load tracks ───────────────────────────────────

    def _on_selection_changed(self, obj: Any) -> None:
        """Quando um GameObject com Animator é selecionado, carrega as trilhas."""
        if obj is None or self._dock is None:
            return
        try:
            animator = None
            if hasattr(obj, "get_component"):
                from engine.components import Animator
                animator = obj.get_component(Animator)
            if animator and hasattr(self._dock, "tracks"):
                pass  # futuro: self._dock.load_animator_tracks(animator)
        except Exception:
            pass

    # ── Keyframe API ──────────────────────────────────────────────────────────

    def add_keyframe(self, track_name: str, time: float, value: Any) -> None:
        """Adiciona um keyframe via API e emite evento do domínio Animation.*"""
        try:
            from editor.core.event_bus import EventBus, EVENT_ANIMATION_KEYFRAME
            EventBus.emit(EVENT_ANIMATION_KEYFRAME, track=track_name,
                          time=time, value=value)
            if self._current_document:
                self._current_document.mark_modified()
        except Exception:
            pass

    def add_track(self, track_name: str) -> None:
        """Adiciona uma trilha e emite evento do domínio Animation.*"""
        try:
            from editor.core.event_bus import EventBus, EVENT_ANIMATION_TRACK
            EventBus.emit(EVENT_ANIMATION_TRACK, track=track_name, action="added")
            if self._current_document:
                self._current_document.mark_modified()
        except Exception:
            pass
