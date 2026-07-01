"""
demos/demo_platformer.py
────────────────────────
Demo de Platformer 2D completa usando:
  - TileMap  (multi-camada: background + collision)
  - TilemapCollider  (integra tiles sólidos com BoxCollider)
  - RigidBody  (gravidade + pulo)
  - BoxCollider  (hitbox do player)
  - Câmera scrolling (segue o player suavemente)

Controles
─────────
  ← →     Mover o player
  Espaço  Pular (até 2× se double_jump=True)
  F1      Toggle debug (desenha colliders e tile rects)
  ESC     Sair

Arquitetura
───────────
  1. PlayerScene.start():
       - Cria o TileMap proceduralmente (nenhum arquivo necessário)
       - Cria o player GameObject com RigidBody + BoxCollider
       - Instancia TilemapCollider ligando tilemap ↔ player

  2. PlayerScene.update(dt):
       Ordem correta de atualização:
         a) Lê input do player
         b) RigidBody.update(dt)  → move o transform
         c) TilemapCollider.resolve(player)  → corrige penetrações
         d) BoxCollider.check_all()  → colisões objeto↔objeto (moedas)
         e) Câmera acompanha player

  3. PlayerScene.draw():
       - Tilemap background (camada "bg")
       - Tilemap foreground/collision (camada "collision")
       - Sprites dos objetos
       - Debug overlay (F1)
       - HUD (moedas, velocidade, estado grounded)
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame

from engine.core           import Scene, Engine
from engine.game_object    import GameObject
from engine.transform      import Transform
from engine.component      import Component
from engine.physics        import RigidBody, BoxCollider, TilemapCollider
from engine.tilemap        import TileMap, TileLayer, Tileset


# ─────────────────────────────────────────────────────────────────────────────
# Constantes visuais
# ─────────────────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 960, 540
TILE_W,   TILE_H   = 32, 32
GRAVITY            = 980.0   # px/s²  (mesmo valor padrão do RigidBody)
WALK_SPEED         = 220.0   # px/s
JUMP_IMPULSE        = -440.0  # px/s  (negativo = para cima)
DOUBLE_JUMP        = True

# Paleta de cores para tiles procedurais
COL_SKY      = (135, 189, 235)
COL_CLOUD    = (230, 240, 250)
COL_GRASS    = (86, 155, 60)
COL_DIRT     = (139, 100, 63)
COL_STONE    = (120, 120, 130)
COL_PLATFORM = (180, 140, 90)
COL_COIN     = (255, 210, 50)
COL_SPIKE    = (220, 60, 60)
COL_PLAYER   = (70, 130, 230)
COL_PLAYER_EYE = (255, 255, 255)


# ─────────────────────────────────────────────────────────────────────────────
# Construção do TileMap procedural
# ─────────────────────────────────────────────────────────────────────────────

def _make_tileset() -> Tileset:
    """
    Cria um Tileset procedural (sem imagem) para a demo.
    Os tiles são desenhados diretamente como retângulos coloridos.
    GIDs:
      1 = grass    (solid)
      2 = dirt     (solid)
      3 = stone    (solid)
      4 = platform (one_way)
      5 = coin     (trigger)
      6 = spike    (damage)
    """
    surface = pygame.Surface((TILE_W * 6, TILE_H), pygame.SRCALPHA)
    colors = [COL_GRASS, COL_DIRT, COL_STONE, COL_PLATFORM, COL_COIN, COL_SPIKE]
    for i, col in enumerate(colors):
        rect = pygame.Rect(i * TILE_W, 0, TILE_W, TILE_H)
        pygame.draw.rect(surface, col, rect)
        # borda interna
        pygame.draw.rect(surface, (0, 0, 0, 60), rect, 1)

    ts = Tileset("demo", surface, TILE_W, TILE_H, first_gid=1)
    ts.set_tile_property(1, "solid", True)
    ts.set_tile_property(2, "solid", True)
    ts.set_tile_property(3, "solid", True)
    ts.set_tile_property(4, "one_way", True)
    ts.set_tile_property(5, "trigger", True)
    ts.set_tile_property(6, "damage",  True)
    return ts


def _make_tilemap(ts: Tileset) -> TileMap:
    """
    Cria um mapa de 60×17 tiles com duas camadas:
      "bg"        — decoração (não-colidível)
      "collision" — tiles sólidos / one-way
    Layout:
      Chão principal na linha 16 (índice 0-based).
      Plataformas flutuantes em pontos específicos.
      Spikes em algumas posições.
    """
    COLS, ROWS = 60, 17
    tm = TileMap(COLS, ROWS, TILE_W, TILE_H)
    tm.add_tileset(ts)

    # ── Camada de fundo (céu + nuvens decorativas)
    bg_data = [[0] * COLS for _ in range(ROWS)]
    tm.add_layer(TileLayer("bg", COLS, ROWS, bg_data))

    # ── Camada de colisão
    col_data = [[0] * COLS for _ in range(ROWS)]

    # Chão principal (linha 16) — grass+dirt
    for c in range(COLS):
        col_data[16][c] = 1   # grass
    for c in range(COLS):
        col_data[15][c] = 2   # dirt logo abaixo (camada visual)

    # Paredes esquerda e direita
    for r in range(ROWS):
        col_data[r][0]       = 3
        col_data[r][COLS-1]  = 3

    # Plataformas flutuantes (gid=4 one_way)
    def platform(col_start, row, length):
        for c in range(col_start, col_start + length):
            col_data[row][c] = 4

    platform(5,  12, 6)
    platform(14,  9, 5)
    platform(22, 12, 4)
    platform(28,  7, 6)
    platform(36, 11, 5)
    platform(44,  8, 4)
    platform(50, 13, 6)

    # Blocos de pedra (plataformas sólidas)
    def solid_platform(col_start, row, length):
        for c in range(col_start, col_start + length):
            col_data[row][c] = 3

    solid_platform(10, 14, 4)
    solid_platform(20, 11, 3)
    solid_platform(32, 14, 3)
    solid_platform(42, 13, 4)

    # Spikes (gid=6, damage)
    for c in [7, 8, 18, 25, 38, 53]:
        col_data[15][c] = 6   # spike no chão

    tm.add_layer(TileLayer("collision", COLS, ROWS, col_data))
    return tm


# ─────────────────────────────────────────────────────────────────────────────
# Componente de sprite simples (retângulo colorido)
# ─────────────────────────────────────────────────────────────────────────────

class RectSprite(Component):
    """Desenha um retângulo colorido centrado no transform do objeto."""

    def __init__(self, width: int, height: int, color: tuple) -> None:
        super().__init__()
        self.width  = width
        self.height = height
        self.color  = color

    def draw(self, screen: pygame.Surface, camera_x: float = 0.0, camera_y: float = 0.0) -> None:
        if self.game_object is None:
            return
        pos = self.game_object.transform.get_world_position()
        rect = pygame.Rect(
            int(pos[0] - self.width  / 2 - camera_x),
            int(pos[1] - self.height / 2 - camera_y),
            self.width, self.height,
        )
        pygame.draw.rect(screen, self.color, rect, border_radius=4)


class PlayerSprite(RectSprite):
    """Sprite do player com olhinhos e estado de animação."""

    def __init__(self) -> None:
        super().__init__(28, 32, COL_PLAYER)
        self.facing = 1   # 1=direita, -1=esquerda
        self.anim_timer = 0.0
        self.squash = 1.0  # escala Y para squash-and-stretch

    def update_anim(self, dt: float, vx: float, vy: float, grounded: bool) -> None:
        self.anim_timer += dt
        if vx > 10:  self.facing = 1
        if vx < -10: self.facing = -1
        # Squash ao pousar
        if grounded:
            self.squash = max(1.0, self.squash - dt * 6)
        else:
            self.squash = 1.0 if vy < 0 else min(1.15, self.squash + dt * 4)

    def draw(self, screen: pygame.Surface, camera_x: float = 0.0, camera_y: float = 0.0) -> None:
        if self.game_object is None:
            return
        pos = self.game_object.transform.get_world_position()
        draw_h = int(self.height * self.squash)
        draw_w = int(self.width / self.squash)
        rect = pygame.Rect(
            int(pos[0] - draw_w / 2 - camera_x),
            int(pos[1] - draw_h / 2 - camera_y),
            draw_w, draw_h,
        )
        pygame.draw.rect(screen, self.color, rect, border_radius=5)
        # Olho
        eye_x = rect.x + (draw_w // 2) + self.facing * 5
        eye_y = rect.y + draw_h // 3
        pygame.draw.circle(screen, COL_PLAYER_EYE, (eye_x, eye_y), 5)
        pygame.draw.circle(screen, (30, 50, 80),   (eye_x + self.facing, eye_y), 3)


# ─────────────────────────────────────────────────────────────────────────────
# Componente de moeda (trigger)
# ─────────────────────────────────────────────────────────────────────────────

class CoinComponent(Component):
    """Moeda coletável via trigger."""
    def __init__(self) -> None:
        super().__init__()
        self.collected = False
        self._float_t  = 0.0

    def update(self, dt: float) -> None:
        self._float_t += dt
        if self.game_object:
            self.game_object.transform.y = (
                self.game_object.transform._base_y
                + 4 * __import__("math").sin(self._float_t * 3)
            )

    def draw(self, screen: pygame.Surface, camera_x: float = 0.0, camera_y: float = 0.0) -> None:
        if self.collected or self.game_object is None:
            return
        pos = self.game_object.transform.get_world_position()
        cx = int(pos[0] - camera_x)
        cy = int(pos[1] - camera_y)
        pygame.draw.circle(screen, COL_COIN,  (cx, cy), 10)
        pygame.draw.circle(screen, (200, 150, 0), (cx, cy), 10, 2)
        pygame.draw.circle(screen, (255, 240, 150), (cx - 3, cy - 3), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Cena principal
# ─────────────────────────────────────────────────────────────────────────────

class PlatformerScene(Scene):

    def __init__(self) -> None:
        super().__init__()
        self.tileset: Tileset    = None  # type: ignore
        self.tilemap: TileMap    = None  # type: ignore
        self.tm_collider: TilemapCollider = None  # type: ignore

        self.player: GameObject  = None  # type: ignore
        self.player_rb: RigidBody   = None  # type: ignore
        self.player_col: BoxCollider = None  # type: ignore
        self.player_spr: PlayerSprite = None  # type: ignore

        self.coins: list[GameObject] = []
        self.coin_count = 0
        self.total_coins = 0

        self.camera_x: float = 0.0
        self.camera_y: float = 0.0

        self.debug: bool = False
        self._jumps_left = 2 if DOUBLE_JUMP else 1
        self._was_grounded = False

        self.font: pygame.font.Font = None  # type: ignore
        self.font_big: pygame.font.Font = None  # type: ignore

        self.death_y = TILE_H * 20    # cair abaixo disso = morrer
        self._respawn_pos = (3 * TILE_W, 13 * TILE_H)
        self._invincible_t = 0.0

    # ─────────────────────────────────────────────────────────────────
    # start
    # ─────────────────────────────────────────────────────────────────

    def start(self) -> None:
        self.font     = pygame.font.SysFont(None, 22)
        self.font_big = pygame.font.SysFont(None, 48)

        # ── Tilemap ──────────────────────────────────────────────────
        self.tileset = _make_tileset()
        self.tilemap = _make_tilemap(self.tileset)
        self.tilemap.bake_layer("collision", self.tileset)

        # ── TilemapCollider ──────────────────────────────────────────
        self.tm_collider = TilemapCollider(
            self.tilemap,
            layer_name="collision",
            max_iter=4,
        )

        # ── Player ───────────────────────────────────────────────────
        self.player = GameObject("Player")
        self.player.transform.x = self._respawn_pos[0]
        self.player.transform.y = self._respawn_pos[1]

        self.player_rb = self.player.add_component(RigidBody(
            mass=1.0,
            gravity_scale=1.0,
            drag=0.0,
            use_gravity=True,
        ))
        self.player_col = self.player.add_component(BoxCollider(
            width=26, height=30,
            debug_draw=False,
        ))
        self.player_spr = self.player.add_component(PlayerSprite())

        self.player.scene = self
        self.game_objects.append(self.player)
        self.player.start()

        # ── Moedas ────────────────────────────────────────────────────
        coin_positions = [
            (7*TILE_W,  11*TILE_H), (9*TILE_W,  11*TILE_H),
            (15*TILE_W, 8*TILE_H),  (16*TILE_W, 8*TILE_H),
            (23*TILE_W, 11*TILE_H), (29*TILE_W, 6*TILE_H),
            (31*TILE_W, 6*TILE_H),  (37*TILE_W, 10*TILE_H),
            (45*TILE_W, 7*TILE_H),  (51*TILE_W, 12*TILE_H),
            (53*TILE_W, 12*TILE_H), (55*TILE_W, 12*TILE_H),
        ]
        for pos in coin_positions:
            go = GameObject(f"Coin_{len(self.coins)}")
            go.transform.x = float(pos[0])
            go.transform.y = float(pos[1])
            go.transform._base_y = float(pos[1])
            coin_comp = go.add_component(CoinComponent())
            coin_col  = go.add_component(BoxCollider(
                width=20, height=20, is_trigger=True,
            ))
            # Callback de coleta
            def make_collect(c_comp, c_go):
                def _collect(info):
                    if not c_comp.collected:
                        c_comp.collected = True
                        c_go.active = False
                        self.coin_count += 1
                return _collect
            coin_col.on_collision_enter = make_collect(coin_comp, go)
            go.scene = self
            self.game_objects.append(go)
            go.start()
            self.coins.append(go)

        self.total_coins = len(self.coins)

    # ─────────────────────────────────────────────────────────────────
    # update
    # ─────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        dt = min(dt, 1/30)  # cap para evitar tunneling em lag

        keys = pygame.key.get_pressed()

        # ── Input de movimento ────────────────────────────────────────
        vx = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: vx = -WALK_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: vx =  WALK_SPEED
        self.player_rb.velocity[0] = vx

        # ── Física ────────────────────────────────────────────────────
        # Reseta grounded antes do step (RigidBody.update também reseta)
        self.player_rb.update(dt)

        # ── Colisão tilemap → corrige posição ─────────────────────────
        was_grounded = self._was_grounded
        self.tm_collider.resolve(self.player)

        # Restaura jumps ao pousar
        if self.player_rb.grounded and not was_grounded:
            self._jumps_left = 2 if DOUBLE_JUMP else 1
        self._was_grounded = self.player_rb.grounded

        # One-way platforms (gid=4)
        if self.player_rb.velocity[1] > 0:   # só ao cair
            prev_bottom = (
                self.player_col.rect.bottom
                - self.player_rb.velocity[1] * dt
            )
            self.tm_collider.resolve_one_way(self.player, prev_bottom)

        # ── Colisão objeto↔objeto (moedas) ────────────────────────────
        BoxCollider.check_all()

        # ── Update animação ───────────────────────────────────────────
        self.player_spr.update_anim(
            dt,
            self.player_rb.velocity[0],
            self.player_rb.velocity[1],
            self.player_rb.grounded,
        )

        # ── Moedas ────────────────────────────────────────────────────
        for coin in self.coins:
            if coin.active:
                coin.update(dt)

        # ── Invencibilidade (após spike) ──────────────────────────────
        if self._invincible_t > 0:
            self._invincible_t -= dt

        # ── Spike damage ─────────────────────────────────────────────
        if self._invincible_t <= 0:
            self._check_spike_damage()

        # ── Morte por queda ───────────────────────────────────────────
        if self.player.transform.y > self.death_y:
            self._respawn()

        # ── Câmera (lerp suave) ───────────────────────────────────────
        target_cx = self.player.transform.x - SCREEN_W / 2
        target_cy = self.player.transform.y - SCREEN_H / 2
        self.camera_x += (target_cx - self.camera_x) * min(1.0, dt * 8)
        self.camera_y += (target_cy - self.camera_y) * min(1.0, dt * 8)

        # Clamp da câmera para não sair do mapa
        map_w = self.tilemap.map_width  * TILE_W
        map_h = self.tilemap.map_height * TILE_H
        self.camera_x = max(0, min(self.camera_x, map_w  - SCREEN_W))
        self.camera_y = max(0, min(self.camera_y, map_h - SCREEN_H))

    # ─────────────────────────────────────────────────────────────────
    # Eventos (pulo)
    # ─────────────────────────────────────────────────────────────────

    def on_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self._jumps_left > 0:
                    self.player_rb.velocity[1] = JUMP_IMPULSE
                    self._jumps_left -= 1
            if event.key == pygame.K_F1:
                self.debug = not self.debug

    # ─────────────────────────────────────────────────────────────────
    # Spike damage
    # ─────────────────────────────────────────────────────────────────

    def _check_spike_damage(self) -> None:
        """Verifica se o player tocou em spike (gid=6)."""
        col = self.player_col
        rect = col.rect
        layer = self.tilemap.get_layer("collision")
        if layer is None:
            return
        tw, th = self.tilemap.tile_width, self.tilemap.tile_height
        c0 = max(0, rect.left   // tw)
        c1 = min(layer.width -1, rect.right  // tw)
        r0 = max(0, rect.top    // th)
        r1 = min(layer.height-1, rect.bottom // th)
        for rr in range(r0, r1+1):
            for cc in range(c0, c1+1):
                gid = layer.get_gid(cc, rr)
                if gid == 6:
                    self._respawn()
                    return

    def _respawn(self) -> None:
        self.player.transform.x = float(self._respawn_pos[0])
        self.player.transform.y = float(self._respawn_pos[1])
        self.player_rb.stop()
        self._jumps_left = 2 if DOUBLE_JUMP else 1
        self._invincible_t = 1.5

    # ─────────────────────────────────────────────────────────────────
    # draw
    # ─────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        # Fundo (céu)
        screen.fill(COL_SKY)

        cx, cy = self.camera_x, self.camera_y

        # ── Nuvens decorativas (parallax leve) ────────────────────────
        self._draw_clouds(screen, cx * 0.3, cy * 0.1)

        # ── Tilemap camadas ───────────────────────────────────────────
        self.tilemap.draw(screen, cx, cy, "bg",        self.tileset)
        self.tilemap.draw(screen, cx, cy, "collision", self.tileset)

        # ── Moedas ────────────────────────────────────────────────────
        for coin in self.coins:
            if coin.active:
                comp = coin.get_component(CoinComponent)
                if comp:
                    comp.draw(screen, cx, cy)

        # ── Player ────────────────────────────────────────────────────
        if self._invincible_t <= 0 or int(self._invincible_t * 10) % 2 == 0:
            self.player_spr.draw(screen, cx, cy)

        # ── Debug overlay ─────────────────────────────────────────────
        if self.debug:
            self._draw_debug(screen, cx, cy)

        # ── HUD ───────────────────────────────────────────────────────
        self._draw_hud(screen)

    def _draw_clouds(self, screen: pygame.Surface, cx: float, cy: float) -> None:
        cloud_data = [
            (200, 60, 90, 35),
            (500, 40, 110, 40),
            (850, 80, 80,  30),
            (1200, 55, 95, 38),
            (1600, 70, 100, 35),
        ]
        for bx, by, w, h in cloud_data:
            sx = int(bx - cx)
            sy = int(by - cy)
            if -w < sx < SCREEN_W + w:
                pygame.draw.ellipse(screen, COL_CLOUD, (sx, sy, w, h))
                pygame.draw.ellipse(screen, COL_CLOUD, (sx + 20, sy - 15, w * 0.7, h))

    def _draw_debug(self, screen: pygame.Surface, cx: float, cy: float) -> None:
        # Desenha todos os tile rects sólidos visíveis
        layer = self.tilemap.get_layer("collision")
        if layer is None:
            return
        tw = self.tilemap.tile_width
        th = self.tilemap.tile_height
        vr = pygame.Rect(cx, cy, SCREEN_W, SCREEN_H)
        solid_rects = self.tilemap.get_solid_rects_in_region(
            cx, cy, SCREEN_W, SCREEN_H, layer_name="collision"
        )
        for r in solid_rects:
            sr = pygame.Rect(r.x - int(cx), r.y - int(cy), r.w, r.h)
            pygame.draw.rect(screen, (0, 255, 0), sr, 1)

        # Collider do player
        pr = self.player_col.rect
        sr = pygame.Rect(pr.x - int(cx), pr.y - int(cy), pr.w, pr.h)
        pygame.draw.rect(screen, (255, 50, 50), sr, 2)

        # Colliders das moedas
        for coin in self.coins:
            if coin.active:
                col = coin.get_component(BoxCollider)
                if col:
                    r2 = col.rect
                    pygame.draw.rect(screen, (255, 220, 0),
                        (r2.x - int(cx), r2.y - int(cy), r2.w, r2.h), 1)

    def _draw_hud(self, screen: pygame.Surface) -> None:
        # Fundo semitransparente
        hud = pygame.Surface((280, 80), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 120))
        screen.blit(hud, (10, 10))

        rb = self.player_rb
        grounded_str = "CHÃO" if rb.grounded else "AR"
        grounded_col = (80, 220, 80) if rb.grounded else (220, 180, 50)
        jumps_col    = (80, 180, 255) if self._jumps_left > 0 else (150, 150, 150)

        screen.blit(self.font.render(
            f"Moedas: {self.coin_count}/{self.total_coins}",
            True, COL_COIN), (18, 16))
        screen.blit(self.font.render(
            f"Vel: vx={rb.velocity[0]:.0f}  vy={rb.velocity[1]:.0f}",
            True, (220, 220, 220)), (18, 36))
        screen.blit(self.font.render(
            f"Estado: {grounded_str}   Pulos restantes: {self._jumps_left}",
            True, grounded_col), (18, 56))
        screen.blit(self.font.render(
            "F1=Debug  ←→=Mover  Espaço=Pulo  ESC=Sair",
            True, (180, 190, 200)), (10, SCREEN_H - 24))

        # Mensagem de vitória
        if self.coin_count == self.total_coins:
            msg = self.font_big.render("Você coletou tudo! 🎉", True, COL_COIN)
            screen.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2, SCREEN_H // 2 - 30))


# ─────────────────────────────────────────────────────────────────────────────
# Entry-point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Zennity Engine — Demo Platformer")
    clock = pygame.time.Clock()

    scene = PlatformerScene()
    scene.start()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                scene.on_event(event)

        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
