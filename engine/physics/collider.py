from __future__ import annotations
from typing import Optional, Callable, List, TYPE_CHECKING
from dataclasses import dataclass, field
import math
import pygame
from engine.component import Component

if TYPE_CHECKING:
    from engine.game_object import GameObject


@dataclass
class CollisionInfo:
    """Informações sobre uma colisão entre dois colliders."""
    other: "BoxCollider"
    overlap_x: float = 0.0
    overlap_y: float = 0.0


class BoxCollider(Component):
    """
    Collider retangular (AABB — Axis-Aligned Bounding Box).

    Registra-se automaticamente no PhysicsWorld ao ser adicionado
    a um GameObject que pertence a uma Scene.

    Callbacks disponíveis:
        on_collision_enter(info: CollisionInfo) -> None
        on_collision_exit(other: BoxCollider)   -> None
    """

    _registry: List["BoxCollider"] = []
    _scene_tilemaps: Dict[tuple, Any] = {}
    _scene_tilemap_components: Dict[int, Any] = {}

    def __init__(
        self,
        width: float = 32.0,
        height: float = 32.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        is_trigger: bool = False,
        debug_draw: bool = False,
    ) -> None:
        super().__init__()
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_trigger = is_trigger   # trigger = detecta mas não resolve colisão
        self.debug_draw = debug_draw

        self._colliding_with: set["BoxCollider"] = set()

        # Callbacks — atribua funções externas a estes
        self.on_collision_enter: Optional[Callable[[CollisionInfo], None]] = None
        self.on_collision_exit: Optional[Callable[["BoxCollider"], None]] = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def start(self) -> None:
        BoxCollider._registry.append(self)

    def destroy(self) -> None:
        if self in BoxCollider._registry:
            BoxCollider._registry.remove(self)

    # ------------------------------------------------------------------
    # Rect utilitário
    # ------------------------------------------------------------------

    @property
    def rect(self) -> pygame.Rect:
        """Retorna o pygame.Rect atual no espaço de mundo."""
        if self.game_object is None:
            return pygame.Rect(0, 0, int(self.width), int(self.height))
        pos = self.game_object.transform.get_world_position()
        left = int(pos[0] + self.offset_x - self.width / 2)
        top  = int(pos[1] + self.offset_y - self.height / 2)
        return pygame.Rect(left, top, int(self.width), int(self.height))

    @classmethod
    def invalidate_tilemap_cache(cls, scene: Any) -> None:
        """Clear cached TilemapCollider instances for the specified scene."""
        scene_id = id(scene)
        cls._scene_tilemap_components.pop(scene_id, None)
        keys_to_remove = [k for k in cls._scene_tilemaps if k[0] == scene_id]
        for k in keys_to_remove:
            cls._scene_tilemaps.pop(k, None)

    # ------------------------------------------------------------------
    # Detecção AABB
    # ------------------------------------------------------------------

    @staticmethod
    def check_all() -> None:
        """
        Verifica colisões entre todos os BoxColliders registrados.
        Purga órfãos e limita as colisões ao escopo da mesma cena ativa.
        """
        BoxCollider._registry = [c for c in BoxCollider._registry if c.game_object is not None and c.game_object.scene is not None]
        registry = list(BoxCollider._registry)
        n = len(registry)

        # Resolução de colisões contra Tilemaps na mesma cena (usando cache estático por instância de mapa)
        for a in registry:
            if a.game_object is None or not a.game_object.active:
                continue
            scene = a.game_object.scene
            if scene is None:
                continue
            
            from engine.physics.rigidbody import RigidBody
            rb = a.game_object.get_component(RigidBody)
            if rb is None or rb.is_kinematic:
                continue

            # Busca por TilemapRenderer ativo na cena usando cache persistente
            scene_id = id(scene)
            if scene_id not in BoxCollider._scene_tilemap_components:
                tm_comp = None
                if hasattr(scene, "game_objects"):
                    from engine.tilemap.tilemap import TilemapRenderer
                    for go in scene.game_objects:
                        found = go.get_component(TilemapRenderer)
                        if found is not None and found.tilemap is not None:
                            tm_comp = found
                            break
                BoxCollider._scene_tilemap_components[scene_id] = tm_comp

            tm_comp = BoxCollider._scene_tilemap_components[scene_id]
            if tm_comp is not None:
                cache_key = (scene_id, id(tm_comp.tilemap))
                if cache_key not in BoxCollider._scene_tilemaps:
                    from engine.physics.tilemap_collider import TilemapCollider
                    BoxCollider._scene_tilemaps[cache_key] = TilemapCollider(tm_comp.tilemap, layer_name="collision")
                
                tm_collider = BoxCollider._scene_tilemaps[cache_key]
                tm_collider.resolve(a.game_object)

        for i in range(n):
            a = registry[i]
            if a.game_object is None or not a.game_object.active:
                continue
            scene_a = a.game_object.scene
            if scene_a is None:
                continue
            for j in range(i + 1, n):
                b = registry[j]
                if b.game_object is None or not b.game_object.active:
                    continue
                if b.game_object.scene != scene_a:
                    continue

                rect_a = a.rect
                rect_b = b.rect

                if rect_a.colliderect(rect_b):
                    # Calcula overlaps para resolução de colisão
                    overlap_x = min(rect_a.right, rect_b.right) - max(rect_a.left, rect_b.left)
                    overlap_y = min(rect_a.bottom, rect_b.bottom) - max(rect_a.top, rect_b.top)
                    info_ab = CollisionInfo(other=b, overlap_x=overlap_x, overlap_y=overlap_y)
                    info_ba = CollisionInfo(other=a, overlap_x=overlap_x, overlap_y=overlap_y)

                    # Resolução física (só para não-triggers)
                    if not a.is_trigger and not b.is_trigger:
                        BoxCollider._resolve(a, b, overlap_x, overlap_y)

                    # Callbacks de enter
                    if b not in a._colliding_with:
                        a._colliding_with.add(b)
                        b._colliding_with.add(a)
                        if a.on_collision_enter:
                            a.on_collision_enter(info_ab)
                        if b.on_collision_enter:
                            b.on_collision_enter(info_ba)
                else:
                    # Callbacks de exit
                    if b in a._colliding_with:
                        a._colliding_with.discard(b)
                        b._colliding_with.discard(a)
                        if a.on_collision_exit:
                            a.on_collision_exit(b)
                        if b.on_collision_exit:
                            b.on_collision_exit(a)

    @staticmethod
    def _resolve(a: "BoxCollider", b: "BoxCollider", overlap_x: float, overlap_y: float) -> None:
        """Resolve penetração pelo eixo de menor sobreposição (MTV)."""
        from engine.physics.rigidbody import RigidBody

        rb_a = a.game_object.get_component(RigidBody) if a.game_object else None
        rb_b = b.game_object.get_component(RigidBody) if b.game_object else None

        # Determina qual eixo resolver (o de menor penetração)
        if overlap_x < overlap_y:
            # Separa no eixo X
            direction = 1 if a.rect.centerx < b.rect.centerx else -1
            correction = overlap_x / 2
            if rb_a and not rb_a.is_kinematic:
                a.game_object.transform.position[0] -= direction * correction
                rb_a.velocity[0] = 0
            if rb_b and not rb_b.is_kinematic:
                b.game_object.transform.position[0] += direction * correction
                rb_b.velocity[0] = 0
        else:
            # Separa no eixo Y
            direction = 1 if a.rect.centery < b.rect.centery else -1
            correction = overlap_y / 2
            if rb_a and not rb_a.is_kinematic:
                a.game_object.transform.position[1] -= direction * correction
                rb_a.velocity[1] = 0
            if rb_b and not rb_b.is_kinematic:
                b.game_object.transform.position[1] += direction * correction
                rb_b.velocity[1] = 0

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if self.debug_draw:
            pygame.draw.rect(screen, (0, 255, 0), self.rect, 1)


