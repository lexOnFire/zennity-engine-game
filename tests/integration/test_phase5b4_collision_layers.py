"""Tests for Phase 5B.4 - Collision Layers & Masks."""
from __future__ import annotations

import pytest
from engine.physics.physics_world import PhysicsWorld
from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.collision_layers import (
    can_collide, DEFAULT_LAYER, ALL_LAYERS, PLAYER_LAYER, ENEMY_LAYER, WORLD_LAYER, PROJECTILE_LAYER, PICKUP_LAYER
)


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


class TestCollisionLayersCore:
    """Test bitmask collision layer filtering."""

    def test_can_collide_both_directions_required(self):
        """Collision requires bidirectional acceptance."""
        # A accepts B's layer, but B doesn't accept A's
        assert not can_collide(
            a_layer=PLAYER_LAYER,
            a_mask=ENEMY_LAYER,
            b_layer=ENEMY_LAYER,
            b_mask=WORLD_LAYER  # Doesn't accept PLAYER
        )

    def test_can_collide_both_must_accept(self):
        """Both must accept each other's layer."""
        assert can_collide(
            a_layer=PLAYER_LAYER,
            a_mask=ENEMY_LAYER | WORLD_LAYER,
            b_layer=ENEMY_LAYER,
            b_mask=PLAYER_LAYER | WORLD_LAYER
        )

    def test_can_collide_same_layer_no_self_mask(self):
        """Same layer doesn't collide unless masked."""
        assert not can_collide(
            a_layer=ENEMY_LAYER,
            a_mask=PLAYER_LAYER,  # Doesn't mask itself
            b_layer=ENEMY_LAYER,
            b_mask=PLAYER_LAYER
        )

    def test_default_layer_mask_compatibility(self):
        """Default layer/mask values collide with everything."""
        assert can_collide(
            a_layer=DEFAULT_LAYER,
            a_mask=ALL_LAYERS,
            b_layer=ENEMY_LAYER,
            b_mask=ALL_LAYERS
        )

    def test_zero_mask_blocks_all(self):
        """Mask=0 blocks all collisions."""
        assert not can_collide(
            a_layer=PLAYER_LAYER,
            a_mask=0,
            b_layer=ENEMY_LAYER,
            b_mask=ALL_LAYERS
        )


class TestColliderLayerMaskProperties:
    """Test layer/mask properties on colliders."""

    def test_box_collider_default_layer_mask(self):
        """BoxCollider defaults to DEFAULT_LAYER and ALL_LAYERS."""
        box = BoxCollider()
        assert box.collision_layer == DEFAULT_LAYER
        assert box.collision_mask == ALL_LAYERS

    def test_circle_collider_default_layer_mask(self):
        """CircleCollider defaults to DEFAULT_LAYER and ALL_LAYERS."""
        circle = CircleCollider()
        assert circle.collision_layer == DEFAULT_LAYER
        assert circle.collision_mask == ALL_LAYERS

    def test_box_collider_custom_layer_mask(self):
        """BoxCollider accepts custom layer and mask in constructor."""
        box = BoxCollider(collision_layer=PLAYER_LAYER, collision_mask=ENEMY_LAYER | WORLD_LAYER)
        assert box.collision_layer == PLAYER_LAYER
        assert box.collision_mask == (ENEMY_LAYER | WORLD_LAYER)

    def test_circle_collider_custom_layer_mask(self):
        """CircleCollider accepts custom layer and mask in constructor."""
        circle = CircleCollider(collision_layer=ENEMY_LAYER, collision_mask=PLAYER_LAYER)
        assert circle.collision_layer == ENEMY_LAYER
        assert circle.collision_mask == PLAYER_LAYER

    def test_invalid_layer_defaults_to_default(self):
        """Invalid layer (0 or negative) defaults to DEFAULT_LAYER."""
        box = BoxCollider(collision_layer=0)
        assert box.collision_layer == DEFAULT_LAYER

        box2 = BoxCollider(collision_layer=-1)
        assert box2.collision_layer == DEFAULT_LAYER

    def test_invalid_mask_defaults_to_all(self):
        """Invalid mask (negative) defaults to ALL_LAYERS."""
        box = BoxCollider(collision_mask=-1)
        assert box.collision_mask == ALL_LAYERS


