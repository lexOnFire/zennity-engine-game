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
        if getattr(component, "unique", False):
            existing = self.get_component(type(component))
            if existing is not None:
                return existing
        component.game_object = self
        self.components.append(component)
        if self.scene and not component._started:
            component.start()
            component._started = True
        return component

    def insert_component(self, component: 'Component', index: int | None = None) -> 'Component':
        if getattr(component, "unique", False):
            existing = self.get_component(type(component))
            if existing is not None and existing is not component:
                return existing
        if component in self.components:
            self.components.remove(component)
        component.game_object = self
        if index is None:
            self.components.append(component)
        else:
            safe_index = max(0, min(int(index), len(self.components)))
            self.components.insert(safe_index, component)
        if self.scene and not component._started:
            component.start()
            component._started = True
        return component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        from .component import Component

        # Transform é criado automaticamente em todo GameObject. Quando a busca
        # é pelo tipo base Component, priorizamos componentes adicionados pelo
        # usuário; buscas específicas como get_component(Transform) continuam
        # retornando o Transform normalmente.
        if component_type is Component:
            for comp in self.components:
                if comp is not self.transform and (isinstance(comp, component_type) or type(comp).__name__ == component_type.__name__):
                    return comp

        for comp in self.components:
            if isinstance(comp, component_type) or type(comp).__name__ == component_type.__name__:
                return comp
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        return [comp for comp in self.components if isinstance(comp, component_type) or type(comp).__name__ == component_type.__name__]

    def remove_component(self, component: 'Component') -> None:
        if component is self.transform or getattr(component, "required", False):
            raise ValueError("Transform is required and cannot be removed from a GameObject")
        if component in self.components:
            component.destroy()
            component.game_object = None
            self.components.remove(component)

    def all_components(self) -> List['Component']:
        return list(self.components)

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
            if getattr(comp, "enabled", True):
                comp.update(dt)
        for child in self.children:
            child.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        for comp in self.components:
            if getattr(comp, "enabled", True):
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
