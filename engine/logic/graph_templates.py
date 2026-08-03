"""Guided templates for creating canonical ``.zlogic`` documents."""

from __future__ import annotations

from typing import Any

from .graph_asset import default_logic_graph, merge_logic_fragment
from .recipes import build_logic_recipe


GRAPH_TEMPLATES: dict[str, dict[str, str]] = {
    "empty": {
        "title": "Grafo vazio",
        "description": "Documento limpo para montar a lógica manualmente.",
        "recipe": "",
    },
    "movement_2d": {
        "title": "Movimento 2D",
        "description": "Movimento contínuo no eixo X, pronto para editar.",
        "recipe": "move_x_every_frame",
    },
    "platformer": {
        "title": "Plataforma",
        "description": "Entrada de pulo pela tecla Espaço.",
        "recipe": "jump_with_space",
    },
    "enemy": {
        "title": "Inimigo / Patrulha",
        "description": "Patrulha horizontal entre limites configuráveis.",
        "recipe": "patrol_x_between_limits",
    },
    "interaction": {
        "title": "Interação",
        "description": "Fluxo condicional editável para interação.",
        "recipe": "if_else_example",
    },
    "ui": {
        "title": "Interface / HUD",
        "description": "Exibe a posição X do objeto no HUD.",
        "recipe": "show_x_on_hud",
    },
}


def build_logic_template(template_id: str, name: str = "NewLogic") -> dict[str, Any]:
    """Create a normalized graph from a registered guided template."""
    template = GRAPH_TEMPLATES.get(str(template_id), GRAPH_TEMPLATES["empty"])
    graph = default_logic_graph(name)
    recipe_id = template["recipe"]
    if not recipe_id:
        return graph
    fragment = build_logic_recipe(recipe_id, (80.0, 100.0))
    graph, _reused = merge_logic_fragment(graph, fragment)
    graph["name"] = str(name).strip() or "NewLogic"
    graph.setdefault("editor", {})["template"] = str(template_id)
    return graph


__all__ = ["GRAPH_TEMPLATES", "build_logic_template"]
