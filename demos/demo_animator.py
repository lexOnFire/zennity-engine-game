"""
demos/demo_animator.py
───────────────────────────

Demo do sistema de Animação da Zennity Engine.
Gera sprites coloridos procedurais (sem PNG externo) e demonstra:
  - Múltiplos clips (idle, run, jump, fall)
  - Transições automáticas baseadas no estado do RigidBody
  - Flip horizontal conforme direção do movimento
  - AnimationEvent (pisca na queda)
  - TilemapCollider + RigidBody + Animator juntos

Controles:
  A / D ou ← →   Mover
  Space           Pular
  F1              Debug colisao
  R               Resetar

Rodar:
  python -m demos.demo_animator
"""
import sys
import os
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.core       import Engine, Scene
from engine.game_object import GameObject
from engine.graphics.renderer2d   import SpriteRenderer
from engine.physics.rigidbody     import RigidBody
from engine.physics.collider      import BoxCollider
from engine.physics.tilemap_collider import TilemapCollider
from engine.tilemap   import TileMap, TileLayer, Tileset, TileData
from engine.animation import SpriteSheet, AnimationClip, Animator

# ─────────────────────────────────────────────
SW, SH   = 800, 600
TW, TH   = 32, 32
MW, MH   = 30, 20
SPEED    = 170.0
JUMP_V   = -430.0
SPAWN    = (80.0, 80.0)

# Tamanho do sprite do player
PW, PH   = 24, 32


# ─────────────────────────────────────────────
# Geração procedural de spritesheet
# ─────────────────────────────────────────────

def _draw_player_frame(
    surface: pygame.Surface,
    x: int, y: int,
    body_color: tuple,
    eye_offset_x: int = 0,
    leg_phase: int = 0,
) -> None:
    """Desenha um frame de personagem simples (cabeca + corpo + pernas)."""
    bx, by = x + 2, y + 2
    bw, bh = PW - 4, PH - 4

    # Corpo
    pygame.draw.rect(surface, body_color, (bx, by + 8, bw, bh - 8))
    # Cabeça
    pygame.draw.rect(surface, body_color, (bx + 2, by, bw - 4, 10))
    # Olho
    eye_x = bx + 6 + eye_offset_x
    pygame.draw.rect(surface, (255, 255, 255), (eye_x, by + 3, 5, 4))
    pygame.draw.rect(surface, (30, 30, 30),   (eye_x + 1, by + 4, 3, 2))
    # Pernas
    leg_colors = [(60, 60, 160), (40, 40, 130)]
    offsets = [0, 4] if leg_phase == 0 else [4, 0]
    pygame.draw.rect(surface, leg_colors[0], (bx + 2,      by + bh - 6, 7, 6 + offsets[0]))
    pygame.draw.rect(surface, leg_colors[1], (bx + bw - 9, by + bh - 6, 7, 6 + offsets[1]))


def _make_spritesheet() -> SpriteSheet:
    """
    Gera uma spritesheet 8 colunas x 1 linha com 8 frames do player:
      0-3  : idle (4 frames)
      4-7  : run  (4 frames)
    Frames de jump/fall são criados separadamente na função _make_extra_frames.
    """
    COLS, ROWS = 8, 1
    sheet = pygame.Surface((PW * COLS, PH * ROWS), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))

    body_color = (220, 90, 60)

    # Idle: sutil variação vertical dos olhos
    for i in range(4):
        eye_off = 0 if i % 2 == 0 else 1
        _draw_player_frame(sheet, i * PW, 0, body_color, eye_offset_x=eye_off, leg_phase=0)

    # Run: alterna fases das pernas
    for i in range(4):
        _draw_player_frame(sheet, (4 + i) * PW, 0, body_color,
                           eye_offset_x=0, leg_phase=i % 2)

    tmp = os.path.join(os.path.dirname(__file__), "_tmp_player_sheet.png")
    pygame.image.save(sheet, tmp)

    ss = SpriteSheet(tmp, PW, PH)
    ss.load()
    return ss


