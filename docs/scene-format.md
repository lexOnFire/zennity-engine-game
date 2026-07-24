# Zennity Scene Format (.zscene)

`.zscene` is the JSON format used by the Zennity editor to save and load
complete scenes.

Current format version: `1`

## Root

```json
{
  "format_version": 1,
  "scene_name": "Level 01",
  "engine_version": "0.1.0",
  "objects": []
}
```

## GameObject

Each object stores identity, editor metadata, transform, visual hints and
components.

```json
{
  "id": "uuid",
  "uuid": "uuid",
  "name": "Player",
  "tag": "Player",
  "layer": 0,
  "active": true,
  "enabled": true,
  "transform": {
    "position": [100.0, 200.0, 0.0],
    "rotation": [0.0, 0.0, 0.0],
    "rz": 0.0,
    "scale": [1.0, 1.0, 1.0]
  },
  "visual": {
    "mesh_type": "rect",
    "sprite_path": null,
    "color": null,
    "material": null
  },
  "components": {
    "collider": {
      "type": "box",
      "width": 32.0,
      "height": 32.0,
      "offset": [0.0, 0.0],
      "is_trigger": false,
      "debug_draw": false
    },
    "rigidbody": {
      "mass": 1.0,
      "gravity_scale": 1.0,
      "drag": 0.0,
      "use_gravity": true,
      "is_kinematic": false,
      "velocity": [0.0, 0.0],
      "acceleration": [0.0, 0.0]
    },
    "scripts": []
  }
}
```

## Editor Integration

The Phase 1 editor exposes scene actions in the File menu:

- New Scene: `Ctrl+N`
- Open Scene: `Ctrl+O`
- Save Scene: `Ctrl+S`
- Save Scene As: `Ctrl+Shift+S`

Serialization lives in `engine.scene`. The viewport is only asked to refresh its
scene model after load/new operations.
