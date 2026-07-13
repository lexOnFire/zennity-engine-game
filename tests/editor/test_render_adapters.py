from types import SimpleNamespace

from editor.render.adapters import (
    BackgroundRendererAdapter,
    FramebufferPresentRendererAdapter,
    FramePreparationAdapter,
    LegacySceneRendererAdapter,
    SpriteRendererAdapter,
)
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


def test_framebuffer_adapter_restores_grid_before_presenting() -> None:
    calls = []
    viewport = SimpleNamespace(
        _pipeline_grid_states=[("scene", True)],
        _restore_grid_state=lambda state: calls.append(("restore", state)),
        _present_legacy_framebuffer=lambda painter: calls.append(("present", painter)),
    )
    context = _context(SimpleNamespace())

    FramebufferPresentRendererAdapter(viewport).render(context)

    assert calls == [
        ("restore", viewport._pipeline_grid_states),
        ("present", context.painter),
    ]


def test_sprite_adapter_uses_prepared_commands() -> None:
    calls = []
    commands = [object()]
    viewport = SimpleNamespace(camera=object(), _pipeline_modern_sprites=commands)
    renderer = SimpleNamespace(
        draw=lambda painter, camera, sprites: calls.append((painter, camera, sprites))
    )
    context = _context(SimpleNamespace())

    SpriteRendererAdapter(viewport, renderer).render(context)

    assert calls == [(context.painter, viewport.camera, commands)]


def test_frame_preparation_creates_and_cleans_context() -> None:
    calls = []
    component = object()
    command = SimpleNamespace(component=component)
    scene = SimpleNamespace()
    painter = SimpleNamespace(end=lambda: calls.append("end"))
    camera = SimpleNamespace(update=lambda dt: calls.append("camera"))
    viewport = SimpleNamespace(
        pg_surface=object(), active_scene=scene, camera=camera,
        editor_state=object(), runtime_manager=object(), selection_manager=object(),
        _last_render_time=0.0, _pipeline_grid_states=[],
        _pipeline_real_show_grid=True, _pipeline_modern_sprites=[],
        _sync_legacy_scale_handles=lambda: calls.append("scale"),
        sync_camera_from_engine=lambda: calls.append("sync"),
        _is_playing=lambda: False, is_game_view=lambda: False,
        _capture_grid_state=lambda: [(scene, True)],
        _set_grid_visible=lambda visible: calls.append(("grid", visible)),
        _restore_grid_state=lambda state: calls.append(("restore", state)),
    )
    sprites = SimpleNamespace(collect=lambda active_scene: [command])
    adapter = FramePreparationAdapter(viewport, lambda owner: painter, sprites)

    context = adapter.create_context()

    assert context is not None
    assert scene._zennity_modern_sprite_component_ids == {id(component)}
    adapter.finish(context)
    assert scene._zennity_modern_sprite_component_ids == set()
    assert calls[-1] == "end"
