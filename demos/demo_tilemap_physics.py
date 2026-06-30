"""
demos/demo_tilemap_physics.py
──────────────────────────────
Demo: BoxCollider + RigidBody + TilemapCollider

Controles:
  A / D ou ← →   Mover
  Space / W / ↑   Pular
  F1              Debug de colisão
  R               Resetar posição

Rodar:
  python -m demos.demo_tilemap_physics
"""
import sys
import os
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.core     import Engine, Scene
from engine.game_object import GameObject
from engine.physics.rigidbody      import RigidBody
from engine.physics.collider       import BoxCollider
from engine.physics.tilemap_collider import TilemapCollider
from engine.tilemap  import TileMap, TileLayer, Tileset, TileData

# ─────────────────────────────────────────────
TW, TH = 32, 32
MW, MH = 30, 20
SPEED   = 160.0
JUMP_V  = -420.0
SCREEN_W, SCREEN_H = 800, 600
SPAWN_X, SPAWN_Y   = 80.0, 100.0


# ─────────────────────────────────────────────
def _make_tileset() -> Tileset:
    """Tileset procedural de cores — sem PNG externo."""
    COLORS = {
        1: (60,  180, 75),   # grama
        2: (150, 100, 55),   # terra
        3: (80,  130, 210),  # céu
        4: (255, 100, 20),   # lava
    }
    sheet = pygame.Surface((TW * 2, TH * 2), pygame.SRCALPHA)
    positions = {1:(0,0), 2:(TW,0), 3:(0,TH), 4:(TW,TH)}
    for gid, (px, py) in positions.items():
        r, g, b = COLORS[gid]
        pygame.draw.rect(sheet, (r, g, b), (px+1, py+1, TW-2, TH-2))
        pygame.draw.rect(sheet, (max(0,r-50),max(0,g-50),max(0,b-50)),
                         (px+1, py+1, TW-2, TH-2), 2)

    tmp = os.path.join(os.path.dirname(__file__), "_tmp_ts_phys.png")
    pygame.image.save(sheet, tmp)

    ts = Tileset(tmp, TW, TH, first_gid=1)
    ts.load()
    ts.set_tile_data(1, TileData(1, solid=True))
    ts.set_tile_data(2, TileData(2, solid=True))
    ts.set_tile_data(3, TileData(3, solid=False))
    ts.set_tile_data(4, TileData(4, solid=False, damage=10, custom={"type":"lava"}))
    return ts


def _build_map(ts: Tileset) -> TileMap:
    tilemap = TileMap(TW, TH, MW, MH)
    tilemap.add_tileset(ts)

    # Fundo
    bg = [3] * (MW * MH)
    tilemap.add_layer(TileLayer("background", MW, MH, bg, z_index=0))

    # Colisão
    col_data = [0] * (MW * MH)

    # Chão (3 linhas inferiores)
    for row in range(MH - 3, MH):
        for c in range(MW):
            col_data[row * MW + c] = 1 if row == MH-3 else 2

    # Lava na última linha
    for c in range(MW):
        col_data[(MH-1)*MW + c] = 4

    # Plataformas
    for (sc, row, ln) in [(2,14,5),(8,12,4),(13,10,5),(20,13,4),(24,11,5)]:
        for c in range(sc, min(sc+ln, MW)):
            col_data[row*MW + c] = 1

    # Paredes laterais
    for row in range(MH):
        col_data[row*MW + 0]      = 2
        col_data[row*MW + MW - 1] = 2

    tilemap.add_layer(TileLayer("collision", MW, MH, col_data, z_index=1))
    tilemap.bake()
    return tilemap


# ─────────────────────────────────────────────
class PhysicsDemoScene(Scene):
    def start(self):
        self.tileset  = _make_tileset()
        self.tilemap  = _build_map(self.tileset)
        self.tm_col   = TilemapCollider(self.tilemap, layer_name="collision")

        # ── Player
        self.player   = GameObject(name="Player")
        self.player.transform.x = SPAWN_X
        self.player.transform.y = SPAWN_Y
        self.player.scene = self

        self.rb  = self.player.add_component(RigidBody(gravity_scale=1.0))
        self.col = self.player.add_component(BoxCollider(width=24, height=32, debug_draw=True))

        # Câmera
        self.cam_x: float = 0.0
        self.cam_y: float = 0.0
        self.show_debug: bool = False

        # Fonte HUD
        self.font = pygame.font.SysFont("monospace", 14)

        # Cor do player
        self.player_color = (220, 80, 80)

    # ------------------------------------------------------------------
    def update(self, dt: float):
        # 1. Input
        keys = pygame.key.get_pressed()
        vx   = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: vx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: vx =  SPEED
        self.rb.velocity[0] = vx

        # 2. Atualiza player (RigidBody aplica gravidade e move o transform)
        self.player.update(dt)

        # 3. Resolve colisões com o tilemap
        self.tm_col.resolve(self.player)

        # 4. Câmera suave seguindo o player
        target_cx = self.player.transform.x - SCREEN_W / 2
        target_cy = self.player.transform.y - SCREEN_H / 2
        max_cx = max(0, self.tilemap.pixel_width  - SCREEN_W)
        max_cy = max(0, self.tilemap.pixel_height - SCREEN_H)
        target_cx = max(0.0, min(target_cx, float(max_cx)))
        target_cy = max(0.0, min(target_cy, float(max_cy)))
        lerp = 0.12
        self.cam_x += (target_cx - self.cam_x) * lerp
        self.cam_y += (target_cy - self.cam_y) * lerp

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                if self.rb.grounded:
                    self.rb.velocity[1] = JUMP_V
            if event.key == pygame.K_F1:
                self.show_debug = not self.show_debug
            if event.key == pygame.K_r:
                self.player.transform.x = SPAWN_X
                self.player.transform.y = SPAWN_Y
                self.rb.stop()

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        screen.fill((20, 20, 35))

        # Tilemap
        self.tilemap.draw(screen, self.cam_x, self.cam_y)

        if self.show_debug:
            self.tilemap.draw_debug(screen, self.cam_x, self.cam_y,
                                    color=(255, 60, 60),
                                    layer_name="collision")

        # Player (retângulo simples enquanto não há sprite)
        pr = self.col.rect
        draw_rect = pygame.Rect(
            pr.x - int(self.cam_x),
            pr.y - int(self.cam_y),
            pr.width, pr.height,
        )
        pygame.draw.rect(screen, self.player_color, draw_rect)
        pygame.draw.rect(screen, (255, 255, 255), draw_rect, 1)

        # HUD
        vx, vy = float(self.rb.velocity[0]), float(self.rb.velocity[1])
        lines = [
            "Zennity Engine — TilemapCollider Demo",
            f"Pos  : ({self.player.transform.x:.0f}, {self.player.transform.y:.0f})",
            f"Vel  : ({vx:.0f}, {vy:.0f})",
            f"Grounded: {self.rb.grounded}",
            "Mover: A/D | Pular: Space | Debug: F1 | Reset: R",
        ]
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, (220, 220, 220))
            screen.blit(surf, (10, 10 + i * 18))


# ─────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    engine = Engine(width=SCREEN_W, height=SCREEN_H,
                    title="Zennity — TilemapCollider Demo", fps=60)
    engine.run(PhysicsDemoScene())
