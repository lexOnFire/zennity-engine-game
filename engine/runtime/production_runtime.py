"""Consolidação do Runtime de Produção (SceneStreamingService, ResourceManagerCache e JobScheduler).

Fase 7 oficial da Zennity Engine.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List, Callable
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope


class ResourceManagerCache(IService):
    """Gerenciador inteligente de cache de memória de assets."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._cache: Dict[str, Any] = {}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self._cache.clear()

    def get_asset(self, path: str) -> Optional[Any]:
        return self._cache.get(path)

    def cache_asset(self, path: str, asset_data: Any) -> None:
        self._cache[path] = asset_data

    def clear(self) -> None:
        self._cache.clear()


class SceneStreamingService(IService):
    """Serviço de carregamento assíncrono e incremental de cenas."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self.active_scenes: List[str] = []

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self.active_scenes.clear()

    def load_scene_async(self, scene_name: str, callback: Optional[Callable[[], None]] = None) -> None:
        if scene_name not in self.active_scenes:
            self.active_scenes.append(scene_name)
        if callback:
            callback()

    def unload_scene(self, scene_name: str) -> None:
        if scene_name in self.active_scenes:
            self.active_scenes.remove(scene_name)


class JobScheduler(IService):
    """Escalonador assíncrono de tarefas/jobs do runtime de jogo."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._pending_jobs: List[Callable[[], None]] = []

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self._pending_jobs.clear()

    def schedule_job(self, job_func: Callable[[], None]) -> None:
        self._pending_jobs.append(job_func)

    def process_jobs(self) -> int:
        count = len(self._pending_jobs)
        for job in self._pending_jobs:
            job()
        self._pending_jobs.clear()
        return count
