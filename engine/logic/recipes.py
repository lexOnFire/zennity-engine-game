"""Educational and reusable recipes for the Visual Logic Graph editor."""
from __future__ import annotations

import unicodedata
import uuid
from copy import deepcopy
from typing import Any, Mapping

from .graph_asset import create_logic_node
from .recipe_catalog import LOGIC_RECIPES


def _search_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def find_logic_recipes(query: str = "", topic: str = "") -> list[dict[str, Any]]:
    """Search recipes by simple query matching title, category, keywords, and steps."""
    wanted = _search_key(query).strip()
    result: list[dict[str, Any]] = []
    for recipe in LOGIC_RECIPES:
        if topic and topic not in recipe.get("topics", ()):
            continue
        searchable = _search_key(" ".join((
            str(recipe.get("title", "")), str(recipe.get("category", "")),
            str(recipe.get("summary", "")), str(recipe.get("keywords", "")),
            " ".join(str(step) for step in recipe.get("steps", ())),
        )))
        if not wanted or all(term in searchable for term in wanted.split()):
            result.append(deepcopy(recipe))
    return result


def build_logic_recipe(recipe_id: str, origin: tuple[float, float] = (0.0, 0.0)) -> dict[str, list[dict[str, Any]]]:
    """Materializes a recipe as an independent fragment of nodes and edges."""
    recipe = next((entry for entry in LOGIC_RECIPES if entry["id"] == recipe_id), None)
    if recipe is None:
        raise KeyError(f"Unknown Logic Graph recipe: {recipe_id}")
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
    """Returns the metadata of a recipe without allowing global mutation."""
    recipe = next((entry for entry in LOGIC_RECIPES if entry["id"] == recipe_id), None)
    if recipe is None:
        raise KeyError(f"Unknown Logic Graph recipe: {recipe_id}")
    return deepcopy(recipe)
