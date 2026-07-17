from __future__ import annotations

import sys
# Restaura o ambiente contra poluição de mocks de outros testes
for name in ["engine.physics.collider", "engine.physics.rigidbody", "engine.physics", "engine.transitions", "engine.audio", "engine.ui.ui_manager", "engine.ui"]:
    if name in sys.modules:
        mod = sys.modules[name]
        if not getattr(mod, "__file__", None) and not getattr(mod, "__path__", None):
            sys.modules.pop(name, None)

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QPushButton

from engine.game_object import GameObject
from engine.components.script_component import ScriptComponent
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from editor.models.scene_model import SceneModel
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.runtime.editor_context import EditorContext
from editor.widgets.inspector_dock import InspectorDock


# Garante uma única instância do QApplication para os testes de UI
@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def editor_context() -> EditorContext:
    return EditorContext()


@pytest.fixture
def scene_model() -> SceneModel:
    return SceneModel()


@pytest.fixture
def scene_viewmodel(scene_model: SceneModel, editor_context: EditorContext) -> SceneViewModel:
    return SceneViewModel(
        scene_model,
        selection_manager=editor_context.selection,
        command_manager=editor_context.commands
    )


@pytest.fixture
def inspector(qapp: QApplication, scene_viewmodel: SceneViewModel) -> InspectorDock:
    dock = InspectorDock()
    dock.set_viewmodel(scene_viewmodel)
    return dock


def test_inspector_empty_state_without_selection(inspector: InspectorDock) -> None:
    # Por padrão, sem objeto selecionado, o layout do Inspector deve conter apenas o label indicativo
    assert inspector.layout_content.count() == 1
    widget = inspector.layout_content.itemAt(0).widget()
    assert widget is not None
    assert "Selecione um objeto" in widget.text()


def test_inspector_populates_fields_on_selection(inspector: InspectorDock, scene_viewmodel: SceneViewModel) -> None:
    obj = GameObject("Target")
    obj.transform.position = np.array([12.5, 45.0, 0.0], dtype=np.float32)
    obj.transform.rotation = np.array([0.0, 0.0, 90.0], dtype=np.float32)
    obj.transform.scale = np.array([2.0, 2.5, 1.0], dtype=np.float32)

    scene_viewmodel.selected_object = obj

    # O layout agora deve ser preenchido (cabeçalho, transform, collapsible sections)
    assert inspector.layout_content.count() > 1
    assert hasattr(inspector, "transform_widget")
    
    tw = inspector.transform_widget
    assert tw.sb_pos_x.value() == 12.5
    assert tw.sb_pos_y.value() == 45.0
    assert tw.sb_rot_z.value() == 90.0
    assert tw.sb_sc_x.value() == 2.0
    assert tw.sb_sc_y.value() == 2.5


def test_inspector_interactive_update_no_command(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, editor_context: EditorContext
) -> None:
    obj = GameObject("Target")
    scene_viewmodel.selected_object = obj
    tw = inspector.transform_widget

    # Modifica o valor interativamente pelo spinbox
    tw.sb_pos_x.setValue(55.0)
    QApplication.processEvents()
    
    # O transform deve atualizar imediatamente
    assert obj.transform.position[0] == 55.0
    # Mas nenhum comando de undo/redo deve ser registrado
    assert not editor_context.commands.can_undo


def test_inspector_commit_creates_undo_command(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, editor_context: EditorContext
) -> None:
    obj = GameObject("Target")
    obj.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)
    scene_viewmodel.selected_object = obj
    tw = inspector.transform_widget

    # Simula edição: valor anterior era 10.0. Novo valor é 30.0.
    tw.sb_pos_x.setValue(30.0)
    tw.sb_pos_x.lineEdit().setText("30.0")
    QApplication.processEvents()
    
    tw.commit_val(tw.sb_pos_x, "position", 0)

    # Um comando de undo deve ser gerado
    assert editor_context.commands.can_undo

    # Desfaz a ação
    editor_context.commands.undo()
    assert obj.transform.position[0] == 10.0
    assert tw.sb_pos_x.value() == 10.0

    # Refaz a ação
    editor_context.commands.redo()
    assert obj.transform.position[0] == 30.0
    assert tw.sb_pos_x.value() == 30.0


