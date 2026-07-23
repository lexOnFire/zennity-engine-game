from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt

from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.graphics.camera2d import Camera2D
from editor.widgets.create_dock import CreateDock


_2D_PRESETS = {
    "Sprite 2D": "Quadrado",
    "Player": "Player",
    "Plataforma": "Plataforma",
    "Inimigo": "Inimigo",
    "Enemy": "Inimigo",
    "Platform": "Plataforma",
}

_3D_PRESETS = {
    "Cube 3D": "Cube",
    "Plane 3D": "Plane",
    "Camera 3D": "Camera",
    "Light 3D": "Light",
}


def install_editor_mvp(window) -> None:
    """Instala recursos MVP no editor sem acoplar na MainWindow.

    Esta função é chamada depois que a janela principal já criou Viewport,
    Hierarchy e Inspector. Assim conseguimos evoluir o editor com baixo risco.
    """
    if hasattr(window, "dock_create"):
        return

    dock = CreateDock(window)
    window.dock_create = dock
    window.addDockWidget(Qt.LeftDockWidgetArea, dock)
    window.splitDockWidget(window.dock_hierarchy, dock, Qt.Vertical)

    dock.create_requested.connect(lambda preset: _create_preset(window, preset))
    dock.template_requested.connect(lambda template: _create_template(window, template))

    if hasattr(window, "menuBar"):
        menu = window.menuBar().addMenu("Criar MVP")
        menu.addAction(dock.toggleViewAction())

    _set_status(window, "MVP de criação 2D/3D carregado")


def _set_status(window, message: str) -> None:
    if hasattr(window, "statusBar"):
        window.statusBar().showMessage(message, 4000)
    if hasattr(window, "log_action"):
        window.log_action(message)


def _sync(window) -> None:
    viewport = getattr(window, "viewport", None)
    if viewport and hasattr(viewport, "_sync_model_from_scene"):
        viewport._sync_model_from_scene()
        viewport.update()
    if hasattr(window, "update_object_count_status"):
        window.update_object_count_status()


def _scene(window):
    viewport = getattr(window, "viewport", None)
    return getattr(viewport, "active_scene", None)


def _center_2d(scene) -> np.ndarray:
    try:
        lay = scene._layout()
        return scene._vp_to_world(
            lay["vp_left"] + lay["vp_w"] / 2,
            lay["vp_top"] + lay["vp_h"] / 2,
            lay,
        )
    except Exception:
        return np.array([400.0, 300.0, 0.0], dtype=np.float32)


def _select_last(scene) -> None:
    if getattr(scene, "editable_objects", None):
        scene.selected_index = len(scene.editable_objects) - 1


def _add_2d_go(scene, go: GameObject) -> None:
    if hasattr(scene, "_add_go"):
        scene._add_go(go)
    elif go not in scene.game_objects:
        scene.game_objects.append(go)
    scene.editable_objects.append(go)
    _select_last(scene)


def _create_empty_2d(window) -> None:
    scene = _scene(window)
    if not scene:
        return
    go = GameObject(f"Empty_{len(scene.editable_objects)}")
    go.transform.position = _center_2d(scene)
    go.transform.scale = np.array([32.0, 32.0, 1.0], dtype=np.float32)
    go.mesh_type = "Empty"
    _add_2d_go(scene, go)
    _sync(window)
    _set_status(window, "Empty Object criado")


def _create_camera_2d(window) -> None:
    scene = _scene(window)
    if not scene:
        return
    go = GameObject(f"Camera2D_{len(scene.editable_objects)}")
    go.transform.position = _center_2d(scene)
    go.transform.scale = np.array([64.0, 40.0, 1.0], dtype=np.float32)
    cam = go.add_component(Camera2D(zoom=1.0))
    Camera2D.main = cam
    go.mesh_type = "Camera 2D"
    _add_2d_go(scene, go)
    _sync(window)
    _set_status(window, "Camera 2D criada")


