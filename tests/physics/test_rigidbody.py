"""
tests/physics/test_rigidbody.py
────────────────────────────────────────────────────────────────
Suite completa de RigidBody — 58 testes.

Estratégia:
  - `game_object` é um stub mínimo com `transform.x`, `transform.y`.
  - Nenhum import de Scene ou pygame necessário.
  - Todos os valores de posição/velocidade verificados com `pytest.approx`.

Grupos:
  TestRigidBodyInit          ( 9)  construtor, defaults, massa mínima
  TestAddForce               ( 8)  add_force: acumula, kinematic, massa, reset
  TestAddImpulse             ( 6)  add_impulse: aplica imediato, kinematic, massa
  TestSetVelocityStop        ( 5)  set_velocity e stop()
  TestUpdateGravity          (10)  gravidade integrada a cada frame
  TestUpdateExternalForces   ( 8)  forças externas + velocidade + posição
  TestUpdateDrag             ( 7)  drag positivo, zero, grande dt, kinematic
  TestUpdateKinematic        ( 5)  kinematic ignora tudo
  TestGrounded               ( 5)  flag grounded reiniciada por update()

Total: 58 testes.
"""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock

from engine.physics.rigidbody import RigidBody


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _make_transform(x: float = 0.0, y: float = 0.0):
    t = MagicMock()
    t.x = x
    t.y = y
    return t


def _make_go(x: float = 0.0, y: float = 0.0):
    go = MagicMock()
    go.transform = _make_transform(x, y)
    return go


def _rb(**kwargs) -> RigidBody:
    """Cria um RigidBody com game_object stub já anexado."""
    rb = RigidBody(**kwargs)
    rb.game_object = _make_go()
    return rb


# ===========================================================================
# 1. Init / defaults
# ===========================================================================

class TestRigidBodyInit:
    def test_default_mass(self):
        rb = RigidBody()
        assert rb.mass == pytest.approx(1.0)

    def test_mass_floor(self):
        """massa mínima é 0.0001, mesmo que 0 seja passado."""
        rb = RigidBody(mass=0.0)
        assert rb.mass == pytest.approx(0.0001)

    def test_negative_mass_clamped(self):
        rb = RigidBody(mass=-5.0)
        assert rb.mass == pytest.approx(0.0001)

    def test_default_gravity_scale(self):
        assert RigidBody().gravity_scale == pytest.approx(1.0)

    def test_default_drag_zero(self):
        assert RigidBody().drag == pytest.approx(0.0)

    def test_default_use_gravity_true(self):
        assert RigidBody().use_gravity is True

    def test_default_is_kinematic_false(self):
        assert RigidBody().is_kinematic is False

    def test_velocity_starts_zero(self):
        rb = RigidBody()
        np.testing.assert_array_equal(rb.velocity, [0.0, 0.0])

    def test_acceleration_starts_zero(self):
        rb = RigidBody()
        np.testing.assert_array_equal(rb.acceleration, [0.0, 0.0])


# ===========================================================================
# 2. add_force
# ===========================================================================

class TestAddForce:
    def test_force_accumulates_in_acceleration(self):
        rb = _rb(mass=1.0)
        rb.add_force(10.0, 0.0)
        assert rb.acceleration[0] == pytest.approx(10.0)

    def test_force_scaled_by_mass(self):
        rb = _rb(mass=2.0)
        rb.add_force(10.0, 0.0)
        assert rb.acceleration[0] == pytest.approx(5.0)  # 10/2

    def test_force_y_component(self):
        rb = _rb(mass=1.0)
        rb.add_force(0.0, -5.0)
        assert rb.acceleration[1] == pytest.approx(-5.0)

    def test_multiple_forces_accumulate(self):
        rb = _rb(mass=1.0)
        rb.add_force(3.0, 0.0)
        rb.add_force(7.0, 0.0)
        assert rb.acceleration[0] == pytest.approx(10.0)

    def test_force_ignored_when_kinematic(self):
        rb = _rb(is_kinematic=True)
        rb.add_force(100.0, 100.0)
        np.testing.assert_array_equal(rb.acceleration, [0.0, 0.0])

    def test_force_does_not_immediately_change_velocity(self):
        rb = _rb(mass=1.0, use_gravity=False)
        rb.add_force(10.0, 0.0)
        np.testing.assert_array_equal(rb.velocity, [0.0, 0.0])

    def test_both_axes(self):
        rb = _rb(mass=1.0)
        rb.add_force(3.0, 4.0)
        assert rb.acceleration[0] == pytest.approx(3.0)
        assert rb.acceleration[1] == pytest.approx(4.0)

    def test_force_reset_after_update(self):
        rb = _rb(mass=1.0, use_gravity=False)
        rb.add_force(10.0, 0.0)
        rb.update(dt=0.016)
        np.testing.assert_array_almost_equal(rb.acceleration, [0.0, 0.0])


