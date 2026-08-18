"""Nós de Save/Load para Logic Graph - Persistência 100% visual via SaveManager."""
from __future__ import annotations

from typing import Any, Mapping
from engine.core.save_manager import SaveManager
from ..registry import registry


def _resolve_save_manager(runtime: Any, game: Any) -> SaveManager:
    """Obtém o SaveManager canônico a partir do game, runtime ou instância padrão."""
    if hasattr(game, "save_manager") and isinstance(game.save_manager, SaveManager):
        return game.save_manager
    if hasattr(runtime, "_save_manager") and isinstance(runtime._save_manager, SaveManager):
        return runtime._save_manager
    save_dir = getattr(game, "save_path", None) or getattr(runtime, "_save_directory", None)
    sm = SaveManager(save_directory=save_dir)
    if not hasattr(runtime, "_save_manager"):
        runtime._save_manager = sm
    return sm


@registry.register_executor('save_game')
def execute_save_game(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Salva o jogo em um arquivo persistente via SaveManager."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1")).strip()
        include_scene = bool(properties.get("include_scene", True))

        if not slot_name:
            return ["exec_failure"]

        save_mgr = _resolve_save_manager(runtime, game)

        scene_name = None
        if include_scene:
            if hasattr(game, "current_scene") and getattr(game.current_scene, "name", None):
                scene_name = game.current_scene.name
            elif hasattr(game, "scene") and getattr(game.scene, "name", None):
                scene_name = game.scene.name

        project_vars = dict(runtime._variables) if hasattr(runtime, "_variables") else {}
        state_machines = dict(runtime._state_machines) if hasattr(runtime, "_state_machines") else {}

        ok = save_mgr.save_game(
            slot_name=slot_name,
            project_variables=project_vars,
            scene_name=scene_name,
            object_state={"state_machines": state_machines} if state_machines else None,
        )

        if ok:
            # Mantém cache em runtime para compatibilidade de sessão
            if not hasattr(runtime, "_save_slots"):
                runtime._save_slots = {}
            runtime._save_slots[slot_name] = {
                "scene": scene_name,
                "variables": project_vars,
                "state_machines": state_machines,
            }
            runtime._store(node_id, "slot_name", slot_name)
            runtime._store(node_id, "saved", True)
            return ["exec_saved"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em save_game: {e}")
        return ["exec_failure"]


@registry.register_executor('load_game')
def execute_load_game(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Carrega o jogo a partir de um arquivo persistente via SaveManager."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1")).strip()

        if not slot_name:
            return ["exec_no_save"]

        save_mgr = _resolve_save_manager(runtime, game)
        exists_on_disk = save_mgr.save_exists(slot_name) if hasattr(save_mgr, "save_exists") else False

        save_data = save_mgr.load_game(slot_name)

        if save_data is None:
            # Se o arquivo existia no disco mas load_game retornou None -> falha de integridade/schema
            if exists_on_disk:
                return ["exec_failure"]

            # Fallback temporário para cache de sessão in-memory se existir
            if hasattr(runtime, "_save_slots") and slot_name in runtime._save_slots:
                save_data = runtime._save_slots[slot_name]
            else:
                return ["exec_no_save"]

        # Restaura variáveis de projeto no escopo do runtime
        loaded_vars = save_data.get("project_variables") or save_data.get("variables")
        if isinstance(loaded_vars, dict):
            if not hasattr(runtime, "_variables"):
                runtime._variables = {}
            runtime._variables.update(loaded_vars)

        # Restaura máquinas de estado
        obj_state = save_data.get("object_state") or {}
        loaded_sm = obj_state.get("state_machines") or save_data.get("state_machines")
        if isinstance(loaded_sm, dict):
            if not hasattr(runtime, "_state_machines"):
                runtime._state_machines = {}
            runtime._state_machines.update(loaded_sm)

        # Restaura cena se especificado e suportado pelo host
        scene_name = save_data.get("scene")
        if scene_name and hasattr(game, "load_scene"):
            try:
                game.load_scene(scene_name)
            except Exception:
                pass

        runtime._store(node_id, "slot_name", slot_name)
        runtime._store(node_id, "loaded", True)

        return ["exec_loaded"]
    except Exception as e:
        print(f"Erro em load_game: {e}")
        return ["exec_failure"]


@registry.register_executor('has_save')
def execute_has_save(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Verifica se um save slot existe via SaveManager."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1")).strip()
        if not slot_name:
            return ["exec_not_exists"]

        save_mgr = _resolve_save_manager(runtime, game)
        exists = False
        if hasattr(save_mgr, "save_exists"):
            exists = save_mgr.save_exists(slot_name)
        elif hasattr(save_mgr, "has_save"):
            exists = save_mgr.has_save(slot_name)

        if not exists and hasattr(runtime, "_save_slots"):
            exists = slot_name in runtime._save_slots

        if exists:
            return ["exec_exists"]
        return ["exec_not_exists"]
    except Exception as e:
        print(f"Erro em has_save: {e}")
        return ["exec_failure"]


@registry.register_executor('delete_save')
def execute_delete_save(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Exclui um save slot via SaveManager."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1")).strip()
        if not slot_name:
            return ["exec_failure"]

        save_mgr = _resolve_save_manager(runtime, game)
        deleted = save_mgr.delete_save(slot_name)

        if hasattr(runtime, "_save_slots") and slot_name in runtime._save_slots:
            del runtime._save_slots[slot_name]
            deleted = True

        if deleted:
            return ["exec_deleted"]
        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em delete_save: {e}")
        return ["exec_failure"]
