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
    """Motor sequencial de execução de estágios de pipeline."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> PipelineEngine:
        self.stages.append(stage)
        return self

    def run(self, task: PipelineTask) -> PipelineTask:
        for stage in self.stages:
            task.logs.append(f"Executando estágio: {stage.name}")
            stage_success = stage.execute(task)
            if not stage_success:
                task.success = False
                task.logs.append(f"Falha no estágio: {stage.name}")
                break
        return task