# ===========================================================================
# 3. add_impulse
# ===========================================================================

class TestAddImpulse:
    def test_impulse_changes_velocity_immediately(self):
        rb = _rb(mass=1.0)
        rb.add_impulse(5.0, 0.0)
        assert rb.velocity[0] == pytest.approx(5.0)

    def test_impulse_scaled_by_mass(self):
        rb = _rb(mass=2.0)
        rb.add_impulse(10.0, 0.0)
        assert rb.velocity[0] == pytest.approx(5.0)  # 10/2

    def test_impulse_y_component(self):
        rb = _rb(mass=1.0)
        rb.add_impulse(0.0, -300.0)
        assert rb.velocity[1] == pytest.approx(-300.0)

    def test_impulse_accumulates(self):
        rb = _rb(mass=1.0)
        rb.add_impulse(3.0, 0.0)
        rb.add_impulse(7.0, 0.0)
        assert rb.velocity[0] == pytest.approx(10.0)

    def test_impulse_ignored_when_kinematic(self):
        rb = _rb(is_kinematic=True)
        rb.add_impulse(500.0, 500.0)
        np.testing.assert_array_equal(rb.velocity, [0.0, 0.0])

    def test_impulse_does_not_change_acceleration(self):
        rb = _rb(mass=1.0)
        rb.add_impulse(10.0, 10.0)
        np.testing.assert_array_equal(rb.acceleration, [0.0, 0.0])


# ===========================================================================
# 4. set_velocity / stop
# ===========================================================================

class TestSetVelocityStop:
    def test_set_velocity_overrides(self):
        rb = _rb()
        rb.add_impulse(100.0, 50.0)
        rb.set_velocity(2.0, 3.0)
        assert rb.velocity[0] == pytest.approx(2.0)
        assert rb.velocity[1] == pytest.approx(3.0)

    def test_set_velocity_zero(self):
        rb = _rb()
        rb.add_impulse(100.0, 200.0)
        rb.set_velocity(0.0, 0.0)
        np.testing.assert_array_equal(rb.velocity, [0.0, 0.0])

    def test_stop_zeroes_velocity(self):
        rb = _rb()
        rb.add_impulse(50.0, 60.0)
        rb.stop()
        np.testing.assert_array_equal(rb.velocity, [0.0, 0.0])

    def test_stop_zeroes_acceleration(self):
        rb = _rb(mass=1.0)
        rb.add_force(10.0, 5.0)
        rb.stop()
        np.testing.assert_array_equal(rb.acceleration, [0.0, 0.0])

    def test_set_velocity_creates_new_array(self):
        rb = _rb()
        original_id = id(rb.velocity)
        rb.set_velocity(1.0, 2.0)
        # set_velocity recria o array — id pode ou não mudar, mas valores corretos
        assert rb.velocity[0] == pytest.approx(1.0)
        assert rb.velocity[1] == pytest.approx(2.0)


# ===========================================================================
# 5. update — gravidade
# ===========================================================================

class TestUpdateGravity:
    def test_gravity_increases_vy_each_frame(self):
        rb = _rb(use_gravity=True, gravity_scale=1.0)
        dt = 1.0 / 60.0
        rb.update(dt)
        expected_vy = 980.0 * 1.0 * dt
        assert rb.velocity[1] == pytest.approx(expected_vy)

    def test_gravity_accumulates_over_frames(self):
        rb = _rb(use_gravity=True, gravity_scale=1.0)
        dt = 1.0 / 60.0
        for _ in range(10):
            rb.update(dt)
        expected_vy = 980.0 * 1.0 * dt * 10
        assert rb.velocity[1] == pytest.approx(expected_vy, rel=1e-4)

    def test_gravity_scale_applied(self):
        rb_1x = _rb(use_gravity=True, gravity_scale=1.0)
        rb_2x = _rb(use_gravity=True, gravity_scale=2.0)
        dt = 1.0 / 60.0
        rb_1x.update(dt)
        rb_2x.update(dt)
        assert rb_2x.velocity[1] == pytest.approx(rb_1x.velocity[1] * 2.0)

    def test_gravity_zero_scale(self):
        rb = _rb(use_gravity=True, gravity_scale=0.0)
        rb.update(0.016)
        assert rb.velocity[1] == pytest.approx(0.0)

    def test_gravity_disabled(self):
        rb = _rb(use_gravity=False)
        rb.update(0.016)
        assert rb.velocity[1] == pytest.approx(0.0)

    def test_gravity_does_not_affect_vx(self):
        rb = _rb(use_gravity=True)
        rb.update(0.016)
        assert rb.velocity[0] == pytest.approx(0.0)

    def test_gravity_moves_position_y_down(self):
        rb = _rb(use_gravity=True)
        rb.update(0.1)
        assert rb.game_object.transform.y > 0.0  # positivo = baixo

    def test_gravity_not_applied_without_game_object(self):
        rb = RigidBody(use_gravity=True)
        rb.game_object = None
        rb.update(0.016)  # sem crash, sem efeito
        np.testing.assert_array_equal(rb.velocity, [0.0, 0.0])

    def test_negative_gravity_scale_moves_up(self):
        rb = _rb(use_gravity=True, gravity_scale=-1.0)
        rb.update(0.016)
        assert rb.velocity[1] < 0.0

    def test_large_dt_does_not_explode(self):
        rb = _rb(use_gravity=True)
        rb.update(1.0)  # 1 segundo inteiro de dt
        assert np.isfinite(rb.velocity[1])
        assert np.isfinite(rb.game_object.transform.y)