class CircleCollider(Component):
    """
    Collider circular para detecção de colisão por distância.

    Callbacks disponíveis:
        on_collision_enter(other: CircleCollider) -> None
        on_collision_exit(other: CircleCollider)  -> None
    """

    _registry: List["CircleCollider"] = []

    def __init__(
        self,
        radius: float = 16.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        is_trigger: bool = False,
        debug_draw: bool = False,
    ) -> None:
        super().__init__()
        self.radius = radius
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_trigger = is_trigger
        self.debug_draw = debug_draw

        self._colliding_with: set["CircleCollider"] = set()

        self.on_collision_enter: Optional[Callable[["CircleCollider"], None]] = None
        self.on_collision_exit: Optional[Callable[["CircleCollider"], None]] = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def start(self) -> None:
        CircleCollider._registry.append(self)

    def destroy(self) -> None:
        if self in CircleCollider._registry:
            CircleCollider._registry.remove(self)

    # ------------------------------------------------------------------
    # Centro utilitário
    # ------------------------------------------------------------------

    @property
    def center(self) -> tuple[float, float]:
        """Retorna o centro do collider no espaço de mundo."""
        if self.game_object is None:
            return (self.offset_x, self.offset_y)
        pos = self.game_object.transform.get_world_position()
        return (float(pos[0]) + self.offset_x, float(pos[1]) + self.offset_y)

    # ------------------------------------------------------------------
    # Detecção círculo-círculo
    # ------------------------------------------------------------------

    @staticmethod
    def check_all() -> None:
        """
        Verifica colisões entre todos os CircleColliders registrados.
        Purga órfãos e limita as colisões ao escopo da mesma cena ativa.
        """
        CircleCollider._registry = [c for c in CircleCollider._registry if c.game_object is not None and c.game_object.scene is not None]
        registry = list(CircleCollider._registry)
        n = len(registry)

        for i in range(n):
            a = registry[i]
            if a.game_object is None or not a.game_object.active:
                continue
            scene_a = a.game_object.scene
            if scene_a is None:
                continue
            for j in range(i + 1, n):
                b = registry[j]
                if b.game_object is None or not b.game_object.active:
                    continue
                if b.game_object.scene != scene_a:
                    continue

                ax, ay = a.center
                bx, by = b.center
                dist = math.hypot(bx - ax, by - ay)
                min_dist = a.radius + b.radius

                if dist < min_dist:
                    if not a.is_trigger and not b.is_trigger:
                        CircleCollider._resolve(a, b, ax, ay, bx, by, dist, min_dist)

                    if b not in a._colliding_with:
                        a._colliding_with.add(b)
                        b._colliding_with.add(a)
                        if a.on_collision_enter:
                            a.on_collision_enter(b)
                        if b.on_collision_enter:
                            b.on_collision_enter(a)
                else:
                    if b in a._colliding_with:
                        a._colliding_with.discard(b)
                        b._colliding_with.discard(a)
                        if a.on_collision_exit:
                            a.on_collision_exit(b)
                        if b.on_collision_exit:
                            b.on_collision_exit(a)

    @staticmethod
    def _resolve(
        a: "CircleCollider", b: "CircleCollider",
        ax: float, ay: float, bx: float, by: float,
        dist: float, min_dist: float,
    ) -> None:
        """Empurra os dois círculos para fora da sobreposição."""
        from engine.physics.rigidbody import RigidBody

        if dist == 0:
            nx, ny = 1.0, 0.0
        else:
            nx, ny = (bx - ax) / dist, (by - ay) / dist

        overlap = (min_dist - dist) / 2
        rb_a = a.game_object.get_component(RigidBody) if a.game_object else None
        rb_b = b.game_object.get_component(RigidBody) if b.game_object else None

        if rb_a and not rb_a.is_kinematic:
            a.game_object.transform.position[0] -= nx * overlap
            a.game_object.transform.position[1] -= ny * overlap
        if rb_b and not rb_b.is_kinematic:
            b.game_object.transform.position[0] += nx * overlap
            b.game_object.transform.position[1] += ny * overlap

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if self.debug_draw:
            cx, cy = self.center
            pygame.draw.circle(screen, (0, 255, 128), (int(cx), int(cy)), int(self.radius), 1)
