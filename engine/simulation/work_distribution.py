"""engine/simulation/work_distribution.py
────────────────────────────────────────────────────────────────
Distribuição temporal de carga de trabalho e suavização de picos de frame (Phase 12 - Item 12.5).

Oferece:
  - TemporalWorkDistributor: Particionador determinístico de fases temporais baseado em frequência
  - Derivação exata de contagem de fases (phases = base_hz // target_hz)
  - Distribuição estável por índice de entidade (idx % phases == current_phase)
  - Zero timers, accumulators, systems ou dicionários por entidade
  - Garantia de equidade (fairness) e ausência de inanição (no starvation)
  - Integração perfeita com SystemScheduler e SimulationLODManager.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Union


class TemporalWorkDistributor:
    """
    Distribuidor determinístico de trabalho temporal que suaviza picos de execução
    dividindo populações de entidades ao longo dos frames de uma frequência base.
    """

    def __init__(
        self,
        target_hz: float,
        base_hz: float = 60.0,
        initial_phase: int = 0,
    ) -> None:
        if not isinstance(target_hz, (int, float)) or not isinstance(base_hz, (int, float)):
            raise ValueError(f"Frequências devem ser numéricas: target_hz={target_hz}, base_hz={base_hz}")
        if math.isnan(target_hz) or math.isinf(target_hz) or math.isnan(base_hz) or math.isinf(base_hz):
            raise ValueError(f"Frequências inválidas (NaN ou Inf): target_hz={target_hz}, base_hz={base_hz}")
        if target_hz <= 0.0 or base_hz <= 0.0:
            raise ValueError(f"Frequências devem ser estritamente positivas: target_hz={target_hz}, base_hz={base_hz}")
        if target_hz > base_hz:
            raise ValueError(f"target_hz ({target_hz}) não pode ser maior que base_hz ({base_hz})")

        self.target_hz: float = float(target_hz)
        self.base_hz: float = float(base_hz)

        # Deriva o número exato de fases discretas
        ratio = self.base_hz / self.target_hz
        self.phase_count: int = max(1, round(ratio))

        if not isinstance(initial_phase, int) or initial_phase < 0:
            raise ValueError(f"initial_phase deve ser inteiro >= 0. Recebido: {initial_phase}")

        self._current_phase: int = initial_phase % self.phase_count

        # Estatísticas de execução
        self._advances: int = 0
        self._entities_processed_last_frame: int = 0
        self._total_entities_processed: int = 0

    @property
    def current_phase(self) -> int:
        """Índice da fase atual no ciclo [0, phase_count - 1]."""
        return self._current_phase

    @property
    def advances(self) -> int:
        """Número total de avanços de fase."""
        return self._advances

    def reset(self, phase: int = 0) -> None:
        """Reseta o distribuidor para o estado inicial determinístico."""
        self._current_phase = phase % self.phase_count
        self._advances = 0
        self._entities_processed_last_frame = 0
        self._total_entities_processed = 0

    def select(self, active_indices: Sequence[int], phase: Optional[int] = None) -> List[int]:
        """
        Filtra os índices que pertencem à fase selecionada (ou fase atual se None).
        Complexidade O(N) com zero alocação de memória por entidade.
        """
        target_phase = self._current_phase if phase is None else (phase % self.phase_count)
        phases = self.phase_count

        if phases == 1:
            selected = list(active_indices)
        else:
            selected = [idx for idx in active_indices if (idx % phases) == target_phase]

        self._entities_processed_last_frame = len(selected)
        self._total_entities_processed += len(selected)
        return selected

    def iter_select(self, active_indices: Sequence[int], phase: Optional[int] = None) -> Iterator[int]:
        """
        Iterador gerador para os índices da fase, com zero alocação intermediária de lista.
        """
        target_phase = self._current_phase if phase is None else (phase % self.phase_count)
        phases = self.phase_count

        count = 0
        if phases == 1:
            for idx in active_indices:
                count += 1
                yield idx
        else:
            for idx in active_indices:
                if (idx % phases) == target_phase:
                    count += 1
                    yield idx

        self._entities_processed_last_frame = count
        self._total_entities_processed += count

    def advance(self) -> int:
        """
        Avança o distribuidor para a próxima fase no ciclo. Retorna a nova fase.
        """
        self._current_phase = (self._current_phase + 1) % self.phase_count
        self._advances += 1
        return self._current_phase

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas leves de distribuição temporal."""
        return {
            "target_hz": self.target_hz,
            "base_hz": self.base_hz,
            "phase_count": self.phase_count,
            "current_phase": self._current_phase,
            "advances": self._advances,
            "entities_processed_last_frame": self._entities_processed_last_frame,
            "total_entities_processed": self._total_entities_processed,
        }
