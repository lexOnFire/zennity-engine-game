# Zennity Prefab Format (.zprefab)

`.zprefab` is the JSON format used by the Zennity engine to save and load reusable, parameterized GameObjects (Prefabs).

Current format version: `1`

## Root Contract

```json
{
  "prefab_uuid": "stable-uuid-of-the-prefab",
  "name": "MyPlayer",
  "source_object_name": "MyPlayer",
  "transform": {
    "position": [0.0, 0.0, 0.0],
    "rotation": [0.0, 0.0, 0.0],
    "rz": 0.0,
    "scale": [1.0, 1.0, 1.0]
  },
  "visual": {
    "mesh_type": "Quadrado",
    "sprite_path": null,
    "asset_uuid": null,
    "color": [255, 255, 255, 255],
    "material": "default"
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
  },
  "children": []
}
```

## Structure Details

* **`prefab_uuid`**: The unique stable identifier matching the asset's `.meta` file.
* **`name`**: The display name of the prefab asset.
* **`source_object_name`**: The original name of the GameObject before zipping.
* **`transform`**: Defaults for position, rotation, and scale.
* **`visual`**: Mesh type, colors, and textures/materials.
* **`components`**: Embedded serialization of attached components (e.g. rigidbodies and colliders).
* **`children`**: Reserved for recursive child hierarchies. Currently initialized to `[]` for flat prefabs, but designed to hold nested GameObjects.
