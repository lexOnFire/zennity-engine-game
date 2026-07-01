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
_TREE_Y      = 228
_TREE_ROW_H  = 24
SNAP_SIZE    = 0.5

_SHAPE_ICON = {
    "Cube":    "[C]",
    "Pyramid": "[Py]",
    "Sphere":  "[Sp]",
    "Plane":   "[Pl]",
    "Capsule": "[Cp]",
    "Camera":  "[Ca]",
    "Light":   "[Lz]"
}

# Modos de câmera disponíveis
CAMERA_MODES = ["Perspectiva", "Top-Down", "Side-Scroller"]

CAMERA_MODE_PRESETS = {
    "Perspectiva":    {"yaw": 0.0,   "pitch": 25.0, "dist": 6.0},
    "Top-Down":       {"yaw": 0.0,   "pitch": 89.9, "dist": 8.0},
    "Side-Scroller":  {"yaw": 90.0,  "pitch": 5.0,  "dist": 7.0},
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
        self.showing_welcome    = True
        self.welcome_step       = 0

        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
        self._tree_scroll: int = 0
        self._rename_index: int = -1
        self._rename_text: str = ""
        self._rename_blink: float = 0.0
        self._rename_cursor_on: bool = True
        self._last_click_index: int = -1
        self._last_click_time: float = 0.0

        self.history = History()
        self.snap_enabled: bool = False
        self._tag_index: int = 0
        
        self._tree_h = 220
        self._tree_max_vis = 9
        self._light_y = _TREE_Y + self._tree_h + 110
        self._active_dropdown = None
        self._is_dragging_tree = False
        self._drag_tree_src = None

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
        self.btn_add_pyramid  = GuiButton(82,  45, 62, 26, "+ Pyramid", bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_sphere   = GuiButton(149, 45, 62, 26, "+ Esf",   bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_plane    = GuiButton(15,  76, 62, 26, "+ Plano", bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_capsule  = GuiButton(82,  76, 62, 26, "+ Caps",  bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_camera   = GuiButton(149, 76, 62, 26, "+ Cam",   bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_light    = GuiButton(15,  107, 62, 26, "+ Luz",   bg_color=(40,100,60),  hover_color=(50,130,80))

        self.btn_mode_translate = GuiButton(15,  138, 62, 26, "Mover",   bg_color=(80,60,120),  hover_color=(100,80,150))
        self.btn_mode_rotate    = GuiButton(82,  138, 62, 26, "Girar",   bg_color=(80,60,120),  hover_color=(100,80,150))
        self.btn_mode_scale     = GuiButton(149, 138, 62, 26, "Escalar", bg_color=(80,60,120),  hover_color=(100,80,150))

        self.btn_snap      = GuiButton(15, 169, 200, 22, "Grade: OFF", bg_color=(55,58,68), hover_color=(70,75,88))
        self.btn_templates = GuiButton(15, 197, 200, 22, "Templates", bg_color=(60,40,100), hover_color=(80,55,130))
        self.btn_undo      = GuiButton(15, _TREE_Y + self._tree_h + 22, 95,  26, "Desfazer", bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_redo      = GuiButton(120, _TREE_Y + self._tree_h + 22, 95,  26, "Refazer",  bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_delete    = GuiButton(15, _TREE_Y + self._tree_h + 52, 200, 26, "Excluir Objeto", bg_color=(140,40,40), hover_color=(175,50,50))

        # Botões de scroll da tree
        self.btn_tree_up   = GuiButton(196, _TREE_Y + 18, 28, 20, "▲", bg_color=(55,58,68), hover_color=(70,75,88))
        self.btn_tree_down = GuiButton(196, _TREE_Y + self._tree_h - 2, 28, 20, "▼", bg_color=(55,58,68), hover_color=(70,75,88))

        self.btn_light_angle_dec = GuiButton(15,  self._light_y, 40, 22, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_light_angle_inc = GuiButton(165, self._light_y, 40, 22, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        # --- Barra superior ---
        self.btn_menu_file   = GuiButton(10, 2, 50, 26, "File", bg_color=(28,30,38), hover_color=(55,60,72))
        self.btn_menu_view   = GuiButton(65, 2, 50, 26, "View", bg_color=(28,30,38), hover_color=(55,60,72))
        self.btn_menu_window = GuiButton(120, 2, 70, 26, "Window", bg_color=(28,30,38), hover_color=(55,60,72))

        # Fictícios/Ações legadas para manter compatibilidade nos eventos
        self.btn_new_scene   = GuiButton(-100, -100, 10, 10, "Novo")
        self.btn_save        = GuiButton(-100, -100, 10, 10, "Salvar")
        self.btn_load        = GuiButton(-100, -100, 10, 10, "Carregar")
        self.btn_camera_mode = GuiButton(-100, -100, 10, 10, "Camera")
        self.btn_welcome     = GuiButton(-100, -100, 10, 10, "Ajuda")

        self.btn_play_pause  = GuiButton(600, 2, 80,  26, "PLAY",          bg_color=(40,120,60),  hover_color=(50,150,80))

        # --- Inspetor direito ---
        self.btn_toggle_static  = GuiButton(1170 + 15, 50,  20, 20, "", bg_color=(45,49,58), hover_color=(70,76,90))
        self.btn_toggle_physics = GuiButton(1170 + 15, 80,  20, 20, "", bg_color=(45,49,58), hover_color=(70,76,90))
        self.btn_vel_dec        = GuiButton(1170 + 15, 135, 40, 20, " - ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_vel_inc        = GuiButton(1170 + 145, 135, 40, 20, " + ", bg_color=(60,65,78), hover_color=(75,80,95))

        self.btn_prev_script     = GuiButton(1170 + 15, 190, 30, 22, " < ",              bg_color=(60,65,78),  hover_color=(75,80,95))
        self.btn_next_script     = GuiButton(1170 + 175, 190, 30, 22, " > ",              bg_color=(60,65,78),  hover_color=(75,80,95))
        self.btn_new_script      = GuiButton(1170 + 15, 215, 190,20, "+ Novo Script",    bg_color=(40,100,60), hover_color=(50,130,80))
        self.btn_edit_script     = GuiButton(1170 + 15, 238, 93, 20, "Editor Ext.",      bg_color=(0,100,160), hover_color=(0,130,200))
        self.btn_internal_editor = GuiButton(1170 + 112, 238, 93, 20, "Editor Int.",      bg_color=(0,100,160), hover_color=(0,130,200))
        self.btn_script_help     = GuiButton(1170 + 15, 261, 190,20, "Guia de Comandos", bg_color=(120,80,40), hover_color=(150,100,50))
        self.btn_clone           = GuiButton(1170 + 15, 352, 190,26, "Clonar Objeto",    bg_color=(80,60,120), hover_color=(100,75,150))

        # Parenting/Hierarquia no Inspetor
        self.btn_prev_parent = GuiButton(1170 + 15, 385, 30, 22, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_next_parent = GuiButton(1170 + 175, 385, 30, 22, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        # Tag
        self.btn_prev_tag = GuiButton(1170 + 15, 440, 30, 22, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_next_tag = GuiButton(1170 + 175, 440, 30, 22, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        self.btn_colors = [
            GuiButton(1170 + 15 + i * 32, 312, 24, 24, "", bg_color=c, hover_color=c)
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
            viewport_x=230.0,
            viewport_y=30.0,
            viewport_width=940.0,
            viewport_height=770.0,
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
        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
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
            
            # Incrementar contadores
            count_map = {
                "Cube":    "cube_count",
                "Pyramid": "pyramid_count",
                "Sphere":  "sphere_count",
                "Plane":   "plane_count",
                "Capsule": "capsule_count",
                "Camera":  "camera_count",
                "Light":   "light_count",
            }
            attr = count_map.get(go.mesh_type, "cube_count")
            setattr(self, attr, getattr(self, attr) + 1)
            
            color = tuple(item["color"])
            go.add_component(self._make_mesh(go.mesh_type, color))
            self._add_go(go)
            self.editable_objects.append(go)

        # Resolvendo parentescos
        for item, go in zip(tpl.get("objects", []), self.editable_objects):
            parent_name = item.get("parent_name")
            if parent_name:
                parent_obj = next((o for o in self.editable_objects if o.name == parent_name), None)
                if parent_obj:
                    parent_obj.add_child(go)

        if self.editable_objects:
            self.selected_index = 0
        self.showing_templates = False
        self._tree_scroll = 0
        self._cancel_rename()
        print(f"[EditorScene] Template carregado: {tpl.get('_template_name')}")

    def _set_camera_mode(self, mode_name: str) -> None:
        preset = CAMERA_MODE_PRESETS.get(mode_name, CAMERA_MODE_PRESETS["Perspectiva"])
        self.camera_controller.target_yaw      = preset["yaw"]
        self.camera_controller.target_pitch    = preset["pitch"]
        self.camera_controller.target_distance = preset["dist"]
        self.btn_camera_mode.text = f"Camera: {mode_name[:5]}"

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
    def _make_mesh(self, shape: str, color: tuple):
        """Cria e retorna um MeshRenderer3D para a forma dada."""
        from editor.mesh_factory import create_plane_mesh, create_capsule_mesh
        if shape == "Cube":
            return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)
        elif shape == "Pyramid":
            return MeshRenderer3D(create_pyramid_mesh(1.0), color=color)
        elif shape == "Sphere":
            return MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=color)
        elif shape == "Plane":
            return MeshRenderer3D(create_plane_mesh(size=2.0, subdivisions=2), color=color)
        elif shape == "Capsule":
            return MeshRenderer3D(create_capsule_mesh(radius=0.4, height=1.0, rings=8, sectors=10), color=color)
        elif shape == "Camera":
            return MeshRenderer3D(create_pyramid_mesh(0.5), color=color)
        elif shape == "Light":
            return MeshRenderer3D(create_sphere_mesh(radius=0.25, rings=6, sectors=6), color=color)
        else:
            return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)

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

        default_colors = {
            "Cube":    (0, 110, 220),
            "Pyramid": (220, 60, 20),
            "Sphere":  (100, 40, 180),
            "Plane":   (60, 160, 80),
            "Capsule": (200, 140, 0),
            "Camera":  (50, 200, 200),
            "Light":   (255, 230, 50),
        }
        default_names = {
            "Cube":    "Bloco",
            "Pyramid": "Piramide",
            "Sphere":  "Bolinha",
            "Plane":   "Plano",
            "Capsule": "Capsula",
            "Camera":  "Camera",
            "Light":   "Luz",
        }
        count_map = {
            "Cube":    "cube_count",
            "Pyramid": "pyramid_count",
            "Sphere":  "sphere_count",
            "Plane":   "plane_count",
            "Capsule": "capsule_count",
            "Camera":  "camera_count",
            "Light":   "light_count",
        }
        attr = count_map.get(shape, "cube_count")
        setattr(self, attr, getattr(self, attr) + 1)
        go.name = f"{default_names.get(shape, shape)}_{getattr(self, attr)}"
        color   = default_colors.get(shape, (200, 200, 200))
        go.add_component(self._make_mesh(shape, color))

        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll_to(self.selected_index)

    def delete_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self._cancel_rename()
        self.history.push(self)
        go = self.editable_objects.pop(self.selected_index)
        self._remove_go(go)
        go.destroy()
        self.selected_index = -1 if not self.editable_objects else max(0, self.selected_index - 1)

    def clone_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self._cancel_rename()
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
        go.transform.position = src.transform.position.copy() + np.array([0.5, 0.0, 0.5])
        go.transform.rotation = src.transform.rotation.copy()
        go.transform.scale    = src.transform.scale.copy()
        renderer = src.get_component(MeshRenderer3D)
        color    = renderer.color if renderer else (200, 200, 200)
        go.add_component(self._make_mesh(go.mesh_type, color))
        
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll_to(self.selected_index)

    # -----------------------------------------------------------------------
    # Hierarquia e Outliner
    # -----------------------------------------------------------------------
    def _build_flat_tree(self) -> List[Tuple[GameObject, int]]:
        flat = []
        roots = [obj for obj in self.editable_objects if getattr(obj, "parent", None) is None]
        
        def traverse(obj, depth):
            flat.append((obj, depth))
            for child in self.editable_objects:
                if getattr(child, "parent", None) == obj:
                    traverse(child, depth + 1)
                    
        for r in roots:
            traverse(r, 0)
            
        # Adiciona órfãos para segurança
        flat_objs = [f[0] for f in flat]
        for obj in self.editable_objects:
            if obj not in flat_objs:
                flat.append((obj, 0))
        return flat

    def _start_rename(self, idx: int) -> None:
        if not (0 <= idx < len(self.editable_objects)):
            return
        self._rename_index = idx
        self._rename_text  = self.editable_objects[idx].name
        self._rename_blink = 0.0
        self._rename_cursor_on = True

    def _commit_rename(self) -> None:
        if self._rename_index >= 0 and self._rename_text.strip():
            self.editable_objects[self._rename_index].name = self._rename_text.strip()
        self._rename_index = -1
        self._rename_text  = ""

    def _cancel_rename(self) -> None:
        self._rename_index = -1
        self._rename_text  = ""

    def _tree_scroll_to(self, idx: int) -> None:
        if idx < 0:
            return
        if idx < self._tree_scroll:
            self._tree_scroll = idx
        elif idx >= self._tree_scroll + self._tree_max_vis:
            self._tree_scroll = idx - self._tree_max_vis + 1

    def _max_scroll(self) -> int:
        return max(0, len(self.editable_objects) - self._tree_max_vis)

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
                "parent_name":        obj.parent.name if obj.parent else None,
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
        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
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
            
            # Incrementar contadores
            count_map = {
                "Cube":    "cube_count",
                "Pyramid": "pyramid_count",
                "Sphere":  "sphere_count",
                "Plane":   "plane_count",
                "Capsule": "capsule_count",
                "Camera":  "camera_count",
                "Light":   "light_count",
            }
            attr = count_map.get(go.mesh_type, "cube_count")
            setattr(self, attr, getattr(self, attr) + 1)
            
            color = tuple(item["color"])
            go.add_component(self._make_mesh(go.mesh_type, color))
            self._add_go(go)
            self.editable_objects.append(go)

        # Resolvendo parentescos
        for item, go in zip(data.get("objects", []), self.editable_objects):
            parent_name = item.get("parent_name")
            if parent_name:
                parent_obj = next((o for o in self.editable_objects if o.name == parent_name), None)
                if parent_obj:
                    parent_obj.add_child(go)

        if self.editable_objects:
            self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll = 0
        self._cancel_rename()
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
        # Adaptação responsiva baseada no tamanho da janela
        screen_surf = pygame.display.get_surface()
        if screen_surf:
            width, height = screen_surf.get_size()
            
            # viewport responsiva para o renderizador 3D (offset 30px no Y para a barra de menu)
            left_w = 230
            right_x = width - 230
            vp_w = right_x - left_w
            vp_h = height - 30
            
            # A câmera do editor renderiza na metade esquerda apenas em play_mode, senão tela cheia na viewport central
            self.camera_comp.viewport_x = float(left_w)
            self.camera_comp.viewport_y = 30.0
            self.camera_comp.viewport_width = float(vp_w // 2 if self.play_mode else vp_w)
            self.camera_comp.viewport_height = float(vp_h)
            
            # Atualiza botões do painel direito
            self.btn_toggle_static.x = right_x + 15
            self.btn_toggle_physics.x = right_x + 15
            self.btn_vel_dec.x = right_x + 15
            self.btn_vel_inc.x = right_x + 145
            self.btn_prev_script.x = right_x + 15
            self.btn_next_script.x = right_x + 175
            self.btn_new_script.x = right_x + 15
            self.btn_edit_script.x = right_x + 15
            self.btn_internal_editor.x = right_x + 112
            self.btn_script_help.x = right_x + 15
            self.btn_clone.x = right_x + 15
            self.btn_prev_parent.x = right_x + 15
            self.btn_next_parent.x = right_x + 175
            self.btn_prev_tag.x = right_x + 15
            self.btn_next_tag.x = right_x + 175
            for i, btn in enumerate(self.btn_colors):
                btn.x = right_x + 15 + i * 32
                
            self.btn_play_pause.x = width // 2 - 40
            
            # Altura útil da árvore
            self._tree_h = max(100, height - _TREE_Y - 180)
            self._tree_max_vis = self._tree_h // _TREE_ROW_H
            
            # Reposiciona botões da árvore
            self.btn_tree_down.y = _TREE_Y + self._tree_h - 2
            self.btn_undo.y = _TREE_Y + self._tree_h + 22
            self.btn_redo.y = _TREE_Y + self._tree_h + 22
            self.btn_delete.y = _TREE_Y + self._tree_h + 52
            self._light_y = _TREE_Y + self._tree_h + 110
            self.btn_light_angle_dec.y = self._light_y
            self.btn_light_angle_inc.y = self._light_y

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
        # Câmera edit-mode e game-mode agora rodam em paralelo no split-screen

        for go in self.game_objects:
            go.update(dt)

    # -----------------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        width, height = screen.get_size()
        left_w = 230
        right_x = width - 230
        vp_w = right_x - left_w
        vp_h = height - 30
        
        if self.play_mode:
            # Viewport da Esquerda (EDIT VIEW)
            pygame.draw.rect(screen, (30, 34, 42), (left_w, 30, vp_w // 2, vp_h))
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
            
            # Viewport da Direita (GAME VIEW)
            self._draw_game_view(screen, left_w, vp_w, vp_h, height)
            
            # Linha divisória vertical
            pygame.draw.line(screen, (55, 60, 72), (left_w + vp_w // 2, 30), (left_w + vp_w // 2, height), 2)
            
            # Títulos dos viewports
            pygame.draw.rect(screen, (40, 44, 52), (left_w + 5, 35, 80, 18), border_radius=3)
            screen.blit(self.font_btn.render("EDIT MODE", True, (0, 200, 255)), (left_w + 10, 38))
            
            pygame.draw.rect(screen, (40, 44, 52), (left_w + vp_w // 2 + 5, 35, 120, 18), border_radius=3)
            screen.blit(self.font_btn.render("GAME VIEW (PLAY)", True, (0, 255, 120)), (left_w + vp_w // 2 + 10, 38))
        else:
            # Modo edição tradicional em tela cheia na viewport central
            pygame.draw.rect(screen, (30, 34, 42), (left_w, 30, vp_w, vp_h))
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
            
            pygame.draw.rect(screen, (40, 44, 52), (left_w + 5, 35, 80, 18), border_radius=3)
            screen.blit(self.font_btn.render("EDIT MODE", True, (0, 200, 255)), (left_w + 10, 38))

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
            
        self._draw_dropdowns(screen)
        
        # Tooltip visual para arrastar hierárquico
        if self._is_dragging_tree and self._drag_tree_src:
            mx, my = pygame.mouse.get_pos()
            label = f"Mover {self._drag_tree_src.name} para..."
            pygame.draw.rect(screen, (0, 150, 220), (mx + 15, my + 5, 200, 24), border_radius=4)
            screen.blit(self.font_body.render(label, True, (255, 255, 255)), (mx + 22, my + 9))

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
        
        def draw_triangle(surface, color, pt, center):
            dx = pt[0] - center[0]
            dy = pt[1] - center[1]
            dist = np.hypot(dx, dy)
            if dist > 0:
                ux, uy = dx / dist, dy / dist
                perp_x, perp_y = -uy, ux
                p1 = (pt[0] + ux * 8, pt[1] + uy * 8)
                p2 = (pt[0] - ux * 8 + perp_x * 6, pt[1] - uy * 8 + perp_y * 6)
                p3 = (pt[0] - ux * 8 - perp_x * 6, pt[1] - uy * 8 - perp_y * 6)
                pygame.draw.polygon(surface, color, [p1, p2, p3])

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
            
            # Desenha triângulos de referência para cliques na rotação
            draw_triangle(screen, (220,50,50), px, c)  # X
            draw_triangle(screen, (50,170,50), py, c)  # Y
            draw_triangle(screen, (50,100,220), pz, c) # Z
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
        height = screen.get_height()
        pygame.draw.rect(screen,(38,42,50),(0,30,_LEFT_W,height - 30))
        pygame.draw.line(screen,(55,60,72),(_LEFT_W,30),(_LEFT_W,height),2)
        screen.blit(self.font_title.render("ADICIONAR FORMAS",True,(0,200,255)),(15,48))
        
        # Desenhar todos os 7 botões de formas
        for btn in [self.btn_add_cube, self.btn_add_pyramid, self.btn_add_sphere,
                    self.btn_add_plane, self.btn_add_capsule, self.btn_add_camera, self.btn_add_light]:
            btn.draw(screen,self.font_btn)
            
        for btn,mode in [(self.btn_mode_translate,"translate"),(self.btn_mode_rotate,"rotate"),(self.btn_mode_scale,"scale")]:
            btn.bg_color = (0,150,220) if self.gizmo_mode==mode else (80,60,120)
            btn.draw(screen,self.font_btn)
            
        self.btn_snap.text     = f"Grade: {'ON (G)' if self.snap_enabled else 'OFF (G)'}"
        self.btn_snap.bg_color = (0,130,80) if self.snap_enabled else (55,58,68)
        self.btn_snap.draw(screen, self.font_btn)
        self.btn_templates.draw(screen, self.font_btn)
        
        # --- Tree/Outliner Hierárquico ---
        screen.blit(self.font_title.render("OBJETOS DA CENA",True,(0,200,255)),(15, _TREE_Y))
        pygame.draw.rect(screen,(30,34,42),(15, _TREE_Y+18, 178, self._tree_h), border_radius=3)
        pygame.draw.rect(screen,(55,60,72),(15, _TREE_Y+18, 178, self._tree_h), 1, border_radius=3)
        
        flat_tree = self._build_flat_tree()
        total = len(flat_tree)
        max_s = self._max_scroll()
        self._tree_scroll = min(self._tree_scroll, max_s)
        
        for slot_i in range(self._tree_max_vis):
            obj_i = self._tree_scroll + slot_i
            if obj_i >= total:
                break
            obj, depth = flat_tree[obj_i]
            # Determinar se este objeto está selecionado
            sel = False
            if 0 <= self.selected_index < len(self.editable_objects):
                sel = (self.editable_objects[self.selected_index] == obj)
                
            ry = _TREE_Y + 18 + slot_i * _TREE_ROW_H
            row = pygame.Rect(16, ry, 177, _TREE_ROW_H - 1)
            
            bg = (60,80,110) if sel else (38,42,50)
            pygame.draw.rect(screen, bg, row, border_radius=2)
            if sel:
                pygame.draw.rect(screen,(0,200,255), row, 1, border_radius=2)
                
            indent = min(depth, 4) * 10
            icon = _SHAPE_ICON.get(getattr(obj, "mesh_type", "Cube"), "[C]")
            screen.blit(self.font_body.render(icon, True, (0,200,255) if sel else (120,130,145)), (20 + indent, ry+4))
            
            # Campo de renomeação inline
            if self._rename_index >= 0 and self.editable_objects[self._rename_index] == obj:
                pygame.draw.rect(screen,(50,55,65),(38 + indent, ry+2, 148 - indent, _TREE_ROW_H-4), border_radius=2)
                pygame.draw.rect(screen,(0,200,255),(38 + indent, ry+2, 148 - indent, _TREE_ROW_H-4), 1, border_radius=2)
                display = self._rename_text
                if self._rename_cursor_on:
                    display += "|"
                screen.blit(self.font_body.render(display, True,(255,255,255)),(41 + indent, ry+4))
            else:
                label = obj.name
                max_len = 16 - (indent // 10) * 2
                if len(label) > max_len:
                    label = label[:max(5, max_len-2)] + ".."
                screen.blit(self.font_body.render(label, True,(255,255,255)),(38 + indent, ry+4))
                
        # Scrollbar
        if total > self._tree_max_vis:
            bar_h = max(16, self._tree_h * self._tree_max_vis // max(total,1))
            bar_y = _TREE_Y + 18 + (self._tree_h - bar_h) * self._tree_scroll // max(max_s, 1)
            pygame.draw.rect(screen,(80,88,105),(194, bar_y, 4, bar_h), border_radius=2)
            self.btn_tree_up.draw(screen, self.font_btn)
            self.btn_tree_down.draw(screen, self.font_btn)
            
        screen.blit(self.font_body.render(f"{len(self.editable_objects)} objeto(s)", True,(100,105,115)),(15, _TREE_Y + self._tree_h + 2))
        
        self.btn_undo.bg_color = (60,80,110) if self.history.can_undo else (45,49,58)
        self.btn_redo.bg_color = (60,80,110) if self.history.can_redo else (45,49,58)
        self.btn_undo.draw(screen,self.font_btn)
        self.btn_redo.draw(screen,self.font_btn)
        if 0 <= self.selected_index < len(self.editable_objects):
            self.btn_delete.draw(screen,self.font_btn)
            
        screen.blit(self.font_title.render("DIRECAO DA LUZ",True,(0,200,255)),(15, self._light_y - 22))
        self.btn_light_angle_dec.draw(screen,self.font_btn)
        screen.blit(self.font_body.render(f"Sol: {int(self.light_angle)} deg",True,(255,255,255)),(65, self._light_y + 2))
        self.btn_light_angle_inc.draw(screen,self.font_btn)

    def _draw_top_bar(self, screen: pygame.Surface) -> None:
        width = screen.get_width()
        # Fundo da barra de menus superior
        pygame.draw.rect(screen, (28, 30, 38), (0, 0, width, 30))
        pygame.draw.line(screen, (55, 60, 72), (0, 30), (width, 30), 2)
        
        # Desenha File, View, Window
        self.btn_menu_file.draw(screen, self.font_btn)
        self.btn_menu_view.draw(screen, self.font_btn)
        self.btn_menu_window.draw(screen, self.font_btn)
        
        # PLAY / STOP
        self.btn_play_pause.bg_color    = (180,40,40) if self.play_mode else (40,120,60)
        self.btn_play_pause.hover_color = (220,50,50) if self.play_mode else (50,150,80)
        self.btn_play_pause.text        = "STOP" if self.play_mode else "PLAY"
        self.btn_play_pause.draw(screen, self.font_btn)
        
        # Undo / Redo display
        undo_col = (0,200,255) if self.history.can_undo else (80,85,95)
        redo_col = (0,200,255) if self.history.can_redo else (80,85,95)
        screen.blit(self.font_btn.render(f"Undo: {len(self.history._undo)}",True,undo_col),(width - 160, 8))
        screen.blit(self.font_btn.render(f"Redo: {len(self.history._redo)}",True,redo_col),(width - 90, 8))

    def _draw_dropdowns(self, screen: pygame.Surface) -> None:
        if not self._active_dropdown:
            return
            
        mx, my = pygame.mouse.get_pos()
        
        if self._active_dropdown == "file":
            opts = ["Novo Scene", "Salvar", "Carregar", "Sair"]
            rx, ry = 10, 30
            rw = 120
        elif self._active_dropdown == "view":
            grade_str = "Desativar Grade" if self.snap_enabled else "Ativar Grade"
            opts = ["Camera: Persp", "Camera: Top", "Camera: Side", grade_str, "Templates"]
            rx, ry = 65, 30
            rw = 150
        elif self._active_dropdown == "window":
            fs_str = "Modo Janela" if getattr(self.engine, "is_fullscreen", False) else "Tela Cheia"
            opts = [fs_str + " (F11)", "Guia de Ajuda"]
            rx, ry = 120, 30
            rw = 160
        else:
            return
            
        rh = len(opts) * 26
        pygame.draw.rect(screen, (30, 34, 42), (rx, ry, rw, rh), border_radius=4)
        pygame.draw.rect(screen, (55, 60, 72), (rx, ry, rw, rh), 1, border_radius=4)
        
        for i, opt in enumerate(opts):
            row_rect = pygame.Rect(rx + 1, ry + i * 26 + 1, rw - 2, 24)
            hover = row_rect.collidepoint(mx, my)
            if hover:
                pygame.draw.rect(screen, (0, 150, 220), row_rect, border_radius=3)
            
            color = (255, 255, 255)
            screen.blit(self.font_body.render(opt, True, color), (rx + 8, ry + i * 26 + 5))

    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        width, height = screen.get_size()
        right_x = width - 230
        pygame.draw.rect(screen,(38,42,50),(right_x,30,230,height - 30))
        pygame.draw.line(screen,(55,60,72),(right_x,30),(right_x,height),2)
        if not (0 <= self.selected_index < len(self.editable_objects)):
            screen.blit(self.font_body.render("Selecione um objeto",True,(140,145,155)),(right_x + 15,60))
            return
        sel = self.editable_objects[self.selected_index]
        pos,rot,sc = sel.transform.position,sel.transform.rotation,sel.transform.scale
        screen.blit(self.font_title.render("PROPRIEDADES 3D",True,(0,200,255)),(right_x + 15,48))
        self.btn_toggle_static.draw(screen,self.font_btn)
        if getattr(sel,"is_static",False): pygame.draw.rect(screen,(0,200,255),(right_x + 19,54,12,12))
        screen.blit(self.font_body.render("Estatico",True,(240,240,240)),(right_x + 45,52))
        self.btn_toggle_physics.draw(screen,self.font_btn)
        if getattr(sel,"use_physics",True): pygame.draw.rect(screen,(0,200,255),(right_x + 19,84,12,12))
        screen.blit(self.font_body.render("Simular Gravidade",True,(240,240,240)),(right_x + 45,82))
        screen.blit(self.font_body.render("Impulso Vertical:",True,(220,220,220)),(right_x + 15,115))
        self.btn_vel_dec.draw(screen,self.font_btn)
        screen.blit(self.font_body.render(f"{sel.initial_velocity_y:+.1f} m/s",True,(255,255,255)),(right_x + 65,137))
        self.btn_vel_inc.draw(screen,self.font_btn)
        screen.blit(self.font_body.render("Comportamento (Script):",True,(220,220,220)),(right_x + 15,170))
        self.btn_prev_script.draw(screen,self.font_btn)
        pygame.draw.rect(screen,(45,49,58),(right_x + 50,190,120,22),border_radius=3)
        sn = os.path.basename(getattr(sel,"script_path","")) or "Nenhum"
        if len(sn)>13: sn=sn[:11]+".."
        screen.blit(self.font_body.render(sn,True,(255,255,255)),(right_x + 56,194))
        self.btn_next_script.draw(screen,self.font_btn)
        for btn in [self.btn_new_script,self.btn_edit_script,self.btn_internal_editor,self.btn_script_help]:
            btn.draw(screen,self.font_btn)
        screen.blit(self.font_body.render("Cor do Objeto:",True,(220,220,220)),(right_x + 15,292))
        for btn in self.btn_colors: btn.draw(screen,self.font_btn)
        self.btn_clone.draw(screen,self.font_btn)
        # Parent / Hierarquia
        screen.blit(self.font_body.render("Pai:",True,(220,220,220)),(right_x + 15,368))
        self.btn_prev_parent.draw(screen,self.font_btn)
        p_name = sel.parent.name if sel.parent else "Nenhum"
        if len(p_name) > 13: p_name = p_name[:11] + ".."
        pygame.draw.rect(screen,(45,49,58),(right_x + 50,385,120,22),border_radius=3)
        screen.blit(self.font_body.render(p_name,True,(255,255,255)),(right_x + 56,389))
        self.btn_next_parent.draw(screen,self.font_btn)

        # Tag
        screen.blit(self.font_body.render("Tag:",True,(220,220,220)),(right_x + 15,423))
        self.btn_prev_tag.draw(screen,self.font_btn)
        tag_val = getattr(sel,"tag","") or "Nenhuma"
        pygame.draw.rect(screen,(45,49,58),(right_x + 50,440,120,22),border_radius=3)
        screen.blit(self.font_body.render(tag_val,True,(255,255,255)),(right_x + 56,444))
        self.btn_next_tag.draw(screen,self.font_btn)
        # Status bar centralizada na parte inferior do viewport dinamicamente
        left_w = 230
        vp_w = width - 460
        viewport_center_x = left_w + (vp_w - 480) // 2
        viewport_bottom_y = height - 55
        
        ov = pygame.Surface((480,42),pygame.SRCALPHA)
        ov.fill((30,34,42,200)); screen.blit(ov,(viewport_center_x,viewport_bottom_y))
        pygame.draw.rect(screen,(0,200,255),(viewport_center_x,viewport_bottom_y,480,42),1,border_radius=4)
        snap_tag = " [SNAP]" if self.snap_enabled else ""
        screen.blit(self.font_xyz.render(f"OBJETO: {sel.name.upper()}{snap_tag}",True,(0,200,255)),(viewport_center_x + 10,viewport_bottom_y + 3))
        screen.blit(self.font_body.render(
            f"Pos: X:{pos[0]:.1f} Y:{pos[1]:.1f} Z:{pos[2]:.1f}  "
            f"Tam: X:{sc[0]:.1f} Y:{sc[1]:.1f} Z:{sc[2]:.1f}  "
            f"Rot: X:{int(rot[0])}° Y:{int(rot[1])}° Z:{int(rot[2])}°",
            True,(240,240,240)),(viewport_center_x + 10,viewport_bottom_y + 21))

    def _draw_xyz_widget(self, screen: pygame.Surface) -> None:
        width = screen.get_width()
        right_x = width - 230
        C  = (right_x - 60, 60)
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
            lbl = self.font_xyz.render(label,True,(255,255,255))
            screen.blit(lbl, lbl.get_rect(center=e))
        pygame.draw.circle(screen,(120,125,135),C,4)
        self.gizmo_ex,self.gizmo_ey,self.gizmo_ez = endpoints

    def _draw_help_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        ov.fill((20,24,30,230)); screen.blit(ov,(0,0))
        
        screen_w, screen_h = screen.get_size()
        mw, mh = 760, 520
        mx = (screen_w - mw) // 2
        my = (screen_h - mh) // 2
        
        modal=pygame.Rect(mx,my,mw,mh)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=8)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=8)
        pygame.draw.rect(screen,(42,47,57),pygame.Rect(mx,my,mw,35),border_radius=8)
        screen.blit(self.font_title.render("Guia de Comandos — Zennity Engine",True,(0,200,255)),(mx + 20, my + 8))
        screen.blit(self.font_btn.render("[ESC] Fechar",True,(200,80,80)),(mx + mw - 100, my + 8))
        y = my + 65
        for line in HELP_LINES:
            col=(0,200,255) if line.startswith("  ") else (220,222,226)
            screen.blit(self.font_body.render(line,True,col),(mx + 40, y)); y+=18

    def _draw_templates_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((20,24,30,230)); screen.blit(ov,(0,0))
        
        screen_w, screen_h = screen.get_size()
        mw, mh = 480, 100 + len(self._template_list)*60 + 40
        mx = (screen_w - mw) // 2
        my = (screen_h - mh) // 2
        
        modal = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=8)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=8)
        screen.blit(self.font_title.render("Carregar Template",True,(0,200,255)),(mx + 20, my + 15))
        
        self.btn_templates_close.x = mx + mw - 100
        self.btn_templates_close.y = my + 15
        self.btn_templates_close.draw(screen, self.font_btn)
        
        for i, (btn, tpl) in enumerate(zip(self.btn_template_items, self._template_list)):
            btn.x = mx + 20
            btn.y = my + 60 + i * 60
            btn.width = mw - 40
            btn.draw(screen, self.font_btn)
            desc = tpl.get("_template_desc","")
            if desc:
                screen.blit(self.font_body.render(desc[:55],True,(160,165,175)),(mx + 25, my + 60 + i*60 + 26))

    def _draw_game_view(self, screen: pygame.Surface, left_w: int, vp_w: int, vp_h: int, height: int) -> None:
        game_x = left_w + vp_w // 2
        game_w = vp_w // 2
        
        # Fundo do viewport do jogo (tom ligeiramente mais escuro para distinguir)
        pygame.draw.rect(screen, (22, 24, 30), (game_x, 30, game_w, vp_h))
        
        # Encontra a primeira câmera customizada criada pelo usuário
        spawned_cam = next((obj for obj in self.editable_objects if getattr(obj, "mesh_type", None) == "Camera"), None)
        
        # Salva o estado atual da câmera do editor
        old_vx = self.camera_comp.viewport_x
        old_vy = self.camera_comp.viewport_y
        old_vw = self.camera_comp.viewport_width
        old_vh = self.camera_comp.viewport_height
        old_view = self.camera_comp.view_matrix.copy()
        old_proj = self.camera_comp.projection_matrix.copy()
        
        # Carrega módulos de transformadas
        from engine.graphics.math3d import view_matrix, projection_matrix
        
        self.camera_comp.viewport_x = float(game_x)
        self.camera_comp.viewport_y = 30.0
        self.camera_comp.viewport_width = float(game_w)
        self.camera_comp.viewport_height = float(vp_h)
        
        if spawned_cam:
            self.camera_comp.view_matrix = view_matrix(spawned_cam.transform.position, spawned_cam.transform.rotation)
            self.camera_comp.projection_matrix = projection_matrix(60.0, float(game_w)/float(vp_h), 0.1, 100.0)
        else:
            # Sem câmera criada: usa uma câmera de visualização estática padrão do jogo
            self.camera_comp.view_matrix = view_matrix(np.array([0.0, 3.0, -8.0], np.float32), np.array([15.0, 0.0, 0.0], np.float32))
            self.camera_comp.projection_matrix = projection_matrix(60.0, float(game_w)/float(vp_h), 0.1, 100.0)
            
        # Renderiza a cena sem gizmos, grids ou ícones auxiliares
        for go in self.game_objects:
            if go.name == "EditorCamera" or getattr(go, "mesh_type", "") in ["Camera", "Light"]:
                continue
            go.draw(screen)
            
        # Restaura a câmera do editor
        self.camera_comp.viewport_x = old_vx
        self.camera_comp.viewport_y = old_vy
        self.camera_comp.viewport_width = old_vw
        self.camera_comp.viewport_height = old_vh
        self.camera_comp.view_matrix = old_view
        self.camera_comp.projection_matrix = old_proj

    def _draw_welcome_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((10,14,20,210)); screen.blit(ov,(0,0))
        
        screen_w, screen_h = screen.get_size()
        mw, mh = 600, 220
        mx = (screen_w - mw) // 2
        my = (screen_h - mh) // 2
        
        modal = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=10)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=10)
        step = WELCOME_STEPS[self.welcome_step]
        screen.blit(self.font_title.render(step[0], True,(0,200,255)),(mx + 20, my + 18))
        # word-wrap manual simples
        words = step[1].split()
        line_buf, lines_out = [], []
        for w in words:
            test = " ".join(line_buf+[w])
            if self.font_body.size(test)[0] > 540:
                lines_out.append(" ".join(line_buf))
                line_buf = [w]
            else:
                line_buf.append(w)
        if line_buf: lines_out.append(" ".join(line_buf))
        for i, ln in enumerate(lines_out):
            screen.blit(self.font_body.render(ln,True,(220,222,226)),(mx + 20, my + 50 + i*20))
        total = len(WELCOME_STEPS)
        prog = f"{self.welcome_step+1}/{total}"
        screen.blit(self.font_btn.render(prog,True,(120,125,135)),(mx + 20, my + 168))
        # botões
        if self.welcome_step > 0:
            pygame.draw.rect(screen,(60,65,78),(mx + 170, my + 170, 80, 26),border_radius=5)
            screen.blit(self.font_btn.render("< Anterior",True,(200,200,200)),(mx + 175, my + 176))
        if self.welcome_step < total-1:
            pygame.draw.rect(screen,(40,120,60),(mx + 260, my + 170, 80, 26),border_radius=5)
            screen.blit(self.font_btn.render("Proximo >",True,(255,255,255)),(mx + 265, my + 176))
        else:
            pygame.draw.rect(screen,(40,120,60),(mx + 260, my + 170, 80, 26),border_radius=5)
            screen.blit(self.font_btn.render("Comecar!",True,(255,255,255)),(mx + 265, my + 176))
        pygame.draw.rect(screen,(120,40,40),(mx + mw - 40, my + 15, 30, 22),border_radius=5)
        screen.blit(self.font_btn.render("X",True,(255,255,255)),(mx + mw - 34, my + 18))

    # -----------------------------------------------------------------------
    # handle_event
    # -----------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        # --- Cliques nos menus de topo ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._active_dropdown:
                # Obter opções e coordenadas do dropdown ativo para testar clique
                if self._active_dropdown == "file":
                    opts = ["Novo Scene", "Salvar", "Carregar", "Sair"]
                    rx, ry = 10, 30
                    rw = 120
                elif self._active_dropdown == "view":
                    grade_str = "Desativar Grade" if self.snap_enabled else "Ativar Grade"
                    opts = ["Camera: Persp", "Camera: Top", "Camera: Side", grade_str, "Templates"]
                    rx, ry = 65, 30
                    rw = 150
                elif self._active_dropdown == "window":
                    fs_str = "Modo Janela" if getattr(self.engine, "is_fullscreen", False) else "Tela Cheia"
                    opts = [fs_str + " (F11)", "Guia de Ajuda"]
                    rx, ry = 120, 30
                    rw = 160
                
                rh = len(opts) * 26
                if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                    slot = (my - ry) // 26
                    opt = opts[slot]
                    self._active_dropdown = None
                    
                    if opt == "Novo Scene":
                        # Limpa cena
                        self.history.push(self)
                        for obj in list(self.editable_objects): self._remove_go(obj); obj.destroy()
                        self.editable_objects.clear()
                        self.selected_index = -1
                        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
                        self._tree_scroll = 0
                        self._cancel_rename()
                    elif opt == "Salvar":
                        self.save_scene()
                    elif opt == "Carregar":
                        self.load_scene()
                    elif opt == "Sair":
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                    elif opt == "Camera: Persp":
                        self._set_camera_mode("Perspectiva")
                        self.camera_mode_index = 0
                    elif opt == "Camera: Top":
                        self._set_camera_mode("Top-Down")
                        self.camera_mode_index = 1
                    elif opt == "Camera: Side":
                        self._set_camera_mode("Side-Scroller")
                        self.camera_mode_index = 2
                    elif opt in ["Ativar Grade", "Desativar Grade"]:
                        self.snap_enabled = not self.snap_enabled
                    elif opt == "Templates":
                        self.showing_templates = True
                    elif "Tela Cheia" in opt or "Modo Janela" in opt:
                        if hasattr(self.engine, "toggle_fullscreen"):
                            self.engine.toggle_fullscreen()
                    elif opt == "Guia de Ajuda":
                        self.showing_welcome = True
                        self.welcome_step = 0
                    return
                else:
                    self._active_dropdown = None

            # Clicar nos botões do menu superior para abrir dropdowns
            if self.btn_menu_file.is_clicked(event):
                self._active_dropdown = "file"; return
            if self.btn_menu_view.is_clicked(event):
                self._active_dropdown = "view"; return
            if self.btn_menu_window.is_clicked(event):
                self._active_dropdown = "window"; return

        # Boas-vindas modal
        if self.showing_welcome:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                screen_w, screen_h = pygame.display.get_surface().get_size()
                mw, mh = 600, 220
                w_mx = (screen_w - mw) // 2
                w_my = (screen_h - mh) // 2
                total = len(WELCOME_STEPS)
                # fechar X
                if pygame.Rect(w_mx + mw - 40, w_my + 15, 30, 22).collidepoint(mx,my):
                    self.showing_welcome = False; return
                # anterior
                if self.welcome_step > 0 and pygame.Rect(w_mx + 170, w_my + 170, 80, 26).collidepoint(mx,my):
                    self.welcome_step -= 1; return
                # próximo / começar
                if pygame.Rect(w_mx + 260, w_my + 170, 80, 26).collidepoint(mx,my):
                    if self.welcome_step < total-1:
                        self.welcome_step += 1
                    else:
                        self.showing_welcome = False
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.showing_welcome = False
            return

        # Templates modal
        if self.showing_templates:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_templates_close.is_clicked(event):
                    self.showing_templates = False; return
                for btn, tpl in zip(self.btn_template_items, self._template_list):
                    if btn.is_clicked(event):
                        self._load_template(tpl); return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.showing_templates = False
            return

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

        # --- Rename inline: captura teclado ---
        if self._rename_index >= 0:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._commit_rename(); return
                elif event.key == pygame.K_ESCAPE:
                    self._cancel_rename(); return
                elif event.key == pygame.K_BACKSPACE:
                    self._rename_text = self._rename_text[:-1]; return
                else:
                    ch = event.unicode
                    if ch and ch.isprintable():
                        self._rename_text += ch
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                tree_rect = pygame.Rect(15, _TREE_Y+18, 178, self._tree_h)
                if not tree_rect.collidepoint(mx, my):
                    self._commit_rename()

        if self.btn_add_cube.is_clicked(event):    self.spawn_object("Cube");    return
        if self.btn_add_pyramid.is_clicked(event): self.spawn_object("Pyramid"); return
        if self.btn_add_sphere.is_clicked(event):  self.spawn_object("Sphere");  return
        if self.btn_add_plane.is_clicked(event):   self.spawn_object("Plane");   return
        if self.btn_add_capsule.is_clicked(event): self.spawn_object("Capsule"); return
        if self.btn_add_camera.is_clicked(event):  self.spawn_object("Camera");  return
        if self.btn_add_light.is_clicked(event):   self.spawn_object("Light");   return

        for btn,mode in [(self.btn_mode_translate,"translate"),(self.btn_mode_rotate,"rotate"),(self.btn_mode_scale,"scale")]:
            if btn.is_clicked(event):
                self.gizmo_mode = None if self.gizmo_mode==mode else mode; return

        if self.btn_snap.is_clicked(event):
            self.snap_enabled = not self.snap_enabled; return

        if self.btn_templates.is_clicked(event):
            self.showing_templates = True; return

        if self.btn_camera_mode.is_clicked(event):
            self.camera_mode_index = (self.camera_mode_index + 1) % len(CAMERA_MODES)
            self._set_camera_mode(CAMERA_MODES[self.camera_mode_index]); return

        if self.btn_welcome.is_clicked(event):
            self.showing_welcome = True
            self.welcome_step    = 0; return

        if self.btn_undo.is_clicked(event): self.history.undo(self); return
        if self.btn_redo.is_clicked(event): self.history.redo(self); return

        # Novo, Salvar, Carregar barra superior
        if self.btn_new_scene.is_clicked(event):
            self.history.push(self)
            for obj in list(self.editable_objects):
                self._remove_go(obj); obj.destroy()
            self.editable_objects.clear()
            self.selected_index = -1
            self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
            self._tree_scroll = 0
            self._cancel_rename()
            print("[EditorScene] Nova cena criada.")
            return

        if self.btn_play_pause.is_clicked(event): self._toggle_play(); return
        if self.btn_save.is_clicked(event):       self.save_scene();   return
        if self.btn_load.is_clicked(event):       self.load_scene();   return

        # Scrollbar do Outliner
        if self.btn_tree_up.is_clicked(event):
            self._tree_scroll = max(0, self._tree_scroll - 1); return
        if self.btn_tree_down.is_clicked(event):
            self._tree_scroll = min(self._max_scroll(), self._tree_scroll + 1); return

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
            if mx < _LEFT_W:
                tree_rect = pygame.Rect(15, _TREE_Y+18, 178, self._tree_h)
                if tree_rect.collidepoint(mx, my):
                    slot_i = (my - (_TREE_Y+18)) // _TREE_ROW_H
                    obj_i  = self._tree_scroll + slot_i
                    flat_tree = self._build_flat_tree()
                    if 0 <= obj_i < len(flat_tree):
                        self._drag_tree_src = flat_tree[obj_i][0]
                        self._is_dragging_tree = True
                        return
            width = pygame.display.get_surface().get_width()
            right_limit = 230 + (width - 460) // 2 if self.play_mode else width - 230
            if 230 <= mx <= right_limit and 0<=self.selected_index<len(self.editable_objects):
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
            if self._is_dragging_tree:
                self._is_dragging_tree = False
                mx, my = event.pos
                tree_rect = pygame.Rect(15, _TREE_Y+18, 178, self._tree_h)
                if tree_rect.collidepoint(mx, my):
                    slot_i = (my - (_TREE_Y+18)) // _TREE_ROW_H
                    obj_i  = self._tree_scroll + slot_i
                    flat_tree = self._build_flat_tree()
                    if 0 <= obj_i < len(flat_tree):
                        target_parent = flat_tree[obj_i][0]
                        if target_parent != self._drag_tree_src:
                            curr = target_parent
                            loop = False
                            while curr:
                                if curr == self._drag_tree_src:
                                    loop = True
                                    break
                                curr = curr.parent
                            if not loop:
                                self.history.push(self)
                                self._drag_tree_src.parent = target_parent
                    else:
                        self.history.push(self)
                        self._drag_tree_src.parent = None
                else:
                    self.history.push(self)
                    self._drag_tree_src.parent = None
                    
                if self.click_start_pos:
                    dx = event.pos[0] - self.click_start_pos[0]
                    dy = event.pos[1] - self.click_start_pos[1]
                    if np.hypot(dx, dy) < 4.0:
                        real_idx = self.editable_objects.index(self._drag_tree_src)
                        now = pygame.time.get_ticks() / 1000.0
                        if real_idx == self._last_click_index and (now - self._last_click_time) < 0.4:
                            self._start_rename(real_idx)
                        else:
                            self.selected_index = real_idx
                        self._last_click_index = real_idx
                        self._last_click_time  = now
                self.click_start_pos = None
                return
            if self.click_start_pos:
                dx=event.pos[0]-self.click_start_pos[0]
                dy=event.pos[1]-self.click_start_pos[1]
                if np.hypot(dx,dy)<4.0:
                    mx,my=event.pos
                    # Seleção de objeto na lista/árvore hierárquica
                    if mx<_LEFT_W:
                        tree_rect = pygame.Rect(15, _TREE_Y+18, 178, self._tree_h)
                        if tree_rect.collidepoint(mx, my):
                            slot_i = (my - (_TREE_Y+18)) // _TREE_ROW_H
                            obj_i  = self._tree_scroll + slot_i
                            flat_tree = self._build_flat_tree()
                            if 0 <= obj_i < len(flat_tree):
                                clicked_obj, depth = flat_tree[obj_i]
                                real_idx = self.editable_objects.index(clicked_obj)
                                now = pygame.time.get_ticks() / 1000.0
                                if real_idx == self._last_click_index and (now - self._last_click_time) < 0.4:
                                    self._start_rename(real_idx)
                                else:
                                    self.selected_index = real_idx
                                self._last_click_index = real_idx
                                self._last_click_time  = now
                    elif mx <= (pygame.display.get_surface().get_width() - 230):
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
            
            # Parenting cycling
            if self.btn_prev_parent.is_clicked(event) or self.btn_next_parent.is_clicked(event):
                def is_descendant(p, child):
                    if p == child: return True
                    if p.parent is None: return False
                    return is_descendant(p.parent, child)
                candidates = [None] + [o for o in self.editable_objects if o != sel and not is_descendant(o, sel)]
                cur_parent = sel.parent
                try:    pi = candidates.index(cur_parent)
                except: pi = 0
                delta = -1 if self.btn_prev_parent.is_clicked(event) else 1
                pi = (pi + delta) % len(candidates)
                new_parent = candidates[pi]
                self.history.push(self)
                if cur_parent:
                    cur_parent.remove_child(sel)
                if new_parent:
                    new_parent.add_child(sel)
                return
                
            # Tag cycling
            if self.btn_prev_tag.is_clicked(event) or self.btn_next_tag.is_clicked(event):
                cur_tag = getattr(sel, "tag", "")
                try:    ti = TAG_OPTIONS.index(cur_tag)
                except: ti = 0
                delta = -1 if self.btn_prev_tag.is_clicked(event) else 1
                ti = (ti + delta) % len(TAG_OPTIONS)
                sel.tag = TAG_OPTIONS[ti]; return
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
            PhysicsSim.clear_registries()
