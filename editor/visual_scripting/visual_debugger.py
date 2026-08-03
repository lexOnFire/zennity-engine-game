"""
editor/visual_scripting/visual_debugger.py
─────────────────────────────────────────────────────────────────────────────
Visual Debugger para o Logic Editor (Breakpoints, Watch Variables, Pulse de Execução em Play Mode).
"""
from __future__ import annotations

from typing import Dict, Set, Any
import time


class VisualDebugger:
    """Gerenciador central de breakpoints e acompanhamento visual no Play Mode."""

    def __init__(self) -> None:
        self.breakpoints: Set[str] = set()       # IDs de nós com breakpoint
        self.watched_variables: Dict[str, Any] = {} # var_name -> valor atual
        self.active_pulses: Dict[str, float] = {}   # node_id -> timestamp da última execução
        self.is_paused = False
        self.paused_at_node: str | None = None

    def toggle_breakpoint(self, node_id: str) -> bool:
        if node_id in self.breakpoints:
            self.breakpoints.remove(node_id)
            return False
        else:
            self.breakpoints.add(node_id)
            return True

    def notify_node_executed(self, node_id: str, variables: Dict[str, Any] | None = None) -> bool:
        """Registra a execução de um nó. Retorna True se atingiu um Breakpoint e deve pausar."""
        now = time.time()
        self.active_pulses[node_id] = now

        if variables:
            self.watched_variables.update(variables)

        if node_id in self.breakpoints:
            self.is_paused = True
            self.paused_at_node = node_id
            return True

        return False

    def get_pulse_intensity(self, node_id: str) -> float:
        """Retorna de 0.0 a 1.0 o brilho visual de pulso (fade out em 0.5s)."""
        last = self.active_pulses.get(node_id, 0.0)
        elapsed = time.time() - last
        if elapsed > 0.5:
            return 0.0
        return max(0.0, 1.0 - (elapsed / 0.5))

    def resume(self) -> None:
        self.is_paused = False
        self.paused_at_node = None
