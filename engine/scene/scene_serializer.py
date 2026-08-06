from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from engine.game_object import GameObject
from engine.components.script_component import ScriptComponent
from engine.core.component import Transform
from engine.core.component_registry import component_registry
from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody
from engine.graphics.camera import Camera
from engine.audio import AudioSource
from engine.scene.scene_format import DEFAULT_LAYER, DEFAULT_SCENE_NAME, ENGINE_VERSION, SCENE_FORMAT_VERSION


def _normalize_layer(value: Any) -> str:
    """CONSOLIDATION: 'layer' era gravado/lido como int aqui, mas o editor
    real (editor/scene_persistence.py) sempre grava como string (ex.:
    "Default", "0"). 14 das 15 cenas .zscene reais do projeto usam string --
    `int(data.get("layer", 0))` estourava ValueError sempre que essa
    ferramenta (usada por prefabs/exporter/validator) lia uma cena de
    produção de verdade. Layer agora é sempre string, com fallback seguro
    para qualquer valor recebido (int, string numérica, ou ausente)."""
    if value is None:
        return DEFAULT_LAYER
    return str(value)


def _vector(value: Any, size: int, default: float) -> list[float]:
    if value is None:
        return [default for _ in range(size)]
    values = list(value)
    if len(values) < size:
        values.extend(default for _ in range(size - len(values)))
    return [float(item) for item in values[:size]]


def _get_scene_objects(scene: Any) -> list[Any]:
    objects = getattr(scene, "editable_objects", None)
    if objects is None:
        objects = getattr(scene, "game_objects", [])
    return list(objects)


def _portable_asset_path(value: Any) -> Any:
    if value in (None, ""):
        return value
    path = Path(str(value))
    if not path.is_absolute():
        portable = path.as_posix()
    else:
        try:
            portable = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return str(value)
    parts = Path(portable).parts
    if parts and parts[0].casefold() == "assets":
        return Path("Assets", *parts[1:]).as_posix()
    return portable


def _canonicalize_asset_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonicalize_asset_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonicalize_asset_paths(item) for item in value]
    if isinstance(value, tuple):
        return [_canonicalize_asset_paths(item) for item in value]
    if isinstance(value, str):
        path = Path(value.replace("\\", "/"))
        if path.parts and path.parts[0].casefold() == "assets":
            return _portable_asset_path(value)
    return value


def _component_by_class_name(obj: GameObject, *class_names: str) -> Any:
    names = set(class_names)
    for component in getattr(obj, "components", []):
        if type(component).__name__ in names:
            return component
    return None


def _serialize_collider(obj: GameObject) -> dict[str, Any] | None:
    box = _component_by_class_name(obj, "BoxCollider", "BoxCollider2D")
    if box is not None:
        return {
            "type": "box",
            "width": float(box.width),
            "height": float(box.height),
            "offset": [float(box.offset_x), float(box.offset_y)],
            "is_trigger": bool(box.is_trigger),
            "debug_draw": bool(box.debug_draw),
        }

    circle = _component_by_class_name(obj, "CircleCollider")
    if circle is not None:
        return {
            "type": "circle",
            "radius": float(circle.radius),
            "offset": [float(circle.offset_x), float(circle.offset_y)],
            "is_trigger": bool(circle.is_trigger),
            "debug_draw": bool(circle.debug_draw),
        }

    return None


def _serialize_rigidbody(obj: GameObject) -> dict[str, Any] | None:
    rigidbody = _component_by_class_name(obj, "RigidBody")
    if rigidbody is None:
        return None

    return {
        "mass": float(rigidbody.mass),
        "gravity_scale": float(rigidbody.gravity_scale),
        "drag": float(rigidbody.drag),
        "use_gravity": bool(rigidbody.use_gravity),
        "is_kinematic": bool(rigidbody.is_kinematic),
        "velocity": _vector(rigidbody.velocity, 2, 0.0),
        "acceleration": _vector(rigidbody.acceleration, 2, 0.0),
    }


def _serialize_camera(obj: GameObject) -> dict[str, Any] | None:
    """CONSOLIDATION: o serializer nunca gravava components.camera -- só
    entraria via `items` se Camera tivesse .serialize(). O editor real grava
    camera como chave própria sempre que o objeto tem uma câmera; sem isso,
    salvar uma cena com MainCamera através deste caminho (prefabs/exporter)
    perdia a câmera silenciosamente."""
    camera = _component_by_class_name(obj, "Camera")
    if camera is None:
        return None
    return {
        "zoom": float(getattr(camera, "zoom", 1.0)),
        "background_color": list(getattr(camera, "clear_color", (30, 30, 30))),
        "viewport_rect": list(getattr(camera, "viewport_rect", (0.0, 0.0, 1.0, 1.0))),
        "priority": int(getattr(camera, "priority", 0)),
        "active": bool(getattr(camera, "active", True)),
    }


