"""
engine/core/component.py
────────────────────────────────────────────────────────────────
Fonte canônica de Component e Transform.
O arquivo engine/component.py é agora um shim que importa daqui.

Conceito:
  Um Component é um bloco de comportamento que vive dentro de um
  GameObject. A engine não sabe o que cada Component faz — ela apenas
  orquestra o ciclo de vida (start → update → draw → destroy).

Ciclo de vida:
    start()        ← chamado uma única vez, quando o GO entra na cena
    update(dt)     ← chamado todo frame (lógica)
    draw(screen)   ← chamado todo frame (renderização)
    destroy()      ← chamado quando o GO ou componente é removido

Garantia de _started:
    _started é False até start() ser chamado. O setter .scene do
    GameObject garante que start() é invocado exatamente uma vez.
    Não chame start() manualmente.

Uso:
    from engine.core import Component, Transform

    class Health(Component):
        def __init__(self, max_hp: int = 100):
            super().__init__()
            self.hp = max_hp

        def start(self):
            Logger.info(f"{self.game_object.name} HP inicializado: {self.hp}")

        def take_damage(self, amount: int):
            self.hp -= amount
            if self.hp <= 0:
                self.game_object.destroy()

Transform:
    Todo GO começa com um Transform já adicionado.
    Acesse via  go.transform  ou  comp.transform  de qualquer componente.

    Suporta posição, rotação e escala em 2D (z=0, rx=0, ry=0) e 3D.
    Vetores internos são np.float32 para operações vetorizadas rápidas.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from engine.game_object import GameObject


# ============================================================== #
#  Component — classe base                                       #
# ============================================================== #

class Component:
    """Bloco de comportamento reutilizável que vive dentro de um GameObject."""

    def __init__(self) -> None:
        #: GO ao qual este componente está anexado.
        self.game_object: Optional["GameObject"] = None
        #: True após start() ser chamado. Não modifique manualmente.
        self._started: bool = False

    # ------------------------------------------------------------------ #
    # Atalhos                                                             #
    # ------------------------------------------------------------------ #

    @property
    def transform(self) -> "Transform":
        """Acesso rápido ao Transform do GameObject."""
        assert self.game_object is not None, (
            f"{type(self).__name__} não está anexado a nenhum GameObject."
        )
        return self.game_object.transform

    @property
    def scene(self):
        """Cena ativa do GameObject, ou None se não estiver em cena."""
        return self.game_object.scene if self.game_object else None

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                       #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Chamado uma vez antes do primeiro update. Sobrescreva se necessário."""

    def update(self, dt: float) -> None:
        """Chamado todo frame. Sobrescreva para lógica de jogo."""

    def draw(self, screen) -> None:
        """Chamado todo frame após update. Sobrescreva para renderização."""

    def destroy(self) -> None:
        """Chamado quando o componente ou seu GO é destruído."""

    # ------------------------------------------------------------------ #
    # repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        go_name = self.game_object.name if self.game_object else "<detached>"
        return f"<{type(self).__name__} on='{go_name}' started={self._started}>"


# ============================================================== #
#  Transform — posição, rotação, escala                         #
# ============================================================== #

