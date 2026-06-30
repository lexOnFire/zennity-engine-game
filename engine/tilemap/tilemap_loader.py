from __future__ import annotations
import json
import os
from typing import Any, Dict

from .tileset import Tileset, TileData
from .tilemap import TileMap, TileLayer


class TilemapLoader:
    """
    Loads a TileMap from a JSON file.

    Supports two formats:
    ─────────────────────
    1. **Tiled JSON export** (orthogonal, CSV or array encoding, no compression).
       In Tiled: File > Export As > JSON Map Files.
    2. **Zennity native JSON** — a simpler hand-crafted format (see template below).

    Zennity native format
    ─────────────────────
    {
        "tile_width":  32,
        "tile_height": 32,
        "map_width":   20,
        "map_height":  15,
        "tilesets": [
            {
                "image":       "assets/tileset.png",
                "tile_width":  32,
                "tile_height": 32,
                "first_gid":   1,
                "spacing":     0,
                "margin":      0,
                "tile_data": {
                    "1": { "solid": true },
                    "2": { "solid": true, "one_way": true },
                    "5": { "damage": 10, "custom": { "type": "lava" } }
                }
            }
        ],
        "layers": [
            {
                "name":    "background",
                "z_index": 0,
                "visible": true,
                "opacity": 1.0,
                "data":    [0, 0, 1, 1, ...]
            },
            {
                "name":    "collision",
                "z_index": 1,
                "visible": true,
                "opacity": 1.0,
                "data":    [0, 0, 1, 1, ...]
            }
        ]
    }
    """

    @staticmethod
    def load(path: str, base_dir: str = "") -> TileMap:
        """
        Load a TileMap from *path*.

        Parameters
        ----------
        path     : str – Path to the JSON file.
        base_dir : str – Base directory for resolving relative image paths.
                         Defaults to the directory containing the JSON file.
        """
        abs_path = os.path.abspath(path)
        if not base_dir:
            base_dir = os.path.dirname(abs_path)

        with open(abs_path, "r", encoding="utf-8") as f:
            raw: Dict[str, Any] = json.load(f)

        # Detect format
        if "tilesets" in raw and "orientation" in raw:
            return TilemapLoader._load_tiled(raw, base_dir)
        else:
            return TilemapLoader._load_zennity(raw, base_dir)

    # ------------------------------------------------------------------
    # Zennity native loader
    # ------------------------------------------------------------------

    @staticmethod
    def _load_zennity(raw: Dict[str, Any], base_dir: str) -> TileMap:
        tw  = raw["tile_width"]
        th  = raw["tile_height"]
        mw  = raw["map_width"]
        mh  = raw["map_height"]

        tilemap = TileMap(tile_width=tw, tile_height=th, map_width=mw, map_height=mh)

        for ts_data in raw.get("tilesets", []):
            image_path = os.path.join(base_dir, ts_data["image"])
            ts = Tileset(
                image_path  = image_path,
                tile_width  = ts_data["tile_width"],
                tile_height = ts_data["tile_height"],
                first_gid   = ts_data.get("first_gid", 1),
                spacing     = ts_data.get("spacing",   0),
                margin      = ts_data.get("margin",    0),
            )
            ts.load()

            for gid_str, meta in ts_data.get("tile_data", {}).items():
                gid  = int(gid_str)
                data = TileData(
                    tile_id = gid,
                    solid   = meta.get("solid",   False),
                    one_way = meta.get("one_way", False),
                    damage  = meta.get("damage",  0),
                    custom  = meta.get("custom",  {}),
                )
                ts.set_tile_data(gid, data)

            tilemap.add_tileset(ts)

        for layer_data in raw.get("layers", []):
            layer = TileLayer(
                name    = layer_data["name"],
                width   = mw,
                height  = mh,
                data    = layer_data["data"],
                visible = layer_data.get("visible", True),
                opacity = layer_data.get("opacity", 1.0),
                z_index = layer_data.get("z_index", 0),
            )
            tilemap.add_layer(layer)

        return tilemap

    # ------------------------------------------------------------------
    # Tiled JSON loader
    # ------------------------------------------------------------------

    @staticmethod
    def _load_tiled(raw: Dict[str, Any], base_dir: str) -> TileMap:
        tw = raw["tilewidth"]
        th = raw["tileheight"]
        mw = raw["width"]
        mh = raw["height"]

        tilemap = TileMap(tile_width=tw, tile_height=th, map_width=mw, map_height=mh)

        for ts_data in raw.get("tilesets", []):
            image_path = os.path.join(base_dir, ts_data["image"])
            ts = Tileset(
                image_path  = image_path,
                tile_width  = ts_data["tilewidth"],
                tile_height = ts_data["tileheight"],
                first_gid   = ts_data.get("firstgid",  1),
                spacing     = ts_data.get("spacing",   0),
                margin      = ts_data.get("margin",    0),
            )
            ts.load()

            # Parse per-tile properties from Tiled ("tiles" array)
            for tile_entry in ts_data.get("tiles", []):
                local_id = tile_entry.get("id", 0)
                gid      = ts.first_gid + local_id
                props    = {}
                for p in tile_entry.get("properties", []):
                    props[p["name"]] = p["value"]

                data = TileData(
                    tile_id = gid,
                    solid   = props.get("solid",   False),
                    one_way = props.get("one_way", False),
                    damage  = int(props.get("damage", 0)),
                    custom  = {k: v for k, v in props.items()
                               if k not in ("solid", "one_way", "damage")},
                )
                ts.set_tile_data(gid, data)

            tilemap.add_tileset(ts)

        z = 0
        for layer_data in raw.get("layers", []):
            if layer_data.get("type") != "tilelayer":
                continue
            raw_data = layer_data.get("data", [])
            layer = TileLayer(
                name    = layer_data["name"],
                width   = mw,
                height  = mh,
                data    = raw_data,
                visible = layer_data.get("visible", True),
                opacity = layer_data.get("opacity", 1.0),
                z_index = z,
            )
            tilemap.add_layer(layer)
            z += 1

        return tilemap
