from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pygame

from engine.core.services import IService
from engine.core.lifecycle import ServiceScope
from engine.assets.asset_handle import AssetHandle


class RuntimeAssetManager(IService):
    """
    Serviço central de gerenciamento de recursos em tempo de execução.
    Suporta contagem de referências (RefCounter) e liberação controlada de RAM/VRAM.
    """

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._images: Dict[str, pygame.Surface] = {}
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._fonts: Dict[Tuple[str, int], pygame.font.Font] = {}
        self._meshes: Dict[str, Any] = {}
        self._ref_counts: Dict[str, int] = {}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        self.clear_all()

    def acquire(self, key: str) -> None:
        """Incrementa a contagem de referência de um recurso."""
        self._ref_counts[key] = self._ref_counts.get(key, 0) + 1

    def release(self, key: str) -> int:
        """Decrementa a contagem de referência. Retorna a contagem atual."""
        if key in self._ref_counts:
            self._ref_counts[key] = max(0, self._ref_counts[key] - 1)
            return self._ref_counts[key]
        return 0

    def get_ref_count(self, key: str) -> int:
        return self._ref_counts.get(key, 0)

    def get_image(self, path: str, alpha: bool = True) -> pygame.Surface:
        key = f"image:{path}"
        self.acquire(key)
        if path not in self._images:
            if not os.path.exists(path):
                fallback = pygame.Surface((32, 32))
                fallback.fill((255, 0, 255))
                self._images[path] = fallback
            else:
                img = pygame.image.load(path)
                self._images[path] = img.convert_alpha() if alpha else img.convert()
        return self._images[path]

    def get_sound(self, path: str) -> pygame.mixer.Sound:
        key = f"sound:{path}"
        self.acquire(key)
        if path not in self._sounds:
            if not os.path.exists(path):
                class NullSound:
                    def play(self, *args, **kwargs): pass
                    def stop(self): pass
                    def set_volume(self, *args): pass
                self._sounds[path] = NullSound() # type: ignore
            else:
                self._sounds[path] = pygame.mixer.Sound(path)
        return self._sounds[path]

    def get_font(self, name: Optional[str], size: int) -> pygame.font.Font:
        key_name = name or "sys_default"
        cache_key = (key_name, size)
        ref_key = f"font:{key_name}:{size}"
        self.acquire(ref_key)
        if cache_key not in self._fonts:
            if name is None or not os.path.exists(name):
                self._fonts[cache_key] = pygame.font.SysFont("Arial", size)
            else:
                self._fonts[cache_key] = pygame.font.Font(name, size)
        return self._fonts[cache_key]

    def unload_unused_assets(self) -> int:
        """Desaloca recursos em memória cuja contagem de referências é 0."""
        unloaded = 0
        
        # Unload Images
        for path in list(self._images.keys()):
            if self.get_ref_count(f"image:{path}") <= 0:
                del self._images[path]
                self._ref_counts.pop(f"image:{path}", None)
                unloaded += 1
                
        # Unload Sounds
        for path in list(self._sounds.keys()):
            if self.get_ref_count(f"sound:{path}") <= 0:
                del self._sounds[path]
                self._ref_counts.pop(f"sound:{path}", None)
                unloaded += 1
                
        return unloaded

    def clear_all(self) -> None:
        self._images.clear()
        self._sounds.clear()
        self._fonts.clear()
        self._meshes.clear()
        self._ref_counts.clear()
