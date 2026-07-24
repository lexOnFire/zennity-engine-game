from __future__ import annotations
"""
engine/animation/spritesheet.py
─────────────────────────────────

SpriteSheet — fatia uma imagem em frames individuais.

Suporta dois layouts:
  - Grade regular   : todos os frames têm o mesmo tamanho (mais comum)
  - Rects customizados : cada frame tem posicão e tamanho próprios
                         (ex: atlas gerado por TexturePacker)
"""

from typing import Dict, List, Optional, Tuple
import pygame


class SpriteSheet:
    """
    Fatia uma spritesheet em pygame.Surfaces individuais.

    Parameters
    ----------
    image_path  : str          – Caminho para o PNG/JPG.
    frame_width : int          – Largura de cada frame (grade regular).
    frame_height: int          – Altura de cada frame (grade regular).
    spacing     : int          – Gap entre frames (padrão 0).
    margin      : int          – Borda externa da sheet (padrão 0).
    scale       : float        – Fator de escala aplicado ao carregar
                                 (ex: 2.0 = dobra o tamanho, útil para
                                 pixel art em baixa resolução).
    color_key   : tuple | None – Cor tratada como transparente (ex: (255,0,255)).
    """

    def __init__(
        self,
        image_path:   str,
        frame_width:  int,
        frame_height: int,
        spacing:      int   = 0,
        margin:       int   = 0,
        scale:        float = 1.0,
        color_key:    Optional[Tuple] = None,
    ) -> None:
        self.image_path   = image_path
        self.frame_width  = frame_width
        self.frame_height = frame_height
        self.spacing      = spacing
        self.margin       = margin
        self.scale        = scale
        self.color_key    = color_key

        self._sheet:   Optional[pygame.Surface] = None
        self._frames:  List[pygame.Surface]     = []   # indexed sequentially
        self._named:   Dict[str, pygame.Surface] = {}  # optional name map
        self._loaded:  bool = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> "SpriteSheet":
        """Carrega e fatia a sheet. Retorna self para encadeamento."""
        if self._loaded:
            return self

        raw = pygame.image.load(self.image_path).convert_alpha()
        if self.color_key is not None:
            raw.set_colorkey(self.color_key)

        sheet_w, sheet_h = raw.get_size()
        step_x = self.frame_width  + self.spacing
        step_y = self.frame_height + self.spacing

        cols = (sheet_w - self.margin * 2 + self.spacing) // step_x
        rows = (sheet_h - self.margin * 2 + self.spacing) // step_y

        for row in range(rows):
            for col in range(cols):
                x = self.margin + col * step_x
                y = self.margin + row * step_y
                rect = pygame.Rect(x, y, self.frame_width, self.frame_height)
                surf = raw.subsurface(rect).copy()
                if self.scale != 1.0:
                    nw = max(1, int(self.frame_width  * self.scale))
                    nh = max(1, int(self.frame_height * self.scale))
                    surf = pygame.transform.scale(surf, (nw, nh))
                self._frames.append(surf)

        self._loaded = True
        return self

    # ------------------------------------------------------------------
    # Frame access
    # ------------------------------------------------------------------

    def get(self, index: int) -> pygame.Surface:
        """Retorna o frame pelo índice sequencial."""
        return self._frames[index]

    def get_range(self, start: int, end: int) -> List[pygame.Surface]:
        """
        Retorna frames do intervalo [start, end) (exclusive end).
        Exemplo: sheet.get_range(0, 4) → frames 0,1,2,3
        """
        return self._frames[start:end]

    def get_row(self, row: int) -> List[pygame.Surface]:
        """Retorna todos os frames de uma linha."""
        cols = self._cols()
        start = row * cols
        return self._frames[start: start + cols]

    def name(self, frame_name: str, index: int) -> "SpriteSheet":
        """Associa um nome a um frame. Retorna self."""
        self._named[frame_name] = self._frames[index]
        return self

    def get_named(self, frame_name: str) -> pygame.Surface:
        return self._named[frame_name]

    def _cols(self) -> int:
        """Número de colunas calculado a partir da sheet."""
        if not self._frames:
            return 0
        raw = pygame.image.load(self.image_path)
        step_x = self.frame_width + self.spacing
        return (raw.get_width() - self.margin * 2 + self.spacing) // step_x

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    @property
    def frames(self) -> List[pygame.Surface]:
        return list(self._frames)

    # ------------------------------------------------------------------
    # Flip helpers
    # ------------------------------------------------------------------

    @staticmethod
    def flip_h(frames: List[pygame.Surface]) -> List[pygame.Surface]:
        """Retorna uma nova lista com todos os frames espelhados horizontalmente."""
        return [pygame.transform.flip(f, True, False) for f in frames]

    @staticmethod
    def flip_v(frames: List[pygame.Surface]) -> List[pygame.Surface]:
        """Retorna uma nova lista com todos os frames espelhados verticalmente."""
        return [pygame.transform.flip(f, False, True) for f in frames]

    # ------------------------------------------------------------------
    # Factory: cria sheet de uma única linha de frames (atalho comum)
    # ------------------------------------------------------------------

    @classmethod
    def from_strip(
        cls,
        image_path:   str,
        frame_count:  int,
        frame_height: Optional[int] = None,
        scale:        float = 1.0,
        color_key:    Optional[Tuple] = None,
    ) -> "SpriteSheet":
        """
        Cria uma SpriteSheet a partir de um strip horizontal.
        (Uma linha, frame_count frames de largura igual.)
        """
        img = pygame.image.load(image_path)
        fw = img.get_width() // frame_count
        fh = frame_height or img.get_height()
        sheet = cls(image_path, fw, fh, scale=scale, color_key=color_key)
        sheet.load()
        return sheet

    def __repr__(self) -> str:
        return (
            f"<SpriteSheet '{self.image_path}' "
            f"{self.frame_width}x{self.frame_height} "
            f"frames={self.frame_count}>"
        )
