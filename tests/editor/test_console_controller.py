from types import SimpleNamespace

import pytest

from editor.console_controller import ConsoleController


class Output:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.text = ""

    def appendPlainText(self, value: str) -> None:
        self.lines.append(value)

    def setPlainText(self, value: str) -> None:
        self.text = value

    def clear(self) -> None:
        self.lines.clear()
        self.text = ""


def test_console_is_bounded_and_respects_visible_levels() -> None:
    output = Output()
    host = SimpleNamespace(
        console_output=output,
        console_level_checks={
            "INFO": SimpleNamespace(isChecked=lambda: True),
            "ERROR": SimpleNamespace(isChecked=lambda: False),
        },
    )
    controller = ConsoleController(host, maximum_records=2)

    controller.log("info", "one")
    controller.log("error", "hidden")
    controller.log("info", "three")
    controller.refresh()

    assert controller.records == [("ERROR", "hidden"), ("INFO", "three")]
    assert output.lines == ["[INFO] one", "[INFO] three"]
    assert output.text == "[INFO] three"


def test_console_rejects_an_unbounded_zero_capacity() -> None:
    with pytest.raises(ValueError, match="maximum_records"):
        ConsoleController(SimpleNamespace(), maximum_records=0)
