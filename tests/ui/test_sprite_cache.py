from __future__ import annotations

from pathlib import Path

import pygame

from engine.ui.runtime_components import ImageComponent, InfiniteBackground


def setup_function() -> None:
    ImageComponent.clear_caches()
    InfiniteBackground.clear_cache()


def test_transformed_surface_reuses_same_geometry(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "sprite.png"
    path.write_bytes(b"sprite")
    source = pygame.Surface((8, 8), pygame.SRCALPHA)
    monkeypatch.setattr(pygame.image, "load", lambda _: source)

    first = ImageComponent.transformed_surface(str(path), 32, 16, 255, 12.34)
    second = ImageComponent.transformed_surface(str(path), 32, 16, 255, 12.31)

    assert first is second
    assert len(ImageComponent._transformed_cache) == 1


def test_transformed_cache_is_lru_bounded(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "sprite.png"
    path.write_bytes(b"sprite")
    monkeypatch.setattr(pygame.image, "load", lambda _: pygame.Surface((4, 4)))
    monkeypatch.setattr(ImageComponent, "_max_transformed_cache", 2)

    ImageComponent.transformed_surface(str(path), 10, 10, 255, 0)
    ImageComponent.transformed_surface(str(path), 20, 20, 255, 0)
    ImageComponent.transformed_surface(str(path), 30, 30, 255, 0)

    assert len(ImageComponent._transformed_cache) == 2
    assert all(key[1] != 10 for key in ImageComponent._transformed_cache)


def test_changing_sprite_path_invalidates_old_geometry(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "sprite.png"
    path.write_bytes(b"sprite")
    monkeypatch.setattr(pygame.image, "load", lambda _: pygame.Surface((4, 4)))
    component = ImageComponent(str(path))
    ImageComponent.transformed_surface(str(path), 10, 10, 255, 0)

    component.sprite_path = str(tmp_path / "other.png")

    assert ImageComponent._surface_cache == {}
    assert ImageComponent._transformed_cache == {}


def test_background_tile_cache_reuses_scaled_surface() -> None:
    background = InfiniteBackground("Assets/background.png", alpha=128)
    source = pygame.Surface((4, 4), pygame.SRCALPHA)

    first = background._background_tile(source, 20, 10)
    second = background._background_tile(source, 20, 10)

    assert first is second
    assert first.get_alpha() == 128


def test_runtime_components_do_not_apply_performance_patch_at_import() -> None:
    source = Path("engine/ui/runtime_components.py").read_text(encoding="utf-8")

    assert "apply_sprite_performance_patch" not in source
    assert "sprite_performance_patch" not in source
