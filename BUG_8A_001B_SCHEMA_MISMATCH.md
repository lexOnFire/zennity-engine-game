# BUG-8A-001B — Scene Format Incompatibility

## ROOT CAUSE FOUND

Benchmark `.zscene` files use **incompatible JSON schema** compared to canonical editor format.

### Golden Schema (Working - ZennityRunLevel.zscene)

```json
{
  "format_version": 2,
  "scene_name": "ZennityRunLevel",
  "engine_version": "Zennity 0.1.0",
  "objects": [
    {
      "id": "unique-id",
      "name": "ObjectName",
      "tag": "Tag",
      "active": true,
      "transform": {
        "position": [x, y, z],
        "rotation": [x, y, z],
        "rz": 0.0,
        "scale": [x, y, z]
      },
      "visual": {
        "mesh_type": "...",
        "color": [r, g, b],
        "texture": "...",
        "enabled": true,
        "material": "...",
        "layer": "...",
        "order": 0
      },
      "components": {
        "collider": {
          "type": "box",
          "width": 32.0,
          "height": 32.0,
          "is_trigger": false
        }
      },
      "enabled": true,
      "static": false,
      "layer": "Default"
    }
  ]
}
```

### Benchmark Schema (BROKEN - MainMenu.zscene)

```json
{
  "format": "zennity.scene",  // ❌ WRONG: should be "format_version": 2
  "name": "Main Menu",         // ❌ WRONG: should be "scene_name"
  "objects": [
    {
      "id": "main_camera",
      "name": "MainCamera",
      "type": "Camera2D",       // ❌ WRONG: should be in components, not top-level
      "x": 0,                   // ❌ WRONG: should be transform.position[0]
      "y": 0,                   // ❌ WRONG: should be transform.position[1]
      "enabled": true,
      "camera": {
        "zoom": 1.0,
        "viewport_width": 1280,
        "viewport_height": 720,
        "clear_color": [0.1, 0.1, 0.1, 1.0]
      }
    },
    {
      "id": "menu_ui_container",
      "name": "MenuUI",
      "type": "Canvas",         // ❌ WRONG: type field not in canonical
      "x": 0,
      "y": 0,
      "enabled": true,
      "ui": {
        "asset": "Assets/UI/MainMenu.zui",
        "auto_load": true
      },
      "logic_graphs": [         // ❌ WRONG: not in canonical schema
        {
          "path": "Assets/Logic/MainMenuLogic.zlogic",
          "name": "MainMenuLogic"
        }
      ]
    }
  ],
  "variables": {                // ❌ WRONG: not in canonical schema
    "coins": 0,
    "score": 0,
    "has_key": false,
    "health": 100,
    "current_level": 1
  }
}
```

## DIFFERENCES SUMMARY

| Field | Golden | Benchmark | Status |
|-------|--------|-----------|--------|
| `format_version` | `2` | MISSING | ❌ |
| `format` | MISSING | `"zennity.scene"` | ❌ |
| `scene_name` | ✅ | `"name"` instead | ❌ |
| `engine_version` | ✅ | MISSING | ❌ |
| `objects[].transform` | ✅ dict | `x, y` fields | ❌ |
| `objects[].type` | MISSING | Present (wrong) | ❌ |
| `objects[].components` | ✅ dict | MISSING | ❌ |
| `objects[].visual` | ✅ dict | MISSING | ❌ |
| `objects[].tag` | ✅ | MISSING | ❌ |
| `objects[].static` | ✅ | MISSING | ❌ |
| `ui` field | MISSING | Separate | ❌ |
| `logic_graphs` | MISSING | Separate | ❌ |
| `variables` | MISSING | Separate | ❌ |

## BREAKING ISSUES

### Issue 1: Missing Transform Object
**Benchmark**:
```json
"x": 0,
"y": 0
```

**Expected**:
```json
"transform": {
  "position": [0, 0, 0],
  "rotation": [0, 0, 0],
  "rz": 0.0,
  "scale": [1, 1, 1]
}
```

### Issue 2: Type Field in Wrong Place
**Benchmark**:
```json
"type": "Camera2D"  // top-level
```

**Expected**:
```json
// type removed, components describe what it is
"components": {
  "camera": {...}
}
```

### Issue 3: Custom Fields Not in Canonical Schema
**Benchmark**:
```json
"ui": {...}
"logic_graphs": [...]
"variables": {...}
```

**Expected**:
```json
// All in "components" if needed
// "variables" not in scene (project-level)
"components": {
  "canvas": {
    "ui_asset": "...",
    ...
  }
}
```

## IMPACT

- Deserializer reads `format_version` first
- If not present or wrong: **FAIL**
- Looks for `scene_name`, not `name`: **FAIL**
- Expects `transform` object, finds `x, y`: **FAIL**
- No graceful fallback in loader

## SOLUTION

All benchmark scenes must be **REGENERATED** or **CONVERTED** to canonical format.

Options:
1. **Regenerate** using editor save (preferred)
   - Create each scene manually in editor
   - Add components properly
   - Save with canonical serializer
   
2. **Convert** existing files (risky)
   - Map benchmark format → canonical
   - Test deserializer doesn't silently fail
   - Verify all fields

Preferred: **Option 1** (regenerate in editor).

## FILES AFFECTED

All benchmark scenes:
- ❌ Assets/Scenes/MainMenu.zscene
- ❌ Assets/Scenes/Level1.zscene
- ❌ Assets/Scenes/Level2.zscene
- ❌ Assets/Scenes/GameOver.zscene
- ❌ Assets/Scenes/Victory.zscene

Plus any scenes with:
- ❌ Camera2D with `"type": "Camera2D"`
- ❌ Canvas with `"type": "Canvas"`
- ❌ Prefab references with `"type": "Prefab"`
- ❌ Position as `x, y` instead of `transform.position`

## NEXT STEPS

1. Understand editor's canonical scene factory
2. Regenerate each benchmark scene using real editor save
3. Validate with deserializer
4. Test roundtrip (load → save → load)
5. Verify all 5 scenes open

## STATUS

BUG-8A-001B: **ROOT CAUSE IDENTIFIED**

**Not an Asset Browser bug.**
**Not a routing bug.**
**Issue: Incompatible scene serialization format.**

Playtest remains **BLOCKED** until scenes are regenerated.
