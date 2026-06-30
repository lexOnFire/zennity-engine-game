"""
Cena principal do editor 3D da Zennity Engine.
Melhorias nesta versão:
  - Undo/Redo (Ctrl+Z / Ctrl+Shift+Z)
  - PhysicsSim integrado com RigidBody3D da engine
  - MOUSEWHEEL correto (pygame.MOUSEWHEEL)
  - Snap de grade configurável (tecla G)
  - Barra de status mostra contagem do histórico
  - Scripts prontos (biblioteca builtin)
  - Templates de cena (Plataformer, Arremesso, Sandbox)
  - Sistema de Tags nos objetos
  - AudioManager integrado
  - Modos de câmera (Perspectiva, Top-Down, Side-Scroller)
  - Painel de boas-vindas para iniciantes
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

_LEFT_W   = 230
_RIGHT_X  = 770
_VP_X     = _LEFT_W
_VP_W     = _RIGHT_X - _VP_X
_VP_Y     = 0
_VP_H     = 600

# Modos de câmera disponíveis
CAMERA_MODES = ["Perspectiva", "Top-Down", "Side-Scroller"]

CAMERA_MODE_PRESETS = {
    "Perspectiva":    {"yaw": 0.0,   "pitch": 25.0, "dist": 6.0},
    "Top-Down":       {"yaw": 0.0,   "pitch": 89.9, "dist": 8.0},
    "Side-Scroller": {"yaw": 90.0,  "pitch": 5.0,  "dist": 7.0},
}


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

TAG_OPTIONS = ["", "player", "inimigo", "perigoso", "coletavel", "chao"]

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
    "Scripts prontos (selecione no inspetor):",
    "  builtin_wasd.py          Mover com WASD",
    "  builtin_jump.py          Pular com Espaço",
    "  builtin_rotate.py        Rotação contínua",
    "  builtin_follow_player.py Seguir o jogador",
    "  builtin_destroy_on_collision.py  Desaparecer ao colidir",
    "",
    "Tags (para scripts de colisão):",
    "  Defina a tag do objeto no inspetor direito.",
    "  Use getattr(outro_obj, 'tag', '') para checar.",
    "",
    "Áudio em scripts:",
    "  from engine.audio import AudioManager",
    "  AudioManager.play('sons/pulo.wav')",
    "  AudioManager.stop_all()",
    "",
    "Pulo com RigidBody3D:",
    "  from engine.physics.rigidbody3d import RigidBody3D",
    "  rb = obj.get_component(RigidBody3D)",
    "  if rb and Input.get_key_down(pygame.K_SPACE): rb.add_impulse(0, 5, 0)",
]

WELCOME_STEPS = [
    ("Bem-vindo à Zennity Engine! 🎮",
     "Esta é a tela do editor 3D. Aqui você cria seus jogos sem escrever código."),
    ("Adicionar Objetos",
     "Clique em '+ Cubo', '+ Pirâm' ou '+ Esf' no painel esquerdo para adicionar objetos à cena."),
    ("Templates prontos",
     "Clique em 'Templates' para carregar uma cena pronta: Plataformer, Arremesso ou Sandbox."),
    ("Propriedades do objeto",
     "Clique num objeto para selecioná-lo. No painel direito você ajusta posição, tamanho, cor, física e scripts."),
    ("Scripts prontos",
     "No inspetor, use '< >' para escolher um script pronto. Ex: builtin_wasd.py move o objeto com WASD."),
    ("Tags para colisões",
     "Defina a 'Tag' do objeto (ex: player, inimigo). Scripts podem detectar colisões pela tag."),
    ("Modo de câmera",
     "Use o botão 'Câmera' no topo para trocar entre Perspectiva, Top-Down e Side-Scroller."),
    ("Testar o jogo",
     "Clique em PLAY para testar. Clique em STOP para voltar ao editor. Posições são restauradas."),
]

SNAP_SIZE: float = 0.5


class EditorScene(Scene):

    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        self.font_title = self.font_body = self.font_btn = self.font_xyz = None

        self.camera_comp: Optional[Camera3D] = None
        self.camera_controller: Optional[OrbitCameraController] = None
        self.camera_mode_index: int = 0  # 0=Perspectiva, 1=Top-Down, 2=Side-Scroller

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
        self.showing_welcome    = True   # painel boas-vindas na primeira abertura
        self.welcome_step       = 0

        self.cube_count = self.pyramid_count = self.sphere_count = 0
        self.history = History()
        self.snap_enabled: bool = False

        # tag selecionada no ciclo de tags
        self._tag_index: int = 0

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

        self.btn_snap      = GuiButton(15, 115, 200, 22, "Grade: OFF", bg_color=(55,58,68), hover_color=(70,75,88))
        self.btn_templates = GuiButton(15, 143, 200, 22, "📂 Templates", bg_color=(60,40,100), hover_color=(80,55,130))
        self.btn_undo      = GuiButton(15, 300, 95,  26, "↩ Desfazer", bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_redo      = GuiButton(120,300, 95,  26, "Refazer ↪",  bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_delete    = GuiButton(15, 330, 200, 26, "Excluir Objeto", bg_color=(140,40,40), hover_color=(175,50,50))

        self.btn_light_angle_dec = GuiButton(15,  380, 40, 22, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_light_angle_inc = GuiButton(165, 380, 40, 22, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        # --- Barra superior ---
        self.btn_play_pause  = GuiButton(245, 15, 80,  26, "PLAY",      bg_color=(40,120,60),  hover_color=(50,150,80))
        self.btn_save        = GuiButton(335, 15, 70,  26, "Salvar",    bg_color=(100,70,40),  hover_color=(130,90,50))
        self.btn_load        = GuiButton(415, 15, 70,  26, "Carregar",  bg_color=(100,70,40),  hover_color=(130,90,50))
        self.btn_camera_mode = GuiButton(495, 15, 100, 26, "Câmera: Persp", bg_color=(40,70,120), hover_color=(55,95,160))
        self.btn_welcome     = GuiButton(605, 15, 50,  26, "❓ Ajuda",   bg_color=(80,60,20),   hover_color=(110,85,30))

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

        # Tag
        self.btn_prev_tag = GuiButton(785, 385, 30, 22, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_next_tag = GuiButton(945, 385, 30, 22, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        self.btn_colors = [
            GuiButton(785 + i * 32, 312, 24, 24, "", bg_color=c, hover_color=c)
            for i, c in enumerate(COLOR_PALETTE)
        ]

        # Templates modal
        self.showing_templates = False
        self._template_list    = self._load_template_list()
        self.btn_template_items = []
        for i, tpl in enumerate(self._template_list):
            self.btn_template_items.append(
                GuiButton(280, 120 + i * 60, 440, 48,
                          tpl.get("_template_name", f"Template {i+1}"),
                          bg_color=(50,55,70), hover_color=(70,78,100))
            )
        self.btn_templates_close = GuiButton(660, 80, 80, 28, "Fechar", bg_color=(140,40,40), hover_color=(175,50,50))

        # --- Câmera ---
        cam_obj = GameObject("EditorCamera")
        self.camera_comp = cam_obj.add_component(Camera3D(
            fov=60.0, near=0.1, far=100.0,
            viewport_x=float(_VP_X),
            viewport_y=float(_VP_Y),
            viewport_width=float(_VP_W),
            viewport_height=float(_VP_H),
        ))
        self.camera_controller = cam_obj.add_component(OrbitCameraController())
        self._add_go(cam_obj)

        self.spawn_object("Cube")

    # -----------------------------------------------------------------------
    def _load_template_list(self) -> List[Dict]:
        templates = []
        demos_dir = os.path.join(os.path.dirname(__file__), "..", "demos")
        for fname in sorted(os.listdir(demos_dir)):
            if fname.startswith("template_") and fname.endswith(".json"):
                try:
                    with open(os.path.join(demos_dir, fname)) as f:
                        data = json.load(f)
                    data["_file"] = os.path.join(demos_dir, fname)
                    templates.append(data)
                except Exception:
                    pass
        return templates

    def _load_template(self, tpl: Dict) -> None:
        self.history.push(self)
        for obj in list(self.editable_objects):
            self._remove_go(obj); obj.destroy()
        self.editable_objects.clear()
        self.selected_index = -1
        self.cube_count = self.pyramid_count = self.sphere_count = 0
        for item in tpl.get("objects", []):
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
            go.tag                = item.get("tag", "")
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
            self.selected_index = 0
        self.showing_templates = False
        print(f"[EditorScene] Template carregado: {tpl.get('_template_name')}")

    def _set_camera_mode(self, mode_name: str) -> None:
        preset = CAMERA_MODE_PRESETS.get(mode_name, CAMERA_MODE_PRESETS["Perspectiva"])
        self.camera_controller.target_yaw   = preset["yaw"]
        self.camera_controller.target_pitch = preset["pitch"]
        self.camera_controller.target_distance = preset["dist"]
        self.btn_camera_mode.text = f"Câmera: {mode_name[:5]}"

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
    def spawn_object(self, shape: str) -> None:
        self.history.push(self)
        go = GameObject()
        go.transform.position = np.array([0.0, 0.0, 1.5], dtype=np.float32)
        go.mesh_type          = shape
        go.is_static          = False
        go.use_physics        = True
        go.initial_velocity_y = 0.0
        go.script_path        = ""
        go.tag                = ""
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
        go.tag                = getattr(src, "tag", "")
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
                "tag":                getattr(obj, "tag", ""),
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
            go.tag                = item.get("tag", "")
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
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (255,255,255), (_VP_X, _VP_Y, _VP_W, _VP_H))
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
        if self.showing_templates:
            self._draw_templates_modal(screen)
        elif self.code_editor.is_open:
            self.code_editor.draw(screen)
        elif self.showing_help_modal:
            self._draw_help_modal(screen)
        elif self.showing_welcome:
            self._draw_welcome_modal(screen)

    # ---------------------------------------