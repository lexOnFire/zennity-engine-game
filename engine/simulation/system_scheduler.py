"""engine/simulation/system_scheduler.py
────────────────────────────────────────────────────────────────
Agendador genérico de sistemas de simulação com políticas de tick desacopladas.

Oferece:
  - TickPolicy (every_frame ou fixed_hz)
  - Accumulator determinístico com limite de catch-up anti-spiral-of-death
  - Validação estrita de delta time e frequência
  - Ordem de execução estável por prioridade e inserção
  - Profiling de baixa sobrecarga
  - Desacoplamento total de Qt, GameObject, LogicGraph e Threads.
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class TickPolicy:
    """Define a política de execução de um System."""

    def __init__(self, is_fixed: bool, hz: Optional[float] = None) -> None:
        self.is_fixed = is_fixed
        self.hz = hz
        self.interval = (1.0 / hz) if (is_fixed and hz is not None) else 0.0

    @classmethod
    def every_frame(cls) -> "TickPolicy":
        """Executa a cada frame com o frame_dt real."""
        return cls(is_fixed=False, hz=None)

    @classmethod
    def fixed_hz(cls, hz: float) -> "TickPolicy":
        """Executa em frequência fixa (ex: 60Hz, 30Hz, 10Hz, 1Hz, 2.5Hz)."""
        if not isinstance(hz, (int, float)):
            raise ValueError(f"Frequência 'hz' deve ser numérica. Recebido: {type(hz).__name__}")
        if math.isnan(hz) or math.isinf(hz):
            raise ValueError(f"Frequência 'hz' inválida (NaN ou Inf). Recebido: {hz}")
        if hz <= 0:
            raise ValueError(f"Frequência 'hz' deve ser estritamente positiva (> 0). Recebido: {hz}")
        return cls(is_fixed=True, hz=float(hz))

    def __repr__(self) -> str:
        if not self.is_fixed:
            return "<TickPolicy EVERY_FRAME>"
        return f"<TickPolicy FIXED hz={self.hz:.2f} interval={self.interval:.4f}s>"


class _SystemEntry:
    """Entrada interna de registro de um sistema no agendador."""

    def __init__(
        self,
        system: Any,
        policy: TickPolicy,
        priority: int,
        insertion_order: int,
    ) -> None:
        self.system = system
        self.policy = policy
        self.priority = priority
        self.insertion_order = insertion_order
        self.accumulator: float = 0.0
        self.initialized: bool = False
        
        # Profiling stats
        self.calls: int = 0
        self.total_time_s: float = 0.0
        self.last_duration_s: float = 0.0
        self.max_duration_s: float = 0.0
        self.scheduled_ticks: int = 0
        self.executed_ticks: int = 0
        self.dropped_ticks: int = 0

    def reset_stats(self) -> None:
        self.accumulator = 0.0
        self.calls = 0
        self.total_time_s = 0.0
        self.last_duration_s = 0.0
        self.max_duration_s = 0.0
        self.scheduled_ticks = 0
        self.executed_ticks = 0
        self.dropped_ticks = 0


class SystemScheduler:
    """
    Agendador e despachante determinístico para instâncias de System.
    """

    def __init__(self, max_catch_up_steps: int = 4) -> None:
        if max_catch_up_steps < 1:
            raise ValueError("max_catch_up_steps deve ser >= 1")
        self.max_catch_up_steps = max_catch_up_steps
        self._entries: List[_SystemEntry] = []
        self._system_to_entry: Dict[Any, _SystemEntry] = {}
        self._insertion_counter: int = 0
        self._is_ticking: bool = False
        self._pending_add: List[Tuple[Any, TickPolicy, int]] = []
        self._pending_remove: List[Any] = []
        self.paused: bool = False

    def register(
        self,
        system: Any,
        policy: Optional[TickPolicy] = None,
        priority: Optional[int] = None,
    ) -> None:
        """Registra um sistema no agendador."""
        if system in self._system_to_entry:
            raise ValueError(f"Sistema já registrado: {system}")

        if policy is None:
            policy = TickPolicy.every_frame()

        if priority is None:
            priority = getattr(system, "priority", 1000)

        if self._is_ticking:
            self._pending_add.append((system, policy, priority))
            return

        self._do_register(system, policy, priority)

    def _do_register(self, system: Any, policy: TickPolicy, priority: int) -> None:
        if system in self._system_to_entry:
            raise ValueError(f"Sistema já registrado: {system}")

        entry = _SystemEntry(
            system=system,
            policy=policy,
            priority=priority,
            insertion_order=self._insertion_counter,
        )
        self._insertion_counter += 1
        self._entries.append(entry)
        self._system_to_entry[system] = entry
        self._sort_entries()

        # Chama inicialização/start exatamente uma vez se existir
        if hasattr(system, "start") and callable(system.start):
            system.start()
            entry.initialized = True
        elif hasattr(system, "initialize") and callable(system.initialize):
            system.initialize()
            entry.initialized = True

    def remove(self, system: Any) -> None:
        """Remove um sistema do agendador e executa shutdown."""
        if system not in self._system_to_entry:
            return

        if self._is_ticking:
            self._pending_remove.append(system)
            return

        self._do_remove(system)

    def _do_remove(self, system: Any) -> None:
        entry = self._system_to_entry.pop(system, None)
        if entry is None:
            return

        if entry in self._entries:
            self._entries.remove(entry)

        if hasattr(system, "shutdown") and callable(system.shutdown):
            system.shutdown()

    def _sort_entries(self) -> None:
        # Ordem determinística estável: menor prioridade primeiro, depois insertion_order
        self._entries.sort(key=lambda e: (e.priority, e.insertion_order))

    def update(self, scene: Any, dt: float) -> None:
        """Executa um ciclo de agendamento com validação estrita de dt."""
        if not isinstance(dt, (int, float)):
            raise ValueError(f"Delta time 'dt' deve ser numérico. Recebido: {type(dt).__name__}")
        if math.isnan(dt) or math.isinf(dt):
            raise ValueError(f"Delta time 'dt' inválido (NaN ou Inf). Recebido: {dt}")
        if dt < 0:
            raise ValueError(f"Delta time 'dt' não pode ser negativo. Recebido: {dt}")

        if self.paused:
            return

        self._is_ticking = True
        try:
            for entry in list(self._entries):
                system = entry.system
                # Respeita flag enabled do sistema se houver
                if hasattr(system, "enabled") and not system.enabled:
                    continue

                if not entry.policy.is_fixed:
                    # Every frame: despacha frame_dt diretamente
                    self._dispatch_update(entry, scene, dt)
                else:
                    # Fixed rate: accumulator com catch-up limitado e epsilon
                    interval = entry.policy.interval
                    entry.accumulator += dt
                    steps = 0
                    eps = 1e-9

                    while (entry.accumulator + eps) >= interval and steps < self.max_catch_up_steps:
                        entry.scheduled_ticks += 1
                        self._dispatch_update(entry, scene, interval)
                        entry.accumulator -= interval
                        steps += 1

                    # Política de excesso: se sobrou tempo acumulado acima do limite,
                    # descarta o excedente para evitar spiral-of-death
                    if (entry.accumulator + eps) >= interval:
                        dropped = int((entry.accumulator + eps) // interval)
                        entry.dropped_ticks += dropped
                        entry.accumulator = max(0.0, entry.accumulator - (dropped * interval))
        finally:
            self._is_ticking = False
            self._flush_pending_mutations()

    def _dispatch_update(self, entry: _SystemEntry, scene: Any, dt: float) -> None:
        system = entry.system
        entry.calls += 1
        entry.executed_ticks += 1

        t0 = time.perf_counter()
        try:
            if hasattr(system, "update") and callable(system.update):
                system.update(scene, dt)
        finally:
            duration = time.perf_counter() - t0
            entry.last_duration_s = duration
            entry.total_time_s += duration
            if duration > entry.max_duration_s:
                entry.max_duration_s = duration

    def _flush_pending_mutations(self) -> None:
        while self._pending_remove:
            sys = self._pending_remove.pop(0)
            self._do_remove(sys)

        while self._pending_add:
            sys, policy, priority = self._pending_add.pop(0)
            self._do_register(sys, policy, priority)

    def pause(self) -> None:
        """Pausa o agendador."""
        self.paused = True

    def resume(self) -> None:
        """Retoma o agendador sem catch-up do período pausado."""
        self.paused = False

    def reset(self) -> None:
        """Limpa accumulators e profiling de todos os sistemas registrados."""
        for entry in self._entries:
            entry.reset_stats()
        self.paused = False

    def clear(self) -> None:
        """Remove todos os sistemas e executa shutdown."""
        systems = [e.system for e in list(self._entries)]
        for s in systems:
            self._do_remove(s)
        self._entries.clear()
        self._system_to_entry.clear()
        self._insertion_counter = 0
        self._pending_add.clear()
        self._pending_remove.clear()
        self.paused = False

    def profiling_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Retorna snapshot read-only das métricas de profiling dos sistemas."""
        snapshot = {}
        for entry in self._entries:
            name = getattr(entry.system, "name", entry.system.__class__.__name__)
            calls = entry.calls
            avg_ms = (entry.total_time_s * 1000.0 / calls) if calls > 0 else 0.0
            snapshot[name] = {
                "calls": calls,
                "total_ms": entry.total_time_s * 1000.0,
                "last_ms": entry.last_duration_s * 1000.0,
                "avg_ms": avg_ms,
                "max_ms": entry.max_duration_s * 1000.0,
                "scheduled_ticks": entry.scheduled_ticks,
                "executed_ticks": entry.executed_ticks,
                "dropped_ticks": entry.dropped_ticks,
                "priority": entry.priority,
                "policy": str(entry.policy),
            }
        return snapshot
