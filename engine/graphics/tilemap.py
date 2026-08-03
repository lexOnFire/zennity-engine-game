import warnings
from pathlib import Path
import pygame
from typing import Dict, List, Tuple, Optional, Any
from ..core.component import Component
from engine.tilemap.tilemap import TileMap, TilemapRenderer, TileLayer

warnings.warn(
    "engine.graphics.tilemap está deprecado. Use engine.tilemap.",
    DeprecationWarning,
    stacklevel=2,
)

Tilemap = TileMap


class LegacyTileset:
    """
    Data structure representing a collection of tiles extracted from a texture.
    """
    def __init__(self, texture: pygame.Surface, tile_size: int = 32):
        self.texture = texture
        self.tile_size = tile_size
        self._tiles: Dict[int, pygame.Surface] = {}
        self._build_tiles()

    def _build_tiles(self):
        """Slices the texture into individual tile surfaces based on tile_size."""
        if not self.texture:
            return
            
        width = self.texture.get_width()
        height = self.texture.get_height()
        
        cols = width // self.tile_size
        rows = height // self.tile_size
        
        tile_id = 1 # ID 0 is reserved for empty/no tile
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                tile_surface = self.texture.subsurface(rect).copy()
                self._tiles[tile_id] = tile_surface
                tile_id += 1

    def get_tile(self, tile_id: int) -> Optional[pygame.Surface]:
        if tile_id == 0:
            return None
        return self._tiles.get(tile_id)


class Tilemap(Component):
    """
    Data component storing the grid of tiles.
    """
    component_type = "Tilemap"
    unique = True

    def __init__(self, width: int = 10, height: int = 10, tile_size: int = 32):
        super().__init__()
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # Layers are list of dicts mapping (x,y) -> tile_id
        # We start with 1 default layer
        self.layers: List[Dict[Tuple[int, int], int]] = [{}]
        
    def add_layer(self):
        self.layers.append({})
        
    def get_tile(self, layer_idx: int, x: int, y: int) -> int:
        if 0 <= layer_idx < len(self.layers):
            return self.layers[layer_idx].get((x, y), 0)
        return 0

    def set_tile(self, layer_idx: int, x: int, y: int, tile_id: int):
        if 0 <= layer_idx < len(self.layers):
            if 0 <= x < self.width and 0 <= y < self.height:
                if tile_id == 0:
                    self.layers[layer_idx].pop((x, y), None)
                else:
                    self.layers[layer_idx][(x, y)] = tile_id
                    
    def clear(self):
        self.layers = [{}]
        
    def resize(self, new_width: int, new_height: int):
        self.width = max(1, new_width)
        self.height = max(1, new_height)
        # Remove tiles outside new bounds
        for layer in self.layers:
            keys_to_remove = []
            for (x, y) in layer.keys():
                if x >= self.width or y >= self.height:
                    keys_to_remove.append((x, y))
            for k in keys_to_remove:
                layer.pop(k, None)

    def serialize_properties(self) -> dict:
        serialized_layers = []
        for layer in self.layers:
            s_layer = {f"{x},{y}": tile_id for (x, y), tile_id in layer.items()}
            serialized_layers.append(s_layer)

        return {
            "width": int(self.width),
            "height": int(self.height),
            "tile_size": int(self.tile_size),
            "layers": serialized_layers,
        }

    def serialize(self) -> dict:
        data = super().serialize()
        # Compatibility with the first Tilemap tests/files that stored fields at top level.
        data.update(self.serialize_properties())
        return data

    def deserialize_properties(self, data: dict) -> None:
        self.width = data.get('width', 10)
        self.height = data.get('height', 10)
        self.tile_size = data.get('tile_size', 32)
        
        self.layers = []
        serialized_layers = data.get('layers', [{}])
        for s_layer in serialized_layers:
            layer = {}
            for coord_str, tile_id in s_layer.items():
                try:
                    x_str, y_str = coord_str.split(',')
                    layer[(int(x_str), int(y_str))] = int(tile_id)
                except (ValueError, TypeError):
                    continue
            self.layers.append(layer)

    def deserialize(self, data: dict) -> None:
        super().deserialize(data)
        properties = data.get("properties", data)
        if isinstance(properties, dict):
            self.deserialize_properties(properties)


