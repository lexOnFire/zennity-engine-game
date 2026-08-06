"""Agrupamento hierárquico de nós do Logic Graph para melhor descoberta."""

from __future__ import annotations
from typing import Dict, List

# Mapeamento: categoria_original → {subcategoria: [node_ids]}
NODE_GROUPS: Dict[str, Dict[str, List[str]]] = {
    "Movement": {
        "Contínuo": ["move", "continuous_motion", "update_continuous_motion", "add_force"],
        "Instantâneo": ["jump", "teleport", "set_position"],
        "Patrulha": ["patrol", "patrol_path"],
        "Resumir/Pausar": ["pause_motion", "resume_motion", "resume_continuous_motion"],
    },
    "Physics": {
        "Força": ["add_force", "add_velocity", "set_velocity"],
        "Colisão": ["on_collision"],
        "Sensor": ["check_collision", "overlap_check"],
    },
    "UI": {
        "Texto": ["set_ui_text"],
        "Valores": ["set_ui_progress_bar", "set_ui_value", "increment_ui", "decrement_ui"],
        "Diálogos": ["start_dialogue", "dialogue_choose"],
        "Animação": ["animate_ui_value", "animate_material"],
    },
    "Objects": {
        "Criar": ["create_object", "create_prefab", "clone_object"],
        "Remover": ["destroy_object"],
        "Propriedades": ["get_property", "set_property"],
    },
    "Animation": {
        "Controle": ["play_animation", "stop_animation", "pause_animation"],
        "Eventos": ["on_animation_finish", "on_animation_loop"],
    },
    "Logic": {
        "Comparação": ["compare_number", "compare_text", "equal"],
        "Booleano": ["and", "or", "not"],
        "Controle": ["branch", "switch", "cooldown"],
    },
    "Variables": {
        "Obter/Definir": ["get_variable", "set_variable"],
        "Incrementar": ["increment_variable", "decrement_variable"],
    },
    "Text": {
        "Manipulação": ["join_text", "text_from_number", "to_text"],
        "Buscar": ["substring", "text_length"],
    },
    "Math": {
        "Básico": ["add_number", "subtract_number", "multiply_number", "divide_number"],
        "Avançado": ["absolute_number", "clamp_number", "round_number", "random_number"],
    },
    "Audio": {
        "Reprodução": ["play_sound", "play_music"],
        "Controle": ["stop_sound", "set_volume"],
    },
    "Graphics": {
        "Câmera": ["set_camera_position", "camera_follow"],
        "Efeitos": ["set_color", "set_opacity", "animate_material"],
    },
    "Input": {
        "Teclado": ["on_key_press", "key_held"],
        "Mouse": ["on_mouse_click", "mouse_position"],
    },
    "Spawning": {
        "Criar": ["create_object", "create_prefab"],
        "Limite": ["spawn_limit"],
    },
    "Events": {
        "Eventos": ["on_trigger_enter", "on_trigger_exit", "on_collision"],
    },
    "Position": {
        "Posição": ["set_position", "get_position"],
        "Distância": ["distance_to"],
    },
    "Action": {
        "Cena": ["restart_scene", "load_scene"],
        "Esperar": ["wait_time"],
    },
}

def get_node_group_path(node_type: str) -> str:
    """Retorna o caminho hierárquico de um nó: 'Categoria/Subcategoria'."""
    for category, subcategories in NODE_GROUPS.items():
        for subcategory, nodes in subcategories.items():
            if node_type in nodes:
                return f"{category}/{subcategory}"
    return ""

def get_all_groups() -> Dict[str, Dict[str, List[str]]]:
    """Retorna todo o mapa de grupos."""
    return NODE_GROUPS
