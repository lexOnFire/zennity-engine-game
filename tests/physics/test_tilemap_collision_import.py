"""Testes de regressão da resolução de colisão entre BoxCollider e TileMap (Pre-Phase 13 Sprint R1)."""
from __future__ import annotations

from unittest.mock import MagicMock
import pygame
import pytest

from engine.core.game_object import GameObject
from engine.core.scene import Scene
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.tilemap.tilemap import TileLayer, TileMap, TilemapRenderer


def test_box_collider_tilemap_collision_resolution():
    """Valida que BoxCollider.check_all() importa TileMap e executa resolução de colisão sem ImportError."""
    pygame.init()
    scene = Scene("PhysicsTilemapScene")

    # Mock de Tileset com first_gid e is_solid
    mock_tileset = MagicMock()
    mock_tileset.first_gid = 1
    mock_tileset.is_solid = MagicMock(return_value=True)

    tilemap = TileMap(tile_width=16, tile_height=16, map_width=10, map_height=10)
    tilemap.add_tileset(mock_tileset)
    layer = TileLayer(name="collision", width=10, height=10, data=[1] * 100)
    tilemap.add_layer(layer)

    # GameObject do mapa com TilemapRenderer
    map_go = GameObject("TilemapGO")
    renderer = TilemapRenderer(tilemap=tilemap)
    map_go.add_component(renderer)
    scene.add_game_object(map_go)

    # GameObject do jogador com RigidBody e BoxCollider
    player_go = GameObject("Player")
    player_go.transform.position = (16.0, 16.0, 0.0)
    rb = RigidBody()
    rb.is_kinematic = False
    player_go.add_component(rb)
    collider = BoxCollider(width=16.0, height=16.0)
    player_go.add_component(collider)
    scene.add_game_object(player_go)

    # Executa check_all() sem levantar ImportError
    BoxCollider.check_all()
