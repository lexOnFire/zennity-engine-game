"""Testes unitários e de integração para SystemScheduler e TickPolicy (Phase 11 - Item 11.1)."""
from __future__ import annotations

import math
import pytest
from engine.system import System, SystemPriority, SystemScheduler, TickPolicy


class DummyCountingSystem(System):
    def __init__(self, name: str = "Dummy", priority: int = 1000) -> None:
        super().__init__()
        self._name = name
        self.priority = priority
        self.start_calls = 0
        self.update_calls = 0
        self.shutdown_calls = 0
        self.received_dts: list[float] = []

    @property
    def name(self) -> str:
        return self._name

    def start(self) -> None:
        self.start_calls += 1

    def update(self, scene, dt: float) -> None:
        self.update_calls += 1
        self.received_dts.append(dt)

    def shutdown(self) -> None:
        self.shutdown_calls += 1


def test_tick_policy_validation():
    # Valid
    p_frame = TickPolicy.every_frame()
    assert not p_frame.is_fixed
    assert p_frame.hz is None

    p_60 = TickPolicy.fixed_hz(60)
    assert p_60.is_fixed
    assert p_60.hz == 60.0
    assert math.isclose(p_60.interval, 1.0 / 60.0)

    p_frac = TickPolicy.fixed_hz(2.5)
    assert p_frac.hz == 2.5
    assert math.isclose(p_frac.interval, 0.4)

    # Invalid
    with pytest.raises(ValueError):
        TickPolicy.fixed_hz(0)
    with pytest.raises(ValueError):
        TickPolicy.fixed_hz(-10)
    with pytest.raises(ValueError):
        TickPolicy.fixed_hz(float("nan"))
    with pytest.raises(ValueError):
        TickPolicy.fixed_hz(float("inf"))
    with pytest.raises(ValueError):
        TickPolicy.fixed_hz("invalid")  # type: ignore


def test_scheduler_every_frame_and_fixed_hz():
    scheduler = SystemScheduler()
    sys_frame = DummyCountingSystem("FrameSys")
    sys_10hz = DummyCountingSystem("10HzSys")

    scheduler.register(sys_frame, TickPolicy.every_frame())
    scheduler.register(sys_10hz, TickPolicy.fixed_hz(10))

    assert sys_frame.start_calls == 1
    assert sys_10hz.start_calls == 1

    # Frame 1: 0.05s
    scheduler.update(None, 0.05)
    assert sys_frame.update_calls == 1
    assert sys_10hz.update_calls == 0  # Precisa de 0.10s

    # Frame 2: 0.05s (Total 0.10s)
    scheduler.update(None, 0.05)
    assert sys_frame.update_calls == 2
    assert sys_10hz.update_calls == 1
    assert math.isclose(sys_10hz.received_dts[0], 0.1)


def test_catch_up_limit_and_excess_drop():
    scheduler = SystemScheduler(max_catch_up_steps=4)
    sys_10hz = DummyCountingSystem("10HzSys")
    scheduler.register(sys_10hz, TickPolicy.fixed_hz(10))

    # Delta time muito grande (2.0s = 20 ticks teóricos a 10Hz)
    scheduler.update(None, 2.0)

    # Limitado a 4 ticks
    assert sys_10hz.update_calls == 4

    # Profiling reflete ticks executados e descartados
    stats = scheduler.profiling_snapshot()["10HzSys"]
    assert stats["executed_ticks"] == 4
    assert stats["dropped_ticks"] == 16  # 20 - 4 = 16


def test_deterministic_priority_and_insertion_order():
    scheduler = SystemScheduler()
    execution_order = []

    class OrderSystem(System):
        def __init__(self, name: str, prio: int):
            super().__init__()
            self._name = name
            self.priority = prio
        @property
        def name(self) -> str:
            return self._name
        def update(self, scene, dt: float):
            execution_order.append(self._name)

    sys_b = OrderSystem("B", prio=200)
    sys_a = OrderSystem("A", prio=100)
    sys_c = OrderSystem("C", prio=200)  # Mesma prioridade que B, inserido depois

    scheduler.register(sys_b)
    scheduler.register(sys_a)
    scheduler.register(sys_c)

    scheduler.update(None, 0.016)
    # A (100), depois B (200, primeiro inserido), depois C (200, segundo inserido)
    assert execution_order == ["A", "B", "C"]


