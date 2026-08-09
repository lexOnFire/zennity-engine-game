"""Tests for Phase 5B.3 - Raycast 2D implementation."""
from __future__ import annotations

import math
import pytest
from pathlib import Path

# Test RaycastHit and PhysicsWorld.raycast()
from engine.physics.physics_world import PhysicsWorld, RaycastHit
from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody


class MockGameObject:
    """Mock GameObject for testing."""
    def __init__(self, name: str, x: float = 0.0, y: float = 0.0):
        self.name = name
        self.position = [x, y]
        self.active = True
        self.components = []
        self.children = []
        self.transform = MockTransform(x, y)
        self.scene = None

    def get_component(self, component_type):
        """Get component by type."""
        for c in self.components:
            if isinstance(c, component_type):
                return c
        return None


class MockTransform:
    """Mock Transform for testing."""
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.position = [x, y]

    def get_world_position(self):
        """Get world position."""
        return tuple(self.position)


class TestRaycastHitDataclass:
    """Tests for RaycastHit data structure."""

    def test_raycast_hit_creation(self):
        """RaycastHit can be created with all fields."""
        obj = MockGameObject("test")
        collider = BoxCollider(width=10, height=10)
        collider.game_object = obj

        hit = RaycastHit(
            hit_object=obj,
            hit_point=(5.0, 5.0),
            hit_distance=5.0,
            hit_normal=(1.0, 0.0),
            collider=collider,
        )

        assert hit.hit_object == obj
        assert hit.hit_point == (5.0, 5.0)
        assert hit.hit_distance == 5.0
        assert hit.hit_normal == (1.0, 0.0)
        assert hit.collider == collider

    def test_raycast_hit_frozen(self):
        """RaycastHit is immutable (frozen dataclass)."""
        obj = MockGameObject("test")
        hit = RaycastHit(
            hit_object=obj,
            hit_point=(5.0, 5.0),
            hit_distance=5.0,
            hit_normal=(1.0, 0.0),
            collider=None,
        )

        with pytest.raises(AttributeError):
            hit.hit_distance = 10.0


