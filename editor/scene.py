"""
Cena principal do editor 3D da Zennity Engine.
Melhorias nesta versão:
  - Undo/Redo (Ctrl+Z / Ctrl+Shift+Z)
  - PhysicsSim integrado com RigidBody3D da engine
  - MOUSEWHEEL correto (pygame.MOUSEWHEEL)
  - Snap de grade configurável (tecla G)
  - Barra de status mostra contagem do histórico
"""
from __future__ import annotations
import os
import json
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import pygame

from engine.core import Scene
from engine.game_object import GameObject
from engine.assets import Assets
from engine.graphics.renderer3d import Camera3D, MeshRenderer3D
from engine.graphics.math3d import project_vertices

from .gui import GuiButton
from .mesh_factory import create_pyramid_mesh, create_sphere_mesh
from .camera_controller import OrbitCameraController
from .physics_sim import PhysicsSim
from .script_manager import ScriptManager
from .code_editor import CodeEditor
from .history import History

_IDENTITY = np.eye(4, dtype=np.float32)

# ---------------------------------------------------------------------------
def _point_in_polygon(x: float, y: float, poly: List[Tuple[int, int]]) -> bool:
    n = len(poly)
    if n < 3:
        return False
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xints:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


COLOR_PALETTE = [
    (200, 200, 200), (220, 50, 50), (50, 170, 50),
    (50, 100, 220),  (240, 200, 0), (200, 50, 200),
]

HELP_LINES = [
    "Atalhos de teclado:",
    "  Ctrl+Z           Desfazer (Undo)",
    "  Ctrl+Shift+Z     Refazer (Redo)",
    "  Ctrl+D           Clonar objeto selecionado",
    "  Delete           Excluir objeto selecionado",
    "  G                Ativar/desativar snap de grade (0.5)",
    "  Scroll Mouse     Zoom da câmera",
    "  Botão Direito    Orbitar câmera",
    "",
    "Scripts de comportamento (start / update):",
    "  from engine.input import Input; import pygame",
    "  if Input.get_key(pygame.K_d): obj.transform.position[0] += 2.0 * dt",
    "",
    "  Pulo com RigidBody3D:",
    "  from engine.physics.rigidbody3d import RigidBody3D",
    "  rb = obj.get_component(RigidBody3D)",
    "  if rb and Input.get_key_down(pygame.K_SPACE): rb.add_impulse(0, 5, 0)",
    "",
    "  Rotação contínua:",
    "  obj.transform.rotation[1] = (obj.transform.rotation[1] + 45*dt) % 360",
]

SNAP_SIZE: float = 0.5


