"""
zennity_run.py
════════════════════════════════════════════════════════════════════════════
ZENNITY RUN — A Fenda de Zennity
Jogo 2D completo construído com a Zennity Engine, usando o máximo possível
dos subsistemas de runtime oferecidos pela engine:

  • Engine + SceneManager + Transitions (Fade / Wipe / Slide / Crossfade)
  • GameObject / Transform / Component (ECS)
  • RigidBody + BoxCollider + TilemapCollider (física 2D)
  • TileMap / TileLayer / Tileset / TileData + TilemapRenderer
  • Camera2D (câmera com scroll suave e limites de mundo)
  • SpriteRenderer + engine.animation (SpriteSheet, AnimationClip, Animator)
    para o sprite e a animação do player
  • ParticleSystem (partículas de moeda coletada, poeira de pulo, dano)
  • UI (UICanvas, Panel, Label, Button, ProgressBar, Anchor, Pivot, UIManager)
  • AudioManager / AudioSource (música + efeitos sonoros, gerados
    proceduralmente em .wav — o projeto não tem assets de áudio ainda)

Fluxo de cenas:
    SplashScene → MenuScene → GameScene ⇄ PauseScene (push/pop)
                                   │
                        GameOverScene / VictoryScene

Controles
─────────
    ← → / A D     Mover
    Espaço / W/↑  Pular (pulo duplo)
    Esc           Pausar
    F1            Debug de colisão
    R             Reiniciar posição do player

Como rodar
───────────
    python zennity_run.py
    (precisa de: pygame-ce/pygame, numpy — já são dependências da engine)
"""
from __future__ import annotations

import math
import os
import random
import struct
import sys
import wave

import numpy as np
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core import Engine, Scene
from engine.core.scene_manager import SceneManager
from engine.transitions import (
    FadeTransition, WipeTransition, CrossfadeTransition,
    SlideTransition, SlideDirection,
)
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.physics.tilemap_collider import TilemapCollider
from engine.tilemap import TileMap, TileLayer, Tileset, TilemapRenderer
from engine.tilemap.tileset import TileData
from engine.graphics.camera2d import Camera2D
from engine.graphics.particles import ParticleSystem
from engine.graphics.renderer import SpriteRenderer
from engine.animation import SpriteSheet, AnimationClip, Animator
from engine.ui import (
    UICanvas, UIManager, Panel, Label, Button, ProgressBar, Anchor, Pivot,
)
from engine.audio import AudioManager

# ══════════════════════════════════════════════════════════════════════════
# Constantes globais
# ══════════════════════════════════════════════════════════════════════════
SW, SH   = 960, 540
TW, TH   = 32, 32
MW, MH   = 70, 17
GRAVITY_SCALE = 1.0
WALK_SPEED  = 210.0
JUMP_V      = -430.0
DOUBLE_JUMP = True
PW, PH      = 24, 30

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Assets")
AUDIO_DIR  = os.path.join(ASSETS_DIR, "Audio", "_zennity_run")
TMP_DIR    = os.path.join(ASSETS_DIR, "_zennity_run_tmp")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

COL_SKY      = (120, 178, 230)
COL_CLOUD    = (235, 244, 252)
COL_GRASS    = (86, 168, 64)
COL_DIRT     = (140, 100, 63)
COL_STONE    = (120, 122, 132)
COL_LAVA     = (235, 90, 30)
COL_COIN     = (255, 205, 45)
COL_PLAYER   = (235, 100, 70)
COL_ENEMY    = (150, 70, 200)
COL_FLAG     = (60, 200, 120)


# ══════════════════════════════════════════════════════════════════════════
# Áudio procedural — a engine só toca arquivos .wav; como o projeto ainda não
# tem assets sonoros, geramos alguns efeitos e uma música curta em disco na
# primeira execução (ficam em cache em Assets/Audio/_zennity_run/).
# ══════════════════════════════════════════════════════════════════════════

def _write_wav(path: str, samples) -> None:
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def _tone(freq: float, dur: float, vol: float = 0.5, decay: bool = True, wave_fn=math.sin):
    n = int(44100 * dur)
    out = []
    for i in range(n):
        t = i / 44100.0
        env = (1.0 - t / dur) if decay else 1.0
        s = wave_fn(2 * math.pi * freq * t) * vol * env
        out.append(int(max(-1.0, min(1.0, s)) * 32000))
    return out


def _noise(dur: float, vol: float = 0.4):
    n = int(44100 * dur)
    out = []
    for i in range(n):
        env = 1.0 - (i / n)
        s = random.uniform(-1, 1) * vol * env
        out.append(int(max(-1.0, min(1.0, s)) * 32000))
    return out


