"""Bounded, reusable asset preview metadata for the editor."""
from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QPixmap

from engine.animation.clip_asset import load_animation_asset
from engine.animation.controller_asset import load_animator_controller
from engine.logic.blackboard import load_blackboard_asset
from engine.logic.graph_asset import load_logic_graph


@dataclass(frozen=True)
class AssetPreview:
    label: str
    details: str
    pixmap: QPixmap | None = None


class AssetPreviewService:
    """Create previews once per file revision and retain a bounded working set."""

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3"}

    def __init__(self, danger_color: str, *, maximum_entries: int = 32) -> None:
        if maximum_entries < 1:
            raise ValueError("maximum_entries must be positive")
        self.danger_color = str(danger_color)
        self.maximum_entries = int(maximum_entries)
        self._cache: OrderedDict[tuple[str, int, int], AssetPreview] = OrderedDict()
        self.cache_hits = 0
        self.cache_misses = 0

    def preview(self, path: Path) -> AssetPreview:
        path = Path(path)
        if not path.exists() or path.is_dir():
            return AssetPreview(
                "📁 Folder",
                f"<b>{path.name}</b><br><br>Tipo: Diretório do Projeto<br>Caminho: {path}",
            )
        stat = path.stat()
        key = (str(path.resolve()), int(stat.st_mtime_ns), int(stat.st_size))
        cached = self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            self._cache.move_to_end(key)
            return cached
        self.cache_misses += 1
        result = self._build(path, stat.st_size, stat.st_mtime)
        self._drop_stale_revisions(key[0])
        self._cache[key] = result
        while len(self._cache) > self.maximum_entries:
            self._cache.popitem(last=False)
        return result

    @property
    def cached_entries(self) -> int:
        return len(self._cache)

    def _drop_stale_revisions(self, resolved_path: str) -> None:
        for key in [item for item in self._cache if item[0] == resolved_path]:
            self._cache.pop(key, None)

    def _build(self, path: Path, size_bytes: int, modified: float) -> AssetPreview:
        size = self._format_size(size_bytes)
        date = datetime.fromtimestamp(modified).strftime("%d/%m/%Y %H:%M")
        extension = path.suffix.lower()
        if extension in self.IMAGE_EXTENSIONS:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                details = (
                    f"<b>{path.name}</b><br><br>Tipo: Textura 2D<br>"
                    f"Tamanho: {pixmap.width()} x {pixmap.height()} px<br>"
                    f"Formato: {extension[1:].upper()}<br>Tamanho Físico: {size}<br>Importado: {date}"
                )
                return AssetPreview("", details, pixmap)
        if extension in self.AUDIO_EXTENSIONS:
            return AssetPreview("🔊 Audio", (
                f"<b>{path.name}</b><br><br>Tipo: Clipe de Áudio (AudioClip)<br>"
                f"Formato: {extension[1:].upper()}<br>Tamanho: {size}<br>Importado: {date}<br>"
                "<i>Dica: Arraste para o Inspector para criar um AudioSource</i>"
            ))
        if extension == ".py":
            return AssetPreview("🐍 Script", (
                f"<b>{path.name}</b><br><br>Tipo: Script de Comportamento<br>"
                f"Tamanho: {size}<br>Linguagem: Python 3<br>Modificado: {date}"
            ))
        if extension == ".zanim":
            return self._animation(path, size, date)
        if extension == ".zanimator":
            return self._animator(path, size, date)
        if extension == ".zlogic":
            return self._logic(path, size, date)
        if extension == ".zblackboard":
            return self._blackboard(path, size, date)
        if extension in {".zscene", ".json"}:
            return AssetPreview("🎬 Scene", (
                f"<b>{path.name}</b><br><br>Tipo: Cena de Jogo<br>Formato: Zennity JSON<br>"
                f"Tamanho: {size}<br>Modificado: {date}"
            ))
        return AssetPreview("📄 File", (
            f"<b>{path.name}</b><br><br>Tipo: Recurso Genérico<br>"
            f"Formato: {extension.upper() or 'N/A'}<br>Tamanho: {size}<br>Modificado: {date}"
        ))

    def _animation(self, path: Path, size: str, date: str) -> AssetPreview:
        try:
            asset = load_animation_asset(path)
            details = (
                f"Nome: {asset['name']}<br>Quadros: {len(asset['frames'])}<br>"
                f"FPS: {asset['fps']:g}<br>Repetir: {'Sim' if asset['loop'] else 'Não'}<br>"
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            details = self._invalid(exc)
        return AssetPreview("🎞 Animation", f"<b>{path.name}</b><br><br>Tipo: Clip de Animação 2D<br>{details}Tamanho: {size}<br>Modificado: {date}")

    def _animator(self, path: Path, size: str, date: str) -> AssetPreview:
        try:
            asset = load_animator_controller(path)
            details = (
                f"Nome: {asset['name']}<br>Estado inicial: {asset['initial_state']}<br>"
                f"Estados: {len(asset['states'])}<br>Transições: {len(asset['transitions'])}<br>"
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            details = self._invalid(exc)
        return AssetPreview("◉ Animator Controller", f"<b>{path.name}</b><br><br>Tipo: Animator Controller<br>{details}Tamanho: {size}<br>Modificado: {date}")

    def _logic(self, path: Path, size: str, date: str) -> AssetPreview:
        try:
            graph = load_logic_graph(path)
            target = graph.get("target", {})
            details = (
                f"Nome: {graph['name']}<br>Status: {'Ativo' if graph.get('enabled', True) else 'Desvinculado'}<br>"
                f"Alvo: {target.get('value', 'Nenhum')} ({target.get('type', 'name')})<br>"
                f"Nós: {len(graph['nodes'])}<br>Conexões: {len(graph['edges'])}<br>"
                f"Variáveis: {len(graph['variables'])}<br>"
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            details = self._invalid(exc)
        return AssetPreview("◇ Logic Graph", f"<b>{path.name}</b><br><br>Tipo: Logic Graph Visual<br>{details}Tamanho: {size}<br>Modificado: {date}<br><br><i>Duplo clique para editar</i>")

    def _blackboard(self, path: Path, size: str, date: str) -> AssetPreview:
        try:
            asset = load_blackboard_asset(path)
            details = f"Variáveis de projeto: {len(asset.get('variables', {}))}<br>"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            details = self._invalid(exc)
        return AssetPreview("▦ Blackboard", f"<b>{path.name}</b><br><br>Tipo: Blackboard do Projeto<br>{details}Tamanho: {size}<br>Modificado: {date}")

    def _invalid(self, error: Exception) -> str:
        return f"<span style='color:{self.danger_color}'>Asset inválido: {error}</span><br>"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        size_kb = size_bytes / 1024.0
        return f"{size_kb:.2f} KB" if size_kb < 1024.0 else f"{size_kb / 1024.0:.2f} MB"
