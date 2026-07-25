import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.pipeline.stage import PipelineTask, PipelineEngine
from engine.build.cooking import AssetValidationStage, AssetCookingStage
from editor.wizards.build_wizard_dock import BuildWizardDock
from editor.wizards.project_settings_dock import ProjectSettingsDock


def test_pipeline_engine_architecture():
    """Valida a infraestrutura unificada de Pipeline (PipelineEngine / Stage / Task)."""
    engine = PipelineEngine("TestPipeline")
    engine.add_stage(AssetValidationStage())
    engine.add_stage(AssetCookingStage())

    task = PipelineTask("CookingTask", input_data="Level01.zscene")
    result = engine.run(task)

    assert result.success is True
    assert "cooked://" in result.output_data
    assert len(result.logs) >= 3


def test_build_wizard_dock(qapp):
    """Valida o assistente visual de build consumindo o PipelineEngine."""
    wizard = BuildWizardDock()
    wizard.run_pipeline_wizard()

    assert wizard.progress_bar.value() == 100
    assert "Resultado Final:" in wizard.txt_log.toPlainText()


def test_project_settings_dock(qapp):
    """Valida o dock de configurações de projeto."""
    settings = ProjectSettingsDock()
    assert settings.txt_name.text() == "Zennity Game"
    assert settings.chk_vsync.isChecked() is True