class TestSerializationRoundtrip:
    """Test layer/mask serialization."""

    def test_box_collider_serialize_roundtrip(self):
        """BoxCollider layer/mask survives serialize/deserialize."""
        box1 = BoxCollider(
            width=20, height=20,
            collision_layer=PLAYER_LAYER,
            collision_mask=ENEMY_LAYER | WORLD_LAYER
        )
        box1.game_object = MockGameObject("test")

        props = box1.serialize_properties()
        assert props["collision_layer"] == PLAYER_LAYER
        assert props["collision_mask"] == (ENEMY_LAYER | WORLD_LAYER)

        box2 = BoxCollider()
        box2.deserialize_properties(props)
        assert box2.collision_layer == PLAYER_LAYER
        assert box2.collision_mask == (ENEMY_LAYER | WORLD_LAYER)
        assert box2.width == 20
        assert box2.height == 20

    def test_legacy_asset_backward_compat(self):
        """Assets without layer/mask get defaults."""
        box = BoxCollider()
        legacy_props = {"width": 32.0, "height": 32.0}  # No layer/mask

        box.deserialize_properties(legacy_props)
        assert box.collision_layer == DEFAULT_LAYER
        assert box.collision_mask == ALL_LAYERS


class TestPhysicsWorldFiltering:
    """Test collision detection with layer/mask filtering."""

    def setup_method(self):
        """Create physics world."""
        self.world = PhysicsWorld()

    def test_blocked_collision_not_detected(self):
        """Colliders that don't accept each other's layers don't collide."""
        obj_a = MockGameObject("a", x=0.0, y=0.0)
        obj_b = MockGameObject("b", x=15.0, y=0.0)

        box_a = BoxCollider(width=20, height=20, collision_layer=PLAYER_LAYER, collision_mask=WORLD_LAYER)
        box_a.game_object = obj_a

        box_b = BoxCollider(width=20, height=20, collision_layer=ENEMY_LAYER, collision_mask=WORLD_LAYER)
        box_b.game_object = obj_b

        self.world.register_collider(box_a)
        self.world.register_collider(box_b)

        contacts = self.world.detect_collisions()
        assert len(contacts) == 0  # No collision because PLAYER and ENEMY don't accept each other

    def test_allowed_collision_detected(self):
        """Colliders that accept each other's layers do collide."""
        obj_a = MockGameObject("a", x=0.0, y=0.0)
        obj_b = MockGameObject("b", x=15.0, y=0.0)

        box_a = BoxCollider(width=20, height=20, collision_layer=PLAYER_LAYER, collision_mask=ENEMY_LAYER)
        box_a.game_object = obj_a

        box_b = BoxCollider(width=20, height=20, collision_layer=ENEMY_LAYER, collision_mask=PLAYER_LAYER)
        box_b.game_object = obj_b

        self.world.register_collider(box_a)
        self.world.register_collider(box_b)

        contacts = self.world.detect_collisions()
        assert len(contacts) > 0  # Collision happens


class TestTriggerLayerFiltering:
    """Test trigger detection with layer/mask."""

    def setup_method(self):
        """Create physics world."""
        self.world = PhysicsWorld()

    def test_trigger_respects_layers(self):
        """Trigger only fires if layers match."""
        obj_a = MockGameObject("player", x=0.0, y=0.0)
        obj_b = MockGameObject("pickup", x=15.0, y=0.0)

        box_a = BoxCollider(width=20, height=20, collision_layer=PLAYER_LAYER, collision_mask=PICKUP_LAYER)
        box_a.game_object = obj_a

        # Trigger that only accepts PLAYER, not ENEMY
        box_b = BoxCollider(
            width=20, height=20, is_trigger=True,
            collision_layer=PICKUP_LAYER,
            collision_mask=PLAYER_LAYER  # Only PLAYER
        )
        box_b.game_object = obj_b

        self.world.register_collider(box_a)
        self.world.register_collider(box_b)

        contacts = self.world.detect_collisions()
        assert len(contacts) > 0
        assert contacts[0].is_trigger


