from editor.render.render_pipeline import (
    BackgroundPass,
    FramebufferPresentPass,
    LegacySceneAdapter,
    LegacyScenePass,
    RenderContext,
    RenderPipeline,
    TransformGizmoPass,
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
    present = FramebufferPresentPass(lambda context: calls.append(("present", context)))
    transform_gizmo = TransformGizmoPass(
        lambda context: calls.append(("transform_gizmo", context))
    )
    context = _context()

    pipeline = RenderPipeline([first, disabled, legacy, present, transform_gizmo])
    pipeline.render(context)

    assert calls == [
        ("background", context),
        ("legacy", context),
        ("present", context),
        ("transform_gizmo", context),
    ]


def test_pipeline_exposes_immutable_pass_snapshot_and_supports_append() -> None:
    pipeline = RenderPipeline()
    render_pass = BackgroundPass()
    pipeline.add_pass(render_pass)

    assert pipeline.passes == (render_pass,)