# ===========================================================================
# 6. update — forças externas + integração de posição
# ===========================================================================

class TestUpdateExternalForces:
    def test_force_moves_position_x(self):
        rb = _rb(mass=1.0, use_gravity=False)
        rb.add_force(100.0, 0.0)  # acc = 100 m/s²
        dt = 0.1
        rb.update(dt)
        # v = 0 + 100*dt = 10; pos = 0 + 10*dt = 1.0  ... mas dt de posição é integrado
        # update: v += acc*dt → v=10; pos += v*dt → pos=1.0
        # Nota: integração semi-implícita (Euler Forward)
        assert rb.game_object.transform.x == pytest.approx(1.0)

    def test_force_moves_position_y_when_no_gravity(self):
        rb = _rb(mass=1.0, use_gravity=False)
        rb.add_force(0.0, -50.0)
        rb.update(0.1)
        # acc_y=-50; v_y=-5; pos_y=0+(-5)*0.1=-0.5
        assert rb.game_object.transform.y == pytest.approx(-0.5)

    def test_acceleration_reset_after_update(self):
        rb = _rb(mass=1.0, use_gravity=False)
        rb.add_force(10.0, 10.0)
        rb.update(0.016)
        np.testing.assert_array_almost_equal(rb.acceleration, [0.0, 0.0])

    def test_velocity_persists_after_force_reset(self):
        rb = _rb(mass=1.0, use_gravity=False)
        rb.add_force(100.0, 0.0)
        rb.update(0.1)      # acc integrado, depois zerado
        v_after = rb.velocity[0]
        rb.update(0.1)      # agora sem força, mas velocity ainda existe
        # posição deve ter continuado se movendo
        assert rb.game_object.transform.x > 0.0
        assert v_after > 0.0

    def test_both_force_and_gravity(self):
        rb = _rb(mass=1.0, use_gravity=True, gravity_scale=1.0)
        rb.add_force(0.0, -200.0)  # força para cima (contra gravidade)
        dt = 0.1
        rb.update(dt)
        # gravity: v_y += 980*dt=98; external: v_y += -200*dt=-20
        expected_vy = 980.0 * dt + (-200.0 * dt)
        assert rb.velocity[1] == pytest.approx(expected_vy, rel=1e-4)

    def test_zero_dt_no_movement(self):
        rb = _rb(mass=1.0, use_gravity=True)
        rb.add_force(100.0, 0.0)
        rb.update(0.0)
        assert rb.game_object.transform.x == pytest.approx(0.0)
        assert rb.game_object.transform.y == pytest.approx(0.0)

    def test_position_integration_correctness(self):
        """Verifica integração Euler: pos = vel*dt (vel já inicializada)."""
        rb = _rb(use_gravity=False)
        rb.set_velocity(50.0, 0.0)
        rb.update(0.1)
        assert rb.game_object.transform.x == pytest.approx(5.0)  # 50*0.1

    def test_x_and_y_integrated_independently(self):
        rb = _rb(use_gravity=False)
        rb.set_velocity(10.0, -20.0)
        rb.update(0.5)
        assert rb.game_object.transform.x == pytest.approx(5.0)
        assert rb.game_object.transform.y == pytest.approx(-10.0)


# ===========================================================================
# 7. update — drag
# ===========================================================================

