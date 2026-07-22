from editor.runtime.viewport_physics_stepper import ViewportPhysicsStepper


def test_physics_stepper_applies_gravity_and_lands_on_static_floor() -> None:
    objects = {
        "Player": {"x": 0.0, "y": 0.0, "w": 10.0, "h": 10.0, "active": True,
                   "rigidbody": {"use_gravity": True, "is_kinematic": False}, "collider": {"type": "box"}},
        "Floor": {"x": 0.0, "y": 10.0, "w": 100.0, "h": 10.0, "active": True,
                  "rigidbody": {"is_kinematic": True}, "collider": {"type": "box"}},
    }
    velocities, grounded = {}, {}

    ViewportPhysicsStepper().step(objects, velocities, grounded, {}, 1, 0.1)

    assert objects["Player"]["y"] == 0.0
    assert velocities["Player"] == 0.0
    assert grounded["Player"] is True


def test_physics_stepper_respects_logic_owned_vertical_axis() -> None:
    objects = {"Player": {"x": 0.0, "y": 0.0, "w": 10.0, "h": 10.0, "active": True,
                          "rigidbody": {"use_gravity": True}, "collider": {}}}
    velocities = {"Player": 20.0}
    ViewportPhysicsStepper().step(objects, velocities, {}, {"Player": {"y"}}, 1, 0.1)
    assert velocities["Player"] == 0.0 and objects["Player"]["y"] == 0.0
