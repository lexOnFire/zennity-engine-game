"""
editor/layout.py
================
Sistema de Layout do Editor Zennity.

Centraliza todas as constantes, métricas e funções de cálculo de posição
dos painéis do editor, eliminando magic numbers espalhados pelo código.

Uso:
    from editor.layout import Layout

    lay = Layout(screen_width=1400, screen_height=800)
    lay.update(screen_width, screen_height)  # chame a cada resize

    # Painéis
    lay.left_panel_rect    -> pygame.Rect
    lay.right_panel_rect   -> pygame.Rect
    lay.top_bar_rect       -> pygame.Rect
    lay.status_bar_rect    -> pygame.Rect
    lay.viewport_rect      -> pygame.Rect   # full edit mode
    lay.viewport_edit_rect -> pygame.Rect   # metade esquerda (play mode split)
    lay.viewport_game_rect -> pygame.Rect   # metade direita  (play mode split)

    # Posições relativas dentro dos painéis
    lay.left(x)  -> x absoluto dentro do painel esquerdo
    lay.right(x) -> x absoluto dentro do painel direito
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple
import pygame


# ---------------------------------------------------------------------------
# Constantes fixas de layout
# ---------------------------------------------------------------------------

TOP_BAR_H       = 30    # altura da barra superior
STATUS_BAR_H    = 22    # altura da barra de status inferior

LEFT_PANEL_W    = 232   # largura do painel esquerdo (Outliner + Adicionar)
RIGHT_PANEL_W   = 230   # largura do painel direito  (Inspector)

# Áreas internas do painel esquerdo
LEFT_PADDING    = 12    # margem interna horizontal
ROW_H           = 26    # altura padrão de botão/linha
ROW_H_SMALL     = 22    # botão compacto (snap, templates…)
ROW_GAP         = 4     # espaçamento entre linhas

# Seção: Adicionar formas
ADD_SECTION_Y   = 36    # Y do label da seção
ADD_ROW1_Y      = 46    # primeira fileira de botões
ADD_ROW2_Y      = 76    # segunda fileira
ADD_ROW3_Y      = 106   # terceira fileira (luz)
BTN_W_THIRD     = 66    # largura de botão 1/3 da coluna
BTN_X_COL1      = 12
BTN_X_COL2      = 82
BTN_X_COL3      = 152

# Seção: Gizmo
GIZMO_SECTION_Y = 128
GIZMO_ROW_Y     = 140

# Snap + Templates
SNAP_Y          = 172
TEMPLATES_Y     = 198
BTN_W_FULL      = 208   # botão largura total do painel

# Outliner (Árvore de cena)
TREE_Y          = 232   # Y fixo do topo da árvore
TREE_ROW_H      = 26    # altura de cada linha da árvore
TREE_MIN_H      = 100   # altura mínima da árvore
TREE_MARGIN_BOT = 180   # espaço reservado abaixo da árvore

# Inspector (painel direito) — offsets relativos a right_panel.x + 15
INSPECTOR_PAD   = 15    # margem interna
INSPECTOR_W     = 200   # largura útil dentro do painel

# Seções do inspector (Y absolutos — fixos, pois o painel não faz scroll)
INSP_HEADER_Y   = 36
INSP_PHYSICS_Y  = 62
INSP_SCRIPT_Y   = 168
INSP_COLOR_Y    = 288
INSP_CLONE_Y    = 352
INSP_HIER_Y     = 382
INSP_TAG_Y      = 418
INSP_TRANSFORM_Y = 476


# ---------------------------------------------------------------------------
# Dataclass principal
# ---------------------------------------------------------------------------

@dataclass
class Layout:
    """
    Calcula e armazena todos os rects e posições do editor.
    Chame ``update()`` sempre que a janela for redimensionada.
    """
    screen_w: int = 1280
    screen_h: int = 800

    # Rects gerados por update()
    left_panel_rect:    pygame.Rect = field(default_factory=pygame.Rect)
    right_panel_rect:   pygame.Rect = field(default_factory=pygame.Rect)
    top_bar_rect:       pygame.Rect = field(default_factory=pygame.Rect)
    status_bar_rect:    pygame.Rect = field(default_factory=pygame.Rect)
    viewport_rect:      pygame.Rect = field(default_factory=pygame.Rect)
    viewport_edit_rect: pygame.Rect = field(default_factory=pygame.Rect)
    viewport_game_rect: pygame.Rect = field(default_factory=pygame.Rect)

    # Derived scalars
    right_x:        int = 0
    viewport_y:     int = TOP_BAR_H
    viewport_h:     int = 0
    viewport_w:     int = 0
    tree_h:         int = 200
    tree_max_vis:   int = 8
    undo_y:         int = 0
    redo_y:         int = 0
    delete_y:       int = 0
    light_section_y:int = 0
    play_button_x:  int = 0

    def __post_init__(self) -> None:
        self.update(self.screen_w, self.screen_h)

    # ------------------------------------------------------------------
    def update(self, w: int, h: int) -> None:
        """Recalcula todos os rects a partir das dimensões da janela."""
        self.screen_w = w
        self.screen_h = h

        self.right_x     = w - RIGHT_PANEL_W
        self.viewport_y  = TOP_BAR_H
        self.viewport_h  = h - TOP_BAR_H - STATUS_BAR_H
        self.viewport_w  = self.right_x - LEFT_PANEL_W

        # Painéis principais
        self.top_bar_rect    = pygame.Rect(0, 0, w, TOP_BAR_H)
        self.status_bar_rect = pygame.Rect(0, h - STATUS_BAR_H, w, STATUS_BAR_H)
        self.left_panel_rect = pygame.Rect(0, TOP_BAR_H, LEFT_PANEL_W, h - TOP_BAR_H)
        self.right_panel_rect= pygame.Rect(self.right_x, TOP_BAR_H, RIGHT_PANEL_W, h - TOP_BAR_H)

        # Viewport
        self.viewport_rect      = pygame.Rect(LEFT_PANEL_W, TOP_BAR_H, self.viewport_w, self.viewport_h)
        half_w                  = self.viewport_w // 2
        self.viewport_edit_rect = pygame.Rect(LEFT_PANEL_W,          TOP_BAR_H, half_w, self.viewport_h)
        self.viewport_game_rect = pygame.Rect(LEFT_PANEL_W + half_w, TOP_BAR_H, half_w, self.viewport_h)

        # Outliner dinâmico
        self.tree_h        = max(TREE_MIN_H, h - TREE_Y - TREE_MARGIN_BOT)
        self.tree_max_vis  = self.tree_h // TREE_ROW_H

        # Botões abaixo da árvore
        self.undo_y          = TREE_Y + self.tree_h + 22
        self.redo_y          = self.undo_y
        self.delete_y        = TREE_Y + self.tree_h + 54
        self.light_section_y = TREE_Y + self.tree_h + 110

        # Botão PLAY centralizado
        self.play_button_x = w // 2 - 44

    # ------------------------------------------------------------------
    # Helpers de posição absoluta
    # ------------------------------------------------------------------

    def left(self, relative_x: int) -> int:
        """Converte X relativo ao painel esquerdo em X absoluto na tela."""
        return relative_x  # painel esquerdo começa em x=0

    def right(self, relative_x: int) -> int:
        """Converte X relativo (dentro do painel direito) em X absoluto."""
        return self.right_x + relative_x

    def inspector_x(self) -> int:
        """X do início da área de conteúdo do inspector."""
        return self.right_x + INSPECTOR_PAD

    # ------------------------------------------------------------------
    # Helpers para posições de botões do inspector
    # ------------------------------------------------------------------

    def insp_btn_left(self) -> int:
        """X do botão esquerdo / campo no inspector."""
        return self.inspector_x()

    def insp_btn_right(self, btn_w: int = 28) -> int:
        """X do botão direito do inspector (ex: '>' de selector)."""
        return self.inspector_x() + INSPECTOR_W - btn_w

    def insp_field_rect(self, y: int, h: int = 22) -> pygame.Rect:
        """Rect do campo de texto central no inspector (entre os dois botões '<' e '>')."""
        return pygame.Rect(self.inspector_x() + 34, y, INSPECTOR_W - 68, h)

    def insp_color_btn_x(self, index: int, btn_w: int = 26, gap: int = 32) -> int:
        """X do i-ésimo botão de cor no inspector."""
        return self.inspector_x() + index * gap

    # ------------------------------------------------------------------
    # Helpers para viewport
    # ------------------------------------------------------------------

    def viewport_camera_params(self, play_mode: bool) -> Tuple[float, float, float, float]:
        """
        Retorna (viewport_x, viewport_y, viewport_width, viewport_height)
        para a Camera3D, levando em conta o modo play (split view).
        """
        vx = float(LEFT_PANEL_W)
        vy = float(TOP_BAR_H)
        vw = float(self.viewport_w // 2 if play_mode else self.viewport_w)
        vh = float(self.viewport_h)
        return vx, vy, vw, vh

    def viewport_split_x(self) -> int:
        """X da linha divisória entre Edit e Game view no modo play."""
        return LEFT_PANEL_W + self.viewport_w // 2

    # ------------------------------------------------------------------
    # Helpers para a status bar
    # ------------------------------------------------------------------

    def status_text_y(self) -> int:
        return self.screen_h - STATUS_BAR_H + 4

    def status_center_x(self, surf_w: int) -> int:
        return self.screen_w // 2 - surf_w // 2

    # ------------------------------------------------------------------
    # Debug / print
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Layout({self.screen_w}x{self.screen_h} | "
            f"left={LEFT_PANEL_W} right={self.right_x} "
            f"vp={self.viewport_w}x{self.viewport_h} "
            f"tree_h={self.tree_h} tree_vis={self.tree_max_vis})"
        )