def _serialize_audio(obj: GameObject) -> dict[str, Any] | None:
    """CONSOLIDATION: mesmo problema do camera -- AudioSource nunca era
    gravado como components.audio por este caminho."""
    audio = _component_by_class_name(obj, "AudioSource")
    if audio is None:
        return None
    return {
        "path": _portable_asset_path(getattr(audio, "audio_clip", "")),
        "volume": float(getattr(audio, "volume", 1.0)),
        "pitch": float(getattr(audio, "pitch", 1.0)),
        "loop": bool(getattr(audio, "loop", False)),
        "autoplay": bool(getattr(audio, "play_on_awake", False)),
        "mute": bool(getattr(audio, "mute", False)),
    }


_DEDICATED_COMPONENT_TYPES = ("BoxCollider", "CircleCollider", "RigidBody", "Camera", "AudioSource")


def _serialize_component_items(obj: GameObject) -> list[dict[str, Any]]:
    """BUG FIX (encontrado ao consolidar): BoxCollider/CircleCollider/
    RigidBody/Camera/AudioSource já são gravados em suas próprias chaves
    dedicadas (components.collider/rigidbody/camera/audio) -- mas este loop
    também os serializava de novo aqui em "items" incondicionalmente, porque
    itera TODOS os componentes com .serialize(). Isso fazia
    deserialize_game_object tentar instanciar o MESMO componente duas vezes
    (uma via items, outra via o dict dedicado), estourando o guard de
    componente UNIQUE (ex.: "BoxCollider é UNIQUE — já existe um no
    GameObject"). Agora "items" só contém componentes SEM tratamento
    dedicado (Animator, Tilemap, UI, etc.)."""
    items: list[dict[str, Any]] = []
    for component in getattr(obj, "components", []):
        if isinstance(component, Transform):
            continue
        if type(component).__name__ in _DEDICATED_COMPONENT_TYPES:
            continue
        if hasattr(component, "serialize"):
            items.append(component.serialize())
    return items


def serialize_game_object(obj: GameObject) -> dict[str, Any]:
    """Serialize one GameObject into .zscene-compatible data."""
    transform = obj.transform
    rotation = _vector(transform.rotation, 3, 0.0)
    components: dict[str, Any] = {"scripts": list(getattr(obj, "scripts", []))}
    component_items = _serialize_component_items(obj)
    if component_items:
        components["items"] = component_items

    collider = _serialize_collider(obj)
    if collider is not None:
        components["collider"] = collider

    rigidbody = _serialize_rigidbody(obj)
    if rigidbody is not None:
        components["rigidbody"] = rigidbody

    camera = _serialize_camera(obj)
    if camera is not None:
        components["camera"] = camera

    audio = _serialize_audio(obj)
    if audio is not None:
        components["audio"] = audio

    object_id = str(getattr(obj, "id", getattr(obj, "uuid", "")))
    prefab_uuid = getattr(obj, "prefab_uuid", None)
    asset_guid = getattr(obj, "asset_guid", getattr(obj, "asset_uuid", None))
    sprite_path = _portable_asset_path(getattr(obj, "sprite_path", None))
    return _canonicalize_asset_paths({
        "id": object_id,
        "uuid": object_id,
        "prefab_uuid": prefab_uuid,
        "name": str(getattr(obj, "name", "GameObject")),
        "tag": str(getattr(obj, "tag", "Untagged")),
        "layer": _normalize_layer(getattr(obj, "layer", None)),
        "static": bool(getattr(obj, "static", False)),
        "active": bool(getattr(obj, "active", True)),
        "enabled": bool(getattr(obj, "enabled", getattr(obj, "active", True))),
        "transform": {
            "position": _vector(transform.position, 3, 0.0),
            "rotation": rotation,
            "rz": float(getattr(transform, "rz", rotation[2])),
            "scale": _vector(transform.scale, 3, 1.0),
        },
        "visual": {
            "mesh_type": getattr(obj, "mesh_type", None),
            "sprite_path": sprite_path,
            # CONSOLIDATION: "texture" é o campo que o editor real e o
            # runtime exportado (engine/build/runtime_scene_loader.py) de
            # fato leem. Gravamos os dois nomes com o mesmo valor: sprite_path
            # por compatibilidade com quem já lê este formato, texture para
            # bater com o resto do projeto.
            "texture": sprite_path or "",
            "asset_guid": asset_guid,
            "asset_uuid": asset_guid,
            "color": getattr(obj, "color", None),
            "material": getattr(obj, "material", "Default_Material"),
            "layer": str(getattr(obj, "render_layer", "Default")),
            "order": int(getattr(obj, "sort_order", 0)),
            "enabled": bool(getattr(obj, "renderer_enabled", True)),
        },
        "components": components,
    })