def test_inspector_commit_identical_value_no_command(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, editor_context: EditorContext
) -> None:
    obj = GameObject("Target")
    scene_viewmodel.selected_object = obj
    tw = inspector.transform_widget

    # Tenta commitar o mesmo valor original (0.0 por padrão)
    tw.commit_val(tw.sb_pos_x, "position", 0)

    assert not editor_context.commands.can_undo


def test_inspector_selection_switch_updates_fields(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel
) -> None:
    obj1 = GameObject("Obj1")
    obj1.transform.position = np.array([1.0, 1.0, 0.0], dtype=np.float32)
    obj2 = GameObject("Obj2")
    obj2.transform.position = np.array([2.0, 2.0, 0.0], dtype=np.float32)

    scene_viewmodel.selected_object = obj1
    assert inspector.transform_widget.sb_pos_x.value() == 1.0

    scene_viewmodel.selected_object = obj2
    assert inspector.transform_widget.sb_pos_x.value() == 2.0


def test_inspector_deleted_object_does_not_crash(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, scene_model: SceneModel
) -> None:
    obj = GameObject("Deletable")
    scene_model.add_object(obj)
    scene_viewmodel.selected_object = obj
    
    # Simula a deleção
    scene_model.remove_object(obj)
    scene_viewmodel.selected_object = None

    # O inspector deve limpar tudo e exibir o estado vazio sem estourar exceções
    assert inspector.layout_content.count() == 1
    widget = inspector.layout_content.itemAt(0).widget()
    assert "Selecione um objeto" in widget.text()


def test_inspector_invalid_input_handling(inspector: InspectorDock, scene_viewmodel: SceneViewModel) -> None:
    obj = GameObject("Target")
    scene_viewmodel.selected_object = obj
    tw = inspector.transform_widget

    # Simula valor original sendo 10.0
    tw.sb_pos_x.original_value = 10.0
    tw.sb_pos_x.setValue(20.0)
    
    # Define o texto do line edit para algo inválido
    tw.sb_pos_x.lineEdit().setText("texto_invalido")
    QApplication.processEvents()
    
    # Commitar valor inválido deve reverter o spinbox para o original (10.0)
    tw.commit_val(tw.sb_pos_x, "position", 0)
    assert tw.sb_pos_x.value() == 10.0


def test_inspector_empty_input_reverts_to_original(inspector: InspectorDock, scene_viewmodel: SceneViewModel) -> None:
    obj = GameObject("Target")
    scene_viewmodel.selected_object = obj
    tw = inspector.transform_widget

    tw.sb_pos_x.original_value = 42.0
    tw.sb_pos_x.setValue(0.0)
    
    # Força texto limpo a ser vazio
    tw.sb_pos_x.lineEdit().setText("")
    QApplication.processEvents()
    
    tw.commit_val(tw.sb_pos_x, "position", 0)
    assert tw.sb_pos_x.value() == 42.0


# ── Novos Testes da Fase 8.1 ───────────────────────────────────────

def test_rigidbody_properties_undo_redo(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, editor_context: EditorContext
) -> None:
    obj = GameObject("RBObject")
    rb = RigidBody()
    rb.mass = 1.0
    rb.gravity_scale = 1.0
    rb.is_kinematic = False
    obj.add_component(rb)

    scene_viewmodel.selected_object = obj
    assert hasattr(inspector, "rb_widget")
    
    rw = inspector.rb_widget
    assert rw.sb_mass.value() == 1.0
    
    # 1. Teste de Edição de Massa
    rw.sb_mass.setValue(5.5)
    rw.sb_mass.lineEdit().setText("5.5")
    QApplication.processEvents()
    
    rw.commit_val(rw.sb_mass, "mass")
    assert rb.mass == 5.5
    assert editor_context.commands.can_undo
    
    editor_context.commands.undo()
    assert rb.mass == 1.0
    assert rw.sb_mass.value() == 1.0
    
    editor_context.commands.redo()
    assert rb.mass == 5.5
    assert rw.sb_mass.value() == 5.5

    # 2. Teste de Edição de Cinemático
    rw.chk_kin.setChecked(True)
    rw.commit_kinematic()
    assert rb.is_kinematic is True
    
    editor_context.commands.undo()
    assert rb.is_kinematic is False
    assert rw.chk_kin.isChecked() is False


