"""Testes dos nós de runtime de áudio avançado (Pre-Phase 13 Sprint R2)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest

from engine.logic.runtime.nodes.audio_advanced_nodes import (
    execute_play_sound_fade,
    execute_set_pitch,
    execute_set_volume,
    execute_stop_all_sounds,
)


def test_audio_play_sound_fade():
    """Valida o despacho de play_sound_fade para AudioManager."""
    runtime = SimpleNamespace(_stored={}, _store=lambda n, k, v: None)
    game = SimpleNamespace()

    # Falha se path não for fornecido
    bad_node = {"id": "n1", "properties": {"path": ""}}
    assert execute_play_sound_fade(runtime, bad_node, game, 0.016) == ["exec_failure"]

    # Sucesso se o host/game tiver método customizado
    game.play_sound_fade = MagicMock()
    good_node = {"id": "n2", "properties": {"path": "Assets/Audio/theme.mp3", "fade_in": 1.5, "volume": 0.8}}
    assert execute_play_sound_fade(runtime, good_node, game, 0.016) == ["exec_playing"]
    game.play_sound_fade.assert_called_once_with("Assets/Audio/theme.mp3", 1.5, 0.0, 0.8)


def test_audio_set_volume():
    """Valida o controle de volume master/sfx/music."""
    runtime = SimpleNamespace(
        _stored={},
        _store=lambda nid, k, v: runtime._stored.setdefault(nid, {}).__setitem__(k, v),
    )
    game = SimpleNamespace()

    with patch("engine.audio.AudioManager.set_master_volume") as mock_set_master:
        node = {"id": "vol_node", "properties": {"volume": 0.75, "channel": "master"}}
        assert execute_set_volume(runtime, node, game, 0.016) == ["exec_success"]
        mock_set_master.assert_called_once_with(0.75)
        assert runtime._stored["vol_node"]["volume"] == 0.75


def test_audio_set_pitch_explicit_unsupported():
    """Valida que set_pitch aceita 1.0 como neutro e retorna explicitamente exec_failure para pitch != 1.0."""
    runtime = SimpleNamespace(
        _stored={},
        _store=lambda nid, k, v: runtime._stored.setdefault(nid, {}).__setitem__(k, v),
    )
    game = SimpleNamespace()

    # Pitch 1.0 (neutro)
    node_neutral = {"id": "p1", "properties": {"pitch": 1.0}}
    assert execute_set_pitch(runtime, node_neutral, game, 0.016) == ["exec_success"]

    # Pitch != 1.0 é não suportado pelo backend SDL standard -> falha explícita (sem fake pitch)
    node_pitch_fast = {"id": "p2", "properties": {"pitch": 1.5}}
    assert execute_set_pitch(runtime, node_pitch_fast, game, 0.016) == ["exec_failure"]


def test_audio_stop_all_sounds():
    """Valida stop_all_sounds."""
    runtime = SimpleNamespace(_stored={}, _store=lambda n, k, v: None)
    game = SimpleNamespace()

    with patch("pygame.mixer.get_init", return_value=True), patch("pygame.mixer.stop") as mock_stop:
        assert execute_stop_all_sounds(runtime, {"id": "s1"}, game, 0.016) == ["exec_success"]
        mock_stop.assert_called_once()
