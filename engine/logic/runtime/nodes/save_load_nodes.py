"""Nós de Save/Load para Logic Graph - Persistência 100% visual."""
from __future__ import annotations

import json
from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('save_game')
def execute_save_game(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Salva o jogo em um arquivo."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1"))
        include_scene = bool(properties.get("include_scene", True))

        if not hasattr(runtime, "_save_slots"):
            runtime._save_slots = {}

        save_data = {
            "scene": game.current_scene if (include_scene and hasattr(game, "current_scene")) else None,
            "variables": dict(runtime._variables) if hasattr(runtime, "_variables") else {},
            "state_machines": dict(runtime._state_machines) if hasattr(runtime, "_state_machines") else {},
            "timestamp": str(__import__('datetime').datetime.now())
        }

        runtime._save_slots[slot_name] = save_data
        runtime._store(node_id, "slot_name", slot_name)
        runtime._store(node_id, "saved", True)

        # Também salvar em arquivo JSON (opcional)
        if hasattr(game, "save_path"):
            import os
            os.makedirs(game.save_path, exist_ok=True)
            with open(f"{game.save_path}/{slot_name}.json", "w") as f:
                json.dump(save_data, f, indent=2)

        return ["exec_saved"]
    except Exception as e:
        print(f"Erro em save_game: {e}")
        return ["exec_failure"]


@registry.register_executor('load_game')
def execute_load_game(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Carrega o jogo de um arquivo."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1"))

        if not hasattr(runtime, "_save_slots"):
            return ["exec_no_save"]

        if slot_name not in runtime._save_slots:
            # Tentar carregar de arquivo
            if hasattr(game, "save_path"):
                try:
                    with open(f"{game.save_path}/{slot_name}.json", "r") as f:
                        save_data = json.load(f)
                except:
                    return ["exec_no_save"]
            else:
                return ["exec_no_save"]
        else:
            save_data = runtime._save_slots[slot_name]

        # Restaurar variáveis
        if "variables" in save_data:
            if not hasattr(runtime, "_variables"):
                runtime._variables = {}
            runtime._variables.update(save_data["variables"])

        # Restaurar state machines
        if "state_machines" in save_data:
            if not hasattr(runtime, "_state_machines"):
                runtime._state_machines = {}
            runtime._state_machines.update(save_data["state_machines"])

        # Restaurar cena (se necessário)
        if save_data.get("scene") and hasattr(game, "load_scene"):
            game.load_scene(save_data["scene"])

        runtime._store(node_id, "slot_name", slot_name)
        runtime._store(node_id, "loaded", True)

        return ["exec_loaded"]
    except Exception as e:
        print(f"Erro em load_game: {e}")
        return ["exec_failure"]


@registry.register_executor('delete_save')
def execute_delete_save(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Deleta um save slot."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1"))

        if hasattr(runtime, "_save_slots") and slot_name in runtime._save_slots:
            del runtime._save_slots[slot_name]

        # Deletar arquivo também
        if hasattr(game, "save_path"):
            import os
            try:
                os.remove(f"{game.save_path}/{slot_name}.json")
            except:
                pass

        return ["exec_deleted"]
    except Exception as e:
        print(f"Erro em delete_save: {e}")
        return ["exec_failure"]


@registry.register_executor('has_save')
def execute_has_save(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Verifica se um save slot existe."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        slot_name = str(properties.get("slot_name", "save_slot_1"))

        has_save = False
        if hasattr(runtime, "_save_slots"):
            has_save = slot_name in runtime._save_slots

        if not has_save and hasattr(game, "save_path"):
            import os
            has_save = os.path.exists(f"{game.save_path}/{slot_name}.json")

        if has_save:
            return ["exec_exists"]
        else:
            return ["exec_not_exists"]
    except Exception as e:
        print(f"Erro em has_save: {e}")
        return ["exec_failure"]