def test_collider_properties_undo_redo_sync(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, editor_context: EditorContext
) -> None:
    obj = GameObject("ColObject")
    col = BoxCollider(width=100, height=200)
    obj.add_component(col)
    
    scene_viewmodel.selected_object = obj
    assert hasattr(inspector, "col_widget")
    
    cw = inspector.col_widget
    assert cw.sb_w.value() == 100
    
    # Edita largura e valida se escala do transform sincroniza
    cw.sb_w.setValue(300)
    cw.sb_w.lineEdit().setText("300")
    QApplication.processEvents()
    
    cw.commit_val(cw.sb_w, "width")
    assert col.width == 300
    assert obj.transform.scale[0] == 300.0
    
    # Teste de Undo
    editor_context.commands.undo()
    assert col.width == 100
    assert obj.transform.scale[0] == 100.0
    
    # Teste de Redo
    editor_context.commands.redo()
    assert col.width == 300
    assert obj.transform.scale[0] == 300.0


def test_script_property_undo_redo(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, editor_context: EditorContext
) -> None:
    obj = GameObject("ScriptObject")
    obj.script_path = ""
    scene_viewmodel.selected_object = obj
    
    assert hasattr(inspector, "script_widget")
    sw = inspector.script_widget
    
    # Simula seleção de script
    sw.cb_scripts.addItem("scripts/behavior_test.py")
    idx = sw.cb_scripts.findText("scripts/behavior_test.py")
    sw.cb_scripts.setCurrentIndex(idx)
    sw.on_script_activated(idx)
    
    assert obj.script_path == "scripts/behavior_test.py"
    assert editor_context.commands.can_undo
    
    editor_context.commands.undo()
    assert obj.script_path == ""
    
    editor_context.commands.redo()
    assert obj.script_path == "scripts/behavior_test.py"


def test_script_inspector_lists_assets_scripts_and_uses_buttons(
    inspector: InspectorDock,
    scene_viewmodel: SceneViewModel,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    scripts_dir = tmp_path / "Assets" / "Scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "player_controller.py").write_text(
        "from engine.runtime import ScriptBehaviour\n",
        encoding="utf-8",
    )
    (scripts_dir / "enemy_ai.py").write_text(
        "from engine.runtime import ScriptBehaviour\n",
        encoding="utf-8",
    )
    (scripts_dir / "enemy_ai.py.meta").write_text("{}", encoding="utf-8")

    obj = GameObject("ScriptObject")
    obj.add_component(ScriptComponent(""))
    scene_viewmodel.selected_object = obj

    sw = inspector.script_widget
    items = [sw.cb_scripts.itemText(index) for index in range(sw.cb_scripts.count())]
    buttons = {button.text() for button in sw.findChildren(QPushButton)}
    checkboxes = {checkbox.text() for checkbox in sw.findChildren(QCheckBox)}

    assert "Assets/Scripts/player_controller.py" in items
    assert "Assets/Scripts/enemy_ai.py" in items
    assert all(not item.endswith(".meta") for item in items)
    assert {"Editar", "Criar"}.issubset(buttons)
    assert "Editar" not in checkboxes


def test_script_inspector_create_button_creates_script_template(
    inspector: InspectorDock,
    scene_viewmodel: SceneViewModel,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    obj = GameObject("Player Ship")
    script = obj.add_component(ScriptComponent(""))
    scene_viewmodel.selected_object = obj

    inspector.script_widget.create_script()

    created = tmp_path / "Assets" / "Scripts" / "player_ship.py"
    assert created.exists()
    assert "class PlayerShipBehaviour(ScriptBehaviour)" in created.read_text(encoding="utf-8")
    assert script.script_path == "Assets/Scripts/player_ship.py"
