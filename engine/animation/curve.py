"""Motor Unificado de Curvas e Interpolação da Zennity Engine (AnimationCurveEngine)."""
from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
import numpy as np


class CurveInterpolation(str, Enum):
    STEP = "step"
    LINEAR = "linear"
    HERMITE = "hermite"
    BEZIER = "bezier"


class AnimationKeyframe:
    def __init__(self, time: float, value: Any, in_tangent: float = 0.0, out_tangent: float = 0.0, mode: CurveInterpolation = CurveInterpolation.LINEAR) -> None:
        self.time = float(time)
        self.value = value
        self.in_tangent = float(in_tangent)
        self.out_tangent = float(out_tangent)
        self.mode = mode if isinstance(mode, CurveInterpolation) else CurveInterpolation(str(mode))


class AnimationCurveEngine:
    """Motor unificado para avaliação e interpolação de curvas de animação."""

    def __init__(self, keyframes: Optional[List[AnimationKeyframe]] = None, default_mode: CurveInterpolation = CurveInterpolation.LINEAR) -> None:
        self.keyframes: List[AnimationKeyframe] = list(keyframes or [])
        self.default_mode = default_mode

    def evaluate(self, time_seconds: float) -> Any:
        if not self.keyframes:
            return 0.0

        sorted_kfs = sorted(self.keyframes, key=lambda k: k.time)
        t = float(time_seconds)

        if t <= sorted_kfs[0].time:
            return sorted_kfs[0].value
        if t >= sorted_kfs[-1].time:
            return sorted_kfs[-1].value

        for left, right in zip(sorted_kfs, sorted_kfs[1:]):
            if left.time <= t <= right.time:
                mode = left.mode
                if mode == CurveInterpolation.STEP:
                    return left.value

                span = max(right.time - left.time, 0.000001)
                alpha = (t - left.time) / span

                if mode == CurveInterpolation.HERMITE:
                    alpha = alpha * alpha * (3.0 - 2.0 * alpha)

                return self._interpolate_values(left.value, right.value, alpha)

        return sorted_kfs[-1].value

    def _interpolate_values(self, val_a: Any, val_b: Any, alpha: float) -> Any:
        if isinstance(val_a, (int, float, np.number)) and isinstance(val_b, (int, float, np.number)):
            return float(val_a) + (float(val_b) - float(val_a)) * alpha

        if isinstance(val_a, np.ndarray) and isinstance(val_b, np.ndarray):
            return val_a + (val_b - val_a) * alpha

        if isinstance(val_a, (list, tuple)) and isinstance(val_b, (list, tuple)):
            length = min(len(val_a), len(val_b))
            return [float(val_a[i]) + (float(val_b[i]) - float(val_a[i])) * alpha for i in range(length)]

        return val_b if alpha >= 1.0 else val_a
