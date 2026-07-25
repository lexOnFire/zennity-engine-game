import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.pipeline.stage import PipelineTask, PipelineStage, PipelineEngine
from engine.build.stages import (
    ResolveDependenciesStage,
    AssetCookingStage,
    AssetCompressionStage,
    PackageGenerationStage,
    ManifestGenerationStage,
    ExecutableLinkStage,
)
from engine.runtime.production_runtime import (
    SceneStreamingService,
    ResourceManagerCache,
    JobScheduler,
)


class CustomPluginStage(PipelineStage):
    def __init__(self) -> None:
        super().__init__("CustomPluginStage")

    def execute(self, task: PipelineTask) -> bool:
        task.logs.append("Estágio customizado do plugin executado!")
        return True


def test_real_build_pipeline_stages():
    """Valida a execução sequencial dos 6 estágios concretos do Build Pipeline Real."""
    pipeline = PipelineEngine("ProductionBuildPipeline")
    pipeline.add_stage(ResolveDependenciesStage())
    pipeline.add_stage(AssetCookingStage())
    pipeline.add_stage(AssetCompressionStage())
    pipeline.add_stage(PackageGenerationStage())
    pipeline.add_stage(ManifestGenerationStage())
    pipeline.add_stage(ExecutableLinkStage())

    task = PipelineTask("FullBuild", input_data="GameProject")
    result = pipeline.run(task)

    assert result.success is True
    assert result.output_data == "game_data.zpak"
    assert result.metadata["executable"] == "Game.exe"
    assert len(result.logs) == 12


def test_pipeline_plugin_extensibility():
    """Valida a injeção dinâmica de estágios por plugins (register_stage after=...)."""
    pipeline = PipelineEngine("ExtensiblePipeline")
    pipeline.add_stage(ResolveDependenciesStage())
    pipeline.add_stage(AssetCookingStage())

    # Plugin injeta estágio após AssetCookingStage
    pipeline.register_stage(CustomPluginStage(), after="AssetCookingStage")
    assert pipeline.stages[2].name == "CustomPluginStage"

    task = PipelineTask("PluginTask", input_data="Test")
    result = pipeline.run(task)
    assert "Estágio customizado do plugin executado!" in result.logs[-1]


def test_fase7_production_runtime_services(qapp):
    """Valida a inicialização automática dos serviços do Runtime de Produção via EngineBootstrap."""
    context = EngineBootstrap.boot()

    streaming = context.services.get_optional(SceneStreamingService)
    assert streaming is not None
    streaming.load_scene_async("Level01.zscene")
    assert "Level01.zscene" in streaming.active_scenes

    cache = context.services.get_optional(ResourceManagerCache)
    assert cache is not None
    cache.cache_asset("texture.png", {"width": 512})
    assert cache.get_asset("texture.png")["width"] == 512

    scheduler = context.services.get_optional(JobScheduler)
    assert scheduler is not None
    executed = []
    scheduler.schedule_job(lambda: executed.append(True))
    assert scheduler.process_jobs() == 1
    assert executed == [True]
