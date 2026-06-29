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
        self.scene: Optional['Scene'] = None
        
        # Every GameObject must have a Transform component
        from .component import Transform
        self.transform = Transform()
        self.add_component(self.transform)

    def add_component(self, component: 'Component') -> 'Component':
        """Adds a component to this GameObject."""
        component.game_object = self
        self.components.append(component)
        # If the GameObject is already part of an active scene, start it
        if self.scene and not component._started:
            component.start()
            component._started = True
        return component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """Returns the first component of the given type, or None."""
        for comp in self.components:
            if isinstance(comp, component_type):
                return comp
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        """Returns a list of all components of the given type."""
        return [comp for comp in self.components if isinstance(comp, component_type)]

    def remove_component(self, component: 'Component') -> None:
        """Removes a component from this GameObject."""
        if component in self.components:
            component.destroy()
            component.game_object = None
            self.components.remove(component)

    def add_child(self, child: 'GameObject') -> 'GameObject':
        """Adds a child GameObject. The child's transform will be relative to this one."""
        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        child.scene = self.scene
        self.children.append(child)
        # propagate scene reference to child's descendants
        child._propagate_scene(self.scene)
        return child

    def remove_child(self, child: 'GameObject') -> None:
        """Removes a child GameObject."""
        if child in self.children:
            child.parent = None
            child.scene = None
            self.children.remove(child)
            child._propagate_scene(None)

    def _propagate_scene(self, scene: Optional['Scene']) -> None:
        self.scene = scene
        for comp in self.components:
            if scene and not comp._started:
                comp.start()
                comp._started = True
        for child in self.children:
            child._propagate_scene(scene)

    def update(self, dt: float) -> None:
        """Updates all components and active children."""
        if not self.active:
            return
            
        # Update components
        for comp in self.components:
            if not comp._started and self.scene:
                comp.start()
                comp._started = True
            comp.update(dt)
            
        # Update children
        for child in self.children:
            child.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Draws all components and active children."""
        if not self.active:
            return
            
        # Draw components
        for comp in self.components:
            comp.draw(screen)
            
        # Draw children
        for child in self.children:
            child.draw(screen)

    def destroy(self) -> None:
        """Destroys this GameObject, its components, and all its children."""
        self.active = False
        
        # Destroy all components
        for comp in self.components:
            comp.destroy()
        self.components.clear()
        
        # Destroy all children
        for child in self.children:
            child.destroy()
        self.children.clear()
        
        if self.parent:
            self.parent.children.remove(self)
            self.parent = None
            
        self.scene = None
