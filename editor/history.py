"""
Sistema de Undo/Redo para o editor 3D.

Armazena snapshots do estado de cada objeto editável a cada ação
relevante (mover, escalar, girar, criar, deletar, clonar, alterar cor, etc.).
Usa uma deque com limite de tamanho para manter a memória controlada.
"""
from __future__ import annotations
import copy
from collections import deque
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from engine.game_object import GameObject


# ---------------------------------------------------------------------------
# Snapshot de um único objeto
# ---------------------------------------------------------------------------
def _snap_obj(obj: "GameObject") -> Dict[str, Any]:
    """Captura o estado transformável de um objeto."""
    return {
        "name":               obj.name,
        "mesh_type":          getattr(obj, "mesh_type", "Cube"),
        "is_static":          getattr(obj, "is_static", False),
        "use_physics":        getattr(obj, "use_physics", True),
        "initial_velocity_y": getattr(obj, "initial_velocity_y", 0.0),
        "script_path":        getattr(obj, "script_path", ""),
        "tag":                getattr(obj, "tag", ""),
        "position":           obj.transform.position.copy(),
        "rotation":           obj.transform.rotation.copy(),
        "scale":              obj.transform.scale.copy(),
        "color":              _get_color(obj),
    }


def _get_color(obj: "GameObject") -> tuple:
    from engine.graphics.renderer3d import MeshRenderer3D
    r = obj.get_component(MeshRenderer3D)
    return tuple(r.color) if r else (200, 200, 200)


# ---------------------------------------------------------------------------
# Snapshot da cena inteira
# ---------------------------------------------------------------------------
def _snap_scene(scene: Any) -> Dict[str, Any]:
    return {
        "selected_index": scene.selected_index,
        "light_angle":    getattr(scene, "light_angle", 45.0),
        "objects":        [_snap_obj(o) for o in scene.editable_objects],
    }


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------
class History:
    """
    Pilha de Undo/Redo com limite de 50 estados.

    Uso:
        history.push(scene)        # antes de qualquer mudança
        ... realiza mudança ...
        history.undo(scene)        # restaura estado anterior
        history.redo(scene)        # refaz
    """

    MAX_SIZE: int = 50

    def __init__(self) -> None:
        self._undo: deque[Dict] = deque(maxlen=self.MAX_SIZE)
        self._redo: deque[Dict] = deque(maxlen=self.MAX_SIZE)

    # ------------------------------------------------------------------
    @property
    def can_undo(self) -> bool:
        return len(self._undo) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo) > 0

    # ------------------------------------------------------------------
    def push(self, scene: Any) -> None:
        """Salva o estado atual antes de uma ação. Limpa o redo."""
        self._undo.append(_snap_scene(scene))
        self._redo.clear()

    # ------------------------------------------------------------------
    def undo(self, scene: Any) -> None:
        if not self.can_undo:
            return
        # Salva estado atual no redo antes de reverter
        self._redo.append(_snap_scene(scene))
        self._restore(scene, self._undo.pop())

    def redo(self, scene: Any) -> None:
        if not self.can_redo:
            return
        self._undo.append(_snap_scene(scene))
        self._restore(scene, self._redo.pop())

    # ------------------------------------------------------------------
    def _restore(self, scene: Any, snapshot: Dict) -> None:
        """Reconstrói a cena a partir de um snapshot."""
        from engine.game_object import GameObject
        from engine.graphics.renderer3d import MeshRenderer3D

        # Remove objetos atuais
        for obj in list(scene.editable_objects):
            scene._remove_go(obj)
            obj.destroy()
        scene.editable_objects.clear()
        scene.cube_count    = 0
        scene.pyramid_count = 0
        scene.sphere_count  = 0
        scene.plane_count   = 0
        scene.capsule_count = 0

        # Restaura ângulo da luz
        if "light_angle" in snapshot:
            scene.light_angle = snapshot["light_angle"]

        # Recria objetos do snapshot usando _make_mesh / _deserialize_object
        for s in snapshot["objects"]:
            go = GameObject()
            go.name               = s["name"]
            go.mesh_type          = s["mesh_type"]
            go.is_static          = s["is_static"]
            go.use_physics        = s["use_physics"]
            go.initial_velocity_y = s["initial_velocity_y"]
            go.script_path        = s["script_path"]
            go.tag                = s.get("tag", "")
            go.transform.position = s["position"].copy()
            go.transform.rotation = s["rotation"].copy()
            go.transform.scale    = s["scale"].copy()
            color = s["color"]

            # usa _make_mesh da cena para suportar todos os tipos de forma
            go.add_component(scene._make_mesh(go.mesh_type, color))

            # atualiza contadores
            attr_map = {
                "Cube":    "cube_count",
                "Pyramid": "pyramid_count",
                "Sphere":  "sphere_count",
                "Plane":   "plane_count",
                "Capsule": "capsule_count",
            }
            attr = attr_map.get(go.mesh_type)
            if attr:
                setattr(scene, attr, getattr(scene, attr) + 1)

            scene._add_go(go)
            scene.editable_objects.append(go)

        scene.selected_index = min(
            snapshot["selected_index"],
            len(scene.editable_objects) - 1,
        )
        scene._tree_scroll_to(scene.selected_index)
