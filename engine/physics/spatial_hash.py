"""Uniform-grid broad phase used to reduce collision narrow-phase checks."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Iterable

Bounds = tuple[float, float, float, float]


@dataclass(frozen=True)
class BroadPhaseStats:
    active_colliders: int = 0
    possible_pairs: int = 0
    candidate_pairs: int = 0
    culled_pairs: int = 0
    occupied_cells: int = 0
    overflow_colliders: int = 0


class SpatialHashBroadPhase:
    """Generate conservative, deterministic candidate pairs using a grid."""

    def __init__(self, cell_size: float = 128.0, max_cells_per_collider: int = 4096) -> None:
        if cell_size <= 0.0:
            raise ValueError("cell_size must be greater than zero")
        if max_cells_per_collider < 1:
            raise ValueError("max_cells_per_collider must be positive")
        self.cell_size = float(cell_size)
        self.max_cells_per_collider = int(max_cells_per_collider)
        self.stats = BroadPhaseStats()

    def candidate_pairs(
        self,
        colliders: Iterable[Any],
        bounds_for: Callable[[Any], Bounds],
        scene_for: Callable[[Any], Any],
    ) -> list[tuple[Any, Any]]:
        ordered = list(colliders)
        possible = len(ordered) * (len(ordered) - 1) // 2
        buckets: dict[tuple[int, int, int], list[int]] = {}
        scene_members: dict[int, list[int]] = {}
        overflow: list[int] = []

        for index, collider in enumerate(ordered):
            scene_key = id(scene_for(collider))
            scene_members.setdefault(scene_key, []).append(index)
            cells = self._cells_for(bounds_for(collider))
            if cells is None:
                overflow.append(index)
                continue
            for cell_x, cell_y in cells:
                buckets.setdefault((scene_key, cell_x, cell_y), []).append(index)

        candidates: set[tuple[int, int]] = set()
        for members in buckets.values():
            for offset, first in enumerate(members):
                for second in members[offset + 1 :]:
                    candidates.add((first, second) if first < second else (second, first))

        for first in overflow:
            scene_key = id(scene_for(ordered[first]))
            for second in scene_members[scene_key]:
                if first != second:
                    candidates.add((first, second) if first < second else (second, first))

        pairs = [(ordered[first], ordered[second]) for first, second in sorted(candidates)]
        self.stats = BroadPhaseStats(
            active_colliders=len(ordered),
            possible_pairs=possible,
            candidate_pairs=len(pairs),
            culled_pairs=max(0, possible - len(pairs)),
            occupied_cells=len(buckets),
            overflow_colliders=len(overflow),
        )
        return pairs

    def _cells_for(self, bounds: Bounds) -> list[tuple[int, int]] | None:
        left, top, right, bottom = bounds
        min_x = math.floor(min(left, right) / self.cell_size)
        max_x = math.floor(max(left, right) / self.cell_size)
        min_y = math.floor(min(top, bottom) / self.cell_size)
        max_y = math.floor(max(top, bottom) / self.cell_size)
        cell_count = (max_x - min_x + 1) * (max_y - min_y + 1)
        if cell_count > self.max_cells_per_collider:
            return None
        return [
            (cell_x, cell_y)
            for cell_x in range(min_x, max_x + 1)
            for cell_y in range(min_y, max_y + 1)
        ]
