"""Graph Registry — central registry for NodeDefinitions.

Expõe:
  - register_node()  decorator para declarar nós
  - GraphRegistry    classe singleton para busca de nós

Os nós são armazenados em NodeDefinition.__registry__ (dict[id → NodeDefinition]).
O decorator register_node() popula esse dict ao ser aplicado.
"""
from __future__ import annotations
from typing import Optional
from engine.core.metadata import NodeDefinition


# ─────────────────────────────────────────────────────────────────────────────
#  register_node decorator
# ─────────────────────────────────────────────────────────────────────────────

def register_node(**kwargs):
    """Decorator that creates a NodeDefinition and registers it globally."""
    def decorator(cls):
        kw = dict(kwargs)
        # Backwards compatibility: accept plain strings for name/category/description
        if "name" in kw:
            kw["name_key"] = kw.pop("name")
        if "category" in kw:
            kw["category_key"] = kw.pop("category")
        if "description" in kw:
            kw.setdefault("description_key", kw.pop("description"))

        definition = NodeDefinition(**kw)
        definition.runtime_class = cls

        # Attach to class for introspection
        cls.__node_definition__ = definition

        # Register in global dict
        _NODE_REGISTRY[str(definition.id)] = definition
        return cls

    return decorator


# ─────────────────────────────────────────────────────────────────────────────
#  Internal registry dict
# ─────────────────────────────────────────────────────────────────────────────
_NODE_REGISTRY: dict[str, "NodeDefinition"] = {}


# ─────────────────────────────────────────────────────────────────────────────
#  GraphRegistry — singleton façade used by GraphCanvas and GenericGraphEditor
# ─────────────────────────────────────────────────────────────────────────────

class GraphRegistry:
    """Global registry for all registered NodeDefinitions."""

    @classmethod
    def get_node(cls, node_id: str) -> Optional["NodeDefinition"]:
        """Return the NodeDefinition for the given id, or None."""
        return _NODE_REGISTRY.get(str(node_id))

    @classmethod
    def list_nodes(cls) -> list["NodeDefinition"]:
        """Return all registered NodeDefinitions."""
        return list(_NODE_REGISTRY.values())

    @classmethod
    def has_node(cls, node_id: str) -> bool:
        return str(node_id) in _NODE_REGISTRY

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        _NODE_REGISTRY.clear()


__all__ = ["register_node", "GraphRegistry"]
