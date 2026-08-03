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
    JobTask,
)


class CustomPluginStage(PipelineStage):
    def __init__(self) -> None:
        super().__init__("CustomPluginStage")

    def execute(self, task: PipelineTask) -> bool:
        task.logs.append("Estágio customizado do plugin executado!")
        return True


def test_real_build_pipeline_stages():
    """Valida a execução dos 6 estágios concretos com processamento real no disco, Zlib e SHA-256."""
    pipeline = PipelineEngine("ProductionBuildPipeline")
    pipeline.add_stage(ResolveDependenciesStage("engine"))
    pipeline.add_stage(AssetCookingStage())
    pipeline.add_stage(AssetCompressionStage())
    pipeline.add_stage(PackageGenerationStage())
    pipeline.add_stage(ManifestGenerationStage())
    pipeline.add_stage(ExecutableLinkStage())

    task = PipelineTask("FullBuild", input_data="GameProject")
    result = pipeline.run(task)

    assert result.success is True
    assert result.output_data == "game_data.zpak"
    assert result.metadata["executable"] == "ZennityGame.exe"
    assert result.metadata["resolved_deps_count"] > 0
    assert "SHA256-" in result.metadata["manifest_id"]
    assert len(result.logs) == 12


def test_pipeline_plugin_extensibility():
    """Valida a injeção dinâmica de estágios por plugins (register_stage after=...)."""
    pipeline = PipelineEngine("ExtensiblePipeline")
    pipeline.add_stage(ResolveDependenciesStage("engine"))
    pipeline.add_stage(AssetCookingStage())

    pipeline.register_stage(CustomPluginStage(), after="AssetCookingStage")
    assert pipeline.stages[2].name == "CustomPluginStage"

    task = PipelineTask("PluginTask", input_data="Test")
    result = pipeline.run(task)
    assert "Estágio customizado do plugin executado!" in result.logs[-1]


def test_resource_manager_lru_and_budget():
    """Valida a política LRU Eviction e o limite de orçamento de memória (Memory Budget)."""
    cache = ResourceManagerCache(memory_budget_mb=10.0)

    # Adiciona assets ocupando 4MB cada (Total: 8MB <= 10MB)
    cache.cache_asset("asset1.png", "data1", size_mb=4.0)
    cache.cache_asset("asset2.png", "data2", size_mb=4.0)
    assert cache.current_usage_mb == 8.0

    # Adiciona asset3 ocupando 4MB (Excede 10MB -> expulsa asset1.png que é o mais antigo)
    cache.cache_asset("asset3.png", "data3", size_mb=4.0)
    assert cache.get_asset("asset1.png") is None
    assert cache.get_asset("asset2.png") == "data2"
    assert cache.get_asset("asset3.png") == "data3"


def test_scene_streaming_by_distance():
    """Valida o streaming de cena por distância e cancelamento de operação."""
    streaming = SceneStreamingService()

    # Posição do jogador (0, 0), posição da cena (10, 0), limite (50) -> Carrega
    loaded = streaming.load_scene_by_distance("ZoneA.zscene", (0, 0), (10, 0), max_stream_distance=50.0)
    assert loaded is True
    assert "ZoneA.zscene" in streaming.active_scenes

    # Posição do jogador (200, 0), posição da cena (10, 0), limite (50) -> Descarrega
    loaded = streaming.load_scene_by_distance("ZoneA.zscene", (200, 0), (10, 0), max_stream_distance=50.0)
    assert loaded is False
    assert "ZoneA.zscene" not in streaming.active_scenes


def test_job_scheduler_priorities_and_dependencies():
    """Valida o JobScheduler com filas de prioridades e dependências entre tarefas."""
    scheduler = JobScheduler()
    executed_order = []

    j_low = JobTask("LowPriority", lambda: executed_order.append("Low"), priority=1)
    j_high = JobTask("HighPriority", lambda: executed_order.append("High"), priority=10)

    # Job dependente
    j_dep = JobTask("DependentJob", lambda: executed_order.append("Dependent"), priority=20, depends_on=[j_low])

    scheduler.schedule_job(j_low)
    scheduler.schedule_job(j_high)
    scheduler.schedule_job(j_dep)

    # 1ª Rodada: Executa High (Prioridade 10) e Low (Prioridade 1). Dependent aguarda Low terminar.
    assert scheduler.process_jobs() == 2
    assert executed_order == ["High", "Low"]

    # 2ª Rodada: Agora Low terminou (completed=True), executa Dependent
    assert scheduler.process_jobs() == 1
    assert executed_order == ["High", "Low", "Dependent"]
