"""
demo_tilemap.py
───────────────
Demo do sistema de Tilemap da Zennity Engine.

Como usar:
1. Coloque um tileset PNG em demos/assets/tileset_demo.png
   (qualquer imagem com tiles de 32x32 serve — ex: Kenney.nl)
2. Execute:  python -m demos.demo_tilemap

Este demo gera um mapa procedural com tiles coloridos caso não
encontre o arquivo de tileset real, para que você possa testar
mesmo sem assets prontos.
"""
import sys
import os
import atexit
import pygame

# Garante que o pacote 'engine' seja encontrado ao rodar direto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.core import Engine, Scene
from engine.input import Input
from engine.tilemap import TileMap, TileLayer, Tileset, TileData


# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────

TW, TH = 32, 32   # tile size
MW, MH = 30, 20   # map size in tiles

# Path do tileset tempário gerado proceduralmente
_TMP_TILESET_PATH = os.path.join(os.path.dirname(__file__), "_tmp_tileset.png")


def _cleanup_tmp_tileset() -> None:
    """Remove o arquivo temporário ao encerrar o processo."""
    # BUG FIX: o arquivo PNG temporário nunca era apagado, poluindo o diretório
    # e potencialmente causando leituras desatualizadas em execuções seguintes.
    if os.path.isfile(_TMP_TILESET_PATH):
        try:
            os.remove(_TMP_TILESET_PATH)
        except OSError:
            pass


atexit.register(_cleanup_tmp_tileset)


def _make_procedural_tileset() -> Tileset:
    """
    Gera um tileset de cores sólidas em memória (sem PNG externo).
    Tile 1 = grama (verde escuro)  — solid
    Tile 2 = terra (marrom)        — solid
    Tile 3 = céu   (azul)          — decorativo
    Tile 4 = lava  (laranja)       — damage=10
    """
    COLORS = {
        1: (34,  139, 34),    # grama
        2: (139, 90,  43),    # terra
        3: (100, 149, 237),   # céu
        4: (255, 120,  20),   # lava
    }

    # Cria sheet 2x2 tiles
    sheet = pygame.Surface((TW * 2, TH * 2), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))
    positions = {1: (0, 0), 2: (TW, 0), 3: (0, TH), 4: (TW, TH)}
    for gid, (px, py) in positions.items():
        pygame.draw.rect(sheet, COLORS[gid], (px, py, TW - 2, TH - 2))
        # borda mais escura
        r, g, b = COLORS[gid]
        pygame.draw.rect(sheet, (max(0, r - 40), max(0, g - 40), max(0, b - 40)),
                         (px, py, TW - 2, TH - 2), 2)

    # BUG FIX: use o path centralizado para não deixar o arquivo órfão.
    pygame.image.save(sheet, _TMP_TILESET_PATH)

    ts = Tileset(
        image_path  = _TMP_TILESET_PATH,
        tile_width  = TW,
        tile_height = TH,
        first_gid   = 1,
        spacing     = 0,
        margin      = 0,
    )
    ts.load()

    ts.set_tile_data(1, TileData(tile_id=1, solid=True))
    ts.set_tile_data(2, TileData(tile_id=2, solid=True))
    ts.set_tile_data(3, TileData(tile_id=3, solid=False))
    ts.set_tile_data(4, TileData(tile_id=4, solid=False, damage=10,
                                 custom={"type": "lava"}))
    return ts


