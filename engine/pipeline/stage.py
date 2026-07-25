"""Conceito Unificado de Pipeline (PipelineStage, PipelineTask e PipelineEngine) da Zennity Engine.

Padroniza os fluxos de:
- Asset Pipeline
- Build Pipeline
- Graph Compiler
- Animation Import
- Extension Loading
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PipelineTask:
    """Tarefa de dados processada pelas etapas do pipeline."""

    def __init__(self, name: str, input_data: Any) -> None:
        self.name = name
        self.input_data = input_data
        self.output_data: Any = None
        self.metadata: Dict[str, Any] = {}
        self.success: bool = True
        self.logs: List[str] = []


class PipelineStage(ABC):
    """Estágio abstrato de um pipeline (Input -> Validation -> Transformation -> Result)."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def execute(self, task: PipelineTask) -> bool:
        """Executa a transformação ou validação na tarefa."""
        pass


class PipelineEngine:
    """Motor de execução de estágios de pipeline extensível e observável."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> PipelineEngine:
        self.stages.append(stage)
        return self

    def register_stage(self, stage: PipelineStage, after: Optional[str] = None) -> PipelineEngine:
        """Injeta dinamicamente um estágio de plugin após outro estágio especificado."""
        if not after:
            self.stages.append(stage)
            return self

        for idx, existing in enumerate(self.stages):
            if existing.name == after:
                self.stages.insert(idx + 1, stage)
                return self

        self.stages.append(stage)
        return self

    def run(self, task: PipelineTask) -> PipelineTask:
        from engine.core.context import EngineContext
        from engine.diagnostics.service import DiagnosticsService

        context = EngineContext.current()
        diag_service = context.services.get_optional(DiagnosticsService) if context else None

        for stage in self.stages:
            task.logs.append(f"Executando estágio: {stage.name}")
            
            if diag_service:
                with diag_service.measure(f"Pipeline.{stage.name}"):
                    stage_success = stage.execute(task)
            else:
                stage_success = stage.execute(task)

            if not stage_success:
                task.success = False
                task.logs.append(f"Falha no estágio: {stage.name}")
                break
        return task
