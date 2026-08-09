"""Phase 8B — Checkpoint C.1: Solid Collision Resolution & Physics World Audit.

Validates:
- Solid collision response in PhysicsWorld (penetration resolution & velocity zeroing)
- Dynamic vs Static body collision blocking (Player stops at Wall)
- Player can move away from Wall after collision
- Trigger colliders do NOT block solid movement
- Collision events still fire on solid contact
"""
from pathlib import Path
import pytest
from engine.core.game_object import GameObject
from engine.physics.physics_world import PhysicsWorld
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider


def test_move_by_transform_behavior():
    player = GameObject("Player")
    player.transform.x = 0.0
    player.transform.y = 0.0
    # Object without RigidBody moves transform position directly
    player.transform.x += 10.0
    assert player.transform.x == 10.0


def test_rigidbody_velocity_behavior():
    player = GameObject("Player")
    rb = RigidBody(use_gravity=False, is_kinematic=False)
    player.add_component(rb)
    rb.set_velocity(100.0, 0.0)
    assert rb.velocity[0] == 100.0
    assert rb.velocity[1] == 0.0


def test_dynamic_body_hits_static_wall():
    world = PhysicsWorld()
    player = GameObject("Player")
    player.transform.x = 0.0
    player.transform.y = 0.0
    rb = RigidBody(use_gravity=False, is_kinematic=False)
    player.add_component(rb)
    col_p = BoxCollider(width=48.0, height=48.0, is_trigger=False)
    player.add_component(col_p)

    wall = GameObject("Wall")
    wall.transform.x = 50.0
    wall.transform.y = 0.0
    col_w = BoxCollider(width=32.0, height=128.0, is_trigger=False)
    wall.add_component(col_w)

    world.register_rigidbody(rb)
    world.register_collider(col_p)
    world.register_collider(col_w)

    rb.set_velocity(100.0, 0.0)
    dt = 0.016
    for _ in range(50):
        world.step(dt)

    # Player left edge at 0 - 24 = -24, Wall left edge at 50 - 16 = 34
    # Player right edge should stop at 34, so Player center X should be <= 10
    assert player.transform.x <= 10.0, f"Player passed through wall: X={player.transform.x}"


def test_dynamic_body_stops_at_wall():
    world = PhysicsWorld()
    player = GameObject("Player")
    player.transform.x = 0.0
    player.transform.y = 0.0
    rb = RigidBody(use_gravity=False, is_kinematic=False)
    player.add_component(rb)
    col_p = BoxCollider(width=48.0, height=48.0, is_trigger=False)
    player.add_component(col_p)

    wall = GameObject("Wall")
    wall.transform.x = 50.0
    wall.transform.y = 0.0
    col_w = BoxCollider(width=32.0, height=128.0, is_trigger=False)
    wall.add_component(col_w)

    world.register_rigidbody(rb)
    world.register_collider(col_p)
    world.register_collider(col_w)

    rb.set_velocity(100.0, 0.0)
    dt = 0.016
    for _ in range(50):
        world.step(dt)

    # Final position must remain blocked before Wall left edge (X=34)
    final_x = player.transform.x
    world.step(dt)
    assert player.transform.x == final_x


def test_body_can_move_away_from_wall():
    world = PhysicsWorld()
    player = GameObject("Player")
    player.transform.x = 0.0
    player.transform.y = 0.0
    rb = RigidBody(use_gravity=False, is_kinematic=False)
    player.add_component(rb)
    col_p = BoxCollider(width=48.0, height=48.0, is_trigger=False)
    player.add_component(col_p)

    wall = GameObject("Wall")
    wall.transform.x = 50.0
    wall.transform.y = 0.0
    col_w = BoxCollider(width=32.0, height=128.0, is_trigger=False)
    wall.add_component(col_w)

    world.register_rigidbody(rb)
    world.register_collider(col_p)
    world.register_collider(col_w)

    # 1. Drive right into Wall
    rb.set_velocity(100.0, 0.0)
    dt = 0.016
    for _ in range(30):
        world.step(dt)
    blocked_x = player.transform.x

    # 2. Drive left away from Wall
    rb.set_velocity(-100.0, 0.0)
    for _ in range(10):
        world.step(dt)

    assert player.transform.x < blocked_x, "Player failed to move away from wall"


def test_trigger_does_not_block():
    world = PhysicsWorld()
    player = GameObject("Player")
    player.transform.x = 0.0
    player.transform.y = 0.0
    rb = RigidBody(use_gravity=False, is_kinematic=False)
    player.add_component(rb)
    col_p = BoxCollider(width=48.0, height=48.0, is_trigger=False)
    player.add_component(col_p)

    trigger = GameObject("Trigger")
    trigger.transform.x = 50.0
    trigger.transform.y = 0.0
    col_t = BoxCollider(width=32.0, height=128.0, is_trigger=True)
    trigger.add_component(col_t)

    world.register_rigidbody(rb)
    world.register_collider(col_p)
    world.register_collider(col_t)

    rb.set_velocity(100.0, 0.0)
    dt = 0.016
    for _ in range(50):
        world.step(dt)

    # Player passes right through trigger collider
    assert player.transform.x > 30.0, "Trigger incorrectly blocked player movement"


def test_collision_event_still_fires():
    world = PhysicsWorld()
    player = GameObject("Player")
    player.transform.x = 0.0
    player.transform.y = 0.0
    rb = RigidBody(use_gravity=False, is_kinematic=False)
    player.add_component(rb)
    col_p = BoxCollider(width=48.0, height=48.0, is_trigger=False)
    player.add_component(col_p)

    fired = False

    def on_collision(other):
        nonlocal fired
        fired = True

    col_p.on_collision_enter = on_collision

    wall = GameObject("Wall")
    wall.transform.x = 50.0
    wall.transform.y = 0.0
    col_w = BoxCollider(width=32.0, height=128.0, is_trigger=False)
    wall.add_component(col_w)

    world.register_rigidbody(rb)
    world.register_collider(col_p)
    world.register_collider(col_w)

    rb.set_velocity(100.0, 0.0)
    dt = 0.016
    for _ in range(30):
        world.step(dt)

    assert fired is True, "Collision enter event did not fire"
