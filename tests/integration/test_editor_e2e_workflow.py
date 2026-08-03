"""Testes de Integração End-to-End (E2E Integration Flow) do Zennity Studio.

Valida o fluxo de trabalho completo do usuário através de múltiplos subsistemas:
  - Fluxo 1: Open Project -> Select Object -> Edit Property -> Undo -> Redo -> Save Snapshot -> Reopen -> Verify Consistency
  - Fluxo 2: Cross-Workspace Navigation (Hierarchy -> Animation Studio -> Material Graph -> Scene View) sem perda de seleção ou vazamento de estado.
"""
from __future__ import annotations

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


class FakeGameObject:
    def __init__(self, name: str = "Player"):
        self.name = name
        self.active = True
        self.id = f"id_{name.lower()}"
        self.tag = "Untagged"
        self.layer = "Default"
        self.position = [0.0, 0.0, 0.0]
        self.components = []


def test_e2e_project_lifecycle_undo_redo_save_reopen(tmp_path):
    """Fluxo E2E 1: Edição no Inspector -> Undo -> Redo -> Persistência de Snapshot -> Recarregamento."""
    from editor.runtime.editor_context import EditorContext
    from editor.runtime.command_manager import CommandManager
    from editor.premium_inspector_panel import RealInspectorPanel
    from editor.core.event_bus import EventBus, EVENT_OBJECT_MODIFIED
    from editor.workspace.document_framework import DocumentManager, DocumentType

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    # 1. Inicializa o Contexto do Editor e o Gerenciador de Comandos
    ctx = EditorContext()
    cm = CommandManager()
    inspector = RealInspectorPanel()
    inspector.set_command_manager(cm)

    # 2. Instancia objeto de teste e carrega no Inspector via SelectionService
    player = FakeGameObject("HeroPlayer")
    ctx.selection.select_item(player, type="game_object", context="scene")
    inspector.load_object(player)

    assert inspector.current_object is player
    assert player.name == "HeroPlayer"

    # 3. Altera a propriedade no Inspector usando PropertyBindingGroup
    events_log = []
    EventBus.subscribe(EVENT_OBJECT_MODIFIED, lambda **kw: events_log.append(kw))

    inspector.binding_group.set("name", "UltraHero")
    assert player.name == "UltraHero"
    assert cm.can_undo

    # 4. Executa Undo (Desfazer)
    cm.undo()
    assert player.name == "HeroPlayer"

    # 5. Executa Redo (Refazer)
    cm.redo()
    assert player.name == "UltraHero"

    # 6. Simula Salvamento do Documento da Cena (.zscene) no disco
    doc_mgr = DocumentManager()
    DocumentManager._instance = doc_mgr
    scene_file = tmp_path / "MainScene.zscene"

    data_payload = {"objects": [{"name": player.name, "active": player.active}]}
    doc = doc_mgr.open(DocumentType.SCENE, path=scene_file, data=data_payload)
    
    # Gravando no disco
    with open(scene_file, "w", encoding="utf-8") as f:
        json.dump(data_payload, f)
    doc.mark_saved(scene_file)

    assert scene_file.exists()
    assert not doc.is_modified

    # 7. Recarrega a partir do disco e verifica paridade de dados
    with open(scene_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)

    reloaded_doc = doc_mgr.open(DocumentType.SCENE, path=scene_file, data=loaded_data)
    assert reloaded_doc.data["objects"][0]["name"] == "UltraHero"

    DocumentManager._instance = None


def test_e2e_cross_workspace_multi_tool_navigation():
    """Fluxo E2E 2: Navegação entre múltiplos workspaces e editores preservando estado de seleção e documentos."""
    from editor.runtime.editor_context import EditorContext
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.document_framework import DocumentManager, DocumentType
    from editor.workspace.tool_registry import ToolRegistry

    doc_mgr = DocumentManager()
    DocumentManager._instance = doc_mgr

    # 1. Inicializa Orquestrador do Editor Framework 2.0
    ctx = EditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    # 2. Seleciona um objeto no contexto de cena principal
    character = FakeGameObject("MainCharacter")
    orchestrator.select(character, context="hierarchy")

    assert ctx.selection.current_item.payload is character

    # 3. Navega para o Workspace de Animação e abre documento de animação
    anim_doc = orchestrator.open_animation(path="anims/walk.zanim")
    orchestrator.activate_animation_studio()

    assert anim_doc is not None
    assert anim_doc.doc_type == DocumentType.ANIMATION
    assert ToolRegistry.instance().active_tool.id == "animation.studio"

    # 4. Navega para o Workspace de Material Graph e abre documento de material
    mat_doc = orchestrator.open_material(path="materials/skin.zmat")
    orchestrator.activate_material_graph()

    assert mat_doc is not None
    assert mat_doc.doc_type == DocumentType.MATERIAL
    assert ToolRegistry.instance().active_tool.id == "material_graph"

    # 5. Retorna para o workspace principal da Scene View e valida preservação de estado
    orchestrator.activate_visual_scripting()
    assert ctx.selection.current_item.payload is character
    assert len(doc_mgr.all_documents) == 2

    DocumentManager._instance = None
