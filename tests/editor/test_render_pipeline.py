from editor.render.render_pipeline import (
    BackgroundPass,
    LegacySceneAdapter,
    LegacyScenePass,
    RenderContext,
    RenderPipeline,
)


def _context() -> RenderContext:
    return RenderContext(
        viewport=object(), painter=object(), pygame_surface=object(),
        active_scene=object(), editor_context=object(), runtime_manager=object(),
        selection_manager=object(),
    )


def test_pipeline_executes_enabled_passes_in_registration_order() -> None:
    calls = []
    first = BackgroundPass(lambda context: calls.append(("background", context)))
    disabled = BackgroundPass(lambda context: calls.append(("disabled", context)), enabled=False)
    legacy = LegacyScenePass(LegacySceneAdapter(lambda context: calls.append(("legacy", context))))
    context = _context()

    pipeline = RenderPipeline([first, disabled, legacy])
    pipeline.render(context)

    assert calls == [("background", context), ("legacy", context)]


def test_pipeline_exposes_immutable_pass_snapshot_and_supports_append() -> None:
    pipeline = RenderPipeline()
    render_pass = BackgroundPass()
    pipeline.add_pass(render_pass)

    assert pipeline.passes == (render_pass,)