def ensure_sfx() -> dict:
    """Gera (uma vez) os efeitos sonoros e a música e retorna os caminhos."""
    paths = {
        "jump":    os.path.join(AUDIO_DIR, "jump.wav"),
        "coin":    os.path.join(AUDIO_DIR, "coin.wav"),
        "hit":     os.path.join(AUDIO_DIR, "hit.wav"),
        "victory": os.path.join(AUDIO_DIR, "victory.wav"),
        "click":   os.path.join(AUDIO_DIR, "click.wav"),
        "music":   os.path.join(AUDIO_DIR, "music_loop.wav"),
    }
    if not os.path.exists(paths["jump"]):
        _write_wav(paths["jump"], _tone(520, 0.16, 0.5) + _tone(760, 0.10, 0.4))
    if not os.path.exists(paths["coin"]):
        _write_wav(paths["coin"], _tone(880, 0.07, 0.5) + _tone(1320, 0.10, 0.5))
    if not os.path.exists(paths["hit"]):
        _write_wav(paths["hit"], _noise(0.18, 0.5) + _tone(120, 0.12, 0.5, wave_fn=math.sin))
    if not os.path.exists(paths["victory"]):
        seq = []
        for f in (523, 659, 784, 1046):
            seq += _tone(f, 0.18, 0.45)
        _write_wav(paths["victory"], seq)
    if not os.path.exists(paths["click"]):
        _write_wav(paths["click"], _tone(660, 0.05, 0.3))
    if not os.path.exists(paths["music"]):
        notes = [392, 440, 523, 440, 392, 349, 392, 523]
        seq = []
        for f in notes:
            seq += _tone(f, 0.35, 0.16, decay=False, wave_fn=math.sin)
            seq += _tone(f * 1.0, 0.02, 0.0)  # micro respiro
        _write_wav(paths["music"], seq)
    return paths


SFX = ensure_sfx()


# ══════════════════════════════════════════════════════════════════════════
# Geração procedural de sprites (spritesheet do player + tileset)
# ══════════════════════════════════════════════════════════════════════════