def serialize_scene(scene: Any) -> dict[str, Any]:
    """Serialize a scene-like object into a JSON-ready dictionary."""
    from engine.scene.scene_document import SceneDocument

    if isinstance(scene, SceneDocument):
        return scene.to_dict()
    blackboard = getattr(scene, "blackboard", None)
    return {
        "format_version": SCENE_FORMAT_VERSION,
        "scene_name": str(getattr(scene, "name", DEFAULT_SCENE_NAME)),
        "engine_version": ENGINE_VERSION,
        "blackboard": dict(blackboard) if isinstance(blackboard, dict) else {"variables": {}},
        "objects": [serialize_game_object(obj) for obj in _get_scene_objects(scene)],
    }


def _deserialize_collider(data: dict[str, Any]) -> BoxCollider | CircleCollider | None:
    collider_type = str(data.get("type", "box")).lower()
    offset = _vector(data.get("offset", [data.get("offset_x", 0.0), data.get("offset_y", 0.0)]), 2, 0.0)

    if collider_type == "circle":
        return CircleCollider(
            radius=float(data.get("radius", 16.0)),
            offset_x=offset[0],
            offset_y=offset[1],
            is_trigger=bool(data.get("is_trigger", False)),
            debug_draw=bool(data.get("debug_draw", False)),
        )

    if collider_type in {"box", "aabb", "rect", "rectangle"}:
        return BoxCollider(
            width=float(data.get("width", 32.0)),
            height=float(data.get("height", 32.0)),
            offset_x=offset[0],
            offset_y=offset[1],
            is_trigger=bool(data.get("is_trigger", False)),
            debug_draw=bool(data.get("debug_draw", False)),
        )

    return None


def _deserialize_rigidbody(data: dict[str, Any]) -> RigidBody:
    rigidbody = RigidBody(
        mass=float(data.get("mass", 1.0)),
        gravity_scale=float(data.get("gravity_scale", 1.0)),
        drag=float(data.get("drag", 0.0)),
        use_gravity=bool(data.get("use_gravity", True)),
        is_kinematic=bool(data.get("is_kinematic", False)),
    )
    rigidbody.velocity = np.array(_vector(data.get("velocity"), 2, 0.0), dtype=np.float32)
    rigidbody.acceleration = np.array(_vector(data.get("acceleration"), 2, 0.0), dtype=np.float32)
    return rigidbody


def _deserialize_camera(data: dict[str, Any]) -> Camera:
    """
    BUG FIX: components.camera (the dict shape written by the real editor,
    editor/scene_persistence.py) had no deserializer at all — a scene's
    MainCamera silently lost its Camera component on load through this path.
    """
    clear_color = data.get("background_color", data.get("clear_color", (30, 30, 30)))
    return Camera(
        zoom=float(data.get("zoom", 1.0)),
        clear_color=tuple(clear_color),
        viewport_rect=tuple(data.get("viewport_rect", (0.0, 0.0, 1.0, 1.0))),
        priority=int(data.get("priority", 0)),
        active=bool(data.get("active", True)),
    )


def _deserialize_audio_source(data: dict[str, Any]) -> AudioSource:
    """
    BUG FIX: components.audio (the dict shape written by the real editor) had
    no deserializer at all. Accepts both the editor's runtime field names
    (path/autoplay) and the older component-item names (audio_clip/
    play_on_awake) for robustness.
    """
    clip = data.get("path", data.get("audio_clip", ""))
    play_on_awake = data.get("autoplay", data.get("play_on_awake", False))
    return AudioSource(
        audio_clip=str(clip),
        volume=float(data.get("volume", 1.0)),
        pitch=float(data.get("pitch", 1.0)),
        loop=bool(data.get("loop", False)),
        play_on_awake=bool(play_on_awake),
        mute=bool(data.get("mute", False)),
    )


def _component_from_item(data: dict[str, Any]) -> Any:
    component = component_registry.create(data)
    return component