class TestRaycastLayerFiltering:
    """Test raycast with layer mask parameter."""

    def setup_method(self):
        """Create physics world."""
        self.world = PhysicsWorld()

    def test_raycast_default_hits_all_layers(self):
        """Raycast without layer_mask hits all colliders."""
        obj = MockGameObject("target", x=50.0, y=0.0)
        box = BoxCollider(width=10, height=10, collision_layer=ENEMY_LAYER)
        box.game_object = obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 0.0),
            direction=(1.0, 0.0),
            max_distance=100.0
        )
        assert hit is not None

    def test_raycast_layer_mask_filters(self):
        """Raycast respects layer_mask parameter."""
        obj = MockGameObject("target", x=50.0, y=0.0)
        box = BoxCollider(width=10, height=10, collision_layer=ENEMY_LAYER)
        box.game_object = obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 0.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
            layer_mask=PLAYER_LAYER  # Only hit PLAYER layer
        )
        assert hit is None  # Box is ENEMY layer, not accepted

    def test_raycast_layer_mask_allows_hit(self):
        """Raycast hits when layer_mask accepts collider layer."""
        obj = MockGameObject("target", x=50.0, y=0.0)
        box = BoxCollider(width=10, height=10, collision_layer=ENEMY_LAYER)
        box.game_object = obj
        self.world.register_collider(box)

        hit = self.world.raycast(
            origin=(0.0, 0.0),
            direction=(1.0, 0.0),
            max_distance=100.0,
            layer_mask=ENEMY_LAYER  # Accept ENEMY layer
        )
        assert hit is not None


class TestRuntimeLayerChanges:
    """Test layer/mask changes at runtime."""

    def setup_method(self):
        """Create physics world."""
        self.world = PhysicsWorld()

    def test_mask_change_blocks_existing_contact(self):
        """Changing mask should affect next collision detection."""
        obj_a = MockGameObject("a", x=0.0, y=0.0)
        obj_b = MockGameObject("b", x=15.0, y=0.0)

        box_a = BoxCollider(width=20, height=20, collision_layer=PLAYER_LAYER, collision_mask=ENEMY_LAYER)
        box_a.game_object = obj_a

        box_b = BoxCollider(width=20, height=20, collision_layer=ENEMY_LAYER, collision_mask=PLAYER_LAYER)
        box_b.game_object = obj_b

        self.world.register_collider(box_a)
        self.world.register_collider(box_b)

        # First frame: collision detected
        contacts = self.world.detect_collisions()
        assert len(contacts) > 0

        # Change mask to block collision
        box_a.collision_mask = WORLD_LAYER  # No longer accepts ENEMY

        # Next frame: no collision
        contacts = self.world.detect_collisions()
        assert len(contacts) == 0


class TestLogicGraphLayerNodes:
    """Test Logic Graph layer/mask nodes."""

    def test_get_collision_layer_registered(self):
        """Get Collision Layer node is registered."""
        from engine.logic.runtime.registry import registry
        evaluator = registry.evaluators.get("get_collision_layer")
        assert evaluator is not None

    def test_get_collision_mask_registered(self):
        """Get Collision Mask node is registered."""
        from engine.logic.runtime.registry import registry
        evaluator = registry.evaluators.get("get_collision_mask")
        assert evaluator is not None

    def test_set_collision_layer_registered(self):
        """Set Collision Layer node is registered."""
        from engine.logic.runtime.registry import registry
        executor = registry.executors.get("set_collision_layer")
        assert executor is not None

    def test_set_collision_mask_registered(self):
        """Set Collision Mask node is registered."""
        from engine.logic.runtime.registry import registry
        executor = registry.executors.get("set_collision_mask")
        assert executor is not None


class TestRegressions:
    """Ensure Phase 5B.1, 5B.2, 5B.3 still work."""

    def test_5b3_raycast_still_works(self):
        """Raycast continues to work after adding layer_mask parameter."""
        world = PhysicsWorld()
        obj = MockGameObject("target", x=50.0, y=0.0)
        box = BoxCollider(width=10, height=10)
        box.game_object = obj
        world.register_collider(box)

        hit = world.raycast(
            origin=(0.0, 0.0),
            direction=(1.0, 0.0),
            max_distance=100.0
        )
        assert hit is not None

    def test_5b2_collision_events_work(self):
        """Collision events still fire without layer/mask specified."""
        world = PhysicsWorld()
        obj_a = MockGameObject("a", x=0.0, y=0.0)
        obj_b = MockGameObject("b", x=15.0, y=0.0)

        box_a = BoxCollider(width=20, height=20)  # Defaults to DEFAULT_LAYER, ALL_LAYERS
        box_a.game_object = obj_a

        box_b = BoxCollider(width=20, height=20)
        box_b.game_object = obj_b

        world.register_collider(box_a)
        world.register_collider(box_b)

        contacts = world.detect_collisions()
        assert len(contacts) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