class EditorScene(Scene):

    # -----------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        self.font_title = self.font_body = self.font_btn = self.font_xyz = None

        self.camera_comp: Optional[Camera3D] = None
        self.camera_controller: Optional[OrbitCameraController] = None

        self.gizmo_mode: Optional[str] = "translate"
        self.is_dragging_gizmo = False
        self.active_gizmo_axis: Optional[str] = None
        self.gizmo_drag_last_mouse: Tuple[int, int] = (0, 0)
        self.gizmo_screen_points: Dict[str, Tuple[int, int]] = {}
        self.gizmo_screen_center: Optional[Tuple[int, int]] = None
        self.gizmo_ex = self.gizmo_ey = self.gizmo_ez = None

        self.is_dragging_object = False
        self.drag_object_last_mouse: Tuple[int, int] = (0, 0)
        self.click_start_pos: Optional[Tuple[int, int]] = None

        self.play_mode = False
        self.saved_scene_state: Optional[List[Dict[str, Any]]] = None

        self.light_angle: float = 45.0
        self.available_scripts: List[str] = ["Nenhum"]

        self.code_editor = CodeEditor()
        self.showing_help_modal = False

        self.cube_count = self.pyramid_count = self.sphere_count = 0

        # Undo/Redo
        self.history = History()

        # Snap de grade
        self.snap_enabled: bool = False

    # -----------------------------------------------------------------------
    def start(self) -> None:
        print("[EditorScene] Iniciando editor 3D...")
        self.font_title = Assets.get_font(None, 18)
        self.font_body  = Assets.get_font(None, 15)
        self.font_btn   = Assets.get_font(None, 14)
        self.font_xyz   = Assets.get_font(None, 16)

        self.available_scripts = ScriptManager.list_scripts()

        # --- Painel esquerdo ---
        self.btn_add_cube     = GuiButton(15,  45, 62, 26, "+ Cubo",  bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_pyramid  = GuiButton(82,  45, 62, 26, "+ Pirâm", bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_sphere   = GuiButton(149, 45, 62, 26, "+ Esf",   bg_color=(40,100,60),  hover_color=(50,130,80))

        self.btn_mode_translate = GuiButton(15,  80, 62, 26, "Mover",   bg_color=(80,60,120),  hover_color=(100,80,150))
        self.btn_mode_rotate    = GuiButton(82,  80, 62, 26, "Girar",   bg_color=(80,60,120),  hover_color=(100,80,150))
        self.btn_mode_scale     = GuiButton(149, 80, 62, 26, "Escalar", bg_color=(80,60,120),  hover_color=(100,80,150))

        self.btn_snap    = GuiButton(15, 115, 200, 22, "Grade: OFF", bg_color=(55,58,68), hover_color=(70,75,88))
        self.btn_undo    = GuiButton(15, 300, 95,  26, "↩ Desfazer", bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_redo    = GuiButton(120,300, 95,  26, "Refazer ↪", bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_delete  = GuiButton(15, 330, 200, 26, "Excluir Objeto", bg_color=(140,40,40), hover_color=(175,50,50))

        self.btn_light_angle_dec = GuiButton(15,  380, 40, 22, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_light_angle_inc = GuiButton(165, 380, 40, 22, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        # --- Barra superior ---
        self.btn_play_pause = GuiButton(245, 15, 80, 26, "PLAY",     bg_color=(40,120,60),  hover_color=(50,150,80))
        self.btn_save       = GuiButton(335, 15, 70, 26, "Salvar",   bg_color=(100,70,40),  hover_color=(130,90,50))
        self.btn_load       = GuiButton(415, 15, 70, 26, "Carregar", bg_color=(100,70,40),  hover_color=(130,90,50))

        # --- Inspetor direito ---
        self.btn_toggle_static  = GuiButton(785, 50,  20, 20, "", bg_color=(45,49,58), hover_color=(70,76,90))
        self.btn_toggle_physics = GuiButton(785, 80,  20, 20, "", bg_color=(45,49,58), hover_color=(70,76,90))
        self.btn_vel_dec        = GuiButton(785, 135, 40, 20, " - ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_vel_inc        = GuiButton(915, 135, 40, 20, " + ", bg_color=(60,65,78), hover_color=(75,80,95))

        self.btn_prev_script     = GuiButton(785, 190, 30, 22, " < ",              bg_color=(60,65,78),  hover_color=(75,80,95))
        self.btn_next_script     = GuiButton(945, 190, 30, 22, " > ",              bg_color=(60,65,78),  hover_color=(75,80,95))
        self.btn_new_script      = GuiButton(785, 215, 190,20, "+ Novo Script",    bg_color=(40,100,60), hover_color=(50,130,80))
        self.btn_edit_script     = GuiButton(785, 238, 93, 20, "Editor Ext.",      bg_color=(0,100,160), hover_color=(0,130,200))
        self.btn_internal_editor = GuiButton(882, 238, 93, 20, "Editor Int.",      bg_color=(0,100,160), hover_color=(0,130,200))
        self.btn_script_help     = GuiButton(785, 261, 190,20, "Guia de Comandos", bg_color=(120,80,40), hover_color=(150,100,50))
        self.btn_clone           = GuiButton(785, 352, 190,26, "Clonar Objeto",    bg_color=(80,60,120), hover_color=(100,75,150))

        self.btn_colors = [
            GuiButton(785 + i * 32, 312, 24, 24, "", bg_color=c, hover_color=c)
            for i, c in enumerate(COLOR_PALETTE)
        ]

        # --- Câmera ---
        cam_obj = GameObject("EditorCamera")
        self.camera_comp = cam_obj.add_component(Camera3D(
            fov=60.0, near=0.1, far=100.0,
            viewport_x=230.0, viewport_y=0.0,
            viewport_width=540.0, viewport_height=600.0,
        ))
        self.camera_controller = cam_obj.add_component(OrbitCameraController())
        self._add_go(cam_obj)

        self.spawn_object("Cube")

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        go._propagate_scene(self)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)

    def _snap(self, v: np.ndarray) -> np.ndarray:
        if self.snap_enabled:
            return np.round(v / SNAP_SIZE) * SNAP_SIZE
        return v

    # -----------------------------------------------------------------------
    # Spawn / Delete / Clone
    # -----------------------------------------------------------------------
    def spawn_object(self, shape: str) -> None:
        self.history.push(self)
        go = GameObject()
        go.transform.position = np.array([0.0, 0.0, 1.5], dtype=np.float32)
        go.mesh_type          = shape
        go.is_static          = False
        go.use_physics        = True
        go.initial_velocity_y = 0.0
        go.script_path        = ""
        if shape == "Cube":
            self.cube_count += 1
            go.name = f"Bloco_{self.cube_count}"
            go.add_component(MeshRenderer3D(Assets.create_cube_mesh(1.0), color=(0, 110, 220)))
        elif shape == "Pyramid":
            self.pyramid_count += 1
            go.name = f"Piramide_{self.pyramid_count}"
            go.add_component(MeshRenderer3D(create_pyramid_mesh(1.0), color=(220, 60, 20)))
        elif shape == "Sphere":
            self.sphere_count += 1
            go.name = f"Bolinha_{self.sphere_count}"
            go.add_component(MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=(100, 40, 180)))
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1

    def delete_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self.history.push(self)
        go = self.editable_objects.pop(self.selected_index)
        self._remove_go(go)
        go.destroy()
        self.selected_index = -1 if not self.editable_objects else max(0, self.selected_index - 1)

    def clone_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self.history.push(self)
        src = self.editable_objects[self.selected_index]
        go = GameObject()
        go.mesh_type          = getattr(src, "mesh_type", "Cube")
        go.name               = src.name + "_Clone"
        go.is_static          = getattr(src, "is_static", False)
        go.use_physics        = getattr(src, "use_physics", True)
        go.initial_velocity_y = getattr(src, "initial_velocity_y", 0.0)
        go.script_path        = getattr(src, "script_path", "")
        go.transform.position = src.transform.position + np.array([0.5, 0.0, 0.5], np.float32)
        go.transform.rotation = src.transform.rotation.copy()
        go.transform.scale    = src.transform.scale.copy()
        renderer = src.get_component(MeshRenderer3D)
        color    = renderer.color if renderer else (200, 200, 200)
        if go.mesh_type == "Cube":
            go.add_component(MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color))
        elif go.mesh_type == "Pyramid":
            go.add_component(MeshRenderer3D(create_pyramid_mesh(1.0), color=color))
        elif go.mesh_type == "Sphere":
            go.add_component(MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=color))
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1

    # -----------------------------------------------------------------------
    # Save / Load
    # -----------------------------------------------------------------------
    def save_scene(self) -> None:
        data = {"objects": []}
        for obj in self.editable_objects:
            r = obj.get_component(MeshRenderer3D)
            data["objects"].append({
                "name":               obj.name,
                "shape":              getattr(obj, "mesh_type", "Cube"),
                "position":           obj.transform.position.tolist(),
                "rotation":           obj.transform.rotation.tolist(),
                "scale":              obj.transform.scale.tolist(),
                "color":              list(r.color) if r else [200, 200, 200],
                "is_static":          getattr(obj, "is_static", False),
                "use_physics":        getattr(obj, "use_physics", True),
                "initial_velocity_y": getattr(obj, "initial_velocity_y", 0.0),
                "script_path":        getattr(obj, "script_path", ""),
            })
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            print("[EditorScene] Cena salva.")
        except Exception as e:
            print(f"[EditorScene] Erro ao salvar: {e}")

    def load_scene(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        if not os.path.exists(path):
            print("[EditorScene] Nenhuma cena salva."); return
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            print(f"[EditorScene] Erro: {e}"); return
        self.history.push(self)
        for obj in list(self.editable_objects):
            self._remove_go(obj); obj.destroy()
        self.editable_objects.clear()
        self.selected_index = -1
        self.cube_count = self.pyramid_count = self.sphere_count = 0
        for item in data.get("objects", []):
            go = GameObject()
            go.name               = item["name"]
            go.transform.position = np.array(item["position"], np.float32)
            go.transform.rotation = np.array(item["rotation"], np.float32)
            go.transform.scale    = np.array(item["scale"],    np.float32)
            go.mesh_type          = item.get("shape", "Cube")
            go.is_static          = item.get("is_static", False)
            go.use_physics        = item.get("use_physics", True)
            go.initial_velocity_y = item.get("initial_velocity_y", 0.0)
            go.script_path        = item.get("script_path", "")
            color = tuple(item["color"])
            if go.mesh_type == "Cube":
                self.cube_count += 1
                go.add_component(MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color))
            elif go.mesh_type == "Pyramid":
                self.pyramid_count += 1
                go.add_component(MeshRenderer3D(create_pyramid_mesh(1.0), color=color))
            elif go.mesh_type == "Sphere":
                self.sphere_count += 1
                go.add_component(MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=color))
            self._add_go(go)
            self.editable_objects.append(go)
        if self.editable_objects:
            self.selected_index = len(self.editable_objects) - 1
        print("[EditorScene] Cena carregada.")

    # -----------------------------------------------------------------------
    # Seleção por ray-cast 2D
    # -----------------------------------------------------------------------
    def _select_at(self, mx: int, my: int) -> None:
        best_idx, best_depth = -1, float("inf")
        for idx, obj in enumerate(self.editable_objects):
            r = obj.get_component(MeshRenderer3D)
            if r and r.last_screen_coords is not None:
                for face in r.mesh.faces:
                    poly = [tuple(r.last_screen_coords[vi]) for vi in face]
                    if _point_in_polygon(mx, my, poly):
                        cam_z = -(self.camera_comp.view_matrix @ np.append(obj.transform.position, 1.0))[2]
                        if cam_z < best_depth:
                            best_depth, best_idx = cam_z, idx
        if best_idx != -1:
            self.selected_index = best_idx

    # -----------------------------------------------------------------------
    # Grid
    # -----------------------------------------------------------------------
    def _draw_floor_grid(self, screen: pygame.Surface) -> None:
        verts = []
        for x in range(-5, 6): verts += [[x,-0.5,-5.0],[x,-0.5,5.0]]
        for z in range(-5, 6): verts += [[-5.0,-0.5,z],[5.0,-0.5,z]]
        verts = np.array(verts, np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
        vw, vh = self.camera_comp.viewport_width, self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x, self.camera_comp.viewport_y
        sx = vx + (ndc[:,0]+1)*vw/2
        sy = vy + (-ndc[:,1]+1)*vh/2
        near = self.camera_comp.near
        for i in range(0, len(verts), 2):
            if depths[i] > near and depths[i+1] > near:
                p0 = (int(sx[i]),   int(sy[i]))
                p1 = (int(sx[i+1]), int(sy[i+1]))
                center = (abs(verts[i][0])<0.01 and abs(verts[i][2]-verts[i+1][2])>0.01) or \
                         (abs(verts[i][2])<0.01 and abs(verts[i][0]-verts[i+1][0])>0.01)
                pygame.draw.line(screen, (170,175,185) if center else (220,222,226), p0, p1, 2 if center else 1)

    # -----------------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.play_mode:
            for obj in self.editable_objects:
                ScriptManager.update(obj, dt)
            PhysicsSim.step(self.editable_objects, dt)
        elif self.is_dragging_gizmo and 0 <= self.selected_index < len(self.editable_objects):
            sel = self.editable_objects[self.selected_index]
            mp  = pygame.mouse.get_pos()
            dx  = mp[0] - self.gizmo_drag_last_mouse[0]
            dy  = mp[1] - self.gizmo_drag_last_mouse[1]
            self.gizmo_drag_last_mouse = mp
            if self.gizmo_mode == "translate":
                if   self.active_gizmo_axis == 'x': sel.transform.position[0] += dx * 0.015
                elif self.active_gizmo_axis == 'y': sel.transform.position[1] -= dy * 0.015
                elif self.active_gizmo_axis == 'z': sel.transform.position[2] -= dy * 0.015
                sel.transform.position = self._snap(sel.transform.position)
            elif self.gizmo_mode == "scale":
                if   self.active_gizmo_axis == 'x': sel.transform.scale[0] = max(0.1, sel.transform.scale[0]+dx*0.015)
                elif self.active_gizmo_axis == 'y': sel.transform.scale[1] = max(0.1, sel.transform.scale[1]-dy*0.015)
                elif self.active_gizmo_axis == 'z': sel.transform.scale[2] = max(0.1, sel.transform.scale[2]-dy*0.015)
                elif self.active_gizmo_axis == 'center':
                    ns = max(0.1, sel.transform.scale[0]+(dx-dy)*0.015)
                    sel.transform.scale = np.array([ns,ns,ns], np.float32)
            elif self.gizmo_mode == "rotate":
                if   self.active_gizmo_axis == 'x': sel.transform.rotation[0] = (sel.transform.rotation[0]+dy*0.5)%360
                elif self.active_gizmo_axis == 'y': sel.transform.rotation[1] = (sel.transform.rotation[1]+dx*0.5)%360
                elif self.active_gizmo_axis == 'z': sel.transform.rotation[2] = (sel.transform.rotation[2]+dx*0.5)%360
        else:
            if not pygame.mouse.get_pressed()[0]:
                self.is_dragging_gizmo = False
                self.active_gizmo_axis = None
            if self.is_dragging_object and 0 <= self.selected_index < len(self.editable_objects):
                sel = self.editable_objects[self.selected_index]
                mp  = pygame.mouse.get_pos()
                dx  = mp[0] - self.drag_object_last_mouse[0]
                dy  = mp[1] - self.drag_object_last_mouse[1]
                self.drag_object_last_mouse = mp
                yr  = np.radians(self.camera_controller.yaw)
                pr  = np.radians(self.camera_controller.pitch)
                right = np.array([np.cos(yr),0.0,-np.sin(yr)], np.float32)
                up    = np.array([np.sin(pr)*np.sin(yr),np.cos(pr),np.sin(pr)*np.cos(yr)], np.float32)
                keys  = pygame.key.get_pressed()
                if keys[pygame.K_x]:
                    sel.transform.position -= up    * (dy * 0.015)
                    sel.transform.position  = self._snap(sel.transform.position)
                elif keys[pygame.K_z]:
                    sel.transform.position += right * (dx * 0.015)
                    sel.transform.position  = self._snap(sel.transform.position)
            elif not pygame.mouse.get_pressed()[0]:
                self.is_dragging_object = False
        for go in self.game_objects:
            go.update(dt)

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (255,255,255), (250,0,550,600))
        self._draw_floor_grid(screen)
        for go in self.game_objects:
            go.draw(screen)
            if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                r = go.get_component(MeshRenderer3D)
                if r:
                    ow,oc,olw = r.wireframe, r.color, r.line_width
                    r.wireframe, r.color, r.line_width = True, (255,0,0), 3
                    r.draw(screen)
                    r.wireframe, r.color, r.line_width = ow, oc, olw
        self._draw_gizmo(screen)
        self._draw_left_panel(screen)
        self._draw_top_bar(screen)
        self._draw_right_panel(screen)
        self._draw_xyz_widget(screen)
        if self.code_editor.is_open:
            self.code_editor.draw(screen)
        elif self.showing_help_modal:
            self._draw_help_modal(screen)

    # -----------------------------------------------------------------------
    # Draw helpers
    # -----------------------------------------------------------------------
    def _draw_gizmo(self, screen: pygame.Surface) -> None:
        if self.selected_index < 0 or self.play_mode or not self.gizmo_mode:
            return
        sel = self.editable_objects[self.selected_index]
        P   = sel.transform.position
        ext = 1.2
        ex  = P + np.array([ext, 0.0, 0.0], np.float32)
        ey  = P + np.array([0.0, ext, 0.0], np.float32)
        ez  = P + np.array([0.0, 0.0, ext], np.float32)
        verts = np.array([P, ex, ey, ez], np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
        near = self.camera_comp.near
        if not all(d > near for d in depths):
            return
        vw, vh = self.camera_comp.viewport_width, self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x, self.camera_comp.viewport_y
        def ts(i): return int(vx+(ndc[i,0]+1)*vw/2), int(vy+(-ndc[i,1]+1)*vh/2)
        c, px, py, pz = ts(0), ts(1), ts(2), ts(3)
        self.gizmo_screen_points  = {'x': px, 'y': py, 'z': pz}
        self.gizmo_screen_center  = c
        if self.gizmo_mode == "rotate":
            for pts_fn, col in [
                (lambda t: P+np.array([0.8*np.cos(t),0,0.8*np.sin(t)],np.float32), (50,170,50)),
                (lambda t: P+np.array([0,0.8*np.cos(t),0.8*np.sin(t)],np.float32), (220,50,50)),
                (lambda t: P+np.array([0.8*np.cos(t),0.8*np.sin(t),0],np.float32), (50,100,220)),
            ]:
                ring = np.array([pts_fn(t) for t in np.linspace(0,2*np.pi,20)], np.float32)
                rn, rd = project_vertices(ring, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                pts = [(int(vx+(rn[k,0]+1)*vw/2), int(vy+(-rn[k,1]+1)*vh/2)) for k in range(len(ring)) if rd[k]>near]
                if len(pts)>1: pygame.draw.lines(screen, col, True, pts, 1)
        else:
            pygame.draw.line(screen,(220,50,50), c,px,3)
            pygame.draw.line(screen,(50,170,50), c,py,3)
            pygame.draw.line(screen,(50,100,220),c,pz,3)
            if self.gizmo_mode == "translate":
                for pt,col in [(px,(220,50,50)),(py,(50,170,50)),(pz,(50,100,220))]:
                    pygame.draw.circle(screen,col,pt,7)
            elif self.gizmo_mode == "scale":
                for pt,col in [(px,(220,50,50)),(py,(50,170,50)),(pz,(50,100,220))]:
                    pygame.draw.rect(screen,col,(pt[0]-6,pt[1]-6,12,12))
                pygame.draw.circle(screen,(240,200,0),c,6)

    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen,(38,42,50),(0,0,230,600))
        pygame.draw.line(screen,(55,60,72),(230,0),(230,600),2)
        screen.blit(self.font_title.render("ADICIONAR FORMAS",True,(0,200,255)),(15,18))
        for btn in [self.btn_add_cube,self.btn_add_pyramid,self.btn_add_sphere]:
            btn.draw(screen,self.font_btn)
        for btn,mode in [(self.btn_mode_translate,"translate"),(self.btn_mode_rotate,"rotate"),(self.btn_mode_scale,"scale")]:
            btn.bg_color = (0,150,220) if self.gizmo_mode==mode else (80,60,120)
            btn.draw(screen,self.font_btn)
        self.btn_snap.text     = f"Grade: {'ON (G)' if self.snap_enabled else 'OFF (G)'}"
        self.btn_snap.bg_color = (0,130,80) if self.snap_enabled else (55,58,68)
        self.btn_snap.draw(screen, self.font_btn)
        screen.blit(self.font_title.render("OBJETOS DA CENA",True,(0,200,255)),(15,145))
        y = 168
        for obj in self.editable_objects[-5:]:
            idx = self.editable_objects.index(obj)
            sel = idx == self.selected_index
            slot = pygame.Rect(15,y,200,22)
            pygame.draw.rect(screen,(60,80,110) if sel else (45,49,58),slot,border_radius=3)
            pygame.draw.rect(screen,(0,200,255) if sel else (70,76,90),slot,1,border_radius=3)
            screen.blit(self.font_body.render(obj.name,True,(255,255,255)),(25,y+4))
            y+=26
        self.btn_undo.bg_color = (60,80,110) if self.history.can_undo else (45,49,58)
        self.btn_redo.bg_color = (60,80,110) if self.history.can_redo else (45,49,58)
        self.btn_undo.draw(screen,self.font_btn)
        self.btn_redo.draw(screen,self.font_btn)
        if 0 <= self.selected_index < len(self.editable_objects):
            self.btn_delete.draw(screen,self.font_btn)
        screen.blit(self.font_title.render("DIREÇÃO DA LUZ",True,(0,200,255)),(15,358))
        self.btn_light_angle_dec.draw(screen,self.font_btn)
        screen.blit(self.font_body.render(f"Sol: {int(self.light_angle)}°",True,(255,255,255)),(65,382))
        self.btn_light_angle_inc.draw(screen,self.font_btn)

    def _draw_top_bar(self, screen: pygame.Surface) -> None:
        self.btn_play_pause.bg_color    = (180,40,40) if self.play_mode else (40,120,60)
        self.btn_play_pause.hover_color = (220,50,50) if self.play_mode else (50,150,80)
        self.btn_play_pause.text        = "STOP" if self.play_mode else "PLAY"
        for btn in [self.btn_play_pause,self.btn_save,self.btn_load]:
            btn.draw(screen,self.font_btn)
        undo_col = (0,200,255) if self.history.can_undo else (80,85,95)
        redo_col = (0,200,255) if self.history.can_redo else (80,85,95)
        screen.blit(self.font_btn.render(f"↩{len(self.history._undo)}",True,undo_col),(500,20))
        screen.blit(self.font_btn.render(f"{len(self.history._redo)}↪",True,redo_col),(535,20))

    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen,(38,42,50),(770,0,230,600))
        pygame.draw.line(screen,(55,60,72),(770,0),(770,600),2)
        if not (0 <= self.selected_index < len(self.editable_objects)):
            screen.blit(self.font_body.render("Selecione um objeto",True,(140,145,155)),(785,50))
            return
        sel = self.editable_objects[self.selected_index]
        pos,rot,sc = sel.transform.position,sel.transform.rotation,sel.transform.scale
        screen.blit(self.font_title.render("PROPRIEDADES 3D",True,(0,200,255)),(785,18))
        self.btn_toggle_static.draw(screen,self.font_btn)
        if getattr(sel,"is_static",False): pygame.draw.rect(screen,(0,200,255),(789,54,12,12))
        screen.blit(self.font_body.render("Estático",True,(240,240,240)),(815,52))
        self.btn_toggle_physics.draw(screen,self.font_btn)
        if getattr(sel,"use_physics",True): pygame.draw.rect(screen,(0,200,255),(789,84,12,12))
        screen.blit(self.font_body.render("Simular Gravidade",True,(240,240,240)),(815,82))
        screen.blit(self.font_body.render("Impulso Vertical:",True,(220,220,220)),(785,115))
        self.btn_vel_dec.draw(screen,self.font_btn)
        screen.blit(self.font_body.render(f"{sel.initial_velocity_y:+.1f} m/s",True,(255,255,255)),(835,137))
        self.btn_vel_inc.draw(screen,self.font_btn)
        screen.blit(self.font_body.render("Comportamento (Script):",True,(220,220,220)),(785,170))
        self.btn_prev_script.draw(screen,self.font_btn)
        pygame.draw.rect(screen,(45,49,58),(820,190,120,22),border_radius=3)
        sn = os.path.basename(getattr(sel,"script_path","")) or "Nenhum"
        if len(sn)>13: sn=sn[:11]+".."
        screen.blit(self.font_body.render(sn,True,(255,255,255)),(826,194))
        self.btn_next_script.draw(screen,self.font_btn)
        for btn in [self.btn_new_script,self.btn_edit_script,self.btn_internal_editor,self.btn_script_help]:
            btn.draw(screen,self.font_btn)
        screen.blit(self.font_body.render("Cor do Objeto:",True,(220,220,220)),(785,292))
        for btn in self.btn_colors: btn.draw(screen,self.font_btn)
        self.btn_clone.draw(screen,self.font_btn)
        ov = pygame.Surface((480,42),pygame.SRCALPHA)
        ov.fill((30,34,42,200)); screen.blit(ov,(260,545))
        pygame.draw.rect(screen,(0,200,255),(260,545,480,42),1,border_radius=4)
        snap_tag = " [SNAP]" if self.snap_enabled else ""
        screen.blit(self.font_xyz.render(f"OBJETO: {sel.name.upper()}{snap_tag}",True,(0,200,255)),(270,548))
        screen.blit(self.font_body.render(
            f"Pos: X:{pos[0]:.1f} Y:{pos[1]:.1f} Z:{pos[2]:.1f}  "
            f"Tam: X:{sc[0]:.1f} Y:{sc[1]:.1f} Z:{sc[2]:.1f}  "
            f"Rot: X:{int(rot[0])}° Y:{int(rot[1])}° Z:{int(rot[2])}°",
            True,(240,240,240)),(270,566))

    def _draw_xyz_widget(self, screen: pygame.Surface) -> None:
        C  = (710, 60)
        vr = self.camera_comp.view_matrix[:3,:3]
        ax = 35.0
        dirs = [
            (vr@np.array([0,0,-1],np.float32),"X",(220,50,50)),
            (vr@np.array([0,1, 0],np.float32),"Y",(50,170,50)),
            (vr@np.array([1,0, 0],np.float32),"Z",(50,100,220)),
        ]
        endpoints = []
        for d,label,col in dirs:
            e = (int(C[0]+ax*d[0]),int(C[1]-ax*d[1]))
            endpoints.append(np.array(e,np.float32))
            pygame.draw.line(screen,col,C,e,2)
            pygame.draw.circle(screen,col,e,9)
            screen.blit(self.font_xyz.render(label,True,(255,255,255)),
                        self.font_xyz.render(label,True,(255,255,255)).get_rect(center=e))
        pygame.draw.circle(screen,(120,125,135),C,4)
        self.gizmo_ex,self.gizmo_ey,self.gizmo_ez = endpoints

    def _draw_help_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        ov.fill((20,24,30,230)); screen.blit(ov,(0,0))
        modal=pygame.Rect(120,40,760,520)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=8)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=8)
        pygame.draw.rect(screen,(42,47,57),pygame.Rect(120,40,760,35),border_radius=8)
        screen.blit(self.font_title.render("Guia de Comandos — Zennity Engine",True,(0,200,255)),(140,48))
        screen.blit(self.font_btn.render("[ESC] Fechar",True,(200,80,80)),(800,48))
        y=105
        for line in HELP_LINES:
            col=(0,200,255) if line.startswith("  ") else (220,222,226)
            screen.blit(self.font_body.render(line,True,col),(160,y)); y+=18

    # -----------------------------------------------------------------------
    # handle_event
    # -----------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.code_editor.handle_event(event):
            return
        if self.showing_help_modal:
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                self.showing_help_modal=False
            return

        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if event.key == pygame.K_z and mods & pygame.KMOD_CTRL:
                if mods & pygame.KMOD_SHIFT: self.history.redo(self)
                else:                        self.history.undo(self)
                return
            if event.key == pygame.K_d and mods & pygame.KMOD_CTRL:
                self.clone_selected(); return
            if event.key == pygame.K_DELETE:
                self.delete_selected(); return
            if event.key == pygame.K_g:
                self.snap_enabled = not self.snap_enabled; return

        if self.btn_add_cube.is_clicked(event):    self.spawn_object("Cube");    return
        if self.btn_add_pyramid.is_clicked(event): self.spawn_object("Pyramid"); return
        if self.btn_add_sphere.is_clicked(event):  self.spawn_object("Sphere");  return

        for btn,mode in [(self.btn_mode_translate,"translate"),(self.btn_mode_rotate,"rotate"),(self.btn_mode_scale,"scale")]:
            if btn.is_clicked(event):
                self.gizmo_mode = None if self.gizmo_mode==mode else mode; return

        if self.btn_snap.is_clicked(event):
            self.snap_enabled = not self.snap_enabled; return

        if self.btn_undo.is_clicked(event): self.history.undo(self); return
        if self.btn_redo.is_clicked(event): self.history.redo(self); return

        if self.btn_play_pause.is_clicked(event): self._toggle_play(); return
        if self.btn_save.is_clicked(event):       self.save_scene();   return
        if self.btn_load.is_clicked(event):       self.load_scene();   return

        if self.btn_light_angle_dec.is_clicked(event) or self.btn_light_angle_inc.is_clicked(event):
            d = -15.0 if self.btn_light_angle_dec.is_clicked(event) else 15.0
            self.light_angle = (self.light_angle+d)%360
            rad = np.radians(self.light_angle)
            ld  = np.array([np.cos(rad),1.0,np.sin(rad)],np.float32)
            ld /= np.linalg.norm(ld)
            for obj in self.editable_objects:
                r=obj.get_component(MeshRenderer3D)
                if r: r.light_dir=ld
            return

        if event.type == pygame.MOUSEWHEEL:
            self.camera_controller.target_distance = max(1.5, min(15.0, self.camera_controller.target_distance - event.y*0.3))
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button==4: self.camera_controller.target_distance = max(1.5,  self.camera_controller.target_distance-0.3)
            if event.button==5: self.camera_controller.target_distance = min(15.0, self.camera_controller.target_distance+0.3)

        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my=event.pos
            for ep,yaw,pitch in [
                (self.gizmo_ex,  0.0,  0.0),
                (self.gizmo_ey,  0.0, 85.0),
                (self.gizmo_ez, 90.0,  0.0),
            ]:
                if ep is not None and np.linalg.norm(np.array([mx,my])-ep)<12.0:
                    self.camera_controller.target_yaw   = yaw
                    self.camera_controller.target_pitch = pitch
                    return

        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my=event.pos
            if self.selected_index>=0 and not self.play_mode and self.gizmo_mode and self.gizmo_screen_points:
                if self.gizmo_mode=="scale" and self.gizmo_screen_center:
                    if np.linalg.norm(np.array([mx,my])-np.array(self.gizmo_screen_center))<10.0:
                        self.history.push(self)
                        self.is_dragging_gizmo=True; self.active_gizmo_axis='center'
                        self.gizmo_drag_last_mouse=event.pos; return
                for axis,pt in self.gizmo_screen_points.items():
                    if np.linalg.norm(np.array([mx,my])-np.array(pt))<12.0:
                        self.history.push(self)
                        self.is_dragging_gizmo=True; self.active_gizmo_axis=axis
                        self.gizmo_drag_last_mouse=event.pos; return

        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            self.click_start_pos=event.pos
            mx,my=event.pos
            if 230<=mx<=770 and 0<=self.selected_index<len(self.editable_objects):
                r=self.editable_objects[self.selected_index].get_component(MeshRenderer3D)
                if r and r.last_screen_coords is not None:
                    for face in r.mesh.faces:
                        if _point_in_polygon(mx,my,[tuple(r.last_screen_coords[vi]) for vi in face]):
                            self.history.push(self)
                            self.is_dragging_object=True
                            self.drag_object_last_mouse=event.pos
                            break
        elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
            self.is_dragging_object=False
            self.is_dragging_gizmo =False
            self.active_gizmo_axis =None
            if self.click_start_pos:
                dx=event.pos[0]-self.click_start_pos[0]
                dy=event.pos[1]-self.click_start_pos[1]
                if np.hypot(dx,dy)<4.0:
                    mx,my=event.pos
                    if mx<230:
                        y=168
                        for obj in self.editable_objects[-5:]:
                            if pygame.Rect(15,y,200,22).collidepoint((mx,my)):
                                self.selected_index=self.editable_objects.index(obj)
                            y+=26
                    elif mx<=770:
                        self._select_at(mx,my)
                self.click_start_pos=None

        if 0<=self.selected_index<len(self.editable_objects):
            sel=self.editable_objects[self.selected_index]
            if self.btn_delete.is_clicked(event):          self.delete_selected(); return
            if self.btn_toggle_static.is_clicked(event):
                self.history.push(self); sel.is_static=not getattr(sel,"is_static",False); return
            if self.btn_toggle_physics.is_clicked(event):
                self.history.push(self); sel.use_physics=not getattr(sel,"use_physics",True); return
            if self.btn_vel_dec.is_clicked(event):
                self.history.push(self); sel.initial_velocity_y=getattr(sel,"initial_velocity_y",0.0)-1.0; return
            if self.btn_vel_inc.is_clicked(event):
                self.history.push(self); sel.initial_velocity_y=getattr(sel,"initial_velocity_y",0.0)+1.0; return
            if self.btn_clone.is_clicked(event): self.clone_selected(); return
            if self.btn_prev_script.is_clicked(event) or self.btn_next_script.is_clicked(event):
                cur=getattr(sel,"script_path","")
                idx=self.available_scripts.index(cur) if cur in self.available_scripts else 0
                ni=(idx+(-1 if self.btn_prev_script.is_clicked(event) else 1))%len(self.available_scripts)
                sel.script_path=self.available_scripts[ni] if ni>0 else ""; return
            if self.btn_new_script.is_clicked(event):
                path=ScriptManager.create_template(sel)
                self.available_scripts=ScriptManager.list_scripts()
                sel.script_path=path; return
            if self.btn_edit_script.is_clicked(event):
                p=getattr(sel,"script_path","")
                if p and os.path.exists(p):
                    try: os.startfile(p)
                    except: import subprocess; subprocess.Popen(["notepad.exe",p])
                return
            if self.btn_internal_editor.is_clicked(event):
                p=getattr(sel,"script_path","")
                if p and os.path.exists(p): self.code_editor.open(p)
                return
            if self.btn_script_help.is_clicked(event): self.showing_help_modal=True; return
            for i,btn in enumerate(self.btn_colors):
                if btn.is_clicked(event):
                    self.history.push(self)
                    r=sel.get_component(MeshRenderer3D)
                    if r: r.color=COLOR_PALETTE[i]
                    return

    # -----------------------------------------------------------------------
    # Play / Stop
    # -----------------------------------------------------------------------
    def _toggle_play(self) -> None:
        if not self.play_mode:
            self.play_mode=True
            self.saved_scene_state=[]
            for obj in self.editable_objects:
                self.saved_scene_state.append({
                    "obj": obj,
                    "pos": obj.transform.position.copy(),
                    "rot": obj.transform.rotation.copy(),
                    "sc":  obj.transform.scale.copy(),
                })
                PhysicsSim.attach_rigidbody(obj)
                ScriptManager.load(obj)
        else:
            self.play_mode=False
            if self.saved_scene_state:
                for state in self.saved_scene_state:
                    o=state["obj"]
                    o.transform.position=state["pos"]
                    o.transform.rotation=state["rot"]
                    o.transform.scale   =state["sc"]
                    PhysicsSim.detach_rigidbody(o)
                    ScriptManager.unload(o)
            self.saved_scene_state=None
