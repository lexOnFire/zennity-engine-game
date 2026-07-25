"""EventBus do Editor — com suporte a Event Domains.

Domains disponíveis:
  Scene.*        — criação, deleção, modificação de objetos de cena
  Selection.*    — mudanças de seleção em qualquer editor
  Workspace.*    — troca de layout, abertura de docks
  Animation.*    — keyframes, tracks, playback
  Graph.*        — nós de Visual Scripting, Behavior Tree, Dialogue, Material
  Build.*        — pipeline de build, empacotamento, exportação
  Runtime.*      — play/pause/stop, estado de simulação

Usar domínios em vez de strings planas facilita o debugging:
  EventBus.emit("Selection.changed", item=sel_item)
  EventBus.subscribe("Selection.*", handler)
"""
from __future__ import annotations

import re
from typing import Any, Callable

from engine.event_bus import EventBus as _EngineEventBus

# Re-exporta o EventBus da engine para compatibilidade
EventBus = _EngineEventBus

# ── Event Domain Constants ─────────────────────────────────────────────────────

# Scene Domain
EVENT_SCENE_OPENED          = "Scene.opened"
EVENT_SCENE_CLOSED          = "Scene.closed"
EVENT_SCENE_SAVED           = "Scene.saved"
EVENT_OBJECT_CREATED        = "Scene.object_created"
EVENT_OBJECT_DELETED        = "Scene.object_deleted"
EVENT_OBJECT_MODIFIED       = "Scene.object_modified"
EVENT_HIERARCHY_UPDATED     = "Scene.hierarchy_updated"

# Selection Domain
EVENT_SELECTION_CHANGED     = "Selection.changed"
EVENT_SELECTION_CLEARED     = "Selection.cleared"
EVENT_SELECTION_MULTI       = "Selection.multi_changed"

# Workspace Domain
EVENT_WORKSPACE_CHANGED     = "Workspace.changed"
EVENT_PANEL_OPENED          = "Workspace.panel_opened"
EVENT_PANEL_CLOSED          = "Workspace.panel_closed"
EVENT_LAYOUT_SAVED          = "Workspace.layout_saved"
EVENT_LAYOUT_RESTORED       = "Workspace.layout_restored"

# Animation Domain
EVENT_ANIMATION_KEYFRAME    = "Animation.keyframe_changed"
EVENT_ANIMATION_TRACK       = "Animation.track_changed"
EVENT_ANIMATION_PLAYBACK    = "Animation.playback_changed"

# Graph Domain
EVENT_GRAPH_NODE_SELECTED   = "Graph.node_selected"
EVENT_GRAPH_NODE_ADDED      = "Graph.node_added"
EVENT_GRAPH_NODE_DELETED    = "Graph.node_deleted"
EVENT_GRAPH_EDGE_ADDED      = "Graph.edge_added"

# Build Domain
EVENT_BUILD_STARTED         = "Build.started"
EVENT_BUILD_STAGE           = "Build.stage_changed"
EVENT_BUILD_COMPLETED       = "Build.completed"
EVENT_BUILD_FAILED          = "Build.failed"

# Runtime Domain
EVENT_PLAY_STATE_CHANGED    = "Runtime.play_state"
EVENT_RUNTIME_LOG           = "Runtime.log"

# Legacy aliases (compatibilidade com código existente)
EVENT_PROPERTY_CHANGED      = "editor.property_changed"
EVENT_ASSET_SELECTED        = "editor.asset_selected"
EVENT_LOG_ADDED             = "editor.log_added"


def subscribe_domain(domain_prefix: str, handler: Callable[..., Any]) -> None:
    """Subscreve em todos os eventos de um domínio usando prefixo glob.

    Exemplo:
        subscribe_domain("Selection.*", on_selection_event)
        subscribe_domain("Scene.*", on_scene_event)
    """
    pattern = re.compile("^" + re.escape(domain_prefix.rstrip("*")) + ".*")

    def _dispatch(**kwargs: Any) -> None:
        # O EventBus da engine não passa o nome do evento, então usamos um wrapper
        try:
            handler(**kwargs)
        except Exception as exc:
            import traceback
            traceback.print_exc()

    # Registra nos eventos conhecidos que correspondam ao padrão
    all_events = [
        EVENT_SCENE_OPENED, EVENT_SCENE_CLOSED, EVENT_SCENE_SAVED,
        EVENT_OBJECT_CREATED, EVENT_OBJECT_DELETED, EVENT_OBJECT_MODIFIED,
        EVENT_HIERARCHY_UPDATED,
        EVENT_SELECTION_CHANGED, EVENT_SELECTION_CLEARED, EVENT_SELECTION_MULTI,
        EVENT_WORKSPACE_CHANGED, EVENT_PANEL_OPENED, EVENT_PANEL_CLOSED,
        EVENT_LAYOUT_SAVED, EVENT_LAYOUT_RESTORED,
        EVENT_ANIMATION_KEYFRAME, EVENT_ANIMATION_TRACK, EVENT_ANIMATION_PLAYBACK,
        EVENT_GRAPH_NODE_SELECTED, EVENT_GRAPH_NODE_ADDED, EVENT_GRAPH_NODE_DELETED,
        EVENT_GRAPH_EDGE_ADDED,
        EVENT_BUILD_STARTED, EVENT_BUILD_STAGE, EVENT_BUILD_COMPLETED, EVENT_BUILD_FAILED,
        EVENT_PLAY_STATE_CHANGED, EVENT_RUNTIME_LOG,
    ]
    for event_name in all_events:
        if pattern.match(event_name):
            EventBus.subscribe(event_name, _dispatch)
