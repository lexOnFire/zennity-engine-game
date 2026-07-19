from types import SimpleNamespace

from editor.inspector_controller import IsolatedInspectorController


class Widget:
    def __init__(self, visible: bool = True) -> None:
        self.visible = visible
        self.text = ""

    def setVisible(self, visible: bool) -> None:
        self.visible = visible

    def isVisible(self) -> bool:
        return self.visible

    def setText(self, text: str) -> None:
        self.text = text


def _host() -> SimpleNamespace:
    return SimpleNamespace(
        _component_expanded={"transform": False},
        transform_header=Widget(),
        transform_body=Widget(),
        btn_collapse_transform=Widget(),
    )


def test_card_visibility_respects_presence_and_expansion() -> None:
    host = _host()
    controller = IsolatedInspectorController(host)

    controller.set_card_present("transform", True)
    assert host.transform_header.visible is True
    assert host.transform_body.visible is False
    assert host.btn_collapse_transform.text == "▶"

    controller.toggle_card("transform")
    assert host.transform_body.visible is True
    assert host.btn_collapse_transform.text == "▼"


def test_dynamic_card_uses_shared_expansion_state() -> None:
    host = _host()
    controller = IsolatedInspectorController(host)
    body = Widget(False)
    button = Widget()

    controller.toggle_dynamic_card("script:movement", body, button)

    assert host._component_expanded["script:movement"] is True
    assert body.visible is True
    assert button.text == "▼"
