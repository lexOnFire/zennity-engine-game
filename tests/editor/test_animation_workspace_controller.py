from types import SimpleNamespace

from editor.animation_workspace_controller import AnimationWorkspaceController


class Field:
    def __init__(self, value=0):
        self._value = value

    def value(self):
        return self._value


def test_frame_count_is_never_zero() -> None:
    host = SimpleNamespace(animator_frame_count=Field(0))
    assert AnimationWorkspaceController(host).frame_count() == 1


def test_mark_dirty_is_suppressed_while_inspector_projects_values() -> None:
    host = SimpleNamespace(_updating_inspector=True, _animation_asset_dirty=False)
    controller = AnimationWorkspaceController(host)

    controller.mark_dirty()

    assert host._animation_asset_dirty is False
