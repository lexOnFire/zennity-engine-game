from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import pygame

from .tileset import Tileset


class TileLayer:
    """
    A single layer of tile data inside a TileMap.

    Parameters
    ----------
    name    : str          – Human-readable layer name (e.g. 'ground', 'decor').
    width   : int          – Map width in tiles.
    height  : int          – Map height in tiles.
    data    : List[int]    – Flat list of GIDs, row-major order (0 = empty).
    visible : bool         – Whether this layer is drawn.
    opacity : float        – Draw opacity 0.0–1.0.
    z_index : int          – Draw order (lower = drawn first).
    """

    def __init__(
        self,
        name:    str,
        width:   int,
        height:  int,
        data:    List[int],
        visible: bool  = True,
        opacity: float = 1.0,
        z_index: int   = 0,
    ) -> None:
        self.name    = name
        self.width   = width
        self.height  = height
        self.data    = data
        self.visible = visible
        self.opacity = max(0.0, min(1.0, opacity))
        self.z_index = z_index

    def get_gid(self, col: int, row: int) -> int:
        """Return the GID at (col, row). Returns 0 for out-of-bounds."""
        if col < 0 or col >= self.width or row < 0 or row >= self.height:
            return 0
        return self.data[row * self.width + col]

    def set_gid(self, col: int, row: int, gid: int) -> None:
        """Set the GID at (col, row)."""
        if 0 <= col < self.width and 0 <= row < self.height:
            self.data[row * self.width + col] = gid


