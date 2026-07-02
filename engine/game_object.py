from __future__ import annotations

import uuid
from typing import List, Type, TypeVar, Optional, TYPE_CHECKING

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
        component.game_object = self
        self.components.append(component)
        if self.scene and not component._started:
            component.start()
            component._started = True
        return component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        for comp in self.components:
            if isinstance(comp, component_type):
                return comp
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        return [comp for comp in self.components if isinstance(comp, component_type)]

    def remove_component(self, component: 'Component') -> None:
        if component in self.components:
            component.destroy()
            component.game_object = None
            self.components.remove(component)

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
            comp.update(dt)
        for child in self.children:
            child.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        for comp in self.components:
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
