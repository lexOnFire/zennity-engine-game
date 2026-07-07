from __future__ import annotations

import uuid
import warnings
from typing import Any

import numpy as np

from engine.core.component import Transform
from engine.core.component_registry import component_registry
from engine.game_object import GameObject


# ---------------------------------------------------------------------------
# Helpers de cópia profunda de valores
# ---------------------------------------------------------------------------

def _deep_copy_value(value: Any) -> Any:
    """Copia profunda de tipos primitivos e coleções simples."""
    if isinstance(value, np.ndarray):
        return value.copy()
    if isinstance(value, list):
        return [_deep_copy_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _deep_copy_value(v) for k, v in value.items()}
    if isinstance(value, set):
        return set(value)
    if isinstance(value, tuple):
        return tuple(_deep_copy_value(v) for v in value)
    # pygame.Color é mutável — copia para isolar
    try:
        import pygame
        if isinstance(value, pygame.Color):
            return pygame.Color(value.r, value.g, value.b, value.a)
    except Exception:
        pass
    # pathlib.Path é imutável mas vale manter o tipo correto
    from pathlib import Path
    if isinstance(value, Path):
        return Path(value)
    return value


def _copy_optional_attr(source: Any, target: Any, name: str) -> None:
    if hasattr(source, name):
        setattr(target, name, _deep_copy_value(getattr(source, name)))


# ---------------------------------------------------------------------------
# Clonagem de componentes
# ---------------------------------------------------------------------------

def _clone_component(component: Any) -> Any:
    """Clona um componente via serialize/deserialize ou fallback por tipo.

    Em caso de falha no serialize, cai no fallback com aviso explícito
    em vez de silenciar o erro.
    """
    clone: Any = None

    if hasattr(component, "serialize"):
        try:
            data = component.serialize()
            clone = component_registry.create(data)
        except Exception as exc:
            warnings.warn(
                f"[clone] serialize/create falhou para "
                f"{type(component).__name__}: {exc}. Usando fallback type().",
                RuntimeWarning,
                stacklevel=2,
            )
            clone = None

    if clone is None:
        try:
            clone = type(component)()
        except Exception as exc:
            warnings.warn(
                f"[clone] Não foi possível instanciar {type(component).__name__}: {exc}. "
                "Componente ignorado.",
                RuntimeWarning,
                stacklevel=2,
            )
            return None

    if clone is not None:
        if hasattr(clone, "id"):
            clone.id = str(uuid.uuid4())
        if hasattr(clone, "_started"):
            clone._started = False
        if hasattr(clone, "game_object"):
            clone.game_object = None

    return clone


# ---------------------------------------------------------------------------
# Clonagem de GameObjects
# ---------------------------------------------------------------------------

_CLONE_ATTRS = (
    "layer",
    "active",
    "enabled",
    "is_static",
    "mesh_type",
    "sprite_path",
    "asset_uuid",
    "color",
    "material",
    "prefab_uuid",
    "scripts",
    "script_path",
)


def clone_game_object(
    source: GameObject,
    _visited: set[str] | None = None,
) -> GameObject:
    """Cria uma cópia completamente desacoplada de um GameObject e seus filhos.

    - Sempre percorre toda a árvore de filhos, mesmo quando o pai está inativo.
    - Protege contra grafos circulares via _visited.
    - Componentes com clone None (falha dupla) são ignorados sem crash.
    """
    if _visited is None:
        _visited = set()

    source_id = str(getattr(source, "id", ""))
    if source_id in _visited:
        warnings.warn(
            f"[clone] Referência circular detectada em GameObject id={source_id}. "
            "Clonagem interrompida neste nó.",
            RuntimeWarning,
            stacklevel=2,
        )
        return GameObject(name="__circular_ref__")
    _visited.add(source_id)

    clone = GameObject(
        name=str(getattr(source, "name", "GameObject")),
        tag=str(getattr(source, "tag", "Untagged")),
    )
    clone.runtime_source_id = source_id

    for attr in _CLONE_ATTRS:
        _copy_optional_attr(source, clone, attr)

    # Transform — copia direta de arrays numpy
    clone.transform.position = np.array(
        source.transform.position, dtype=np.float32
    ).copy()
    clone.transform.rotation = np.array(
        source.transform.rotation, dtype=np.float32
    ).copy()
    clone.transform.scale = np.array(
        source.transform.scale, dtype=np.float32
    ).copy()
    clone.transform.id = str(uuid.uuid4())
    clone.transform._started = False

    # Componentes (exceto Transform)
    for component in getattr(source, "components", []):
        if isinstance(component, Transform) or component is getattr(
            source, "transform", None
        ):
            continue
        cloned_comp = _clone_component(component)
        if cloned_comp is not None:
            clone.add_component(cloned_comp)

    # Filhos — sempre clonados independente de active
    for child in getattr(source, "children", []):
        clone.add_child(clone_game_object(child, _visited=_visited))

    return clone
