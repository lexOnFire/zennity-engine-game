from __future__ import annotations
"""
tilemap_loader.py
-----------------
Loads TileMap + Tileset(s) from JSON files.

Supports two formats:
  1. Tiled Editor JSON (.tmj / .json exported from Tiled)
  2. Zennity native JSON

Usage
-----
    from engine.tilemap import TileMapLoader

    tilemap = TileMapLoader.load("maps/world1.json")
"""
import json
import os
from typing import Any, Dict, List, Optional

import pygame

from .tileset import Tileset, TileData
from .tilemap import TileLayer, TileMap


class TileMapLoader:
    """Static factory — load a TileMap from a JSON file."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def load(path: str) -> TileMap:
        """
        Load a TileMap from *path*.

        Auto-detects Tiled or Zennity-native format based on JSON keys.
        Raises FileNotFoundError / ValueError on bad input.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"[TileMapLoader] File not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"[TileMapLoader] Malformed JSON in {path}: {e}")

        try:
            if TileMapLoader._is_tiled(data):
                return TileMapLoader._load_tiled(data, os.path.dirname(path))
            return TileMapLoader._load_native(data, os.path.dirname(path))
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"[TileMapLoader] Invalid map format in {path}: Missing or invalid key/index/type: {e}")

    # ------------------------------------------------------------------
    # Format detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_tiled(data: Dict) -> bool:
        """Return True if the JSON looks like a Tiled export."""
        return "tilesets" in data and "layers" in data and "tilewidth" in data

    # ------------------------------------------------------------------
    # Tiled format
    # ------------------------------------------------------------------

    @staticmethod
    def _load_tiled(data: Dict, base_dir: str) -> TileMap:
        tw = data["tilewidth"]
        th = data["tileheight"]
        mw = data["width"]
        mh = data["height"]

        tilemap = TileMap(tw, th, mw, mh)

        # --- Tilesets ---
        for ts_data in data.get("tilesets", []):
            # BUG FIX: 'firstgid' is optional in embedded tilesets that use
            # an external TSX file; default to 1 if absent.
            first_gid   = ts_data.get("firstgid", 1)
            tile_width  = ts_data.get("tilewidth",  tw)
            tile_height = ts_data.get("tileheight", th)
            spacing     = ts_data.get("spacing",     0)
            margin      = ts_data.get("margin",      0)

            # Tiled can reference an external image or embed it
            image_rel = ts_data.get("image", "")
            if not image_rel:
                # Inline / external TSX — skip for now
                continue

            image_path = os.path.join(base_dir, image_rel)
            if not os.path.isfile(image_path):
                print(
                    f"[TileMapLoader] Warning: tileset image '{image_path}' not found — skipping."
                )
                continue

            ts = Tileset(
                image_path  = image_path,
                tile_width  = tile_width,
                tile_height = tile_height,
                spacing     = spacing,
                margin      = margin,
                first_gid   = first_gid,
            )
            ts.load()

            # Per-tile metadata ("tileproperties" in Tiled ≤ 0.x; "tiles" array in 1.x+)
            tile_props: Dict[int, Dict] = {}
            for tile_entry in ts_data.get("tiles", []):
                local_id = tile_entry.get("id", -1)
                if local_id < 0:
                    continue
                props = {}
                for prop in tile_entry.get("properties", []):
                    props[prop["name"]] = prop["value"]
                tile_props[local_id] = props

            for local_id, props in tile_props.items():
                gid = first_gid + local_id
                ts.set_tile_data(gid, TileData(
                    tile_id = gid,
                    solid   = bool(props.get("solid",   False)),
                    one_way = bool(props.get("one_way", False)),
                    damage  = int( props.get("damage",  0)),
                    custom  = {k: v for k, v in props.items()
                               if k not in ("solid", "one_way", "damage")},
                ))

            tilemap.add_tileset(ts)

        # --- Layers ---
        for z, layer_data in enumerate(data.get("layers", [])):
            layer_type = layer_data.get("type", "tilelayer")
            if layer_type != "tilelayer":
                continue  # skip objectgroup / imagelayer

            name    = layer_data.get("name",    f"layer_{z}")
            visible = layer_data.get("visible", True)
            opacity = float(layer_data.get("opacity", 1.0))
            raw     = layer_data.get("data", [])

            # Tiled stores GIDs as positive ints; 0 = empty.
            # Some encodings may include negative flip flags — mask them out.
            clean = [max(0, int(g) & 0x1FFFFFFF) for g in raw]

            layer = TileLayer(
                name    = name,
                width   = mw,
                height  = mh,
                data    = clean,
                visible = visible,
                opacity = opacity,
                z_index = z,
            )
            tilemap.add_layer(layer)

        return tilemap

    # ------------------------------------------------------------------
    # Zennity-native format
    # ------------------------------------------------------------------

    @staticmethod
    def _load_native(data: Dict, base_dir: str) -> TileMap:
        tw = data["tile_width"]
        th = data["tile_height"]
        mw = data["map_width"]
        mh = data["map_height"]

        tilemap = TileMap(tw, th, mw, mh)

        # --- Tilesets ---
        for ts_data in data.get("tilesets", []):
            image_rel   = ts_data["image"]
            image_path  = os.path.join(base_dir, image_rel)
            first_gid   = ts_data.get("first_gid", 1)
            spacing     = ts_data.get("spacing",   0)
            margin      = ts_data.get("margin",    0)

            ts = Tileset(
                image_path  = image_path,
                tile_width  = ts_data.get("tile_width",  tw),
                tile_height = ts_data.get("tile_height", th),
                spacing     = spacing,
                margin      = margin,
                first_gid   = first_gid,
            )
            ts.load()

            for tile_entry in ts_data.get("tiles", []):
                gid = tile_entry.get("gid", -1)
                if gid < 0:
                    continue
                ts.set_tile_data(gid, TileData(
                    tile_id = gid,
                    solid   = bool(tile_entry.get("solid",   False)),
                    one_way = bool(tile_entry.get("one_way", False)),
                    damage  = int( tile_entry.get("damage",  0)),
                    custom  = tile_entry.get("custom", {}),
                ))

            tilemap.add_tileset(ts)

        # --- Layers ---
        for z, layer_data in enumerate(data.get("layers", [])):
            layer = TileLayer(
                name    = layer_data.get("name",    f"layer_{z}"),
                width   = mw,
                height  = mh,
                data    = [int(g) for g in layer_data.get("data", [])],
                visible = layer_data.get("visible", True),
                opacity = float(layer_data.get("opacity", 1.0)),
                z_index = layer_data.get("z_index", z),
            )
            tilemap.add_layer(layer)

        return tilemap
