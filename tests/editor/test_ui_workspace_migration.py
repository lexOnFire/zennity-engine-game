from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_animation_workspace_uses_semantic_theme_contract() -> None:
    source = _source("editor/interface_smoke_test.py") + _source("editor/ui/workspace_builder.py") + _source("editor/ui/docks_builder.py")
    theme = _source("editor/ui/theme.py")

    for object_name in (
        "AnimationWorkspace", "AnimationToolbar", "AnimationLibraryPanel",
        "AnimationLibraryTree", "AnimationPreview", "AnimationPropertiesPanel",
    ):
        assert f'"{object_name}"' in source
        assert f"#{object_name}" in theme

    assert 'window.animation_apply_button.setProperty("uiRole", "primary")' in source
    assert 'window.animation_delete_button.setProperty("uiRole", "danger")' in source
    assert "#AnimationWorkspace { background:" not in source
    assert "#AnimationLibraryPanel { background:" not in source


def test_console_and_profiler_share_global_tokens() -> None:
    interface = _source("editor/interface_smoke_test.py") + _source("editor/ui/docks_builder.py") + _source("editor/ui/bottom_panels_builder.py")
    console = _source("editor/widgets/console_dock.py")
    profiler = _source("editor/profiler/profiler_dock.py")
    profiler_shim = _source("editor/widgets/profiler_dock.py")
    theme = _source("editor/ui/theme.py")

    for object_name in ("ConsolePanel", "ConsoleToolbar", "ConsoleOutput", "ProfilerPanel", "ProfilerMetric"):
        assert f'"{object_name}"' in interface
        assert f"#{object_name}" in theme

    assert 'self.txt_display.setObjectName("ConsoleOutput")' in console
    assert "self.txt_display.setStyleSheet" not in console
    assert 'container.setObjectName("ProfilerPanel")' in profiler
    assert 'label.setObjectName("ProfilerMetric")' in profiler
    assert "class ViewportProfilerDock" not in profiler_shim
    assert "from editor.profiler.profiler_dock import ProfilerDock" in profiler_shim


def test_build_report_uses_semantic_status_instead_of_inline_palette() -> None:
    report = _source("editor/widgets/build_report_dialog.py")
    theme = _source("editor/ui/theme.py")

    assert 'self.setObjectName("BuildReportDialog")' in report
    assert 'status_label.setObjectName("BuildStatus")' in report
    assert 'status_label.setProperty("uiState", "success" if self.report.success else "error")' in report
    assert "status_label.setStyleSheet" not in report
    assert "summary.setStyleSheet" not in report
    assert 'QLabel#BuildStatus[uiState="success"]' in theme
    assert 'QLabel#BuildStatus[uiState="error"]' in theme


def test_migrated_workspaces_do_not_introduce_fixed_panel_widths() -> None:
    center = _source("editor/ui/workspace_builder.py")

    assert ".setFixedWidth(" not in center
    assert 'window.animation_content_splitter.setObjectName("AnimationContentSplitter")' in center
    assert "window.animation_content_splitter.setChildrenCollapsible(False)" in center
    assert "window.animation_content_splitter.setStretchFactor(1, 1)" in center
    assert 'window.animation_properties_scroll.setObjectName("AnimationPropertiesScroll")' in center
