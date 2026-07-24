# Zennity Asset Database

The Asset Database scans the project `Assets/` folder and creates stable
metadata for every imported asset.

## Assets Folder

Every project has a root folder named `Assets/`. It is created automatically
when `AssetDatabase.scan()` runs.

New projects also receive standard subfolders:

- `Assets/Scenes/`
- `Assets/Prefabs/`
- `Assets/Scripts/`
- `Assets/Textures/`
- `Assets/Audio/`
- `Assets/Animations/`
- `Assets/Materials/`
- `Assets/Meshes/`

## Supported Types

- `scene`: `.zscene`
- `image`: `.png`, `.jpg`, `.jpeg`, `.bmp`
- `audio`: `.wav`, `.ogg`, `.mp3`
- `script`: `.py`
- `font`: `.ttf`, `.otf`
- `material`: `.zmat`
- `prefab`: `.zprefab`
- `unknown`: any other extension

## Meta Files

For each asset, the database creates a sidecar file:

```text
Assets/Textures/player.png
Assets/Textures/player.png.meta
```

The `.meta` JSON stores the stable identity and import settings:

```json
{
  "uuid": "stable-uuid",
  "type": "image",
  "importer": "image_importer",
  "source_path": "Assets/Textures/player.png",
  "import_settings": {}
}
```

The UUID stays stable across refreshes as long as the `.meta` file exists.

## Scene References

Scenes should reference assets using portable project-relative paths and,
when available, the asset UUID:

```json
{
  "visual": {
    "sprite_path": "Assets/Textures/player.png",
    "asset_uuid": "stable-uuid"
  }
}
```

Absolute filesystem paths should not be saved inside `.zscene` files.