class LegacyTilemapRenderer(Component):
    """
    Renderer component for a Tilemap. Separated for performance and single-responsibility.

    BUG FIX: o Tileset é um objeto (não primitivo), e Component.serialize()
    só reflete primitivos -- então um TilemapRenderer salvo em .zscene perdia
    a referência da textura e voltava invisível ao recarregar a cena, sem erro
    nenhum. Agora o caminho da textura e o tile_size são gravados como
    properties e o Tileset é reconstruído no load.
    """
    component_type = "TilemapRenderer"

    def __init__(
        self,
        tileset: Optional[LegacyTileset] = None,
        texture_path: str = "",
        tile_size: int = 32,
    ):
        super().__init__()
        self.tileset = tileset
        self.texture_path = str(texture_path or "")
        self.tile_size = int(tile_size)
        if self.tileset is None and self.texture_path:
            self._rebuild_tileset()

    def _rebuild_tileset(self) -> None:
        """Recarrega o Tileset a partir de ``texture_path``.

        Tolerante a falhas de propósito: uma textura ausente ou um ambiente
        sem vídeo não podem impedir o carregamento da cena inteira -- o
        tilemap apenas fica sem visual, como já ficava antes desta correção.
        """
        path = self.texture_path
        if not path:
            self.tileset = None
            return
        try:
            candidate = Path(path)
            if not candidate.is_absolute():
                candidate = Path.cwd() / candidate
            surface = pygame.image.load(str(candidate))
            self.tileset = LegacyTileset(surface, self.tile_size)
        except Exception:
            self.tileset = None

    def serialize_properties(self) -> dict:
        return {
            "texture_path": self.texture_path,
            "tile_size": int(self.tile_size),
        }

    def deserialize_properties(self, data: dict) -> None:
        self.texture_path = str(data.get("texture_path", self.texture_path) or "")
        self.tile_size = int(data.get("tile_size", self.tile_size))
        if self.texture_path:
            self._rebuild_tileset()

    def draw(self, screen: pygame.Surface) -> None:
        if not self.tileset:
            return
            
        tilemap = self.game_object.get_component(Tilemap)
        if not tilemap:
            return
            
        # Get camera
        from engine.graphics.active_camera import get_active_camera
        camera = get_active_camera()
        
        world_pos = self.transform.get_world_position()
        zoom = 1.0
        
        # We will iterate through tiles.
        # For a full optimized approach, we should calculate visible bounds.
        # But for now, we iterate over populated tiles in the dicts since it's sparse.
        
        for layer in tilemap.layers:
            for (tx, ty), tile_id in layer.items():
                tile_surf = self.tileset.get_tile(tile_id)
                if not tile_surf:
                    continue
                    
                # Tile world position
                tw_x = world_pos[0] + tx * tilemap.tile_size
                tw_y = world_pos[1] + ty * tilemap.tile_size
                
                if camera:
                    screen_x, screen_y = camera.world_to_screen(
                        (tw_x, tw_y), screen.get_width(), screen.get_height()
                    )
                    zoom = camera.zoom
                else:
                    screen_x, screen_y = tw_x, tw_y
                    
                scaled_size = int(tilemap.tile_size * zoom)
                
                if scaled_size <= 0:
                    continue
                
                # Simple frustum culling
                if (screen_x + scaled_size < 0 or screen_x > screen.get_width() or
                    screen_y + scaled_size < 0 or screen_y > screen.get_height()):
                    continue
                    
                if zoom != 1.0:
                    scaled_surf = pygame.transform.scale(tile_surf, (scaled_size, scaled_size))
                else:
                    scaled_surf = tile_surf
                    
                screen.blit(scaled_surf, (int(screen_x), int(screen_y)))


Tileset = LegacyTileset
TilemapRenderer = LegacyTilemapRenderer
