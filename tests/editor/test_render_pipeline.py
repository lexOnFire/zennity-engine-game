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


def test_optional_metrics_record_only_enabled_passes() -> None:
    pipeline = RenderPipeline([
        BackgroundPass(lambda context: None),
        BackgroundPass(lambda context: None, enabled=False),
    ])
    assert pipeline.metrics == ()

    pipeline.set_profiling_enabled(True)
    pipeline.render(_context())
    pipeline.render(_context())

    assert len(pipeline.metrics) == 1
    metric = pipeline.metrics[0]
    assert metric.pass_name == "BackgroundPass"
    assert metric.pass_index == 0
    assert metric.executions == 2
    assert 0.0 <= metric.last_ms <= metric.max_ms
    assert metric.average_ms >= 0.0

    pipeline.reset_metrics()
    assert pipeline.metrics == ()
