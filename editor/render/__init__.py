"""Infraestrutura do pipeline moderno de renderização da Scene View."""

from .adapters import (
    BackgroundRendererAdapter,
    FramebufferPresentRendererAdapter,
    FramePreparationAdapter,
    GizmoRendererAdapter,
    GridRendererAdapter,
    LegacySceneRendererAdapter,
    OverlayRendererAdapter,
    SpriteRendererAdapter,
)
from .render_pipeline import (
    BackgroundPass,
    FramebufferPresentPass,
    GizmoPass,
    GridPass,
    LegacySceneAdapter,
    LegacyScenePass,
    OverlayPass,
    RenderContext,
    RenderPass,
    RenderPassMetrics,
    RenderPipeline,
    SpriteOverlayPass,
    TransformGizmoPass,
)

__all__ = [
    "BackgroundPass", "BackgroundRendererAdapter", "FramebufferPresentPass",
    "FramebufferPresentRendererAdapter", "FramePreparationAdapter",
    "GizmoPass", "GizmoRendererAdapter", "GridPass", "GridRendererAdapter", "LegacySceneAdapter",
    "LegacySceneRendererAdapter", "OverlayRendererAdapter", "SpriteRendererAdapter",
    "LegacyScenePass", "OverlayPass", "RenderContext", "RenderPass", "RenderPassMetrics",
    "RenderPipeline", "SpriteOverlayPass", "TransformGizmoPass",
]
