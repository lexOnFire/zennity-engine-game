from __future__ import annotations


from editor.runtime.editor_extensions import EditorExtensionManager


class ProbeExtension:
    def __init__(self, name: str, events: list[str], fail_enable: bool = False, fail_disable: bool = False):
        self.name = name
        self.events = events
        self.fail_enable = fail_enable
        self.fail_disable = fail_disable

    def load(self, editor):
        self.events.append(f"load:{self.name}")

    def enable(self, editor):
        if self.fail_enable:
            raise RuntimeError(f"fail_enable:{self.name}")
        self.events.append(f"enable:{self.name}")

    def disable(self, editor):
        if self.fail_disable:
            raise RuntimeError(f"fail_disable:{self.name}")
        self.events.append(f"disable:{self.name}")

    def unload(self, editor):
        self.events.append(f"unload:{self.name}")


def test_extensions_install_once_and_uninstall_in_reverse_order():
    events = []
    manager = EditorExtensionManager(editor=None)

    first = ProbeExtension("first", events)
    second = ProbeExtension("second", events)

    assert manager.install(first) is True
    assert manager.install(first) is False
    assert manager.install(second) is True

    assert events == ["load:first", "enable:first", "load:second", "enable:second"]

    manager.uninstall_all()
    assert events == [
        "load:first", "enable:first",
        "load:second", "enable:second",
        "disable:second", "unload:second",
        "disable:first", "unload:first"
    ]
    assert len(manager.installed_names) == 0


def test_failed_install_is_reported_and_not_registered():
    events = []
    errors = []

    def on_err(n: str, phase: str, exc: Exception):
        errors.append(f"{n}:{phase}:{exc}")

    manager = EditorExtensionManager(editor=None, on_error=on_err)

    # Fail enable -> should rollback
    assert manager.install(ProbeExtension("broken", events, fail_enable=True)) is False

    assert "broken" not in manager.installed_names
    assert len(errors) == 1
    assert errors[0] == "broken:enable:fail_enable:broken"
    # Note: rollback disable/unload might not have been recorded if they didn't fail.
    # Actually, they are called, let's verify events.
    assert events == ["load:broken", "disable:broken", "unload:broken"]


def test_uninstall_failure_does_not_block_remaining_extensions():
    events = []
    errors = []

    def on_err(n: str, phase: str, exc: Exception):
        errors.append(f"{n}:{phase}:{exc}")

    manager = EditorExtensionManager(editor=None, on_error=on_err)

    manager.install(ProbeExtension("first", events))
    manager.install(ProbeExtension("broken", events, fail_disable=True))

    manager.uninstall_all()

    assert len(errors) == 1
    assert errors[0] == "broken:disable:fail_disable:broken"
    assert events[-3:] == ["unload:broken", "disable:first", "unload:first"]