class TestRaycastGeometry:
    """Geometric tests for raycast implementation."""

    def setup_method(self):
        """Create physics world for tests."""
        self.world = PhysicsWorld()
        self.obj_a = MockGameObject("object_a", x=50.0, y=50.0)
        self.obj_b = MockGameObject("object_b", x=100.0, y=50.0)

    def test_ray_vs_box_head_on_hit(self):
        """Ray hits box moving directly towards it."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        # Ray from (0, 50) pointing right (1, 0)
        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_object == self.obj_a
        assert hit.hit_distance == pytest.approx(40.0, abs=0.1)  # 50 - 10 (half width)
        assert hit.hit_normal == (-1.0, 0.0)

    def test_ray_vs_box_miss(self):
        """Ray misses box entirely."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        # Ray from (0, 100) pointing right
        hit = self.world.raycast(
            origin=(0.0, 100.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
        )

        assert hit is None

    def test_ray_vs_circle_head_on_hit(self):
        """Ray hits circle."""
        circle = CircleCollider(radius=10.0)
        circle.game_object = self.obj_a
        self.world.register_collider(circle)

        # Ray from (0, 50) pointing right
        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_object == self.obj_a
        assert hit.hit_distance == pytest.approx(40.0, abs=0.5)  # 50 - 10 (radius)
        assert abs(hit.hit_normal[0]) > 0.9  # Normal pointing left

    def test_ray_vs_circle_miss(self):
        """Ray misses circle."""
        circle = CircleCollider(radius=5.0)
        circle.game_object = self.obj_a
        self.world.register_collider(circle)

        # Ray from (0, 100) pointing right
        hit = self.world.raycast(
            origin=(0.0, 100.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
        )

        assert hit is None

    def test_ray_max_distance_respected(self):
        """Ray respects max_distance parameter."""
        circle = CircleCollider(radius=5.0)
        circle.game_object = self.obj_a
        self.world.register_collider(circle)

        # Ray from (0, 50) but max_distance too short
        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=30.0,  # Too short to reach object at x=50
        )

        assert hit is None

    def test_ray_zero_direction_handled_safely(self):
        """Ray with zero direction returns None without crash."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(50.0, 50.0),
            direction=(0.0, 0.0),  # Zero direction
            max_distance=100.0,
        )

        assert hit is None

    def test_ray_ignore_self_filters(self):
        """ignore_self parameter filters by object name."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        # Ray that would hit object_a
        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
            ignore_self="object_a",  # Ignore the object we'd hit
        )

        assert hit is None

    def test_ray_ignore_self_wrong_name_doesnt_filter(self):
        """ignore_self with wrong name doesn't filter."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
            ignore_self="other_object",  # Different object name
        )

        assert hit is not None
        assert hit.hit_object == self.obj_a

    def test_ray_include_triggers_false_filters_triggers(self):
        """include_triggers=False filters trigger colliders."""
        box = BoxCollider(width=20, height=20, is_trigger=True)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
            include_triggers=False,  # Don't include triggers
        )

        assert hit is None

    def test_ray_include_triggers_true_includes_triggers(self):
        """include_triggers=True includes trigger colliders."""
        box = BoxCollider(width=20, height=20, is_trigger=True)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
            include_triggers=True,  # Include triggers
        )

        assert hit is not None

    def test_ray_nearest_hit_deterministic(self):
        """Raycast returns nearest hit when multiple colliders present."""
        box_a = BoxCollider(width=10, height=10)
        box_a.game_object = self.obj_a
        box_b = BoxCollider(width=10, height=10)
        box_b.game_object = self.obj_b

        self.world.register_collider(box_a)
        self.world.register_collider(box_b)

        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=200.0,
        )

        # Should hit object_a (closer)
        assert hit is not None
        assert hit.hit_object == self.obj_a
        assert hit.hit_distance < 55.0  # Closer than object_b

    def test_ray_diagonal_direction(self):
        """Raycast works with diagonal ray direction."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj_a
        self.world.register_collider(box)

        # Ray from (0, 0) pointing diagonally up-right
        hit = self.world.raycast(
            origin=(0.0, 0.0),
            direction=(1.0, 1.0),  # Normalized by raycast
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_object == self.obj_a


class TestRaycastBoxNormals:
    """Tests for correct normal calculation on box hits."""

    def setup_method(self):
        """Create physics world."""
        self.world = PhysicsWorld()
        self.obj = MockGameObject("target", x=50.0, y=50.0)

    def test_box_left_edge_normal(self):
        """Ray hitting left edge has correct normal."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 50.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_normal == (-1.0, 0.0)

    def test_box_right_edge_normal(self):
        """Ray hitting right edge has correct normal."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(100.0, 50.0),
            direction=(-1.0, 0.0),
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_normal == (1.0, 0.0)

    def test_box_top_edge_normal(self):
        """Ray hitting top edge has correct normal."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(50.0, 0.0),
            direction=(0.0, 1.0),
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_normal == (0.0, -1.0)

    def test_box_bottom_edge_normal(self):
        """Ray hitting bottom edge has correct normal."""
        box = BoxCollider(width=20, height=20)
        box.game_object = self.obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(50.0, 100.0),
            direction=(0.0, -1.0),
            max_distance=100.0,
        )

        assert hit is not None
        assert hit.hit_normal == (0.0, 1.0)


class TestLogicGraphRaycastNode:
    """Tests for Raycast node in Logic Graph."""

    def test_raycast_node_definition_exists(self):
        """Raycast node definition is properly registered."""
        from engine.core.metadata import NodeDefinition
        from engine.logic.node_definitions.physics_nodes import RaycastNode

        node_def = RaycastNode.__node_definition__
        assert isinstance(node_def, NodeDefinition)
        assert node_def.id == "raycast"
        assert node_def.title_key == "Raycast"

    def test_raycast_node_has_correct_pins(self):
        """Raycast node has all required input/output pins."""
        from engine.logic.node_definitions.physics_nodes import RaycastNode

        node_def = RaycastNode.__node_definition__

        # Input pins
        input_ids = [p.id for p in node_def.inputs]
        assert "exec" in input_ids
        assert "origin_x" in input_ids
        assert "origin_y" in input_ids
        assert "direction_x" in input_ids
        assert "direction_y" in input_ids
        assert "max_distance" in input_ids
        assert "ignore_self" in input_ids
        assert "include_triggers" in input_ids

        # Output pins
        output_ids = [p.id for p in node_def.outputs]
        assert "exec_hit" in output_ids
        assert "exec_no_hit" in output_ids
        assert "hit_object" in output_ids
        assert "hit_point_x" in output_ids
        assert "hit_point_y" in output_ids
        assert "hit_distance" in output_ids
        assert "hit_normal_x" in output_ids
        assert "hit_normal_y" in output_ids

    def test_raycast_executor_registered(self):
        """Raycast executor is registered in registry."""
        from engine.logic.runtime.registry import registry

        executor = registry.executors.get("raycast")
        assert executor is not None
        assert callable(executor)

    def test_raycast_evaluator_registered(self):
        """Raycast evaluator is registered in registry."""
        from engine.logic.runtime.registry import registry

        evaluator = registry.evaluators.get("raycast")
        assert evaluator is not None
        assert callable(evaluator)

    def test_raycast_hit_exec_and_no_hit_mutual_exclusion(self):
        """Raycast returns either exec_hit or exec_no_hit, never both."""
        from engine.logic.runtime.registry import registry

        executor = registry.executors.get("raycast")

        # Mock runtime and game
        class MockRuntime:
            def __init__(self):
                self.values = {}
            def _store(self, node_id, key, value):
                self.values[(node_id, key)] = value
            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        class MockGame:
            def __init__(self):
                self.name = "player"
                self.physics_world = PhysicsWorld()

        runtime = MockRuntime()
        game = MockGame()
        dt = 0.016

        # Test with no hit
        node = {
            "id": "raycast_1",
            "properties": {
                "origin_x": 0.0,
                "origin_y": 0.0,
                "direction_x": 1.0,
                "direction_y": 0.0,
                "max_distance": 100.0,
                "ignore_self": False,
                "include_triggers": False,
            }
        }

        result = executor(runtime, node, game, dt)
        assert result == ["exec_no_hit"]
        assert "exec_no_hit" in result
        assert "exec_hit" not in result

        # Test with hit
        obj = MockGameObject("target", x=50.0, y=0.0)
        box = BoxCollider(width=10, height=10)
        box.game_object = obj
        game.physics_world.register_collider(box)

        result = executor(runtime, node, game, dt)
        assert result == ["exec_hit"]
        assert "exec_hit" in result
        assert "exec_no_hit" not in result


class TestLogicGraphRaycastE2E:
    """End-to-end tests for Raycast in Logic Graph."""

    def test_raycast_hit_outputs_populated_on_hit(self):
        """When raycast hits, output data pins are populated."""
        from engine.logic.runtime.registry import registry

        executor = registry.executors.get("raycast")
        evaluator = registry.evaluators.get("raycast")

        class MockRuntime:
            def __init__(self):
                self.values = {}
            def _store(self, node_id, key, value):
                self.values[(node_id, key)] = value
            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        class MockGame:
            def __init__(self):
                self.name = "player"
                self.physics_world = PhysicsWorld()
                self.obj = MockGameObject("target", x=50.0, y=0.0)
                box = BoxCollider(width=10, height=10)
                box.game_object = self.obj
                self.physics_world.register_collider(box)

        runtime = MockRuntime()
        game = MockGame()
        dt = 0.016

        node = {
            "id": "raycast_1",
            "properties": {
                "origin_x": 0.0,
                "origin_y": 0.0,
                "direction_x": 1.0,
                "direction_y": 0.0,
                "max_distance": 100.0,
                "ignore_self": False,
                "include_triggers": False,
            }
        }

        # Execute raycast
        result = executor(runtime, node, game, dt)
        assert result == ["exec_hit"]

        # Evaluate output pins
        node_id = "raycast_1"
        hit_object = evaluator(runtime, node_id, "hit_object", node, game, dt, set())
        assert hit_object is not None
        assert hit_object == game.obj

        hit_distance = evaluator(runtime, node_id, "hit_distance", node, game, dt, set())
        assert isinstance(hit_distance, float)
        assert hit_distance > 0

        hit_point_x = evaluator(runtime, node_id, "hit_point_x", node, game, dt, set())
        assert isinstance(hit_point_x, float)

    def test_raycast_hit_outputs_cleared_on_no_hit(self):
        """When raycast misses, hit outputs are cleared."""
        from engine.logic.runtime.registry import registry

        executor = registry.executors.get("raycast")
        evaluator = registry.evaluators.get("raycast")

        class MockRuntime:
            def __init__(self):
                self.values = {}
            def _store(self, node_id, key, value):
                self.values[(node_id, key)] = value
            def _read_input(self, node_id, port, fallback, game, dt, branch):
                return fallback

        class MockGame:
            def __init__(self):
                self.name = "player"
                self.physics_world = PhysicsWorld()

        runtime = MockRuntime()
        game = MockGame()
        dt = 0.016

        node = {
            "id": "raycast_1",
            "properties": {
                "origin_x": 0.0,
                "origin_y": 100.0,
                "direction_x": 1.0,
                "direction_y": 0.0,
                "max_distance": 100.0,
                "ignore_self": False,
                "include_triggers": False,
            }
        }

        # Execute raycast (no hit)
        result = executor(runtime, node, game, dt)
        assert result == ["exec_no_hit"]

        # Evaluate output pins - should return defaults
        node_id = "raycast_1"
        hit_object = evaluator(runtime, node_id, "hit_object", node, game, dt, set())
        assert hit_object is None

        hit_distance = evaluator(runtime, node_id, "hit_distance", node, game, dt, set())
        assert hit_distance == 0.0


class TestRaycastRegression:
    """Regression tests to ensure Phase 5B.1 and 5B.2 still work."""

    def test_collision_events_still_work(self):
        """Collision events still fire (5B.2 regression)."""
        world = PhysicsWorld()
        obj_a = MockGameObject("a", x=0.0, y=0.0)
        obj_b = MockGameObject("b", x=15.0, y=0.0)

        box_a = BoxCollider(width=20, height=20)
        box_a.game_object = obj_a
        box_b = BoxCollider(width=20, height=20)
        box_b.game_object = obj_b

        world.register_collider(box_a)
        world.register_collider(box_b)

        contacts = world.detect_collisions()
        assert len(contacts) > 0

    def test_collider_registration_still_works(self):
        """Collider registration in physics world (5B.1 regression)."""
        world = PhysicsWorld()
        obj = MockGameObject("test")
        box = BoxCollider(width=10, height=10)
        box.game_object = obj

        world.register_collider(box)
        assert box in world.colliders

        world.unregister_collider(box)
        assert box not in world.colliders


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
