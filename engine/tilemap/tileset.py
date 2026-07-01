from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import pygame


@dataclass
class TileData:
    """
    Metadata for a single tile type.

    Attributes
    ----------
    tile_id   : int  – Unique identifier (GID / local ID) for this tile.
    solid     : bool – Whether the tile blocks movement (used by BoxCollider).
    one_way   : bool – One-way platform tile (blocks only from above).
    damage    : int  – Damage dealt on contact (0 = harmless).
    custom    : dict – Free-form metadata (e.g. {"type": "lava", "speed": 0.5}).
    """
    tile_id: int
    solid:   bool = False
    one_way: bool = False
    damage:  int  = 0
    custom:  Dict = field(default_factory=dict)


class Tileset:
    """
    Slices a spritesheet image into individual tile surfaces and stores per-tile
    metadata.

    Parameters
    ----------
    image_path  : str  – Path to the spritesheet PNG/JPG.
    tile_width  : int  – Width of a single tile in pixels.
    tile_height : int  – Height of a single tile in pixels.
    spacing     : int  – Gap between tiles in the sheet (default 0).
    margin      : int  – Outer border of the sheet (default 0).
    first_gid   : int  – Global tile ID of the first tile (Tiled convention, default 1).
    """

    def __init__(
        self,
        image_path:  str,
        tile_width:  int,
        tile_height: int,
        spacing:     int = 0,
        margin:      int = 0,
        first_gid:   int = 1,
    ) -> None:
        self.image_path  = image_path
        self.tile_width  = tile_width
        self.tile_height = tile_height
        self.spacing     = spacing
        self.margin      = margin
        self.first_gid   = first_gid

        self._sheet:  Optional[pygame.Surface] = None
        self._tiles:  Dict[int, pygame.Surface] = {}   # gid -> surface
        self._meta:   Dict[int, TileData]       = {}   # gid -> metadata
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load and slice the spritesheet. Call once after pygame.init()."""
        if self._loaded:
            return

        raw = pygame.image.load(self.image_path)

        # BUG FIX: convert_alpha() requires an active display surface.
        # Fall back to a plain copy when no display has been created yet.
        try:
            self._sheet = raw.convert_alpha()
        except pygame.error:
            self._sheet = raw.copy()

        sheet_w, sheet_h = self._sheet.get_size()
        step_x = self.tile_width  + self.spacing
        step_y = self.tile_height + self.spacing

        cols = (sheet_w - self.margin * 2 + self.spacing) // step_x
        rows = (sheet_h - self.margin * 2 + self.spacing) // step_y

        gid = self.first_gid
        for row in range(rows):
            for col in range(cols):
                x = self.margin + col * step_x
                y = self.margin + row * step_y
                rect = pygame.Rect(x, y, self.tile_width, self.tile_height)

                # BUG FIX: validate that the rect fits inside the sheet before
                # calling subsurface(), which raises ValueError when out of bounds.
                if (
                    rect.right  > sheet_w
                    or rect.bottom > sheet_h
                    or rect.width  <= 0
                    or rect.height <= 0
                ):
                    print(
                        f"[Tileset] Warning: tile GID {gid} rect {rect} is outside "
                        f"sheet size {sheet_w}x{sheet_h} — skipping."
                    )
                    gid += 1
                    continue

                surf = self._sheet.subsurface(rect).copy()
                self._tiles[gid] = surf
                gid += 1

        self._loaded = True

    # ------------------------------------------------------------------
    # Tile access
    # ------------------------------------------------------------------

    def get_surface(self, gid: int) -> Optional[pygame.Surface]:
        """Return the pygame.Surface for the given global tile ID."""
        return self._tiles.get(gid)

    def set_tile_data(self, gid: int, data: TileData) -> None:
        """Attach metadata to a specific tile."""
        self._meta[gid] = data

    def get_tile_data(self, gid: int) -> Optional[TileData]:
        """Return TileData for a gid, or None if not registered."""
        return self._meta.get(gid)

    def is_solid(self, gid: int) -> bool:
        """Convenience: True if the tile is marked solid."""
        meta = self._meta.get(gid)
        return meta.solid if meta else False

    def is_one_way(self, gid: int) -> bool:
        """Convenience: True if the tile is a one-way platform."""
        meta = self._meta.get(gid)
        return meta.one_way if meta else False

    @property
    def tile_count(self) -> int:
        return len(self._tiles)

    @property
    def tile_size(self) -> Tuple[int, int]:
        return (self.tile_width, self.tile_height)

    def __repr__(self) -> str:
        return (
            f"<Tileset '{self.image_path}' "
            f"{self.tile_width}x{self.tile_height} "
            f"tiles={self.tile_count}>"
        )