class TileMap:
    """
    A multi-layer tile map that renders through any Camera2D / Camera offset.

    Parameters
    ----------
    tile_width   : int      – Tile width in pixels.
    tile_height  : int      – Tile height in pixels.
    map_width    : int      – Map width in tiles.
    map_height   : int      – Map height in tiles.
    """

    def __init__(
        self,
        tile_width:  int,
        tile_height: int,
        map_width:   int,
        map_height:  int,
    ) -> None:
        self.tile_width  = tile_width
        self.tile_height = tile_height
        self.map_width   = map_width
        self.map_height  = map_height

        self._tilesets: Dict[int, Tileset] = {}   # first_gid -> Tileset
        self._layers:   List[TileLayer]    = []

        # Optional pre-baked surface for static maps (massive perf gain)
        self._baked:       Optional[pygame.Surface] = None
        self._bake_dirty:  bool = True

    # ------------------------------------------------------------------
    # Tileset management
    # ------------------------------------------------------------------

    def add_tileset(self, tileset: Tileset) -> None:
        """Register a tileset. The tileset must already be loaded."""
        self._tilesets[tileset.first_gid] = tileset
        self._bake_dirty = True

    def _resolve_tileset(self, gid: int) -> Optional[Tileset]:
        """Find which tileset owns a given GID."""
        best: Optional[Tileset] = None
        for first_gid, ts in self._tilesets.items():
            if first_gid <= gid:
                if best is None or first_gid > best.first_gid:
                    best = ts
        return best

    def get_tile_surface(self, gid: int) -> Optional[pygame.Surface]:
        """Return the surface for a GID across all registered tilesets."""
        if gid <= 0:
            return None
        ts = self._resolve_tileset(gid)
        return ts.get_surface(gid) if ts else None

    # ------------------------------------------------------------------
    # Layer management
    # ------------------------------------------------------------------

    def add_layer(self, layer: TileLayer) -> None:
        """Add a layer and keep them sorted by z_index."""
        self._layers.append(layer)
        self._layers.sort(key=lambda l: l.z_index)
        self._bake_dirty = True

    def get_layer(self, name: str) -> Optional[TileLayer]:
        """Return the first layer matching the given name."""
        for layer in self._layers:
            if layer.name == name:
                return layer
        return None

    def remove_layer(self, name: str) -> None:
        self._layers = [l for l in self._layers if l.name != name]
        self._bake_dirty = True

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def world_to_tile(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert world pixel coordinates to tile (col, row)."""
        return int(wx // self.tile_width), int(wy // self.tile_height)

    def tile_to_world(self, col: int, row: int) -> Tuple[float, float]:
        """Convert tile (col, row) to top-left world pixel position."""
        return float(col * self.tile_width), float(row * self.tile_height)

    @property
    def pixel_width(self) -> int:
        return self.map_width * self.tile_width

    @property
    def pixel_height(self) -> int:
        return self.map_height * self.tile_height

    # ------------------------------------------------------------------
    # Collision helpers (used by physics system)
    # ------------------------------------------------------------------

    def is_solid_at(self, wx: float, wy: float, layer_name: str = "collision") -> bool:
        """
        Check whether the world point (wx, wy) sits on a solid tile.
        Uses the layer named *layer_name* (default 'collision').
        """
        col, row = self.world_to_tile(wx, wy)
        layer = self.get_layer(layer_name)
        if layer is None:
            return False
        gid = layer.get_gid(col, row)
        if gid <= 0:
            return False
        ts = self._resolve_tileset(gid)
        return ts.is_solid(gid) if ts else False

    def get_solid_rects_in_region(
        self,
        x: float, y: float,
        w: float, h: float,
        layer_name: str = "collision",
    ) -> List[pygame.Rect]:
        """
        Return pygame.Rect list for all solid tiles overlapping the AABB
        defined by (x, y, w, h) in world space. Useful for physics resolution.
        """
        rects: List[pygame.Rect] = []
        layer = self.get_layer(layer_name)
        if layer is None:
            return rects

        col_start = max(0, int(x // self.tile_width))
        col_end   = min(layer.width  - 1, int((x + w) // self.tile_width))
        row_start = max(0, int(y // self.tile_height))
        row_end   = min(layer.height - 1, int((y + h) // self.tile_height))

        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                gid = layer.get_gid(col, row)
                if gid <= 0:
                    continue
                ts = self._resolve_tileset(gid)
                if ts and ts.is_solid(gid):
                    wx, wy = self.tile_to_world(col, row)
                    rects.append(pygame.Rect(int(wx), int(wy), self.tile_width, self.tile_height))
        return rects

    # ------------------------------------------------------------------
    # Baking (static maps)
    # ------------------------------------------------------------------

    def bake(self) -> None:
        """
        Pre-render all visible layers onto a single surface.
        Call after all tilesets and layers are set up.
        Dramatically improves performance for static maps.
        """
        surface = pygame.Surface(
            (self.pixel_width, self.pixel_height),
            flags=pygame.SRCALPHA,
        )
        for layer in self._layers:
            if not layer.visible:
                continue
            self._draw_layer(surface, layer, 0, 0)
        self._baked = surface
        self._bake_dirty = False

    def invalidate_bake(self) -> None:
        """Mark the baked surface as dirty (call when tiles change at runtime)."""
        self._baked = None
        self._bake_dirty = True

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_layer(
        self,
        surface: pygame.Surface,
        layer: TileLayer,
        cam_x: float,
        cam_y: float,
    ) -> None:
        """Draw a single layer, culling tiles outside the camera viewport."""
        if not layer.visible:
            return

        surf_w, surf_h = surface.get_size()
        tw, th = self.tile_width, self.tile_height

        # Visible tile range
        col_start = max(0, int(cam_x // tw))
        col_end   = min(layer.width,  int((cam_x + surf_w) // tw) + 1)
        row_start = max(0, int(cam_y // th))
        row_end   = min(layer.height, int((cam_y + surf_h) // th) + 1)

        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                gid = layer.get_gid(col, row)
                if gid <= 0:
                    continue
                tile_surf = self.get_tile_surface(gid)
                if tile_surf is None:
                    continue

                screen_x = col * tw - int(cam_x)
                screen_y = row * th - int(cam_y)

                if layer.opacity < 1.0:
                    tile_surf = tile_surf.copy()
                    tile_surf.set_alpha(int(layer.opacity * 255))

                surface.blit(tile_surf, (screen_x, screen_y))

    def draw(
        self,
        screen: pygame.Surface,
        cam_x: float = 0.0,
        cam_y: float = 0.0,
    ) -> None:
        """
        Draw the tilemap to *screen*, offset by camera position (cam_x, cam_y).

        Parameters
        ----------
        screen : pygame.Surface – Destination surface (the game window).
        cam_x  : float          – Camera X position in world space.
        cam_y  : float          – Camera Y position in world space.
        """
        if not self._bake_dirty and self._baked is not None:
            # Baked path: just blit the pre-rendered surface
            screen.blit(self._baked, (-int(cam_x), -int(cam_y)))
        else:
            # Dynamic path: draw each layer individually
            for layer in self._layers:
                self._draw_layer(screen, layer, cam_x, cam_y)

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def draw_debug(
        self,
        screen: pygame.Surface,
        cam_x: float = 0.0,
        cam_y: float = 0.0,
        color: Tuple = (255, 0, 0, 128),
        layer_name: str = "collision",
    ) -> None:
        """
        Draws red outlines on solid tiles for debugging collisions.
        """
        layer = self.get_layer(layer_name)
        if layer is None:
            return

        surf_w, surf_h = screen.get_size()
        tw, th = self.tile_width, self.tile_height
        col_start = max(0, int(cam_x // tw))
        col_end   = min(layer.width,  int((cam_x + surf_w) // tw) + 1)
        row_start = max(0, int(cam_y // th))
        row_end   = min(layer.height, int((cam_y + surf_h) // th) + 1)

        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                gid = layer.get_gid(col, row)
                if gid <= 0:
                    continue
                ts = self._resolve_tileset(gid)
                if ts and ts.is_solid(gid):
                    sx = col * tw - int(cam_x)
                    sy = row * th - int(cam_y)
                    pygame.draw.rect(screen, color, (sx, sy, tw, th), 2)

    def __repr__(self) -> str:
        return (
            f"<TileMap {self.map_width}x{self.map_height} tiles "
            f"({self.pixel_width}x{self.pixel_height}px) "
            f"layers={len(self._layers)}>"
        )