def _build_map(ts: Tileset) -> TileMap:
    tilemap = TileMap(tile_width=TW, tile_height=TH,
                      map_width=MW, map_height=MH)
    tilemap.add_tileset(ts)

    # ── Camada de fundo (céu)
    bg_data = [3] * (MW * MH)
    bg_layer = TileLayer("background", MW, MH, bg_data,
                         visible=True, opacity=1.0, z_index=0)
    tilemap.add_layer(bg_layer)

    # ── Camada de colisão (chão + plataformas)
    col_data = [0] * (MW * MH)

    # Chão completo nas últimas 3 linhas
    for row in range(MH - 3, MH):
        for col in range(MW):
            col_data[row * MW + col] = 1 if row == MH - 3 else 2

    # Plataformas
    platforms = [
        (3, 14, 4), (8, 12, 4), (14, 10, 5),
        (20, 13, 4), (25, 11, 4),
    ]
    for start_col, row, length in platforms:
        for c in range(start_col, min(start_col + length, MW)):
            col_data[row * MW + c] = 1

    # Lava no fundo (última linha)
    for col in range(MW):
        col_data[(MH - 1) * MW + col] = 4

    col_layer = TileLayer("collision", MW, MH, col_data,
                          visible=True, opacity=1.0, z_index=1)
    tilemap.add_layer(col_layer)

    # Bake para performance
    tilemap.bake()
    return tilemap


# ───────────────────────────────────────────────
# Cena demo
# ───────────────────────────────────────────────

from engine.game_object import GameObject
from engine.graphics.camera2d import Camera2D
from engine.tilemap import TilemapRenderer
import numpy as np

class TilemapDemoScene(Scene):
    def start(self):
        self.tileset = _make_procedural_tileset()
        self.tilemap = _build_map(self.tileset)

        # Configura a árvore ECS para o mapa e câmera
        self.map_obj = GameObject("Map")
        self.map_renderer = self.map_obj.add_component(TilemapRenderer(self.tilemap))
        self.add_game_object(self.map_obj)

        self.cam_obj = GameObject("Camera")
        self.camera2d = self.cam_obj.add_component(Camera2D())
        self.add_game_object(self.cam_obj)

        # Configura a câmera 2D ativa
        Camera2D.main = self.camera2d

        # Câmera local pos
        self.cam_x: float = 0.0
        self.cam_y: float = 0.0
        self.cam_speed: float = 200.0

        # Debug
        self.show_debug: bool = False

        # Fonte para HUD
        self.font = pygame.font.SysFont("monospace", 14)

    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        go._propagate_scene(self)

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.cam_x -= self.cam_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.cam_x += self.cam_speed * dt
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.cam_y -= self.cam_speed * dt
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.cam_y += self.cam_speed * dt

        eng_w = getattr(self, "engine", None)
        screen_w = getattr(eng_w, "width",  800) if eng_w else 800
        screen_h = getattr(eng_w, "height", 600) if eng_w else 600

        # Clamp câmera dentro dos limites do mapa
        max_cam_x = max(0.0, float(self.tilemap.pixel_width  - screen_w))
        max_cam_y = max(0.0, float(self.tilemap.pixel_height - screen_h))
        self.cam_x = max(0.0, min(self.cam_x, max_cam_x))
        self.cam_y = max(0.0, min(self.cam_y, max_cam_y))

        # Atualiza a posição da Camera2D (centrada na tela)
        self.cam_obj.transform.position = np.array([self.cam_x + screen_w / 2.0, self.cam_y + screen_h / 2.0], np.float32)

        # Atualiza todos os GameObjects
        for go in self.game_objects:
            go.update(dt)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.show_debug = not self.show_debug

    def draw(self, screen: pygame.Surface):
        screen.fill((20, 20, 30))

        # Desenha os GameObjects cadastrados
        for go in self.game_objects:
            go.draw(screen)

        if self.show_debug:
            self.tilemap.draw_debug(screen, self.cam_x, self.cam_y,
                                    color=(255, 60, 60, 128), layer_name="collision")

        # HUD
        lines = [
            "Zennity Engine — Tilemap Demo",
            f"Camera: ({int(self.cam_x)}, {int(self.cam_y)})",
            "Mover: WASD / Setas",
            f"Debug colisão [F1]: {'ON' if self.show_debug else 'OFF'}",
        ]
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, (220, 220, 220))
            screen.blit(surf, (10, 10 + i * 18))


# ───────────────────────────────────────────────
# Entry point
# ───────────────────────────────────────────────

if __name__ == "__main__":
    pygame.init()
    engine = Engine(width=800, height=600, title="Zennity — Tilemap Demo", fps=60)
    engine.run(TilemapDemoScene())
