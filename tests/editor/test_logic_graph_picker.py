from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from editor.widgets.logic_graph_picker import LogicGraphPickerDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_logic_graph_picker_can_create_blank_when_list_is_empty(app) -> None:
    dialog = LogicGraphPickerDialog([])

    dialog.create_button.click()

    assert dialog.create_new is True
    assert dialog.selected_path is None


def test_logic_graph_picker_keeps_existing_graph_binding_choice(app) -> None:
    path = Path("Assets/Logic/player.zlogic")
    dialog = LogicGraphPickerDialog(
        [(path, {"name": "Player", "nodes": [], "target": {"value": "Player"}})]
    )
    dialog._accept_current()

    assert dialog.create_new is False
    assert dialog.selected_path == path
