"""
engine/time.py
────────────────────────────────────────────────────────────────
Contrato:

    Acessado via instância (da Application):
        app.time.delta          # dt do frame atual, sem scale
        app.time.scaled_delta   # dt * scale (use em física e animações)
        app.time.raw_delta      # dt bruto sem cap e sem scale (uso rário)
        app.time.fps            # fps medido
        app.time.fps_target     # fps alvo
        app.time.frame          # número de frames desde o início
        app.time.elapsed        # tempo total acumulado (com scale)
        app.time.scale          # fator de escala (1.0 = normal)
        app.time.paused         # bool: congela dt sem parar o clock

    Acessado via classe (qualquer lugar, sem import da Application):
        Time.current().delta
        Time.current().frame
        Time.current().elapsed

Escala de tempo:
    # Slow motion 50 %
    app.time.scale = 0.5

    # Pausa toda a simulação
    app.time.paused = True

    # Retorna ao normal
    app.time.scale = 1.0
    app.time.paused = False

Notas:
  - SceneManager.update(dt) recebe sempre o dt sem scale.
    Cada sistema decide se usa scaled_delta ou raw_delta.
  - elapsed acumula scaled_delta, não raw_delta.
  - tick() é chamado exclusivamente pelo loop da Application.
"""
from __future__ import annotations

from typing import Optional
import pygame


class Time:
    """Serviço de tempo gerenciado pela Application."""

    # Referência à instância ativa (preenchida por Application)
    _current: Optional["Time"] = None

    def __init__(self, target_fps: int = 60, dt_cap: float = 0.1) -> None:
        self._clock = pygame.time.Clock()

        # Configuração
        self.fps_target: int   = target_fps
        self.dt_cap:     float = dt_cap

        # Estado por frame
        self.delta:        float = 0.0   # dt sem scale (segundos)
        self.scaled_delta: float = 0.0   # dt * scale
        self.raw_delta:    float = 0.0   # dt bruto, sem cap nem scale

        # Acumuladores
        self.elapsed: float = 0.0        # tempo total (com scale)
        self.frame:   int   = 0          # contador de frames

        # Controles
        self.scale:  float = 1.0         # fator de escala global
        self.paused: bool  = False       # congela dt sem parar o clock

        # Alias retrocompat
        self.fps_actual: float = 0.0

        # Registra como instância ativa
        Time._current = self

    # ------------------------------------------------------------------ #
    # Tick — chamado pelo loop da Application                             #
    # ------------------------------------------------------------------ #

    def tick(self) -> float:
        """
        Avança o clock um frame.
        Retorna delta (dt sem scale) para o SceneManager.
        """
        raw_ms = self._clock.tick(self.fps_target)

        self.raw_delta = raw_ms / 1000.0
        self.delta     = min(self.raw_delta, self.dt_cap)
        self.frame    += 1
        self.fps_actual = self._clock.get_fps()

        if self.paused:
            self.scaled_delta = 0.0
        else:
            self.scaled_delta = self.delta * self.scale

        self.elapsed += self.scaled_delta
        return self.delta

    # ------------------------------------------------------------------ #
    # Propriedades de conveniência                                        #
    # ------------------------------------------------------------------ #

    @property
    def fps(self) -> float:
        """FPS medido pelo clock do Pygame."""
        return self.fps_actual

    @property
    def dt(self) -> float:
        """Alias de delta. Prefer delta para clareza."""
        return self.delta

    # ------------------------------------------------------------------ #
    # Acesso estático (sem import de Application)                         #
    # ------------------------------------------------------------------ #

    @classmethod
    def current(cls) -> "Time":
        """
        Retorna a instância de Time ativa.

        Uso em qualquer sistema sem precisar importar Application:
            dt = Time.current().delta
            f  = Time.current().frame
        """
        if cls._current is None:
            raise RuntimeError(
                "Time não foi inicializado. "
                "Crie uma Application antes de usar Time.current()."
            )
        return cls._current

    # ------------------------------------------------------------------ #
    # repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"<Time frame={self.frame} elapsed={self.elapsed:.2f}s "
            f"fps={self.fps:.1f} scale={self.scale} paused={self.paused}>"
        )
