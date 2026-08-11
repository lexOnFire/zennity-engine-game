"""Caches must be bounded, or scoped to something that ends.

PHASE 9.5B Stage 3 cache classification:

===========================  ==================  ============================
cache                        lifetime            bound
===========================  ==================  ============================
ImageComponent._transformed  project             256 entries (_trim_cache)
InfiniteBackground._tile     project             64 entries (_trim_cache)
AudioManager._sound_cache    play session        cleared by AudioManager.clear()
UIRenderer._font_cache       play session        dies with its RuntimeScene
UIRenderer._image_cache      play session        dies with its RuntimeScene
engine.assets cache          play session        cleared by clear_cache()
===========================  ==================  ============================

A project-lifetime cache is legitimate and must NOT be cleared on Stop -- doing
so would re-decode every texture on the next Play.  What matters is that it has
a ceiling.
"""

from __future__ import annotations

import gc
import weakref

import pytest

from engine.runtime import RuntimeManager
from tests._lifecycle_probe import scene_with_objects


def test_sprite_caches_are_bounded():
    from engine.ui import sprite_performance_patch as patch

    assert patch._MAX_SPRITE_CACHE > 0
    assert patch._MAX_BACKGROUND_CACHE > 0

    cache = {}
    for index in range(patch._MAX_SPRITE_CACHE + 50):
        cache[index] = object()
        patch._trim_cache(cache, patch._MAX_SPRITE_CACHE)

    assert len(cache) <= patch._MAX_SPRITE_CACHE, "sprite cache exceeded its ceiling"


def test_trim_cache_evicts_oldest_first():
    from engine.ui.sprite_performance_patch import _trim_cache

    cache = {"a": 1, "b": 2, "c": 3}
    _trim_cache(cache, 2)
    assert len(cache) == 2
    assert "a" not in cache, "eviction did not drop the oldest entry"


def test_audio_cache_is_cleared_on_stop():
    from engine.audio import AudioManager

    AudioManager._sound_cache["sentinel.wav"] = object()
    AudioManager.clear()
    assert "sentinel.wav" not in AudioManager._sound_cache


def test_ui_renderer_caches_die_with_the_session():
    """Session-scoped by construction: one UIRenderer per RuntimeScene."""
    manager = RuntimeManager()
    scene = scene_with_objects()
    try:
        runtime_scene = manager.start_play(scene)
        renderer_reference = weakref.ref(runtime_scene.ui_renderer)
        runtime_scene.ui_renderer._image_cache["sentinel.png"] = object()
        del runtime_scene
        manager.stop_play()
        gc.collect()
        assert renderer_reference() is None, (
            "the session's UIRenderer outlived its RuntimeScene, so its caches "
            "grow across Play cycles"
        )
    finally:
        manager.stop_play()


@pytest.mark.parametrize("cycles", [10])
def test_audio_cache_does_not_grow_across_cycles(cycles):
    from engine.audio import AudioManager

    manager = RuntimeManager()
    scene = scene_with_objects()
    try:
        for _ in range(cycles):
            manager.start_play(scene)
            manager.tick(1.0 / 60.0)
            manager.stop_play()
        assert len(AudioManager._sound_cache) == 0
    finally:
        manager.stop_play()
