from __future__ import annotations

from types import SimpleNamespace

import pygame

from engine.physics.physics_world import PhysicsWorld


class StubBoxCollider:
    type_name = "BoxCollider"

    def __init__(self, x: int, y: int, size: int = 16, scene: object | None = None) -> None:
        self.rect = pygame.Rect(x, y, size, size)
        self.enabled = True
        self.is_trigger = False
        self.game_object = SimpleNamespace(active=True, scene=scene, components=[])
        self.on_collision_enter = None
        self.on_collision_exit = None


def test_broad_phase_culls_separated_colliders_before_narrow_phase() -> None:
    world = PhysicsWorld(broad_phase_cell_size=64.0)
    scene = object()
    world.colliders = [StubBoxCollider(index * 128, 0, scene=scene) for index in range(100)]

    assert world.detect_collisions() == []
    assert world.broad_phase_stats.possible_pairs == 4950
    assert world.broad_phase_stats.candidate_pairs == 0
    assert world.broad_phase_stats.culled_pairs == 4950


def test_broad_phase_preserves_overlapping_contact_detection() -> None:
    world = PhysicsWorld(broad_phase_cell_size=64.0)
    scene = object()
    first = StubBoxCollider(0, 0, scene=scene)
    second = StubBoxCollider(8, 8, scene=scene)
    world.colliders = [first, second]

    contacts = world.detect_collisions()

    assert len(contacts) == 1
    assert contacts[0].a is first
    assert contacts[0].b is second
    assert world.broad_phase_stats.candidate_pairs == 1


def test_oversized_collider_uses_bounded_overflow_path() -> None:
    world = PhysicsWorld(broad_phase_cell_size=1.0)
    scene = object()
    giant = StubBoxCollider(0, 0, size=10_000, scene=scene)
    inside = StubBoxCollider(5, 5, scene=scene)
    world.colliders = [giant, inside]

    assert len(world.detect_collisions()) == 1
    assert world.broad_phase_stats.overflow_colliders == 1
