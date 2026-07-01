"""
Zennity Editor — Design System

Paleta dark profissional com hierarquia clara de superfícies,
um único accent color e semântica de cores para botões.
"""
from typing import Tuple

# ---------------------------------------------------------------------------
# Superfícies (do mais escuro ao mais claro)
# ---------------------------------------------------------------------------
BG          = (15,  17,  22)   # viewport / fundo geral
PANEL       = (22,  25,  32)   # painéis laterais
SURFACE     = (30,  34,  43)   # cards / seções dentro do painel
SURFACE_2   = (38,  43,  54)   # hover de itens, inputs
BORDER      = (52,  58,  72)   # linhas divisórias
BORDER_SOFT = (38,  43,  54)   # bordas sutis de cards

# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------
TEXT_PRIMARY = (230, 232, 238)   # texto principal
TEXT_MUTED   = (130, 138, 155)   # labels secundários
TEXT_FAINT   = ( 72,  78,  95)   # placeholder / disabled
TEXT_INVERSE = ( 10,  12,  18)   # texto sobre accent

# ---------------------------------------------------------------------------
# Accent — Azul elétrico  (único em toda a UI)
# ---------------------------------------------------------------------------
ACCENT       = ( 64, 156, 255)   # cor principal de seleção / títulos de seção
ACCENT_DIM   = ( 34,  84, 148)   # hover de accent
ACCENT_BG    = ( 22,  40,  80)   # fundo de item selecionado

# ---------------------------------------------------------------------------
# Semântica de botões
# ---------------------------------------------------------------------------
# Primary (ação principal — adicionar forma)
BTN_PRIMARY        = ( 30, 110,  70)
BTN_PRIMARY_HOVER  = ( 38, 138,  88)

# Secondary (ação neutra — undo/redo/snap/templates)
BTN_SECONDARY       = ( 38,  43,  54)
BTN_SECONDARY_HOVER = ( 52,  58,  72)

# Active (modo gizmo ativo)
BTN_ACTIVE       = ( 34,  84, 148)
BTN_ACTIVE_HOVER = ( 50, 110, 195)

# Gizmo modes (inativo)
BTN_GIZMO       = ( 55,  42,  90)
BTN_GIZMO_HOVER = ( 75,  58, 120)

# Destructive
BTN_DANGER       = (140,  36,  36)
BTN_DANGER_HOVER = (175,  46,  46)

# Script / código
BTN_CODE       = (  0,  88, 148)
BTN_CODE_HOVER = (  0, 115, 190)

# Clone / special
BTN_SPECIAL       = ( 70,  52, 115)
BTN_SPECIAL_HOVER = ( 92,  70, 148)

# ---------------------------------------------------------------------------
# Gizmo axes
# ---------------------------------------------------------------------------
GIZMO_X = (218,  62,  62)
GIZMO_Y = ( 50, 180,  80)
GIZMO_Z = ( 60, 120, 230)
GIZMO_W = (240, 195,  40)   # scale uniform handle

# ---------------------------------------------------------------------------
# Viewport
# ---------------------------------------------------------------------------
VIEWPORT_BG    = ( 18,  20,  26)
GRID_MAIN      = (160, 165, 178)   # eixos centrais
GRID_MINOR     = (210, 213, 220)   # linhas secundárias
VIEWPORT_LABEL = (  0, 200, 255)   # badge EDIT MODE / GAME VIEW

# ---------------------------------------------------------------------------
# Status / semânticos
# ---------------------------------------------------------------------------
SUCCESS = ( 48, 190, 110)
WARNING = (215, 160,  40)
ERROR   = (210,  58,  58)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def alpha_blend(color: Tuple[int,int,int], alpha: float, bg: Tuple[int,int,int] = PANEL) -> Tuple[int,int,int]:
    """Mistura simples RGB (sem Surface) para cores de estado."""
    return tuple(int(bg[i] + (color[i] - bg[i]) * alpha) for i in range(3))

# Atalho para cor de grid dependendo do eixo
def grid_color(is_center: bool) -> Tuple[int,int,int]:
    return GRID_MAIN if is_center else GRID_MINOR
