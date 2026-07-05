from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Type, TypeVar, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .component import Component, Transform
    from .core import Scene

T = TypeVar('T', bound='Component')


class GameObject:
    """
    Container de Components. Representa qualquer entidade no mundo do jogo.

    Identidade:
        go.id    — UUID4 único e imutável, atribuído na criação
        go.name  — nome legível para editor e debug (mutável)
        go.tag   — agrupamento semântico ("Player", "Enemy", "Wall")

    Exemplo:
        player = GameObject("Player", tag="Player")
        player.id    # '3f2a1c...' — UUID4 completo
        player.name  # 'Player'
        player.tag   # 'Player'
    """

    def __init__(self, name: str = "GameObject", tag: str = "Untagged") -> None:
        # Identidade
        self._id: str = str(uuid.uuid4())
        self.name:   str  = name
        self.tag:    str  = tag

        self.active: bool = True
        self.parent: Optional['GameObject'] = None
        self.children: List['GameObject'] = []
        self.components: List['Component'] = []
        self._scene: Optional['Scene'] = None

        from .component import Transform
        self.transform = Transform()
        self.add_component(self.transform)
        self.mesh_type: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Identidade                                                          #
    # ------------------------------------------------------------------ #

    @property
    def id(self) -> str:
        """UUID4 único e imutável atribuído na criação."""
        return self._id

    @property
    def short_id(self) -> str:
        """Primeiros 8 caracteres do UUID — útil para logs e debug."""
        return self._id[:8]

    # ------------------------------------------------------------------ #
    # Cena                                                                #
    # ------------------------------------------------------------------ #

    @property
    def scene(self) -> Optional['Scene']:
        return getattr(self, "_scene", None)

    @scene.setter
    def scene(self, val: Optional['Scene']) -> None:
        self._scene = val
        for comp in self.components:
            if val and not comp._started:
                comp.start()
                comp._started = True
        for child in self.children:
            child.scene = val

    # ------------------------------------------------------------------ #
    # Components                                                          #
    # ------------------------------------------------------------------ #

    def add_component(self, component: 'Component') -> 'Component':
        """
        Adiciona *component* ao GameObject.

        Se a classe do componente tiver UNIQUE=True e já existir uma instância
        do mesmo tipo neste GO, levanta TypeError.
        """
        # Verificação UNIQUE
        if getattr(type(component), 'UNIQUE', False):
            existing = self.get_component(type(component))
            if existing is not None and existing is not component:
                raise TypeError(
                    f"Componente {type(component).__name__} é UNIQUE — "
                    f"já existe um no GameObject '{self.name}'."
                )
        component.game_object = self
        self.components.append(component)
        if self.scene and not component._started:
            component.start()
            component._started = True
        return component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        for comp in self.components:
            if isinstance(comp, component_type):
                return comp  # type: ignore[return-value]
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        return [comp for comp in self.components if isinstance(comp, component_type)]  # type: ignore[misc]

    def remove_component(self, component: 'Component') -> None:
        if component in self.components:
            component.destroy()
            component.game_object = None
            self.components.remove(component)

    # ------------------------------------------------------------------ #
    # Serialização (Fase 9)                                               #
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        """
        Retorna um dict com o estado completo do GameObject:
        nome, tag, active, lista de componentes serializados e filhos.
        """
        return {
            "id":         self._id,
            "name":       self.name,
            "tag":        self.tag,
            "active":     self.active,
            "components": [c.serialize() for c in self.components],
            "children":   [child.serialize() for child in self.children],
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "GameObject":
        """
        Reconstrói um GameObject a partir de um dict produzido por serialize().

        Usa ComponentRegistry para instanciar os componentes pelo nome.
        O Transform já é criado pelo __init__ e atualizado via deserialize().
        """
        from engine.component_registry import ComponentRegistry
        from engine.core.component import Transform

        go = cls(name=data.get("name", "GameObject"), tag=data.get("tag", "Untagged"))
        go.active = bool(data.get("active", True))

        # Restaurar o _id original
        go._id = data.get("id", go._id)

        for comp_data in data.get("components", []):
            type_name = comp_data.get("type", "")
            if type_name == "Transform":
                # Transform já existe — apenas deserializa
                go.transform.deserialize(comp_data)
            else:
                klass = ComponentRegistry.get(type_name)
                if klass is None:
                    continue  # componente desconhecido — ignora graciosamente
                instance = klass.__new__(klass)
                # Inicializa via Component.__init__ sem parâmetros
                from engine.core.component import Component
                Component.__init__(instance)
                instance.deserialize(comp_data)
                go.add_component(instance)

        for child_data in data.get("children", []):
            child = cls.deserialize(child_data)
            go.add_child(child)

        return go

    # ------------------------------------------------------------------ #
    # Hierarquia                                                          #
    # ------------------------------------------------------------------ #

    def add_child(self, child: 'GameObject') -> 'GameObject':
        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)
        child.scene = self.scene
        return child

    def remove_child(self, child: 'GameObject') -> None:
        if child in self.children:
            child.parent = None
            self.children.remove(child)
            child.scene = None

    def _propagate_scene(self, scene: Optional['Scene']) -> None:
        self.scene = scene

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                       #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        for comp in self.components:
            if not comp._started and self.scene:
                comp.start()
                comp._started = True
        for child in self.children:
            child.start()

    def update(self, dt: float) -> None:
        if not self.active:
            return
        for comp in self.components:
            if not comp._started and self.scene:
                comp.start()
                comp._started = True
            if comp.enabled:
                comp.update(dt)
        for child in self.children:
            child.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        for comp in self.components:
            if comp.enabled:
                comp.draw(screen)
        for child in self.children:
            child.draw(screen)

    def destroy(self) -> None:
        self.active = False
        for comp in self.components:
            comp.destroy()
        self.components.clear()
        for child in list(self.children):
            child.destroy()
        self.children.clear()
        if self.parent:
            if self in self.parent.children:
                self.parent.children.remove(self)
            self.parent = None
        self.scene = None

    # ------------------------------------------------------------------ #
    # repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        tag_str = f" tag={self.tag}" if self.tag != "Untagged" else ""
        return f"<GameObject '{self.name}' id={self.short_id}{tag_str}>"