def _draw_hero_frame(surf, x, y, color, eye_dx=0, leg_phase=0, squash=1.0):
    bw, bh = PW - 4, int((PH - 6) * squash)
    bx, by = x + 2, y + (PH - bh) - 2
    pygame.draw.rect(surf, color, (bx, by, bw, bh), border_radius=4)
    pygame.draw.rect(surf, (255, 255, 255), (bx + bw // 2 + eye_dx - 2, by + 5, 5, 5))
    pygame.draw.rect(surf, (30, 20, 20), (bx + bw // 2 + eye_dx - 1, by + 6, 3, 3))
    leg_off = [0, 5] if leg_phase == 0 else [5, 0]
    pygame.draw.rect(surf, (60, 40, 90), (bx + 1, by + bh - 4, 6, 6 + leg_off[0]))
    pygame.draw.rect(surf, (45, 30, 70), (bx + bw - 7, by + bh - 4, 6, 6 + leg_off[1]))


def make_hero_sheet() -> SpriteSheet:
    cols = 10
    sheet = pygame.Surface((PW * cols, PH), pygame.SRCALPHA)
    for i in range(4):                       # 0-3 idle
        _draw_hero_frame(sheet, i * PW, 0, COL_PLAYER, eye_dx=(0 if i % 2 == 0 else 1))
    for i in range(4):                       # 4-7 run
        _draw_hero_frame(sheet, (4 + i) * PW, 0, COL_PLAYER, leg_phase=i % 2)
    _draw_hero_frame(sheet, 8 * PW, 0, COL_PLAYER, eye_dx=-1, squash=1.12)   # 8 jump
    _draw_hero_frame(sheet, 9 * PW, 0, COL_PLAYER, eye_dx=1, squash=0.85)    # 9 fall
    path = os.path.join(TMP_DIR, "hero_sheet.png")
    pygame.image.save(sheet, path)
    ss = SpriteSheet(path, PW, PH)
    ss.load()
    return ss


def make_tileset() -> Tileset:
    colors = {1: COL_GRASS, 2: COL_DIRT, 3: COL_STONE, 4: COL_LAVA}
    sheet = pygame.Surface((TW * 4, TH), pygame.SRCALPHA)
    for gid, col in colors.items():
        x = (gid - 1) * TW
        pygame.draw.rect(sheet, col, (x + 1, 1, TW - 2, TH - 2))
        shade = tuple(max(0, c - 45) for c in col)
        pygame.draw.rect(sheet, shade, (x + 1, 1, TW - 2, TH - 2), 2)
    path = os.path.join(TMP_DIR, "tileset.png")
    pygame.image.save(sheet, path)
    ts = Tileset(path, TW, TH, first_gid=1)
    ts.load()
    ts.set_tile_data(1, TileData(1, solid=True))
    ts.set_tile_data(2, TileData(2, solid=True))
    ts.set_tile_data(3, TileData(3, solid=True))
    ts.set_tile_data(4, TileData(4, solid=False, damage=100, custom={"type": "lava"}))
    return ts


def build_level(ts: Tileset) -> TileMap:
    tm = TileMap(TW, TH, MW, MH)
    tm.add_tileset(ts)

    bg = [0] * (MW * MH)
    tm.add_layer(TileLayer("background", MW, MH, bg, z_index=0))

    col = [0] * (MW * MH)
    ground_row = MH - 3
    for c in range(MW):
        col[ground_row * MW + c] = 1
        col[(ground_row + 1) * MW + c] = 2
        col[(ground_row + 2) * MW + c] = 2
    for r in range(MH):
        col[r * MW + 0] = 3
        col[r * MW + (MW - 1)] = 3

    def platform(sc, row, ln, gid=3):
        for c in range(sc, min(sc + ln, MW)):
            col[row * MW + c] = gid

    for (sc, row, ln) in [
        (6, 12, 4), (13, 10, 4), (20, 13, 3), (26, 8, 5),
        (34, 11, 4), (40, 7, 4), (47, 12, 5), (54, 9, 4), (61, 12, 4),
    ]:
        platform(sc, row, ln)

    # covas de lava (buracos no chão) — entre colunas 16-19 e 44-47
    for pit in [(16, 19), (44, 47)]:
        for c in range(pit[0], pit[1]):
            col[ground_row * MW + c] = 4
            col[(ground_row + 1) * MW + c] = 4
            col[(ground_row + 2) * MW + c] = 4

    tm.add_layer(TileLayer("collision", MW, MH, col, z_index=1))
    tm.bake()
    return tm


# ══════════════════════════════════════════════════════════════════════════
# Componentes de gameplay
# ══════════════════════════════════════════════════════════════════════════

def build_hero_animator(player: GameObject, sheet: SpriteSheet, facing_flag) -> "Animator":
    """
    Monta SpriteRenderer + Animator no player, com clips idle/run/jump/fall
    espelhados para direita/esquerda e transições automáticas baseadas no
    RigidBody — igual ao padrão usado em demos/demo_animator.py.

    `facing_flag` é uma função () -> bool que informa se o player está
    olhando para a direita (usada nas condições de transição).
    """
    idle_r = sheet.get_range(0, 4)
    run_r  = sheet.get_range(4, 8)
    jump_r = [sheet.get(8)]
    fall_r = [sheet.get(9)]
    idle_l = SpriteSheet.flip_h(idle_r)
    run_l  = SpriteSheet.flip_h(run_r)
    jump_l = SpriteSheet.flip_h(jump_r)
    fall_l = SpriteSheet.flip_h(fall_r)

    sr = player.add_component(SpriteRenderer(idle_r[0]))
    anim = player.add_component(Animator(default_clip="idle_r"))

    # BUG FIX (limitação #9): AnimationClip.serialize()/deserialize() não
    # persistia `frames` — só sobrevivia o tween de propriedades. Agora que
    # AnimationClip aceita `frame_source` (spritesheet + recorte + flip),
    # passamos essa referência aqui para que, se este Animator/clip for
    # salvo em .zscene, os frames de sprite-cycle voltem a existir no load.
    def _src(frame_range):
        return {
            "sheet": sheet.image_path,
            "frame_width": sheet.frame_width,
            "frame_height": sheet.frame_height,
            "spacing": sheet.spacing,
            "margin": sheet.margin,
            "scale": sheet.scale,
            "color_key": list(sheet.color_key) if sheet.color_key else None,
            "frame_range": list(frame_range),
        }

    # Os frames "_l" já chegam pré-espelhados (SpriteSheet.flip_h acima), então
    # são passados com flip_h=False para o construtor (senão seriam espelhados
    # de novo = volta ao normal). O flag `.flip_h` é setado manualmente depois
    # só para fins de serialização, indicando que o `frame_source` (que
    # descreve o recorte NÃO espelhado da sheet) precisa ser espelhado ao
    # recarregar via deserialize().
    clips = [
        AnimationClip("idle_r", idle_r, fps=6, frame_source=_src((0, 4))),
        AnimationClip("idle_l", idle_l, fps=6, frame_source=_src((0, 4))),
        AnimationClip("run_r",  run_r,  fps=12, frame_source=_src((4, 8))),
        AnimationClip("run_l",  run_l,  fps=12, frame_source=_src((4, 8))),
        AnimationClip("jump_r", jump_r, fps=4, loop=True, frame_source=_src((8, 9))),
        AnimationClip("jump_l", jump_l, fps=4, loop=True, frame_source=_src((8, 9))),
        AnimationClip("fall_r", fall_r, fps=4, loop=True, frame_source=_src((9, 10))),
        AnimationClip("fall_l", fall_l, fps=4, loop=True, frame_source=_src((9, 10))),
    ]
    for clip in clips:
        if clip.name.endswith("_l"):
            clip.flip_h = True
        anim.add_clip(clip)

    rb = player.get_component(RigidBody)

    def is_running(): return abs(rb.velocity[0]) > 15 and rb.grounded
    def is_idle():    return abs(rb.velocity[0]) <= 15 and rb.grounded
    def is_jumping(): return not rb.grounded and rb.velocity[1] < 0
    def is_falling(): return not rb.grounded and rb.velocity[1] >= 0
    def facing_r():   return facing_flag()
    def facing_l():   return not facing_flag()

    for src in ["idle_r", "run_r", "jump_r", "fall_r", "idle_l", "run_l", "jump_l", "fall_l"]:
        anim.add_transition(src, "run_r",  lambda: is_running() and facing_r())
        anim.add_transition(src, "run_l",  lambda: is_running() and facing_l())
        anim.add_transition(src, "idle_r", lambda: is_idle()    and facing_r())
        anim.add_transition(src, "idle_l", lambda: is_idle()    and facing_l())
        anim.add_transition(src, "jump_r", lambda: is_jumping() and facing_r())
        anim.add_transition(src, "jump_l", lambda: is_jumping() and facing_l())
        anim.add_transition(src, "fall_r", lambda: is_falling() and facing_r())
        anim.add_transition(src, "fall_l", lambda: is_falling() and facing_l())

    return sr, anim


class PatrolEnemy:
    """IA simples de patrulha horizontal entre dois limites."""
    def __init__(self, go: GameObject, min_x: float, max_x: float, speed: float = 60.0):
        self.go = go
        self.min_x = min_x
        self.max_x = max_x
        self.speed = speed
        self.dir = 1

    def update(self, dt: float) -> None:
        t = self.go.transform
        t.x += self.speed * self.dir * dt
        if t.x <= self.min_x:
            t.x, self.dir = self.min_x, 1
        elif t.x >= self.max_x:
            t.x, self.dir = self.max_x, -1


# ══════════════════════════════════════════════════════════════════════════
# GameScene — nível principal
# ══════════════════════════════════════════════════════════════════════════

class GameScene(Scene):
    def __init__(self):
        super().__init__("Game")
        self.score = 0

    def start(self) -> None:
        self.max_hp = 100.0
        self.hp = self.max_hp
        self.invincible_t = 0.0
        self.jumps_left = 2 if DOUBLE_JUMP else 1
        self.was_grounded = False
        self.debug = False
        self.won = False

        # ── Nível ────────────────────────────────────────────────────
        self.tileset = make_tileset()
        self.tilemap = build_level(self.tileset)
        self.tm_collider = TilemapCollider(self.tilemap, layer_name="collision", max_iter=4)

        self.map_go = GameObject("Map")
        self.map_go.add_component(TilemapRenderer(self.tilemap))
        self.add_game_object(self.map_go)

        # ── Player ───────────────────────────────────────────────────
        self.spawn = (2 * TW, (MH - 5) * TH)
        self.player = GameObject("Player", tag="Player")
        self.player.transform.x, self.player.transform.y = self.spawn
        self.rb = self.player.add_component(RigidBody(gravity_scale=GRAVITY_SCALE))
        self.col = self.player.add_component(BoxCollider(width=PW - 4, height=PH - 2, debug_draw=False))
        self.dust = self.player.add_component(ParticleSystem(
            emission_rate=0.0, lifetime=0.4, speed=60.0, spread=140.0,
            start_size=5.0, end_size=0.5, start_color=(210, 210, 210),
            end_color=(150, 150, 150), gravity=40.0,
        ))
        self.facing_right = True
        self.sr, self.anim = build_hero_animator(
            self.player, make_hero_sheet(), lambda: self.facing_right
        )
        self.add_game_object(self.player)

        # ── Câmera ───────────────────────────────────────────────────
        self.cam_go = GameObject("Camera")
        self.camera = self.cam_go.add_component(Camera2D(
            target=self.player, smoothness=0.14,
            bounds=(SW / 2.0, SH / 2.0,
                    self.tilemap.pixel_width - SW / 2.0,
                    self.tilemap.pixel_height - SH / 2.0),
        ))
        self.add_game_object(self.cam_go)
        Camera2D.main = self.camera

        # ── Moedas ───────────────────────────────────────────────────
        self.coins = []
        coin_cols = [8, 10, 15, 22, 27, 29, 36, 42, 49, 56, 63, 65]
        rows_for_col = {
            8: 11, 10: 11, 15: 9, 22: 12, 27: 7, 29: 7,
            36: 10, 42: 6, 49: 11, 56: 8, 63: 11, 65: 11,
        }
        for c in coin_cols:
            self._spawn_coin(c * TW + TW // 2, rows_for_col[c] * TH)
        self.total_coins = len(self.coins)

        # ── Inimigos ─────────────────────────────────────────────────
        self.enemies = []
        for (cx, row, span) in [(26, 7, 3.5), (47, 11, 3.0), (61, 11, 2.5)]:
            self._spawn_enemy(cx * TW, row * TH - TH, span * TW)

        # ── Bandeira (objetivo) ───────────────────────────────────────
        self.flag = GameObject("Flag")
        self.flag.transform.x = (MW - 3) * TW
        self.flag.transform.y = (MH - 5) * TH
        flag_col = self.flag.add_component(BoxCollider(width=24, height=64, is_trigger=True))
        flag_col.on_collision_enter = lambda info: self._reach_flag()
        self.add_game_object(self.flag)

        # ── UI / HUD ──────────────────────────────────────────────────
        self._setup_hud()

        # ── Áudio ────────────────────────────────────────────────────
        AudioManager.play_music(SFX["music"], loop=True, fade_ms=400)

        self.font_small = pygame.font.SysFont("consolas", 14)
        self.death_y = self.tilemap.pixel_height + 200

    # ------------------------------------------------------------------
    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)

    def _spawn_coin(self, x: float, y: float) -> None:
        go = GameObject("Coin", tag="Coin")
        go.transform.x, go.transform.y = x, y
        go._base_y = y
        col = go.add_component(BoxCollider(width=18, height=18, is_trigger=True))
        burst = go.add_component(ParticleSystem(
            emission_rate=0.0, lifetime=0.5, speed=120.0, spread=360.0,
            start_size=5.0, end_size=0.5,
            start_color=COL_COIN, end_color=(255, 255, 220), gravity=60.0,
        ))
        go._collected = False
        go._t = random.uniform(0, math.tau)

        def _collect(info, go=go, burst=burst):
            if go._collected:
                return
            go._collected = True
            burst.emit(18)
            self.score += 10
            AudioManager.play_sfx(SFX["coin"], volume=0.6)
            self._refresh_hud()
        col.on_collision_enter = _collect
        self.add_game_object(go)
        self.coins.append(go)

    def _spawn_enemy(self, x: float, y: float, span: float) -> None:
        go = GameObject("Enemy", tag="Enemy")
        go.transform.x, go.transform.y = x, y
        col = go.add_component(BoxCollider(width=26, height=26, is_trigger=True))
        ai = PatrolEnemy(go, x - span, x + span, speed=55.0)

        def _touch(info, ai=ai):
            self._damage_player(18, source_x=ai.go.transform.x)
        col.on_collision_enter = _touch
        self.add_game_object(go)
        self.enemies.append((go, ai))

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def _setup_hud(self) -> None:
        self.ui = UIManager.instance()
        hud = UICanvas(name="GameHUD", z_order=0)

        panel = Panel(x=10, y=10, width=230, height=64,
                       color=(10, 10, 25, 190), border_color=(60, 90, 150, 220),
                       border_radius=10, anchor=Anchor.TOP_LEFT)
        hud.add_child(panel)
        panel.add_child(Label("HP", x=10, y=8, font_size=13, color=(240, 90, 90), bold=True))
        self.hp_bar = ProgressBar(x=34, y=10, width=186, height=14,
                                   value=self.hp, max_value=self.max_hp,
                                   color_fill=(210, 60, 60), color_bg=(45, 18, 18),
                                   show_text=True, font_size=10, smooth=True, smooth_speed=70.0)
        panel.add_child(self.hp_bar)
        self.coin_label = Label(f"Moedas: 0/{len(self.coins) if self.coins else 0}",
                                 x=10, y=34, font_size=13, color=COL_COIN)
        panel.add_child(self.coin_label)
        self.score_label = Label(f"Score: {self.score}", x=-10, y=10, font_size=20,
                                  bold=True, color=(255, 220, 60), shadow=True,
                                  anchor=Anchor.TOP_RIGHT, pivot=Pivot.TOP_RIGHT)
        hud.add_child(self.score_label)
        hud.add_child(Label("Esc: Pausar   F1: Debug", x=0, y=-12, font_size=13,
                             color=(200, 210, 230), anchor=Anchor.BOTTOM_CENTER,
                             pivot=Pivot.BOTTOM_CENTER))
        self.ui.add_canvas(hud)

    def _refresh_hud(self) -> None:
        collected = sum(1 for c in self.coins if c._collected)
        self.coin_label.set_text(f"Moedas: {collected}/{self.total_coins}")
        self.score_label.set_text(f"Score: {self.score}")
        self.hp_bar.set_value(self.hp)

    def _ui_setup(self) -> None:
        # Chamado pelo SceneManager ao voltar do Pause (pop) — restaura o HUD.
        self._setup_hud()
        self._refresh_hud()

    # ------------------------------------------------------------------
    # Lógica de jogo
    # ------------------------------------------------------------------
    def _damage_player(self, amount: float, source_x: float = None) -> None:
        if self.invincible_t > 0:
            return
        self.hp = max(0.0, self.hp - amount)
        self.invincible_t = 1.0
        AudioManager.play_sfx(SFX["hit"], volume=0.7)
        if source_x is not None:
            push = 220.0 if self.player.transform.x > source_x else -220.0
            self.rb.velocity[0] = push
            self.rb.velocity[1] = -220.0
        self._refresh_hud()
        if self.hp <= 0:
            self._game_over()

    def _respawn(self) -> None:
        self.player.transform.x, self.player.transform.y = self.spawn
        self.rb.stop()
        self.invincible_t = 1.2

    def _game_over(self) -> None:
        AudioManager.stop_music(fade_ms=300)
        SceneManager.instance().load(
            GameOverScene(self.score),
            FadeTransition(color=(160, 0, 0), duration_out=0.5, duration_in=0.5),
        )

    def _reach_flag(self) -> None:
        if self.won:
            return
        self.won = True
        AudioManager.stop_music(fade_ms=200)
        AudioManager.play_sfx(SFX["victory"], volume=0.7)
        collected = sum(1 for c in self.coins if c._collected)
        bonus = collected * 25
        SceneManager.instance().load(
            VictoryScene(self.score + bonus, collected, self.total_coins),
            CrossfadeTransition(duration=0.7),
        )

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        dt = min(dt, 1 / 30)
        keys = pygame.key.get_pressed()

        vx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vx = -WALK_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx = WALK_SPEED
            self.facing_right = True
        self.rb.velocity[0] = vx

        for go in self.game_objects:
            go.update(dt)

        BoxCollider.check_all()  # física manual (SceneManager não roda o sistema builtin)

        was_grounded = self.was_grounded
        if self.rb.grounded and not was_grounded:
            self.jumps_left = 2 if DOUBLE_JUMP else 1
            if abs(self.rb.velocity[0]) > 5:
                self.dust.emit(6)
        self.was_grounded = self.rb.grounded

        for go, ai in self.enemies:
            if go.active:
                ai.update(dt)

        for coin in self.coins:
            if coin.active and not coin._collected:
                coin._t += dt * 3.0
                coin.transform.y = coin._base_y + 4 * math.sin(coin._t)
            elif coin._collected:
                coin.get_component(BoxCollider).enabled = False

        if self.invincible_t > 0:
            self.invincible_t -= dt
        self.sr.visible = self.invincible_t <= 0 or int(self.invincible_t * 12) % 2 == 0

        if self.player.transform.y > self.death_y:
            self._damage_player(30)
            self._respawn()
        # Nota: a Camera2D já é atualizada automaticamente dentro do loop
        # `for go in self.game_objects: go.update(dt)` acima (cam_go está
        # nessa lista) — chamar de novo aqui duplicaria o lerp de suavização.

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self.jumps_left > 0:
                    self.rb.velocity[1] = JUMP_V
                    self.jumps_left -= 1
                    AudioManager.play_sfx(SFX["jump"], volume=0.5)
            elif event.key == pygame.K_F1:
                self.debug = not self.debug
            elif event.key == pygame.K_r:
                self._respawn()
            elif event.key == pygame.K_ESCAPE:
                SceneManager.instance().push(
                    PauseScene(), SlideTransition(SlideDirection.UP, duration_out=0.0, duration_in=0.3)
                )

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COL_SKY)
        cam_pos = self.camera.transform.position
        cx = cam_pos[0] - SW / 2.0
        cy = cam_pos[1] - SH / 2.0
        self._draw_clouds(screen, cx * 0.3)

        for go in self.game_objects:
            go.draw(screen)  # TilemapRenderer + ParticleSystem (usam Camera2D.main)

        self._draw_actors(screen, cx, cy)

        if self.debug:
            self.tilemap.draw_debug(screen, cx, cy, layer_name="collision")
            pr = self.col.rect
            pygame.draw.rect(screen, (255, 60, 60), (pr.x - cx, pr.y - cy, pr.w, pr.h), 2)

        self.ui.draw(screen)

    def _draw_clouds(self, screen, cx):
        for i, (bx, by, w, h) in enumerate([(120, 60, 90, 34), (420, 40, 110, 38),
                                              (760, 80, 80, 30), (1100, 55, 95, 36)]):
            sx = int(bx - cx)
            if -w < sx < SW + w:
                pygame.draw.ellipse(screen, COL_CLOUD, (sx, by, w, h))

    def _draw_actors(self, screen, cx, cy):
        # Bandeira
        fx = int(self.flag.transform.x - cx)
        fy = int(self.flag.transform.y - cy)
        pygame.draw.rect(screen, (200, 200, 200), (fx - 2, fy - 64, 4, 64))
        pygame.draw.polygon(screen, COL_FLAG, [(fx + 2, fy - 64), (fx + 34, fy - 52), (fx + 2, fy - 40)])

        # Inimigos
        for go, ai in self.enemies:
            if not go.active:
                continue
            ex = int(go.transform.x - cx)
            ey = int(go.transform.y - cy)
            pygame.draw.rect(screen, COL_ENEMY, (ex - 13, ey - 13, 26, 26), border_radius=6)
            eye_dx = 4 if ai.dir > 0 else -4
            pygame.draw.circle(screen, (255, 255, 255), (ex + eye_dx, ey - 3), 4)

        # Moedas
        for coin in self.coins:
            if coin.active and not coin._collected:
                px = int(coin.transform.x - cx)
                py = int(coin.transform.y - cy)
                pygame.draw.circle(screen, COL_COIN, (px, py), 9)
                pygame.draw.circle(screen, (200, 150, 0), (px, py), 9, 2)

        # Player: desenhado automaticamente pelo SpriteRenderer no loop de
        # go.draw(screen) acima — aqui só controlamos o piscar de invencibilidade.


# ══════════════════════════════════════════════════════════════════════════
# Telas de fluxo: Splash, Menu, Pause, GameOver, Victory
# ══════════════════════════════════════════════════════════════════════════

class SplashScene(Scene):
    def start(self) -> None:
        self.t = 0.0
        self.f1 = pygame.font.SysFont("consolas", 46, bold=True)
        self.f2 = pygame.font.SysFont("consolas", 16)

    def update(self, dt: float) -> None:
        self.t += dt
        if self.t >= 2.0:
            SceneManager.instance().load(
                MenuScene(), FadeTransition(color=(255, 255, 255), duration_out=0.4, duration_in=0.4)
            )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) and self.t < 1.8:
            self.t = 1.8

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((14, 16, 26))
        a = min(1.0, self.t / 0.7)
        title = self.f1.render("ZENNITY RUN", True, (255, 255, 255))
        title.set_alpha(int(a * 255))
        screen.blit(title, (SW // 2 - title.get_width() // 2, SH // 2 - 40))
        sub = self.f2.render("A Fenda de Zennity — construído com a Zennity Engine", True, (150, 160, 190))
        sub.set_alpha(int(a * 200))
        screen.blit(sub, (SW // 2 - sub.get_width() // 2, SH // 2 + 20))


class MenuScene(Scene):
    def start(self) -> None:
        self.ui = UIManager.instance()
        canvas = UICanvas(name="Menu", z_order=0)
        panel = Panel(x=0, y=0, width=380, height=280, color=(12, 14, 32, 225),
                      border_color=(70, 100, 200, 210), border_radius=16,
                      anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)
        canvas.add_child(panel)
        panel.add_child(Label("ZENNITY RUN", x=0, y=22, font_size=28, bold=True,
                               color=(210, 220, 255), shadow=True,
                               anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Label("Colete as moedas e alcance a bandeira!", x=0, y=64,
                               font_size=13, color=(150, 160, 200),
                               anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("▶  Jogar", x=0, y=104, width=240, height=48,
                                on_click=self._play, color_normal=(40, 100, 60),
                                color_hover=(55, 140, 80), font_size=20,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("✕  Sair", x=0, y=166, width=240, height=48,
                                on_click=lambda: (pygame.quit(), sys.exit()),
                                color_normal=(110, 35, 35), color_hover=(160, 50, 50),
                                font_size=20, anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Label("Enter ou clique em Jogar", x=0, y=228, font_size=12,
                               color=(110, 120, 160), anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        self.ui.add_canvas(canvas)

    def _play(self) -> None:
        AudioManager.play_sfx(SFX["click"], volume=0.5)
        SceneManager.instance().load(GameScene(), WipeTransition(horizontal=True, duration_out=0.3, duration_in=0.3))

    def update(self, dt: float) -> None:
        self.ui.update(dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._play()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((10, 12, 24))
        for x in range(0, SW, 42):
            pygame.draw.line(screen, (20, 24, 46), (x, 0), (x, SH))
        for y in range(0, SH, 42):
            pygame.draw.line(screen, (20, 24, 46), (0, y), (SW, y))
        self.ui.draw(screen)


class PauseScene(Scene):
    def start(self) -> None:
        self.ui = UIManager.instance()
        canvas = UICanvas(name="Pause", z_order=10)
        canvas.add_child(Panel(x=0, y=0, width=SW, height=SH, color=(0, 0, 0, 140), border_color=None))
        panel = Panel(x=0, y=0, width=300, height=230, color=(14, 16, 40, 235),
                      border_color=(80, 100, 220, 220), border_radius=14,
                      anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)
        canvas.add_child(panel)
        panel.add_child(Label("PAUSADO", x=0, y=18, font_size=26, bold=True, color=(190, 200, 255),
                               shadow=True, anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("Continuar", x=0, y=72, width=220, height=46, on_click=self._resume,
                                color_normal=(40, 80, 160), color_hover=(60, 110, 210), font_size=18,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("Menu Principal", x=0, y=130, width=220, height=46, on_click=self._to_menu,
                                color_normal=(90, 45, 45), color_hover=(130, 60, 60), font_size=18,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Label("Esc: retomar", x=0, y=192, font_size=12, color=(100, 110, 160),
                               anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        self.ui.add_canvas(canvas)

    def _resume(self) -> None:
        SceneManager.instance().pop(SlideTransition(SlideDirection.DOWN, duration_in=0.3))

    def _to_menu(self) -> None:
        AudioManager.stop_music(fade_ms=200)
        SceneManager.instance().load(MenuScene(), FadeTransition(duration_out=0.3, duration_in=0.3))

    def update(self, dt: float) -> None:
        self.ui.update(dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()

    def draw(self, screen: pygame.Surface) -> None:
        self.ui.draw(screen)  # cena de baixo (GameScene) já foi desenhada


class GameOverScene(Scene):
    def __init__(self, score: int):
        super().__init__("GameOver")
        self.final_score = score

    def start(self) -> None:
        self.ui = UIManager.instance()
        canvas = UICanvas(name="GameOver", z_order=0)
        panel = Panel(x=0, y=0, width=360, height=260, color=(24, 6, 6, 235),
                      border_color=(200, 45, 45, 220), border_radius=16,
                      anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)
        canvas.add_child(panel)
        panel.add_child(Label("GAME OVER", x=0, y=20, font_size=30, bold=True, color=(225, 60, 60),
                               shadow=True, anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Label(f"Score final: {self.final_score}", x=0, y=76, font_size=18,
                               color=(220, 200, 100), anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("↺  Tentar Novamente", x=0, y=124, width=260, height=48,
                                on_click=self._retry, color_normal=(55, 35, 100),
                                color_hover=(85, 55, 160), font_size=17,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("⌂  Menu Principal", x=0, y=182, width=260, height=48,
                                on_click=self._to_menu, color_normal=(65, 22, 22),
                                color_hover=(105, 38, 38), font_size=17,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        self.ui.add_canvas(canvas)

    def _retry(self) -> None:
        SceneManager.instance().load(GameScene(), CrossfadeTransition(duration=0.5))

    def _to_menu(self) -> None:
        SceneManager.instance().load(MenuScene(), CrossfadeTransition(duration=0.5))

    def update(self, dt: float) -> None:
        self.ui.update(dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._retry()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((14, 5, 5))
        self.ui.draw(screen)


class VictoryScene(Scene):
    def __init__(self, score: int, collected: int, total: int):
        super().__init__("Victory")
        self.final_score = score
        self.collected = collected
        self.total = total

    def start(self) -> None:
        self.ui = UIManager.instance()
        canvas = UICanvas(name="Victory", z_order=0)
        panel = Panel(x=0, y=0, width=400, height=300, color=(6, 20, 12, 235),
                      border_color=(60, 200, 120, 220), border_radius=16,
                      anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)
        canvas.add_child(panel)
        panel.add_child(Label("VITÓRIA!", x=0, y=20, font_size=32, bold=True, color=(120, 230, 150),
                               shadow=True, anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Label(f"Moedas: {self.collected}/{self.total}", x=0, y=76, font_size=18,
                               color=COL_COIN, anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Label(f"Score final: {self.final_score}", x=0, y=104, font_size=18,
                               color=(220, 220, 220), anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("↺  Jogar Novamente", x=0, y=152, width=280, height=48,
                                on_click=self._retry, color_normal=(30, 90, 55),
                                color_hover=(45, 130, 80), font_size=17,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        panel.add_child(Button("⌂  Menu Principal", x=0, y=210, width=280, height=48,
                                on_click=self._to_menu, color_normal=(40, 50, 70),
                                color_hover=(60, 75, 100), font_size=17,
                                anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER))
        self.ui.add_canvas(canvas)

    def _retry(self) -> None:
        SceneManager.instance().load(GameScene(), CrossfadeTransition(duration=0.5))

    def _to_menu(self) -> None:
        SceneManager.instance().load(MenuScene(), CrossfadeTransition(duration=0.5))

    def update(self, dt: float) -> None:
        self.ui.update(dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._retry()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((5, 14, 9))
        self.ui.draw(screen)


# ══════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════

def main() -> None:
    engine = Engine(width=SW, height=SH, title="Zennity Run — A Fenda de Zennity", fps=60)
    engine.use_scene_manager()
    engine.run(SplashScene())


if __name__ == "__main__":
    main()
