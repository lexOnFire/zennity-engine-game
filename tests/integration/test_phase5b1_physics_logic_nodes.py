"""
PHASE 5B.1: Physics Logic Graph Core Fixes

Complete test suite for corrected Physics Logic Graph nodes.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock

from engine.physics.rigidbody import RigidBody
from engine.game_object import GameObject
from engine.core.scene import Scene
from engine.logic.runtime.nodes.physics_nodes import (
    RIGIDBODY_PROPERTIES,
    execute_modify_rigidbody,
    execute_apply_force,
    evaluate_get_rigidbody_velocity_x,
    evaluate_get_rigidbody_velocity_y,
    evaluate_get_rigidbody_mass,
    evaluate_get_rigidbody_gravity_scale,
    evaluate_get_rigidbody_use_gravity,
    evaluate_get_rigidbody_is_kinematic,
)


def _make_game_with_objects(scene: Scene) -> MagicMock:
    """Create a mock game object with find_object()."""
    game = MagicMock()

    def find_object_impl(name):
        for obj in scene.game_objects:
            if obj.name == name:
                return obj
        return None

    game.find_object = find_object_impl
    return game


class TestPropertySchema:
    def test_schema_valid(self):
        expected = {"mass", "gravity_scale", "drag", "use_gravity", "is_kinematic", "velocity_x", "velocity_y"}
        assert set(RIGIDBODY_PROPERTIES.keys()) == expected

    def test_schema_rejects_invalid(self):
        assert "angular_drag" not in RIGIDBODY_PROPERTIES
        assert "constraints" not in RIGIDBODY_PROPERTIES


class TestModifyRigidbody:
    def setup_method(self):
        self.scene = Scene("TestScene")
        self.player = GameObject("player")
        self.rb = RigidBody()
        self.player.add_component(self.rb)
        self.scene.game_objects.append(self.player)
        self.player.scene = self.scene
        self.game = _make_game_with_objects(self.scene)

    def test_modify_mass(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'mass', 'value': 5.0}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert self.rb.mass == pytest.approx(5.0)

    def test_modify_gravity_scale(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'gravity_scale', 'value': 2.0}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert self.rb.gravity_scale == pytest.approx(2.0)

    def test_modify_drag(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'drag', 'value': 0.5}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert self.rb.drag == pytest.approx(0.5)

    def test_velocity_x_keeps_numpy(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'velocity_x', 'value': 100.0}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert isinstance(self.rb.velocity, np.ndarray)
        assert self.rb.velocity[0] == pytest.approx(100.0)

    def test_velocity_y_keeps_numpy(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'velocity_y', 'value': -50.0}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert isinstance(self.rb.velocity, np.ndarray)
        assert self.rb.velocity[1] == pytest.approx(-50.0)

    def test_reject_angular_drag(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'angular_drag', 'value': 0.5}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["failure"]

    def test_reject_constraints(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'constraints', 'value': 'xyz'}}
        result = execute_modify_rigidbody(runtime, node, self.game, 0.016)
        assert result == ["failure"]


class TestApplyForce:
    def setup_method(self):
        self.scene = Scene("TestScene")
        self.player = GameObject("player")
        self.rb = RigidBody(mass=1.0, use_gravity=False)
        self.player.add_component(self.rb)
        self.scene.game_objects.append(self.player)
        self.player.scene = self.scene
        self.game = _make_game_with_objects(self.scene)

    def test_force_mode(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'force_x': 100.0, 'force_y': 0.0, 'force_mode': 'force'}}
        result = execute_apply_force(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert self.rb.acceleration[0] > 0.0

    def test_impulse_mode(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'force_x': 0.0, 'force_y': -300.0, 'force_mode': 'impulse'}}
        result = execute_apply_force(runtime, node, self.game, 0.016)
        assert result == ["success"]
        assert self.rb.velocity[1] < 0.0

    def test_invalid_mode(self):
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'force_x': 100.0, 'force_y': 0.0, 'force_mode': 'invalid'}}
        result = execute_apply_force(runtime, node, self.game, 0.016)
        assert result == ["failure"]


class TestTargetResolution:
    def test_target_not_found(self):
        scene = Scene("TestScene")
        game = _make_game_with_objects(scene)
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'nonexistent', 'property': 'mass', 'value': 5.0}}
        result = execute_modify_rigidbody(runtime, node, game, 0.016)
        assert result == ["failure"]

    def test_no_rigidbody(self):
        scene = Scene("TestScene")
        go = GameObject("empty")
        scene.game_objects.append(go)
        go.scene = scene
        game = _make_game_with_objects(scene)
        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'empty', 'property': 'mass', 'value': 5.0}}
        result = execute_modify_rigidbody(runtime, node, game, 0.016)
        assert result == ["failure"]


class TestGetters:
    def setup_method(self):
        self.scene = Scene("TestScene")
        self.player = GameObject("player")
        self.rb = RigidBody(mass=2.0, gravity_scale=0.5, use_gravity=False, is_kinematic=True)
        self.rb.set_velocity(100.0, -50.0)
        self.player.add_component(self.rb)
        self.scene.game_objects.append(self.player)
        self.player.scene = self.scene
        self.game = _make_game_with_objects(self.scene)

    def test_get_velocity_x(self):
        node = {'properties': {'target': 'player'}}
        result = evaluate_get_rigidbody_velocity_x(MagicMock(), 'n1', 'v', node, self.game, 0.016, set())
        assert result == pytest.approx(100.0)

    def test_get_velocity_y(self):
        node = {'properties': {'target': 'player'}}
        result = evaluate_get_rigidbody_velocity_y(MagicMock(), 'n1', 'v', node, self.game, 0.016, set())
        assert result == pytest.approx(-50.0)

    def test_get_mass(self):
        node = {'properties': {'target': 'player'}}
        result = evaluate_get_rigidbody_mass(MagicMock(), 'n1', 'v', node, self.game, 0.016, set())
        assert result == pytest.approx(2.0)

    def test_get_gravity_scale(self):
        node = {'properties': {'target': 'player'}}
        result = evaluate_get_rigidbody_gravity_scale(MagicMock(), 'n1', 'v', node, self.game, 0.016, set())
        assert result == pytest.approx(0.5)

    def test_get_use_gravity(self):
        node = {'properties': {'target': 'player'}}
        result = evaluate_get_rigidbody_use_gravity(MagicMock(), 'n1', 'v', node, self.game, 0.016, set())
        assert result is False

    def test_get_is_kinematic(self):
        node = {'properties': {'target': 'player'}}
        result = evaluate_get_rigidbody_is_kinematic(MagicMock(), 'n1', 'v', node, self.game, 0.016, set())
        assert result is True


class TestE2E:
    def test_apply_force_changes_velocity(self):
        scene = Scene("TestScene")
        player = GameObject("player")
        rb = RigidBody(mass=1.0, use_gravity=False)
        player.add_component(rb)
        scene.game_objects.append(player)
        player.scene = scene
        game = _make_game_with_objects(scene)

        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'force_x': 100.0, 'force_y': 0.0, 'force_mode': 'force'}}
        result = execute_apply_force(runtime, node, game, 0.016)
        assert result == ["success"]

        rb.update(0.1)
        assert rb.velocity[0] > 0.0

    def test_serialization_roundtrip(self):
        scene = Scene("TestScene")
        player = GameObject("player")
        rb = RigidBody()
        player.add_component(rb)
        scene.game_objects.append(player)
        player.scene = scene
        game = _make_game_with_objects(scene)

        runtime = MagicMock()
        node = {'id': 'n1', 'properties': {'target': 'player', 'property': 'velocity_x', 'value': 50.0}}
        execute_modify_rigidbody(runtime, node, game, 0.016)

        data = rb.serialize_properties()
        assert isinstance(data['velocity'], list)
        assert data['velocity'][0] == pytest.approx(50.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