def _make_extra_frames() -> dict:
    """Gera frames individuais para jump e fall."""
    body_color = (220, 90, 60)
    frames = {}
    for name, eye_off, leg_phase in [("jump", -1, 0), ("fall", 1, 1)]:
        surf = pygame.Surface((PW, PH), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        _draw_player_frame(surf, 0, 0, body_color, eye_offset_x=eye_off, leg_phase=leg_phase)
        frames[name] = surf
    return frames


# ─────────────────────────────────────────────
# Tilemap (igual ao demo anterior)
# ─────────────────────────────────────────────

def _make_tile_surface(color: tuple, size=(TW, TH)) -> pygame.Surface:
    surf = pygame.Surface(size, pygame.SRCALPHA)
    r, g, b = color
    pygame.draw.rect(surf, (r, g, b), (1, 1, size[0]-2, size[1]-2))
    pygame.draw.rect(surf, (max(0,r-50),max(0,g-50),max(0,b-50)),
                     (1, 1, size[0]-2, size[1]-2), 2)
    return surf


def _build_tilemap() -> TileMap:
    COLORS = {1:(60,180,75), 2:(150,100,55), 3:(80,130,210), 4:(255,100,20)}
    sheet = pygame.Surface((TW*2, TH*2), pygame.SRCALPHA)
    positions = {1:(0,0), 2:(TW,0), 3:(0,TH), 4:(TW,TH)}
    for gid, (px, py) in positions.items():
        surf = _make_tile_surface(COLORS[gid])
        sheet.blit(surf, (px, py))

    tmp = os.path.join(os.path.dirname(__file__), "_tmp_ts_anim.png")
    pygame.image.save(sheet, tmp)

    ts = Tileset(tmp, TW, TH, first_gid=1)
    ts.load()
    ts.set_tile_data(1, TileData(1, solid=True))
    ts.set_tile_data(2, TileData(2, solid=True))
    ts.set_tile_data(3, TileData(3, solid=False))
    ts.set_tile_data(4, TileData(4, solid=False, damage=10))

    tilemap = TileMap(TW, TH, MW, MH)
    tilemap.add_tileset(ts)
    tilemap.add_layer(TileLayer("background", MW, MH, [3]*(MW*MH), z_index=0))

    col_data = [0]*(MW*MH)
    for row in range(MH-3, MH):
        for c in range(MW):
            col_data[row*MW+c] = 1 if row == MH-3 else 2
    for c in range(MW): col_data[(MH-1)*MW+c] = 4
    for (sc,row,ln) in [(2,14,5),(8,12,4),(13,10,5),(20,13,4),(24,11,5)]:
        for c in range(sc, min(sc+ln, MW)):
            col_data[row*MW+c] = 1
    for row in range(MH):
        col_data[row*MW+0] = 2
        col_data[row*MW+MW-1] = 2

    tilemap.add_layer(TileLayer("collision", MW, MH, col_data, z_index=1))
    tilemap.bake()
    return tilemap


# ─────────────────────────────────────────────
from engine.graphics.camera2d import Camera2D
from engine.tilemap import TilemapRenderer
from typing import List

class AnimatorDemoScene(Scene):
    def start(self):
        self.tilemap  = _build_tilemap()
        self.tm_col   = TilemapCollider(self.tilemap, layer_name="collision")

        # ── Spritesheet + frames extras
        sheet       = _make_spritesheet()
        extra       = _make_extra_frames()

        # ── Clips
        idle_frames = sheet.get_range(0, 4)
        run_frames  = sheet.get_range(4, 8)
        run_left    = SpriteSheet.flip_h(run_frames)
        idle_left   = SpriteSheet.flip_h(idle_frames)
        jump_r      = [extra["jump"]]
        jump_l      = SpriteSheet.flip_h(jump_r)
        fall_r      = [extra["fall"]]
        fall_l      = SpriteSheet.flip_h(fall_r)

        clip_idle_r  = AnimationClip("idle_r",  idle_frames, fps=6)
        clip_idle_l  = AnimationClip("idle_l",  idle_left,   fps=6)
        clip_run_r   = AnimationClip("run_r",   run_frames,  fps=12)
        clip_run_l   = AnimationClip("run_l",   run_left,    fps=12)
        clip_jump_r  = AnimationClip("jump_r",  jump_r,      fps=4, loop=True)
        clip_jump_l  = AnimationClip("jump_l",  jump_l,      fps=4, loop=True)
        clip_fall_r  = AnimationClip("fall_r",  fall_r,      fps=4, loop=True)
        clip_fall_l  = AnimationClip("fall_l",  fall_l,      fps=4, loop=True)

        # ── Map GameObject holding TilemapRenderer
        self.map_obj = GameObject("Map")
        self.map_renderer = self.map_obj.add_component(TilemapRenderer(self.tilemap))
        self.add_game_object(self.map_obj)

        # ── Player
        self.player  = GameObject(name="Player")
        self.player.transform.position = np.array([SPAWN[0], SPAWN[1]], np.float32)
        
        self.rb   = self.player.add_component(RigidBody(gravity_scale=1.0))
        self.col  = self.player.add_component(BoxCollider(width=PW, height=PH, debug_draw=False))
        self.sr   = self.player.add_component(SpriteRenderer(idle_frames[0]))
        self.anim = self.player.add_component(Animator(default_clip="idle_r"))

        for clip in [clip_idle_r, clip_idle_l, clip_run_r, clip_run_l,
                     clip_jump_r, clip_jump_l, clip_fall_r, clip_fall_l]:
            self.anim.add_clip(clip)

        self.add_game_object(self.player)

        # ── Camera GameObject holding Camera2D
        self.cam_obj = GameObject("Camera")
        self.camera2d = self.cam_obj.add_component(Camera2D())
        self.add_game_object(self.cam_obj)
        Camera2D.main = self.camera2d

        # Direção atual do player
        self._facing_right = True

        # ── Transições automáticas
        rb, anim = self.rb, self.anim

        def is_running():  return abs(rb.velocity[0]) > 20 and rb.grounded
        def is_idle():     return abs(rb.velocity[0]) < 20 and rb.grounded
        def is_jumping():  return not rb.grounded and rb.velocity[1] < 0
        def is_falling():  return not rb.grounded and rb.velocity[1] >= 0
        def facing_r():    return self._facing_right
        def facing_l():    return not self._facing_right

        # Transições para cada combinação de estado x direção
        for src in ["idle_r","run_r","jump_r","fall_r",
                    "idle_l","run_l","jump_l","fall_l"]:
            anim.add_transition(src, "run_r",  lambda: is_running() and facing_r())
            anim.add_transition(src, "run_l",  lambda: is_running() and facing_l())
            anim.add_transition(src, "idle_r", lambda: is_idle()    and facing_r())
            anim.add_transition(src, "idle_l", lambda: is_idle()    and facing_l())
            anim.add_transition(src, "jump_r", lambda: is_jumping() and facing_r())
            anim.add_transition(src, "jump_l", lambda: is_jumping() and facing_l())
            anim.add_transition(src, "fall_r", lambda: is_falling() and facing_r())
            anim.add_transition(src, "fall_l", lambda: is_falling() and facing_l())

        # Posição local da câmera para suavização
        self.cam_x: float = 0.0
        self.cam_y: float = 0.0
        self.show_debug: bool = False
        self.font = pygame.font.SysFont("monospace", 14)

    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        go._propagate_scene(self)

    # ------------------------------------------------------------------
    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        vx   = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            vx = -SPEED
            self._facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx = SPEED
            self._facing_right = True
        self.rb.velocity[0] = vx

        # Atualiza todos os GameObjects cadastrados
        for go in self.game_objects:
            go.update(dt)

        self.tm_col.resolve(self.player)

        # Câmera suave seguindo o player
        tx = self.player.transform.position[0] - SW / 2
        ty = self.player.transform.position[1] - SH / 2
        tx = max(0.0, min(tx, float(self.tilemap.pixel_width  - SW)))
        ty = max(0.0, min(ty, float(self.tilemap.pixel_height - SH)))
        self.cam_x += (tx - self.cam_x) * 0.1
        self.cam_y += (ty - self.cam_y) * 0.1

        # Centraliza a Camera2D
        self.cam_obj.transform.position = np.array([self.cam_x + SW / 2.0, self.cam_y + SH / 2.0], np.float32)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                if self.rb.grounded:
                    self.rb.velocity[1] = JUMP_V
            if event.key == pygame.K_F1:
                self.show_debug = not self.show_debug
            if event.key == pygame.K_r:
                self.player.transform.position = np.array([SPAWN[0], SPAWN[1]], np.float32)
                self.rb.stop()

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        screen.fill((20, 20, 35))

        # Desenha os GameObjects (incluindo o mapa e o player via SpriteRenderer)
        for go in self.game_objects:
            go.draw(screen)

        if self.show_debug:
            self.tilemap.draw_debug(screen, self.cam_x, self.cam_y,
                                    layer_name="collision")

        # HUD
        lines = [
            "Zennity Engine — Animator Demo",
            f"Clip  : {self.anim.current_clip}",
            f"Frame : {self.anim.current_frame}",
            f"Grounded: {self.rb.grounded}",
            "Mover: A/D | Pular: Space | Debug: F1 | Reset: R",
        ]
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, (220, 220, 220))
            screen.blit(surf, (10, 10 + i * 18))


# ─────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    engine = Engine(width=SW, height=SH,
                    title="Zennity — Animator Demo", fps=60)
    engine.run(AnimatorDemoScene())
