import pytest
import json
import tempfile
from pathlib import Path

from engine.core.scene import Scene
from engine.core.game_object import GameObject
from engine.graphics.tilemap import Tilemap, TilemapRenderer
from engine.ui import Canvas, LabelComponent, ButtonComponent
from engine.animation import Animator, AnimationClip, Keyframe
from engine.assets.asset_database import AssetDatabase
from engine.packages.manager import PackageManager
from engine.runtime.runtime_manager import RuntimeManager
from engine.scene.scene_serializer import deserialize_scene, serialize_scene

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_v030_stabilization_end_to_end(temp_dir):
    # 1. Package Manager Setup & Install dummy package
    pkg_source = temp_dir / "my_pkg"
    pkg_source.mkdir()
    manifest = {
        "name": "com.zennity.v030",
        "version": "1.0.0",
        "author": "Stabilizer",
        "description": "Integration package",
        "components": ["CustomPkgComponent"]
    }
    with open(pkg_source / "package.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)
        
    pm = PackageManager(project_root=temp_dir)
    installed_pkg = pm.install_local_package(pkg_source)
    assert installed_pkg.name == "com.zennity.v030"
    assert (pm.packages_dir / "com.zennity.v030" / "package.json").exists()

    # 2. Asset Pipeline Setup & Meta generation
    assets_dir = temp_dir / "Assets"
    assets_dir.mkdir(exist_ok=True)
    
    # Create texture dummy and run import
    tex_path = assets_dir / "sprite.png"
    with open(tex_path, "wb") as f:
        f.write(b"fake png data")
        
    db = AssetDatabase(project_root=temp_dir)
    db.scan()
    
    asset_info = db.get_asset_by_path("Assets/sprite.png")
    assert asset_info is not None
    assert Path(f"{tex_path}.meta").exists()

    # 3. Scene Setup with Tilemap, UI, Animation, Audio
    scene = Scene("TestScene")
    
    # Set up Tilemap
    go_tilemap = GameObject("TilemapObj")
    tilemap = go_tilemap.add_component(Tilemap())
    tilemap.width = 10
    tilemap.height = 10
    tilemap.set_tile(0, 0, 0, 1) # Set tile ID 1 at (0, 0) on layer 0
    tilemap_renderer = go_tilemap.add_component(TilemapRenderer())
    
    # Set up UI Canvas + Label + Button
    go_ui = GameObject("UIObj")
    canvas = go_ui.add_component(Canvas())
    label = go_ui.add_component(LabelComponent())
    label.text = "Hello Zennity"
    button = go_ui.add_component(ButtonComponent())
    button.text = "Click me"
    
    # Set up Animation
    go_anim = GameObject("AnimObj")
    animator = go_anim.add_component(Animator())
    clip = AnimationClip(
        "Move",
        frames=[],
        keyframes=[
            Keyframe(time=0.0, property="transform.position.x", value=0.0),
            Keyframe(time=1.0, property="transform.position.x", value=100.0)
        ]
    )
    animator.add_clip(clip)
    animator.play("Move")

    scene.add_game_object(go_tilemap)
    scene.add_game_object(go_ui)
    scene.add_game_object(go_anim)

    # 4. Complete Serialization / Deserialization
    serialized_data = serialize_scene(scene)
    
    # Verify presence of serialized components
    objects = serialized_data.get("objects", [])
    
    tilemap_serialized = False
    ui_serialized = False
    animator_serialized = False
    
    for obj in objects:
        component_section = obj.get("components", {})
        components = component_section.get("items", []) if isinstance(component_section, dict) else []
        for comp in components:
            c_type = comp.get("type")
            properties = comp.get("properties", {})
            if c_type == "Tilemap":
                tilemap_serialized = True
                assert properties.get("width") == 10
            elif c_type == "Label":
                ui_serialized = True
                assert properties.get("text") == "Hello Zennity"
            elif c_type == "Animator":
                animator_serialized = True
                
    assert tilemap_serialized
    assert ui_serialized
    assert animator_serialized

    # Reconstruct scene
    scene_data = deserialize_scene(serialized_data)
    new_scene = Scene(scene_data["scene_name"])
    for obj in scene_data["objects"]:
        new_scene.add_game_object(obj)
    assert len(new_scene.game_objects) == 3

    # 5. Play Mode (Runtime Scene Lifecycle / Execution)
    runtime_manager = RuntimeManager()
    runtime_scene = runtime_manager.start_play(new_scene)
    assert runtime_scene is not None
    
    # Verify fallback camera and listener were created correctly
    runtime_manager.tick(0.1) # Simulate update tick
    
    runtime_manager.stop_play()