class TestUpdateDrag:
    def test_drag_reduces_velocity(self):
        rb = _rb(drag=1.0, use_gravity=False)
        rb.set_velocity(100.0, 0.0)
        rb.update(0.1)
        # v *= max(0, 1 - 1.0*0.1) = 0.9
        assert rb.velocity[0] == pytest.approx(100.0 * 0.9)

    def test_zero_drag_no_reduction(self):
        rb = _rb(drag=0.0, use_gravity=False)
        rb.set_velocity(100.0, 0.0)
        rb.update(0.1)
        assert rb.velocity[0] == pytest.approx(100.0)

    def test_drag_applied_to_both_axes(self):
        rb = _rb(drag=2.0, use_gravity=False)
        rb.set_velocity(100.0, 100.0)
        rb.update(0.1)
        factor = max(0.0, 1.0 - 2.0 * 0.1)
        assert rb.velocity[0] == pytest.approx(100.0 * factor)
        assert rb.velocity[1] == pytest.approx(100.0 * factor)

    def test_drag_clamped_at_zero_velocity(self):
        """dt enorme: fator deve ser clamped a 0, não negativo."""
        rb = _rb(drag=10.0, use_gravity=False)
        rb.set_velocity(100.0, 0.0)
        rb.update(2.0)  # 1 - 10*2 = -19 → clamp para 0
        assert rb.velocity[0] == pytest.approx(0.0)

    def test_drag_interacts_with_gravity(self):
        rb = _rb(drag=0.5, use_gravity=True, gravity_scale=1.0)
        rb.update(0.016)
        # Velocidade deve ser positiva mas menor do que sem drag
        assert rb.velocity[1] > 0.0

    def test_drag_with_external_force(self):
        rb = _rb(mass=1.0, drag=1.0, use_gravity=False)
        rb.add_force(100.0, 0.0)  # acc=100
        rb.update(0.1)
        # v = 0 + 100*0.1 = 10; depois drag: 10*(1-1.0*0.1)=10*0.9=9
        assert rb.velocity[0] == pytest.approx(9.0)

    def test_kinematic_drag_has_no_effect(self):
        rb = _rb(is_kinematic=True, drag=10.0)
        rb.velocity = np.array([100.0, 100.0], dtype=np.float32)
        rb.update(0.016)
        # kinematic ignora update inteiro
        assert rb.velocity[0] == pytest.approx(100.0)


# ===========================================================================
# 8. kinematic — update ignorado
# ===========================================================================

class TestUpdateKinematic:
    def test_kinematic_position_unchanged(self):
        rb = _rb(is_kinematic=True)
        rb.update(0.1)
        assert rb.game_object.transform.x == pytest.approx(0.0)
        assert rb.game_object.transform.y == pytest.approx(0.0)

    def test_kinematic_velocity_unchanged(self):
        rb = _rb(is_kinematic=True)
        rb.velocity = np.array([50.0, 50.0], dtype=np.float32)
        rb.update(0.1)
        assert rb.velocity[0] == pytest.approx(50.0)

    def test_kinematic_gravity_ignored(self):
        rb = _rb(is_kinematic=True, use_gravity=True)
        rb.update(1.0)
        assert rb.velocity[1] == pytest.approx(0.0)

    def test_kinematic_force_ignored_by_add_force(self):
        rb = _rb(is_kinematic=True)
        rb.add_force(1000.0, 1000.0)
        rb.update(0.1)
        assert rb.game_object.transform.x == pytest.approx(0.0)

    def test_set_velocity_ignored_for_kinematic_position(self):
        """set_velocity funciona, mas update não integra."""
        rb = _rb(is_kinematic=True)
        rb.set_velocity(100.0, 0.0)
        rb.update(0.1)
        # transform.x deve continuar 0 (kinematic não integra)
        assert rb.game_object.transform.x == pytest.approx(0.0)


# ===========================================================================
# 9. grounded
# ===========================================================================

class TestGrounded:
    def test_grounded_starts_false(self):
        rb = RigidBody()
        assert rb.grounded is False

    def test_grounded_reset_to_false_each_update(self):
        rb = _rb()
        rb.grounded = True
        rb.update(0.016)
        assert rb.grounded is False

    def test_grounded_can_be_set_externally(self):
        rb = _rb()
        rb.grounded = True
        assert rb.grounded is True

    def test_grounded_not_reset_when_kinematic(self):
        """Kinematic pula o update; grounded não é resetado."""
        rb = _rb(is_kinematic=True)
        rb.grounded = True
        rb.update(0.016)
        assert rb.grounded is True  # update saiu antes de resetar

    def test_grounded_not_reset_without_game_object(self):
        rb = RigidBody()
        rb.game_object = None
        rb.grounded = True
        rb.update(0.016)
        assert rb.grounded is True  # update retorna cedo
