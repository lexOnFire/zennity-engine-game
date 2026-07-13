"""Pipeline ordenado e extensível da Scene View.

Este módulo apenas organiza chamadas de desenho. Ele não altera renderizadores,
estado de cena ou decisões visuais existentes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(slots=True)
class RenderContext:
    viewport: Any
    painter: Any
    pygame_surface: Any
    active_scene: Any
    editor_context: Any
    runtime_manager: Any
    selection_manager: Any


class RenderPass:
    """Interface base de uma etapa independente de desenho."""

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = bool(enabled)

    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    def render(self, context: RenderContext) -> None:
        raise NotImplementedError


class RenderPipeline:
    """Executa RenderPass na mesma ordem em que foram registrados."""

    def __init__(self, passes: Iterable[RenderPass] = ()) -> None:
        self._passes = list(passes)

    @property
    def passes(self) -> tuple[RenderPass, ...]:
        return tuple(self._passes)

    def add_pass(self, render_pass: RenderPass) -> None:
        self._passes.append(render_pass)

    def render(self, context: RenderContext) -> None:
        for render_pass in self._passes:
            if render_pass.enabled():
                render_pass.render(context)


class _CallbackPass(RenderPass):
    def __init__(self, draw: Callable[[RenderContext], None] | None = None, *, enabled: bool = True) -> None:
        super().__init__(enabled=enabled)
        self._draw = draw

    def render(self, context: RenderContext) -> None:
        if self._draw is not None:
            self._draw(context)


class BackgroundPass(_CallbackPass):
    """Limpa o framebuffer e desenha a cor de fundo configurada."""


class LegacySceneAdapter:
    """Fronteira estável para a renderização legada da cena."""

    def __init__(self, draw: Callable[[RenderContext], None]) -> None:
        self._draw = draw

    def draw(self, context: RenderContext) -> None:
        self._draw(context)


class LegacyScenePass(RenderPass):
    """Delega exclusivamente para LegacySceneAdapter.draw()."""

    def __init__(self, adapter: LegacySceneAdapter, *, enabled: bool = True) -> None:
        super().__init__(enabled=enabled)
        self._adapter = adapter

    def render(self, context: RenderContext) -> None:
        self._adapter.draw(context)


class GridPass(_CallbackPass):
    """Delega exclusivamente para o desenho do GridRenderer."""


class SpriteOverlayPass(_CallbackPass):
    """Ponto de entrada do SpriteRenderer moderno."""


class GizmoPass(_CallbackPass):
    """Ponto de entrada do GizmoRegistry e gizmos modernos."""


class OverlayPass(_CallbackPass):
    """Desenha labels, seleção, debug text e overlays futuros."""
