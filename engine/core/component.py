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

Serialização (Fase 9):
    Componentes podem implementar serialize() e deserialize() para
    suportar save/load de cenas e prefabs.

    serialize()     → Dict[str, Any]   — snapshot dos dados do componente
    deserialize(d)  ← Dict[str, Any]   — restaura estado a partir do dict

    O dict retornado por serialize() DEVE incluir a chave "type" com o
    nome do componente (usado pelo ComponentRegistry para recriá-lo).

enable/disable:
    comp.enabled = False   → update() e draw() são ignorados pela engine
    comp.enabled = True    → retoma o ciclo normal

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

        def serialize(self):
            data = super().serialize()
            data["hp"] = self.hp
            return data

        def deserialize(self, data):
            super().deserialize(data)
            self.hp = data.get("hp", 100)

Transform:
    Todo GO começa com um Transform já adicionado.
    Acesse via  go.transform  ou  comp.transform  de qualquer componente.

    Suporta posição, rotação e escala em 2D (z=0, rx=0, ry=0) e 3D.
    Vetores internos são np.float32 para operações vetorizadas rápidas.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from engine.game_object import GameObject


# ============================================================== #
#  Component — classe base                                       #
# ============================================================== #

class Component:
    """Bloco de comportamento reutilizável que vive dentro de um GameObject."""

    # Subclasses com UNIQUE = True só podem existir uma vez por GameObject.
    UNIQUE: bool = False

    def __init__(self) -> None:
        #: GO ao qual este componente está anexado.
        self.game_object: Optional["GameObject"] = None
        #: True após start() ser chamado. Não modifique manualmente.
        self._started: bool = False
        #: Controla se update() e draw() são chamados pela engine.
        self._enabled: bool = True

    # ------------------------------------------------------------------ #
    # enabled                                                             #
    # ------------------------------------------------------------------ #

    @property
    def enabled(self) -> bool:
        """Se False, update() e draw() são ignorados."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        prev = self._enabled
        self._enabled = bool(value)
        if prev and not self._enabled:
            self.on_disable()
        elif not prev and self._enabled:
            self.on_enable()

    def on_enable(self) -> None:
        """Chamado ao ativar o componente. Sobrescreva se necessário."""

    def on_disable(self) -> None:
        """Chamado ao desativar o componente. Sobrescreva se necessário."""

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
    # Serialização (Fase 9)                                               #
    # ------------------------------------------------------------------ #

    @property
    def type_name(self) -> str:
        return getattr(self, "component_type", type(self).__name__)

    def serialize(self) -> Dict[str, Any]:
        """Retorna um dict com o estado serializável."""
        data = {
            "type": self.type_name,
            "enabled": self._enabled,
            "properties": {}
        }
        # Reflexão padrão para propriedades simples
        for key, value in self.__dict__.items():
            if not key.startswith("_") and key not in ["game_object", "type_name", "enabled"]:
                if isinstance(value, (int, float, str, bool, list, dict)):
                    data["properties"][key] = value

        if hasattr(self, "serialize_properties"):
            props = self.serialize_properties()
            if props:
                data["properties"].update(props)
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        """
        Restaura o estado do componente a partir de *data*.
        """
        self._enabled = bool(data.get("enabled", True))
        
        props = data.get("properties", {})
        for key, value in props.items():
            if hasattr(self, key):
                try:
                    setattr(self, key, value)
                except AttributeError:
                    pass
                
        if hasattr(self, "deserialize_properties"):
            self.deserialize_properties(props)

    # ------------------------------------------------------------------ #
    # repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        go_name = self.game_object.name if self.game_object else "<detached>"
        enabled_str = "" if self._enabled else " disabled"
        return f"<{type(self).__name__} on='{go_name}' started={self._started}{enabled_str}>"


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

    UNIQUE = True

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

    # ------------------------------------------------------------------ #
    # Serialização                                                        #
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["position"] = self._position.tolist()
        data["rotation"] = self._rotation.tolist()
        data["scale"]    = self._scale.tolist()
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        if "position" in data:
            self._position = np.array(data["position"], dtype=np.float32)
        if "rotation" in data:
            self._rotation = np.array(data["rotation"], dtype=np.float32)
        if "scale" in data:
            self._scale = np.array(data["scale"], dtype=np.float32)

    def __repr__(self) -> str:
        go_name = self.game_object.name if self.game_object else "<detached>"
        return (
            f"<Transform on='{go_name}' "
            f"pos=({self.x:.1f},{self.y:.1f}) "
            f"rot={self.rz:.1f}° "
            f"scale=({self.sx:.2f},{self.sy:.2f})>"
        )
