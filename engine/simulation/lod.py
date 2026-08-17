"""engine/simulation/lod.py
────────────────────────────────────────────────────────────────
Sistema genérico de Simulation LOD (Level of Detail) por faixas de frequência.

Oferece:
  - SimulationFocus: ponto de interesse desacoplado de câmera ou entidades
  - SimulationLODConfig: configuração determinística de thresholds de distância e histerese
  - SimulationLODManager: gerenciamento compacto e linear de tiers (HIGH, MEDIUM, LOW, SLEEP)
  - Classificação O(N alive) por distâncias euclidianas quadradas (sem math.sqrt())
  - Histerese anti-thrashing para estabilidade de transição
  - Despacho em lote (batching) compatível com SystemScheduler / TickPolicy
  - Proteção estrita de geração contra reciclagem de slots no SimulationEntityPool
  - Desacoplamento total de GameObject, Camera, LogicGraph, Blackboard, Qt e Threads.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

# Tiers canônicos de simulação (valores inteiros compactos)
LOD_HIGH: int = 0
LOD_MEDIUM: int = 1
LOD_LOW: int = 2
LOD_SLEEP: int = 3

TIER_NAMES: Dict[int, str] = {
    LOD_HIGH: "HIGH",
    LOD_MEDIUM: "MEDIUM",
    LOD_LOW: "LOW",
    LOD_SLEEP: "SLEEP",
}


class SimulationFocus:
    """Ponto de interesse espacial para classificação de Simulation LOD."""

    def __init__(self, x: float = 0.0, y: float = 0.0, enabled: bool = True) -> None:
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError(f"Coordenadas do SimulationFocus devem ser numéricas: ({x}, {y})")
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            raise ValueError(f"Coordenadas do SimulationFocus inválidas (NaN ou Inf): ({x}, {y})")

        self.x: float = float(x)
        self.y: float = float(y)
        self.enabled: bool = bool(enabled)

    def set_position(self, x: float, y: float) -> None:
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError(f"Coordenadas devem ser numéricas: ({x}, {y})")
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            raise ValueError(f"Coordenadas inválidas (NaN ou Inf): ({x}, {y})")
        self.x = float(x)
        self.y = float(y)

    def __repr__(self) -> str:
        return f"<SimulationFocus x={self.x:.2f} y={self.y:.2f} enabled={self.enabled}>"


class SimulationLODConfig:
    """Configuração de distâncias de corte e histerese para Simulation LOD."""

    def __init__(
        self,
        high_distance: float = 300.0,
        medium_distance: float = 800.0,
        low_distance: float = 1600.0,
        hysteresis_margin: float = 50.0,
    ) -> None:
        for name, val in [
            ("high_distance", high_distance),
            ("medium_distance", medium_distance),
            ("low_distance", low_distance),
            ("hysteresis_margin", hysteresis_margin),
        ]:
            if not isinstance(val, (int, float)):
                raise ValueError(f"{name} deve ser numérico. Recebido: {type(val).__name__}")
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"{name} inválido (NaN ou Inf): {val}")
            if val < 0.0:
                raise ValueError(f"{name} não pode ser negativo: {val}")

        if not (high_distance < medium_distance < low_distance):
            raise ValueError(
                f"Distâncias de LOD devem ser estritamente crescentes (high < medium < low). "
                f"Recebido: high={high_distance}, medium={medium_distance}, low={low_distance}"
            )

        if hysteresis_margin >= (medium_distance - high_distance) or hysteresis_margin >= (low_distance - medium_distance):
            raise ValueError(
                f"hysteresis_margin ({hysteresis_margin}) deve ser menor que a largura das bandas de LOD."
            )

        self.high_distance: float = float(high_distance)
        self.medium_distance: float = float(medium_distance)
        self.low_distance: float = float(low_distance)
        self.hysteresis_margin: float = float(hysteresis_margin)

        # Distâncias ao quadrado para otimização do loop de classificação
        self.high_sq: float = self.high_distance * self.high_distance
        self.medium_sq: float = self.medium_distance * self.medium_distance
        self.low_sq: float = self.low_distance * self.low_distance

        # Histerese ao quadrado (demote = dist + margin, promote = dist - margin)
        self.high_demote_sq: float = (self.high_distance + self.hysteresis_margin) ** 2
        self.high_promote_sq: float = max(0.0, self.high_distance - self.hysteresis_margin) ** 2

        self.medium_demote_sq: float = (self.medium_distance + self.hysteresis_margin) ** 2
        self.medium_promote_sq: float = max(0.0, self.medium_distance - self.hysteresis_margin) ** 2

        self.low_demote_sq: float = (self.low_distance + self.hysteresis_margin) ** 2
        self.low_promote_sq: float = max(0.0, self.low_distance - self.hysteresis_margin) ** 2


class SimulationLODManager:
    """
    Gerenciador linear compacto de Simulation LOD indexado por slot de entidade.
    """

    def __init__(
        self,
        config: Optional[SimulationLODConfig] = None,
        initial_capacity: int = 1024,
    ) -> None:
        self.config: SimulationLODConfig = config if config is not None else SimulationLODConfig()
        self._capacity: int = max(initial_capacity, 16)

        # Storage linear compacto por índice
        self._tiers: List[int] = [LOD_HIGH] * self._capacity
        self._slot_generations: List[int] = [-1] * self._capacity

        # Dense tier index lists para iteração ultra-rápida
        self._tier_indices: Dict[int, List[int]] = {
            LOD_HIGH: [],
            LOD_MEDIUM: [],
            LOD_LOW: [],
            LOD_SLEEP: [],
        }

        # Contadores de profiling
        self._classification_calls: int = 0
        self._tier_transitions: int = 0
        self._promotions: int = 0
        self._demotions: int = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def get_tier(self, handle: Any) -> int:
        """Retorna o tier atual da entidade respeitando a validação de geração."""
        idx = getattr(handle, "index", handle)
        gen = getattr(handle, "generation", None)

        if not isinstance(idx, int) or idx < 0 or idx >= self._capacity:
            return LOD_HIGH

        if gen is not None and self._slot_generations[idx] != gen:
            return LOD_HIGH

        return self._tiers[idx]

    def get_tier_indices(self, tier: int) -> List[int]:
        """Retorna a lista densa determinística de índices de entidades ativas naquele tier."""
        return self._tier_indices.get(tier, [])

    def iter_tier(self, tier: int) -> Iterator[int]:
        """Iterador determinístico sobre índices de entidades ativas no tier."""
        return iter(self._tier_indices.get(tier, []))

    def _ensure_capacity(self, required_capacity: int) -> None:
        if required_capacity <= self._capacity:
            return
        new_cap = max(required_capacity, self._capacity * 2)
        additional = new_cap - self._capacity
        self._tiers.extend([LOD_HIGH] * additional)
        self._slot_generations.extend([-1] * additional)
        self._capacity = new_cap

    def classify(self, pool: Any, focus: Optional[SimulationFocus] = None) -> None:
        """
        Classifica toda a população viva do pool em relação ao focus com histerese determinística.
        Complexidade: O(N alive).
        """
        self._classification_calls += 1
        pool_cap = getattr(pool, "capacity", 0)
        self._ensure_capacity(pool_cap)

        # Limpa as listas densas de índices por tier
        for t in self._tier_indices:
            self._tier_indices[t].clear()

        # Sem foco ativo: todas as entidades vivas são tratadas como LOD_HIGH
        if focus is None or not focus.enabled:
            for idx in pool.iter_alive_indices():
                gen = pool.generation[idx]
                if self._slot_generations[idx] != gen:
                    self._slot_generations[idx] = gen
                    self._tiers[idx] = LOD_HIGH

                self._tiers[idx] = LOD_HIGH
                self._tier_indices[LOD_HIGH].append(idx)
            return

        fx = focus.x
        fy = focus.y
        px = pool.position_x
        py = pool.position_y
        gens = pool.generation
        cfg = self.config

        for idx in pool.iter_alive_indices():
            current_gen = gens[idx]
            old_gen = self._slot_generations[idx]

            # Slot reutilizado/recém-criado: reinicializa estado sem herdar histerese
            if old_gen != current_gen:
                self._slot_generations[idx] = current_gen
                old_tier = LOD_HIGH
            else:
                old_tier = self._tiers[idx]

            dx = px[idx] - fx
            dy = py[idx] - fy
            dist_sq = dx * dx + dy * dy

            new_tier = self._classify_with_hysteresis(dist_sq, old_tier, cfg)

            if new_tier != old_tier:
                self._tier_transitions += 1
                if new_tier < old_tier:
                    self._promotions += 1
                else:
                    self._demotions += 1

            self._tiers[idx] = new_tier
            self._tier_indices[new_tier].append(idx)

    @staticmethod
    def _classify_with_hysteresis(dist_sq: float, current_tier: int, cfg: SimulationLODConfig) -> int:
        """Determina o novo tier com base na distância ao quadrado e banda de histerese."""
        if current_tier == LOD_HIGH:
            if dist_sq > cfg.low_demote_sq:
                return LOD_SLEEP
            elif dist_sq > cfg.medium_demote_sq:
                return LOD_LOW
            elif dist_sq > cfg.high_demote_sq:
                return LOD_MEDIUM
            return LOD_HIGH

        elif current_tier == LOD_MEDIUM:
            if dist_sq < cfg.high_promote_sq:
                return LOD_HIGH
            elif dist_sq > cfg.low_demote_sq:
                return LOD_SLEEP
            elif dist_sq > cfg.medium_demote_sq:
                return LOD_LOW
            return LOD_MEDIUM

        elif current_tier == LOD_LOW:
            if dist_sq < cfg.high_promote_sq:
                return LOD_HIGH
            elif dist_sq < cfg.medium_promote_sq:
                return LOD_MEDIUM
            elif dist_sq > cfg.low_demote_sq:
                return LOD_SLEEP
            return LOD_LOW

        else:  # LOD_SLEEP
            if dist_sq < cfg.high_promote_sq:
                return LOD_HIGH
            elif dist_sq < cfg.medium_promote_sq:
                return LOD_MEDIUM
            elif dist_sq < cfg.low_promote_sq:
                return LOD_LOW
            return LOD_SLEEP

    def clear(self) -> None:
        """Limpa o storage e reseta gerações de slots."""
        self._tiers = [LOD_HIGH] * self._capacity
        self._slot_generations = [-1] * self._capacity
        for t in self._tier_indices:
            self._tier_indices[t].clear()
        self.reset_profiling_stats()

    def get_stats(self) -> Dict[str, Any]:
        """Retorna snapshot das contagens de entidades por tier e profiling."""
        return {
            "tier_counts": {
                "high": len(self._tier_indices[LOD_HIGH]),
                "medium": len(self._tier_indices[LOD_MEDIUM]),
                "low": len(self._tier_indices[LOD_LOW]),
                "sleep": len(self._tier_indices[LOD_SLEEP]),
            },
            "classification_calls": self._classification_calls,
            "tier_transitions": self._tier_transitions,
            "promotions": self._promotions,
            "demotions": self._demotions,
        }

    def reset_profiling_stats(self) -> None:
        """Zera apenas as métricas de profiling."""
        self._classification_calls = 0
        self._tier_transitions = 0
        self._promotions = 0
        self._demotions = 0
