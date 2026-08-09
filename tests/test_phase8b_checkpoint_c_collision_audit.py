"""
PHASE 8B CHECKPOINT C — COLLISION AUDIT

Diagnostic tests to understand why Player traverses Wall.

Tests:
1. move_by physics contract
2. RigidBody velocity contract
3. Collision detection (AABB)
4. Collision response (solid blocking)
5. Sliding behavior
6. Contact state management
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from engine.core.game_object import GameObject
from engine.core.transform import Transform
from engine.core.scene import Scene
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.physics.physics_world import PhysicsWorld


class TestMoveByphysicsContract:
    """Test A: Verify move_by correctly detects RigidBody and sets velocity"""

    def test_move_by_finds_rigidbody_dynamic(self):
        """move_by should set velocity on dynamic RigidBody"""
        # Setup
        scene = Scene("TestScene")
        player = GameObject("Player")
        player.transform = Transform(x=0, y=0)
        player.scene = scene

        rb = RigidBody()
        rb.game_object = player
        rb.is_kinematic = False
        rb.velocity = [0.0, 0.0]
        player.add_component(rb)

        # Simulate move_by node
        from engine.logic.runtime.nodes.movement_nodes import execute_move_by

        runtime_mock = MagicMock()
        runtime_mock._read_target.return_value = player
        runtime_mock._read_input.side_effect = [5.0, 0.0]  # x=5.0 (speed), y=0

        node = {
            "id": "move_by_1",
            "type": "move_by",
            "properties": {"x": 5.0, "y": 0.0}
        }

        dt = 0.016  # ~60 FPS

        # Execute
        execute_move_by(runtime_mock, node, player, dt)

        # Verify
        assert rb.velocity[0] == 5.0, f"Expected velocity[0]=5.0, got {rb.velocity[0]}"
        assert rb.velocity[1] == 0.0, f"Expected velocity[1]=0.0, got {rb.velocity[1]}"

    def test_move_by_skips_kinematic_rigidbody(self):
        """move_by should call move() for kinematic or non-existent RigidBody"""
        scene = Scene("TestScene")
        player = GameObject("Player")
        player.transform = Transform(x=0, y=0)
        player.scene = scene

        # NO RigidBody, so move_by should call player.move()
        player.move = MagicMock()

        from engine.logic.runtime.nodes.movement_nodes import execute_move_by

        runtime_mock = MagicMock()
        runtime_mock._read_target.return_value = player
        runtime_mock._read_input.side_effect = [5.0, 0.0]

        node = {"id": "move_by_1", "type": "move_by", "properties": {}}
        dt = 0.016

        execute_move_by(runtime_mock, node, player, dt)

        # Should call move() since no RigidBody
        player.move.assert_called_once()


class TestPhysicsWorldCollisionDetection:
    """Test that PhysicsWorld detects Player vs Wall collisions"""

    def test_physics_detects_aabb_overlap(self):
        """PhysicsWorld should detect AABB overlap between Player and Wall"""
        scene = Scene("TestScene")

        # Player: x=0, y=0, w=36, h=48 (dynamic)
        player = GameObject("Player")
        player.transform = Transform(x=0, y=0, w=36, h=48)
        player.scene = scene

        rb_player = RigidBody()
        rb_player.game_object = player
        rb_player.is_kinematic = False
        rb_player.velocity = [100.0, 0.0]  # Moving right
        player.add_component(rb_player)

        coll_player = BoxCollider(width=36, height=48)
        coll_player.game_object = player
        player.add_component(coll_player)

        # Wall: x=300, y=150, w=600, h=32 (kinematic static)
        wall = GameObject("Wall")
        wall.transform = Transform(x=300, y=150, w=600, h=32)
        wall.scene = scene

        rb_wall = RigidBody()
        rb_wall.game_object = wall
        rb_wall.is_kinematic = True  # Static
        wall.add_component(rb_wall)

        coll_wall = BoxCollider(width=600, height=32)
        coll_wall.game_object = wall
        wall.add_component(coll_wall)

        scene.add_game_object(player)
        scene.add_game_object(wall)

        # Physics world setup
        physics = PhysicsWorld(runtime_scene=scene)
        physics.build_from_scene(scene)

        # Run collision detection
        contacts = physics.detect_collisions()

        # Verify
        assert len(contacts) > 0, (
            f"Expected collision detected between Player and Wall, "
            f"but got {len(contacts)} contacts. "
            f"Player rect: {coll_player.rect}, "
            f"Wall rect: {coll_wall.rect}"
        )

        contact = contacts[0]
        assert contact.a in [coll_player, coll_wall], "Player collider not in contact"
        assert contact.b in [coll_player, coll_wall], "Wall collider not in contact"
        assert not contact.is_trigger, "Contact should be solid, not trigger"


class TestSolidCollisionResponse:
    """Test that PhysicsWorld actually blocks Player from penetrating Wall"""

    def test_solid_response_stops_player_at_wall(self):
        """Player moving into Wall should be stopped, not penetrate"""
        scene = Scene("TestScene")

        # Player: moving right from x=-100
        player = GameObject("Player")
        player.transform = Transform(x=-100, y=150, w=36, h=48)
        player.scene = scene

        rb_player = RigidBody()
        rb_player.game_object = player
        rb_player.is_kinematic = False
        rb_player.velocity = [100.0, 0.0]
        player.add_component(rb_player)

        coll_player = BoxCollider(width=36, height=48)
        coll_player.game_object = player
        player.add_component(coll_player)

        # Wall: x=0 (immovable)
        wall = GameObject("Wall")
        wall.transform = Transform(x=0, y=150, w=60, h=48)
        wall.scene = scene

        rb_wall = RigidBody()
        rb_wall.game_object = wall
        rb_wall.is_kinematic = True
        wall.add_component(rb_wall)

        coll_wall = BoxCollider(width=60, height=48)
        coll_wall.game_object = wall
        wall.add_component(coll_wall)

        scene.add_game_object(player)
        scene.add_game_object(wall)

        # Physics step
        physics = PhysicsWorld(runtime_scene=scene)
        physics.build_from_scene(scene)

        # Simulate: Player moves right, should hit Wall and stop
        dt = 0.1
        for _ in range(10):
            # Integrate velocity
            rb_player.integrate(dt)

            # Collision detection + response
            physics.detect_collisions()

            # Player should not penetrate Wall
            player_rect = coll_player.rect
            wall_rect = coll_wall.rect

            # Check no penetration
            penetrates_right = (player_rect.left < wall_rect.right and
                               player_rect.right > wall_rect.left)

            if penetrates_right:
                # If there IS overlap, velocity should have been zeroed
                assert rb_player.velocity[0] <= 0.0, (
                    f"Player penetrating Wall but velocity not stopped! "
                    f"vel_x={rb_player.velocity[0]}, "
                    f"player_x={player.transform.x}, wall_x={wall.transform.x}"
                )


class TestDynamicVsStaticBehavior:
    """Verify Wall must have correct RigidBody config to be static"""

    def test_wall_without_rigidbody_is_static(self):
        """Wall with only Collider (no RigidBody) should block Player"""
        scene = Scene("TestScene")

        # Player: dynamic
        player = GameObject("Player")
        player.transform = Transform(x=0, y=0, w=36, h=48)
        player.scene = scene

        rb_player = RigidBody()
        rb_player.game_object = player
        rb_player.is_kinematic = False
        rb_player.velocity = [50.0, 0.0]
        player.add_component(rb_player)

        coll_player = BoxCollider(width=36, height=48)
        coll_player.game_object = player
        player.add_component(coll_player)

        # Wall: NO RigidBody (should be treated as static)
        wall = GameObject("Wall")
        wall.transform = Transform(x=100, y=0, w=60, h=200)
        wall.scene = scene

        coll_wall = BoxCollider(width=60, height=200)
        coll_wall.game_object = wall
        wall.add_component(coll_wall)

        scene.add_game_object(player)
        scene.add_game_object(wall)

        physics = PhysicsWorld(runtime_scene=scene)
        physics.build_from_scene(scene)
        contacts = physics.detect_collisions()

        # Wall without RigidBody should still be treated as solid
        assert len(contacts) == 1, f"Expected 1 contact, got {len(contacts)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
