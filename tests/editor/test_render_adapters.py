from types import SimpleNamespace

from editor.render.adapters import BackgroundRendererAdapter, LegacySceneRendererAdapter
from editor.render.render_pipeline import RenderContext


def _context(scene, surface=None) -> RenderContext:
    return RenderContext(
        viewport=object(),
        painter=object(),
        pygame_surface=surface or object(),
        active_scene=scene,
        editor_context=object(),
        runtime_manager=object(),
        selection_manager=object(),
    )


def test_background_adapter_prefers_explicit_background_draw() -> None:
    calls = []
    scene = SimpleNamespace(draw_background=lambda surface: calls.append(surface))
    adapter = BackgroundRendererAdapter()
    context = _context(scene)

    adapter.render(context)

    assert adapter.managed
    assert calls == [context.pygame_surface]


def test_legacy_adapter_uses_content_when_background_is_managed() -> None:
    calls = []
    content = lambda surface: None
    scene = SimpleNamespace(draw_content=content)
    viewport = SimpleNamespace(
        _draw_legacy_scene_content=lambda scene_draw=None: calls.append(scene_draw)
    )
    background = BackgroundRendererAdapter()
    background.managed = True
    adapter = LegacySceneRendererAdapter(viewport, background)

    adapter.render(_context(scene))

    assert calls == [content]


def test_legacy_adapter_keeps_integral_draw_fallback() -> None:
    calls = []
    viewport = SimpleNamespace(
        _draw_legacy_scene_content=lambda scene_draw=None: calls.append(scene_draw)
    )
    background = BackgroundRendererAdapter()
    background.managed = False

    LegacySceneRendererAdapter(viewport, background).render(_context(SimpleNamespace()))

    assert calls == [None]

