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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
