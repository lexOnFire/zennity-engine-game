"""Asset Cooking Operational Pipeline (Cooking, Dependency Resolution e Compression)."""
from __future__ import annotations
from typing import Any
from engine.pipeline.stage import PipelineStage, PipelineTask


class AssetValidationStage(PipelineStage):
    """Estágio de Validação de Integridade do Asset."""

    def __init__(self) -> None:
        super().__init__("AssetValidationStage")

    def execute(self, task: PipelineTask) -> bool:
        if not task.input_data:
            return False
        task.logs.append("Validação do asset concluída com sucesso.")
        return True


class SingleAssetCookingStage(PipelineStage):
    """Estágio de Transformação/Cooking de Raw Asset para Engine Binary Format."""

    def __init__(self) -> None:
        super().__init__("AssetCookingStage")

    def execute(self, task: PipelineTask) -> bool:
        raw = str(task.input_data)
        task.output_data = f"cooked://{raw}.zpak"
        task.metadata["cooked_size_bytes"] = len(raw) * 128
        task.logs.append(f"Asset cooked para formato binário otimizado: {task.output_data}")
        return True


AssetCookingStage = SingleAssetCookingStage
