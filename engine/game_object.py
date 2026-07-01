from typing import List, Type, TypeVar, Optional, TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from .component import Component, Transform
    from .core import Scene

T = TypeVar('T', bound='Component')


class GameObject:
    """A container for Components. Represents any entity in the game world."""
    def __init__(self, name: str = "GameObject") -> None:
        self.name: str = name
        self.active: bool = True
        self.parent: Optional['GameObject'] = None
        self.children: List['GameObject'] = []
        self.components: List['Component'] = []
        self._scene: Optional['Scene'] = None

        from .component import Transform
        self.transform = Transform()
        self.add_component(self.transform)

    @property
    def scene(self) -> Optional['Scene']:
        return self._scene

    @scene.setter
    def scene(self, val: Optional['Scene']) -> None:
        self._scene = val
        # Propaga para os componentes atuais
        for comp in self.components:
            if val and not comp._started:
                comp.start()
                comp._started = True
        # Propaga para os filhos
        for child in self.children:
            child.scene = val

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

    def start(self) -> None:
        """Inicia todos os componentes do GameObject imediatamente se houver cena."""
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
        # FIX: iterate over a copy so child.destroy() removing itself from
        # self.children doesn't skip siblings
        for child in list(self.children):
            child.destroy()
        self.children.clear()
        if self.parent:
            if self in self.parent.children:
                self.parent.children.remove(self)
            self.parent = None
        self.scene = None
