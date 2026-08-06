from __future__ import annotations
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication

from editor.inspector.ui_binder_plugin import UIBinderPlugin, PropertyPickerDialog
from editor.inspector.animation_controller_plugin import AnimationControllerPlugin
from editor.dialogue_builder.csv_importer import CSVDialogueImporter
from engine.ui.ui_binder import UIBinder
from engine.animation.animation_controller import AnimationController


@pytest.fixture(autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


class MockObject:
    def __init__(self, name: str, health: int = 100):
        self.name = name
        self.health = health


def test_ui_binder_plugin_creation():
    """Testa criação do widget do plugin UIBinderPlugin."""
    plugin = UIBinderPlugin()
    binder = UIBinder(source_path="player.health", ui_element_name="HealthLabel")
    widget = plugin.create_widget(binder, None)
    
    assert widget is not None
    assert plugin.source_input.text() == "player.health"
    assert plugin.elem_input.text() == "HealthLabel"


def test_property_picker_dialog():
    """Testa diálogo seletor de propriedades para UIBinder."""
    dialog = PropertyPickerDialog()
    player = MockObject("Player", health=100)
    dialog.set_scene_objects([player])
    
    assert dialog.tree.topLevelItemCount() == 1
    item = dialog.tree.topLevelItem(0)
    assert item.text(0) == "Player"
    assert item.childCount() >= 1


def test_animation_controller_plugin():
    """Testa widget do plugin AnimationControllerPlugin."""
    plugin = AnimationControllerPlugin()
    controller = AnimationController()
    controller.add_state("idle", "idle_clip")
    controller.add_state("run", "run_clip")
    controller.set_parameter("speed", 1.5)

    widget = plugin.create_widget(controller, None)
    assert widget is not None
    assert plugin.states_table.rowCount() == 2
    assert plugin.params_table.rowCount() == 1


def test_csv_dialogue_importer(tmp_path: Path):
    """Testa importação de CSV para .zdialogue JSON."""
    csv_file = tmp_path / "dialogue.csv"
    csv_content = "speaker,text,next_node,condition\nMerchant,Hello!,choice1,\nPlayer,Hi,end,\n"
    csv_file.write_text(csv_content, encoding="utf-8")

    importer = CSVDialogueImporter()
    output_json_path = tmp_path / "dialogue.zdialogue"
    importer.import_from_csv(csv_file, output_json_path)

    assert output_json_path.exists()
    data = json.loads(output_json_path.read_text(encoding="utf-8"))
    assert data["category"] == "Dialogue"
    assert len(data["nodes"]) == 2
    assert data["nodes"][0]["inputs"]["speaker"] == "Merchant"
