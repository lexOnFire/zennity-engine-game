"""Receitas didáticas e reutilizáveis para o editor de Lógica Visual."""
from __future__ import annotations

import unicodedata
import uuid
from copy import deepcopy
from typing import Any, Mapping

from .graph_asset import create_logic_node


LOGIC_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "move_x_every_frame",
        "title": "Mover sozinho no eixo X",
        "category": "Posição e movimento",
        "summary": "Move o objeto continuamente para a direita, sem precisar apertar teclas.",
        "keywords": "mover andar sozinho automático x direita cada frame velocidade",
        "steps": (
            "A cada frame inicia o fluxo continuamente.",
            "Mover continuamente acrescenta 120 unidades por segundo no eixo X.",
            "Use um valor negativo em X para mover para a esquerda.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "move", "type": "move_by", "position": (270.0, 0.0), "properties": {"x": 120.0, "y": 0.0}},
        ),
        "edges": (("update", "next", "move", "in", "flow"),),
    },
    {
        "id": "move_y_every_frame",
        "title": "Mover sozinho no eixo Y",
        "category": "Posição e movimento",
        "summary": "Move o objeto continuamente para baixo sem usar o teclado.",
        "keywords": "mover andar sozinho automático y baixo cima cada frame velocidade",
        "steps": (
            "A cada frame executa o movimento.",
            "Mover continuamente acrescenta 120 unidades por segundo no eixo Y.",
            "Use um valor negativo em Y para mover para cima.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "move", "type": "move_by", "position": (270.0, 0.0), "properties": {"x": 0.0, "y": 120.0}},
        ),
        "edges": (("update", "next", "move", "in", "flow"),),
    },
    {
        "id": "set_initial_position",
        "title": "Definir posição ao iniciar",
        "category": "Posição e movimento",
        "summary": "Coloca o objeto em uma coordenada específica quando o Play começa.",
        "keywords": "posição inicial começar spawn teleporte x y ao iniciar",
        "steps": (
            "Ao iniciar executa somente uma vez.",
            "Definir posição troca imediatamente as coordenadas X e Y.",
            "Edite X e Y nas propriedades do bloco.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "position", "type": "set_position", "position": (270.0, 0.0), "properties": {"x": 100.0, "y": 100.0}},
        ),
        "edges": (("start", "next", "position", "in", "flow"),),
    },
    {
        "id": "show_x_on_hud",
        "title": "Mostrar posição X no HUD",
        "category": "Posição e movimento",
        "summary": "Lê a posição atual do objeto e mostra o valor X na interface durante o Play.",
        "keywords": "ler posição coordenada x hud texto debug mostrar",
        "steps": (
            "A cada frame atualiza o texto.",
            "Ler posição fornece as coordenadas atuais do objeto.",
            "Converter para texto transforma X em texto e Atualizar HUD o exibe.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "position", "type": "get_position", "position": (0.0, 180.0)},
            {"key": "text", "type": "to_text", "position": (270.0, 180.0)},
            {"key": "hud", "type": "set_hud", "position": (540.0, 0.0)},
        ),
        "edges": (
            ("update", "next", "hud", "in", "flow"),
            ("position", "x", "text", "value", "number"),
            ("text", "value", "hud", "text", "text"),
        ),
    },
)


def _search_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def find_logic_recipes(query: str = "") -> list[dict[str, Any]]:
    """Pesquisa receitas por linguagem simples, título, categoria e passos."""
    wanted = _search_key(query).strip()
    result: list[dict[str, Any]] = []
    for recipe in LOGIC_RECIPES:
        searchable = _search_key(" ".join((
            str(recipe.get("title", "")), str(recipe.get("category", "")),
            str(recipe.get("summary", "")), str(recipe.get("keywords", "")),
            " ".join(str(step) for step in recipe.get("steps", ())),
        )))
        if not wanted or all(term in searchable for term in wanted.split()):
            result.append(deepcopy(recipe))
    return result


def build_logic_recipe(recipe_id: str, origin: tuple[float, float] = (0.0, 0.0)) -> dict[str, list[dict[str, Any]]]:
    """Materializa uma receita como fragmento independente de nós e conexões."""
    recipe = next((entry for entry in LOGIC_RECIPES if entry["id"] == recipe_id), None)
    if recipe is None:
        raise KeyError(f"Receita de Logic Graph desconhecida: {recipe_id}")
    nodes: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for specification in recipe["nodes"]:
        position = specification.get("position", (0.0, 0.0))
        node = create_logic_node(
            str(specification["type"]),
            (float(origin[0]) + float(position[0]), float(origin[1]) + float(position[1])),
        )
        node["properties"].update(deepcopy(specification.get("properties", {})))
        nodes.append(node)
        by_key[str(specification["key"])] = node
    edges = [{
        "id": uuid.uuid4().hex,
        "from_node": by_key[source]["id"], "from_port": from_port,
        "to_node": by_key[target]["id"], "to_port": to_port,
        "kind": kind,
    } for source, from_port, target, to_port, kind in recipe["edges"]]
    return {"nodes": nodes, "edges": edges}


def logic_recipe(recipe_id: str) -> Mapping[str, Any]:
    """Retorna os metadados de uma receita sem permitir mutação global."""
    recipe = next((entry for entry in LOGIC_RECIPES if entry["id"] == recipe_id), None)
    if recipe is None:
        raise KeyError(f"Receita de Logic Graph desconhecida: {recipe_id}")
    return deepcopy(recipe)