def test_duplicate_registration_rejected():
    scheduler = SystemScheduler()
    sys = DummyCountingSystem()
    scheduler.register(sys)
    with pytest.raises(ValueError, match="já registrado"):
        scheduler.register(sys)


def test_remove_and_shutdown():
    scheduler = SystemScheduler()
    sys = DummyCountingSystem()
    scheduler.register(sys)
    assert sys.start_calls == 1

    scheduler.remove(sys)
    assert sys.shutdown_calls == 1

    scheduler.update(None, 0.1)
    assert sys.update_calls == 0


def test_pause_resume_and_reset():
    scheduler = SystemScheduler()
    sys = DummyCountingSystem()
    scheduler.register(sys, TickPolicy.fixed_hz(10))

    # Run 0.1s -> 1 tick
    scheduler.update(None, 0.1)
    assert sys.update_calls == 1

    # Pause
    scheduler.pause()
    scheduler.update(None, 10.0)  # 10s não geram ticks nem acumulam
    assert sys.update_calls == 1

    # Resume
    scheduler.resume()
    scheduler.update(None, 0.1)  # Apenas este 0.1s é processado
    assert sys.update_calls == 2

    # Reset
    scheduler.reset()
    stats = scheduler.profiling_snapshot()["Dummy"]
    assert stats["calls"] == 0


def test_invalid_dt_rejected():
    scheduler = SystemScheduler()
    sys = DummyCountingSystem()
    scheduler.register(sys)

    with pytest.raises(ValueError):
        scheduler.update(None, -0.01)
    with pytest.raises(ValueError):
        scheduler.update(None, float("nan"))
    with pytest.raises(ValueError):
        scheduler.update(None, float("inf"))
    with pytest.raises(ValueError):
        scheduler.update(None, "invalid")  # type: ignore


def test_long_run_timing_drift_600s():
    scheduler = SystemScheduler()
    sys_10hz = DummyCountingSystem("10HzSys")
    scheduler.register(sys_10hz, TickPolicy.fixed_hz(10))

    # Simula 600 segundos a 60 FPS (dt = 1/60s)
    dt = 1.0 / 60.0
    total_frames = 600 * 60  # 36.000 frames
    for _ in range(total_frames):
        scheduler.update(None, dt)

    # A 10Hz por 600s, esperamos exatamente 6000 ticks (com margem de 1 tick por float epsilon)
    assert abs(sys_10hz.update_calls - 6000) <= 1


def test_frame_pattern_invariance():
    # 10Hz system rodando por 1.0s com diferentes padrões de frame rate
    def run_simulation(dts: list[float]) -> int:
        sched = SystemScheduler()
        s = DummyCountingSystem()
        sched.register(s, TickPolicy.fixed_hz(10))
        for dt in dts:
            sched.update(None, dt)
        return s.update_calls

    # Padrão 60 FPS (60 frames de 1/60s)
    calls_60 = run_simulation([1.0 / 60.0] * 60)
    # Padrão 30 FPS (30 frames de 1/30s)
    calls_30 = run_simulation([1.0 / 30.0] * 30)
    # Padrão irregular (mistura de 0.016, 0.033, 0.05)
    irregular_dts = [0.016] * 30 + [0.033] * 10 + [0.05] * 3 + [0.04]  # soma 1.0s
    calls_irregular = run_simulation(irregular_dts)

    assert calls_60 == 10
    assert calls_30 == 10
    assert calls_irregular == 10


def test_performance_sanity_benchmark():
    scheduler = SystemScheduler()
    systems = [DummyCountingSystem(f"Sys_{i}", priority=i) for i in range(100)]
    for s in systems:
        scheduler.register(s, TickPolicy.fixed_hz(60))

    # 1000 frames
    for _ in range(1000):
        scheduler.update(None, 1.0 / 60.0)

    stats = scheduler.profiling_snapshot()
    assert len(stats) == 100
    assert stats["Sys_0"]["calls"] == 1000