class Transform(Component):
    """
    Componente de transformação espacial (2D e 3D).

    Todo GameObject começa com um Transform já adicionado.
    Vetores internos são np.float32 para operações rápidas.

    Atalhos 2D comuns:
        t.x, t.y           — posição
        t.rz               — rotação em graus (eixo Z)
        t.sx, t.sy         — escala
        t.translate(dx, dy)
    """

    def __init__(
        self,
        x: float = 0.0, y: float = 0.0, z: float = 0.0,
        rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
        sx: float = 1.0, sy: float = 1.0, sz: float = 1.0,
    ) -> None:
        super().__init__()
        self._position = np.array([x, y, z], dtype=np.float32)
        self._rotation = np.array([rx, ry, rz], dtype=np.float32)
        self._scale    = np.array([sx, sy, sz], dtype=np.float32)

    # ------------------------------------------------------------------ #
    # Position                                                            #
    # ------------------------------------------------------------------ #

    @property
    def position(self) -> np.ndarray:
        return self._position

    @position.setter
    def position(self, val) -> None:
        self._position = np.array(val, dtype=np.float32)

    @property
    def x(self) -> float: return float(self._position[0])
    @x.setter
    def x(self, val: float) -> None: self._position[0] = val

    @property
    def y(self) -> float: return float(self._position[1])
    @y.setter
    def y(self, val: float) -> None: self._position[1] = val

    @property
    def z(self) -> float: return float(self._position[2])
    @z.setter
    def z(self, val: float) -> None: self._position[2] = val

    # ------------------------------------------------------------------ #
    # Rotation (graus)                                                    #
    # ------------------------------------------------------------------ #

    @property
    def rotation(self) -> np.ndarray:
        return self._rotation

    @rotation.setter
    def rotation(self, val) -> None:
        self._rotation = np.array(val, dtype=np.float32)

    @property
    def rx(self) -> float: return float(self._rotation[0])
    @rx.setter
    def rx(self, val: float) -> None: self._rotation[0] = val

    @property
    def ry(self) -> float: return float(self._rotation[1])
    @ry.setter
    def ry(self, val: float) -> None: self._rotation[1] = val

    @property
    def rz(self) -> float: return float(self._rotation[2])
    @rz.setter
    def rz(self, val: float) -> None: self._rotation[2] = val

    # ------------------------------------------------------------------ #
    # Scale                                                               #
    # ------------------------------------------------------------------ #

    @property
    def scale(self) -> np.ndarray:
        return self._scale

    @scale.setter
    def scale(self, val) -> None:
        self._scale = np.array(val, dtype=np.float32)

    @property
    def sx(self) -> float: return float(self._scale[0])
    @sx.setter
    def sx(self, val: float) -> None: self._scale[0] = val

    @property
    def sy(self) -> float: return float(self._scale[1])
    @sy.setter
    def sy(self, val: float) -> None: self._scale[1] = val

    @property
    def sz(self) -> float: return float(self._scale[2])
    @sz.setter
    def sz(self, val: float) -> None: self._scale[2] = val

    # ------------------------------------------------------------------ #
    # Métodos                                                             #
    # ------------------------------------------------------------------ #

    def translate(self, dx: float, dy: float, dz: float = 0.0) -> None:
        """Move o transform pelos deltas fornecidos."""
        self._position += np.array([dx, dy, dz], dtype=np.float32)

    def rotate(self, drx: float, dry: float, drz: float) -> None:
        """Rotaciona o transform pelos deltas fornecidos (graus)."""
        self._rotation += np.array([drx, dry, drz], dtype=np.float32)

    def get_model_matrix(self) -> np.ndarray:
        """Retorna a matrix modelo 4x4 (local * parent)."""
        from engine.graphics.math3d import (
            translation_matrix, rotation_matrix, scale_matrix
        )
        pos   = self._position
        rot   = self._rotation
        scale = self._scale

        local = (
            translation_matrix(pos[0], pos[1], pos[2])
            @ rotation_matrix(rot[0], rot[1], rot[2])
            @ scale_matrix(scale[0], scale[1], scale[2])
        )

        if self.game_object and self.game_object.parent:
            parent_t = self.game_object.parent.get_component(Transform)
            if parent_t:
                return parent_t.get_model_matrix() @ local

        return local

    @property
    def world_position(self) -> np.ndarray:
        """Posição no espaço mundo (considera hierarquia)."""
        return self.get_model_matrix()[:3, 3]

    @property
    def world_rotation(self) -> np.ndarray:
        """Rotação acumulada no espaço mundo (graus)."""
        rot = self._rotation.copy()
        if self.game_object and self.game_object.parent:
            parent_t = self.game_object.parent.get_component(Transform)
            if parent_t:
                rot += parent_t.world_rotation
        return rot

    def get_world_position(self) -> np.ndarray:
        """Alias de world_position para compatibilidade."""
        return self.world_position

    def __repr__(self) -> str:
        go_name = self.game_object.name if self.game_object else "<detached>"
        return (
            f"<Transform on='{go_name}' "
            f"pos=({self.x:.1f},{self.y:.1f}) "
            f"rot={self.rz:.1f}° "
            f"scale=({self.sx:.2f},{self.sy:.2f})>"
        )
