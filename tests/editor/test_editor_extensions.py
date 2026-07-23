from __future__ import annotations

from dataclasses import dataclass

from editor.runtime.editor_extensions import EditorExtensionManager


@dataclass
class ProbeExtension:
    name: str
    events: list[str]
    fail_install: bool = False
    fail_uninstall: bool = False

    def install(self, editor) -> None:
        self.events.append(f"install:{self.name}")
        if self.fail_install:
            raise RuntimeError("install failed")

    def uninstall(self, editor) -> None:
        self.events.append(f"uninstall:{self.name}")
        if self.fail_uninstall:
            raise RuntimeError("uninstall failed")


def test_extensions_install_once_and_uninstall_in_reverse_order() -> None:
    events: list[str] = []
    manager = EditorExtensionManager(object())

    assert manager.install(ProbeExtension("first", events)) is True
    assert manager.install(ProbeExtension("second", events)) is True
    assert manager.install(ProbeExtension("first", events)) is False
    assert manager.installed_names == ("first", "second")

    manager.uninstall_all()

    assert events == [
        "install:first",
        "install:second",
        "uninstall:second",
        "uninstall:first",
    ]
    assert manager.installed_names == ()


def test_failed_install_is_reported_and_not_registered() -> None:
    errors: list[tuple[str, str]] = []
    manager = EditorExtensionManager(
        object(), lambda name, exc: errors.append((name, str(exc)))
    )

    assert manager.install(ProbeExtension("broken", [], fail_install=True)) is False

    assert manager.installed_names == ()
    assert errors == [("broken", "install failed")]


def test_uninstall_failure_does_not_block_remaining_extensions() -> None:
    events: list[str] = []
    errors: list[str] = []
    manager = EditorExtensionManager(object(), lambda name, exc: errors.append(name))
    manager.install(ProbeExtension("first", events))
    manager.install(ProbeExtension("broken", events, fail_uninstall=True))

    manager.uninstall_all()

    assert events[-2:] == ["uninstall:broken", "uninstall:first"]
    assert errors == ["broken"]