def deserialize_game_object(data: dict[str, Any]) -> GameObject:
    """Build a GameObject from .zscene object data."""
    obj = GameObject(
        name=str(data.get("name", "GameObject")),
        tag=str(data.get("tag", "Untagged")),
    )

    object_id = data.get("id") or data.get("uuid")
    if object_id:
        obj._id = str(object_id)

    if "prefab_uuid" in data and data["prefab_uuid"] is not None:
        obj.prefab_uuid = str(data["prefab_uuid"])

    obj.layer = _normalize_layer(data.get("layer"))
    obj.static = bool(data.get("static", False))
    obj.active = bool(data.get("active", data.get("enabled", True)))
    obj.enabled = bool(data.get("enabled", obj.active))

    visual = data.get("visual", {}) or {}
    obj.mesh_type = visual.get("mesh_type")
    # CONSOLIDATION: aceita "sprite_path" (nome usado por este módulo/prefabs)
    # OU "texture" (nome usado pelo editor real e pelo runtime exportado) --
    # qualquer um dos dois formatos reais de cena carrega normalmente agora.
    obj.sprite_path = visual.get("sprite_path") or visual.get("texture") or None
    asset_guid = visual.get("asset_guid") or visual.get("asset_uuid")
    if asset_guid is not None:
        obj.asset_guid = asset_guid
        obj.asset_uuid = asset_guid
    if visual.get("color") is not None:
        obj.color = visual.get("color")
    obj.material = visual.get("material", "Default_Material")
    obj.render_layer = str(visual.get("layer", "Default"))
    obj.sort_order = int(visual.get("order", 0))
    obj.renderer_enabled = bool(visual.get("enabled", True))

    transform = data.get("transform", {}) or {}
    obj.transform.position = np.array(_vector(transform.get("position"), 3, 0.0), dtype=np.float32)
    rotation = _vector(transform.get("rotation"), 3, 0.0)
    if "rz" in transform:
        rotation[2] = float(transform["rz"])
    obj.transform.rotation = np.array(rotation, dtype=np.float32)
    obj.transform.scale = np.array(_vector(transform.get("scale"), 3, 1.0), dtype=np.float32)

    components = data.get("components", {}) or {}

    # BUG FIX: this used to be `if items: ... else: collider/rigidbody`, as if
    # a GameObject could only ever be described one way or the other. But the
    # real editor (editor/scene_persistence.py) always writes collider/
    # rigidbody/camera/audio as their own sibling dict keys *and* writes
    # "items" whenever the object also has a UI element — so any real scene
    # with, say, a Player that has both a BoxCollider and a UI Label on it
    # (or simply any object saved by the actual editor) silently lost its
    # collider/rigidbody/camera/audio on load through this path. Both forms
    # are independent and must both be applied.
    component_items = components.get("items")
    if isinstance(component_items, list):
        for item in component_items:
            if isinstance(item, dict):
                component = _component_from_item(item)
                if not isinstance(component, Transform):
                    obj.add_component(component)

    collider_data = components.get("collider")
    if isinstance(collider_data, dict):
        collider = _deserialize_collider(collider_data)
        if collider is not None:
            obj.add_component(collider)

    rigidbody_data = components.get("rigidbody")
    if isinstance(rigidbody_data, dict):
        obj.add_component(_deserialize_rigidbody(rigidbody_data))

    camera_data = components.get("camera")
    if isinstance(camera_data, dict):
        obj.add_component(_deserialize_camera(camera_data))

    audio_data = components.get("audio")
    if isinstance(audio_data, dict):
        obj.add_component(_deserialize_audio_source(audio_data))

    scripts = components.get("scripts")
    if isinstance(scripts, list):
        obj.scripts = list(scripts)
        for script in scripts:
            obj.add_component(ScriptComponent(str(script)))

    # CONSOLIDATION: "editor_data" (animator/behavior/logic_assets, etc.) era
    # completamente ignorado aqui -- qualquer objeto vindo de uma cena salva
    # pelo editor real perdia essas referências ao passar por este loader
    # (usado por prefabs/exporter/validator/testes). Preserva como está, sem
    # tentar interpretar -- quem precisar (behavior/animator/logic runtime)
    # já sabe ler esse dict.
    editor_data = data.get("editor_data")
    if isinstance(editor_data, dict):
        obj.editor_data = dict(editor_data)

    # FIX: Reconstrói hierarquia parent-child
    children_data = data.get("children", [])
    if isinstance(children_data, list):
        for child_data in children_data:
            if isinstance(child_data, dict):
                child = deserialize_game_object(child_data)
                obj.add_child(child)

    return obj


def deserialize_scene(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize .zscene data into a scene data model."""
    # CONSOLIDATION: "blackboard" (variáveis de cena usadas pelos Logic
    # Graphs) era completamente descartado aqui. Preservado no resultado
    # para quem passar por este caminho em vez de load_scene_document.
    blackboard = data.get("blackboard")
    return {
        "format_version": int(data.get("format_version", SCENE_FORMAT_VERSION)),
        "scene_name": str(data.get("scene_name", DEFAULT_SCENE_NAME)),
        "engine_version": str(data.get("engine_version", ENGINE_VERSION)),
        "blackboard": dict(blackboard) if isinstance(blackboard, dict) else {"variables": {}},
        "objects": [
            deserialize_game_object(item)
            for item in data.get("objects", [])
            if isinstance(item, dict)
        ],
    }


def save_scene(scene: Any, path: str | Path) -> Path:
    """Save a scene-like object as a .zscene JSON file."""
    from engine.scene.scene_document import SceneDocument

    return SceneDocument.from_dict(serialize_scene(scene)).save(path)