def _create_preset(window, preset: str) -> None:
    viewport = getattr(window, "viewport", None)
    scene = _scene(window)
    if not viewport or not scene:
        return

    if preset == "Empty Object":
        _create_empty_2d(window)
        return
    if preset == "Camera 2D":
        _create_camera_2d(window)
        return

    if preset in _2D_PRESETS:
        if getattr(viewport, "editor_mode", "2D") != "2D":
            viewport.change_editor_mode("2D")
            scene = _scene(window)
        scene.spawn_object(_2D_PRESETS[preset])
        _sync(window)
        _set_status(window, f"{preset} criado")
        return

    if preset in _3D_PRESETS:
        _set_status(window, "3D experimental: criando preset básico")
        if getattr(viewport, "editor_mode", "2D") != "3D":
            viewport.change_editor_mode("3D")
            scene = _scene(window)
        if hasattr(scene, "spawn_object"):
            scene.spawn_object(_3D_PRESETS[preset])
            _sync(window)
        return


def _clear_editable(scene) -> None:
    for obj in list(getattr(scene, "editable_objects", [])):
        if hasattr(scene, "_remove_go"):
            scene._remove_go(obj)
        elif obj in scene.game_objects:
            scene.game_objects.remove(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1


def _create_template(window, template: str) -> None:
    viewport = getattr(window, "viewport", None)
    if not viewport:
        return
    if getattr(viewport, "editor_mode", "2D") != "2D":
        viewport.change_editor_mode("2D")
    scene = _scene(window)
    if not scene:
        return

    _clear_editable(scene)

    if template == "template_platformer_2d":
        scene.spawn_default_scene()
        scene.spawn_object("Inimigo")
        if scene.editable_objects:
            scene.editable_objects[-1].transform.position = np.array([620.0, 455.0, 0.0], dtype=np.float32)
        _set_status(window, "Template Plataforma 2D criado")
    elif template == "template_topdown_2d":
        _create_topdown_scene(scene)
        _set_status(window, "Template Top-down 2D criado")

    _sync(window)


def _create_topdown_scene(scene) -> None:
    player = GameObject("Player_TopDown")
    player.transform.position = np.array([400.0, 300.0, 0.0], dtype=np.float32)
    player.transform.scale = np.array([36.0, 36.0, 1.0], dtype=np.float32)
    player.add_component(BoxCollider(width=36, height=36))
    player.add_component(RigidBody(mass=1.0, gravity_scale=0.0))
    player.mesh_type = "Player"
    _add_2d_go(scene, player)

    for i, pos in enumerate(([250.0, 220.0, 0.0], [560.0, 380.0, 0.0])):
        enemy = GameObject(f"Enemy_{i + 1}")
        enemy.transform.position = np.array(pos, dtype=np.float32)
        enemy.transform.scale = np.array([34.0, 34.0, 1.0], dtype=np.float32)
        enemy.add_component(BoxCollider(width=34, height=34))
        enemy.add_component(RigidBody(mass=1.0, gravity_scale=0.0))
        enemy.mesh_type = "Inimigo"
        _add_2d_go(scene, enemy)

    for i, pos in enumerate(([400.0, 120.0, 0.0], [400.0, 500.0, 0.0], [160.0, 300.0, 0.0], [640.0, 300.0, 0.0])):
        wall = GameObject(f"Wall_{i + 1}")
        wall.transform.position = np.array(pos, dtype=np.float32)
        wall.transform.scale = np.array([320.0 if i < 2 else 24.0, 24.0 if i < 2 else 260.0, 1.0], dtype=np.float32)
        wall.add_component(BoxCollider(width=int(wall.transform.scale[0]), height=int(wall.transform.scale[1])))
        rb = wall.add_component(RigidBody())
        rb.is_kinematic = True
        wall.mesh_type = "Plataforma"
        _add_2d_go(scene, wall)

    scene.selected_index = 0
