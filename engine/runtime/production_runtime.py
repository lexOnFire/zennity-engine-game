"""Consolidação e Hardening do Runtime de Produção (LRU Cache, Memory Budget, Stream por Distância e Priority JobScheduler)."""
from __future__ import annotations
import time
from collections import OrderedDict
from typing import Dict, Any, Optional, List, Callable
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope


class ResourceManagerCache(IService):
    """Gerenciador inteligente de memória de assets com política LRU e Orçamento de Memória."""

    def __init__(self, memory_budget_mb: float = 512.0) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self.memory_budget_mb = memory_budget_mb
        self.current_usage_mb: float = 0.0
        self._cache: OrderedDict[str, dict] = OrderedDict()

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self.clear()

    def cache_asset(self, path: str, asset_data: Any, size_mb: float = 1.0) -> None:
        if path in self._cache:
            self._cache.move_to_end(path)
            old_size = self._cache[path]["size_mb"]
            self.current_usage_mb -= old_size

        # Expulsa assets frios se exceder o orçamento de memória (LRU Eviction)
        while self.current_usage_mb + size_mb > self.memory_budget_mb and self._cache:
            evicted_path, evicted_item = self._cache.popitem(last=False)
            self.current_usage_mb -= evicted_item["size_mb"]

        self._cache[path] = {"data": asset_data, "size_mb": size_mb, "last_accessed": time.time()}
        self.current_usage_mb += size_mb

    def get_asset(self, path: str) -> Optional[Any]:
        if path in self._cache:
            self._cache.move_to_end(path)
            self._cache[path]["last_accessed"] = time.time()
            return self._cache[path]["data"]
        return None

    def clear(self) -> None:
        self._cache.clear()
        self.current_usage_mb = 0.0


class SceneStreamingService(IService):
    """Serviço de streaming de cenas por distância, pré-carregamento e cancelamento."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self.active_scenes: List[str] = []
        self.pending_cancellations: set[str] = set()

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self.active_scenes.clear()

    def load_scene_by_distance(self, scene_name: str, player_pos: tuple[float, float], scene_pos: tuple[float, float], max_stream_distance: float = 100.0) -> bool:
        """Carrega a cena se o jogador estiver dentro do raio de streaming."""
        if scene_name in self.pending_cancellations:
            self.pending_cancellations.remove(scene_name)
            return False

        dist = ((player_pos[0] - scene_pos[0])**2 + (player_pos[1] - scene_pos[1])**2)**0.5
        if dist <= max_stream_distance:
            if scene_name not in self.active_scenes:
                self.active_scenes.append(scene_name)
            return True
        else:
            self.unload_scene(scene_name)
            return False

    def cancel_streaming(self, scene_name: str) -> None:
        self.pending_cancellations.add(scene_name)

    def unload_scene(self, scene_name: str) -> None:
        if scene_name in self.active_scenes:
            self.active_scenes.remove(scene_name)


class JobTask:
    def __init__(self, name: str, func: Callable[[], None], priority: int = 1, depends_on: Optional[List[JobTask]] = None) -> None:
        self.name = name
        self.func = func
        self.priority = priority
        self.depends_on = depends_on or []
        self.completed = False


class JobScheduler(IService):
    """Escalonador por prioridades e dependências integrado ao DiagnosticsService."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._jobs: List[JobTask] = []

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self._jobs.clear()

    def schedule_job(self, job: JobTask) -> None:
        self._jobs.append(job)

    def process_jobs(self) -> int:
        from engine.core.context import EngineContext
        from engine.diagnostics.service import DiagnosticsService

        context = EngineContext.current()
        diag = context.services.get_optional(DiagnosticsService) if context else None

        # Ordena jobs por prioridade descendente (High -> Low)
        self._jobs.sort(key=lambda j: j.priority, reverse=True)
        executed_count = 0

        for job in list(self._jobs):
            # Verifica se dependências estão concluídas
            if any(not dep.completed for dep in job.depends_on):
                continue

            if diag:
                with diag.measure(f"Job.{job.name}"):
                    job.func()
            else:
                job.func()

            job.completed = True
            executed_count += 1
            self._jobs.remove(job)

        return executed_count
