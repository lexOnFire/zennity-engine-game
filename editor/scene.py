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
  - [v2] Sistema visual coeso — theme.py, GuiButton reformulado,
          tipografia com hierarquia, paleta dark profissional
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

from .gui import GuiButton, SectionHeader, Divider, Badge
from .mesh_factory import create_pyramid_mesh, create_sphere_mesh
from .camera_controller import OrbitCameraController
from .physics_sim import PhysicsSim
from .script_manager import ScriptManager
from .code_editor import CodeEditor
from .history import History
from . import theme as T

_IDENTITY = np.eye(4, dtype=np.float32)

_LEFT_W      = 232
_TREE_Y      = 232
_TREE_ROW_H  = 26
SNAP_SIZE    = 0.5

_SHAPE_ICON = {
    "Cube":    "▣",
    "Pyramid": "△",
    "Sphere":  "○",
    "Plane":   "▬",
    "Capsule": "⬭",
    "Camera":  "◈",
    "Light":   "✦",
}

CAMERA_MODES = ["Perspectiva", "Top-Down", "Side-Scroller"]

CAMERA_MODE_PRESETS = {
    "Perspectiva":   {"yaw":  0.0, "pitch": 25.0, "dist": 6.0},
    "Top-Down":      {"yaw":  0.0, "pitch": 89.9, "dist": 8.0},
    "Side-Scroller": {"yaw": 90.0, "pitch":  5.0, "dist": 7.0},
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
    (200, 200, 200), (220,  50,  50), ( 50, 170,  50),
    ( 50, 100, 220), (240, 200,   0), (200,  50, 200),
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


class EditorScene(Scene):

    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        self.font_title = self.font_body = self.font_btn = self.font_xyz = self.font_section = None

        self.camera_comp: Optional[Camera3D] = None
        self.camera_controller: Optional[OrbitCameraController] = None
        self.camera_mode_index: int = 0

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

        # Notificação de status (feedback visual de ações)
        self._status_msg: str = ""
        self._status_timer: float = 0.0
        self._STATUS_DURATION = 2.5

    # -----------------------------------------------------------------------
    def _notify(self, msg: str, kind: str = "info") -> None:
        """Exibe mensagem temporária na status bar."""
        self._status_msg = msg
        self._status_timer = self._STATUS_DURATION
        self._status_kind = kind  # "info" | "success" | "error"

    def start(self) -> None:
        print("[EditorScene] Iniciando editor 3D...")
        # Tipografia com hierarquia clara
        self.font_title   = Assets.get_font(None, 13)   # seção labels (small caps)
        self.font_body    = Assets.get_font(None, 14)   # texto geral
        self.font_btn     = Assets.get_font(None, 13)   # botões
        self.font_xyz     = Assets.get_font(None, 15)   # valores numéricos
        self.font_section = Assets.get_font(None, 11)   # micro labels

        self.available_scripts = ScriptManager.list_scripts()

        # ── Painel esquerdo ── Botões de formas
        _P = T.BTN_PRIMARY
        _PH = T.BTN_PRIMARY_HOVER
        self.btn_add_cube    = GuiButton( 12,  46, 66, 26, "+ Cubo",    _P, _PH)
        self.btn_add_pyramid = GuiButton( 82,  46, 66, 26, "+ Pirâm",   _P, _PH)
        self.btn_add_sphere  = GuiButton(152,  46, 66, 26, "+ Esfera",  _P, _PH)
        self.btn_add_plane   = GuiButton( 12,  76, 66, 26, "+ Plano",   _P, _PH)
        self.btn_add_capsule = GuiButton( 82,  76, 66, 26, "+ Cápsula", _P, _PH)
        self.btn_add_camera  = GuiButton(152,  76, 66, 26, "+ Câmera",  _P, _PH)
        self.btn_add_light   = GuiButton( 12, 106, 66, 26, "+ Luz",     _P, _PH)

        # Gizmo modes
        _G = T.BTN_GIZMO; _GH = T.BTN_GIZMO_HOVER
        self.btn_mode_translate = GuiButton( 12, 140, 66, 26, "⇔ Mover",  _G, _GH)
        self.btn_mode_rotate    = GuiButton( 82, 140, 66, 26, "↻ Girar",  _G, _GH)
        self.btn_mode_scale     = GuiButton(152, 140, 66, 26, "⤢ Escala", _G, _GH)

        _S = T.BTN_SECONDARY; _SH = T.BTN_SECONDARY_HOVER
        self.btn_snap      = GuiButton(12, 172, 208, 22, "Grade: OFF",  _S, _SH)
        self.btn_templates = GuiButton(12, 198, 208, 22, "Templates",   T.BTN_SPECIAL, T.BTN_SPECIAL_HOVER)

        self.btn_undo   = GuiButton( 12, _TREE_Y + self._tree_h + 22, 99, 26, "↩ Desfazer", _S, _SH)
        self.btn_redo   = GuiButton(117, _TREE_Y + self._tree_h + 22, 99, 26, "↪ Refazer",  _S, _SH)
        self.btn_delete = GuiButton( 12, _TREE_Y + self._tree_h + 54, 208, 26,
                                     "✕ Excluir Objeto", T.BTN_DANGER, T.BTN_DANGER_HOVER)

        self.btn_tree_up   = GuiButton(200, _TREE_Y + 20, 26, 20, "▲", _S, _SH)
        self.btn_tree_down = GuiButton(200, _TREE_Y + self._tree_h - 2, 26, 20, "▼", _S, _SH)

        self.btn_light_angle_dec = GuiButton( 12, self._light_y, 38, 22, "<", _S, _SH)
        self.btn_light_angle_inc = GuiButton(178, self._light_y, 38, 22, ">", _S, _SH)

        # ── Barra superior ──
        self.btn_menu_file   = GuiButton( 10, 2, 52, 26, "File",   T.BG,  T.SURFACE)
        self.btn_menu_view   = GuiButton( 66, 2, 52, 26, "View",   T.BG,  T.SURFACE)
        self.btn_menu_window = GuiButton(122, 2, 72, 26, "Window", T.BG,  T.SURFACE)

        # Botões legados fora de tela
        self.btn_new_scene   = GuiButton(-200, -200, 10, 10, "Novo")
        self.btn_save        = GuiButton(-200, -200, 10, 10, "Salvar")
        self.btn_load        = GuiButton(-200, -200, 10, 10, "Carregar")
        self.btn_camera_mode = GuiButton(-200, -200, 10, 10, "Camera")
        self.btn_welcome     = GuiButton(-200, -200, 10, 10, "Ajuda")

        self.btn_play_pause = GuiButton(600, 3, 88, 25, "▶  PLAY",
                                        T.BTN_PRIMARY, T.BTN_PRIMARY_HOVER)

        # ── Inspetor direito ──
        rx = 1170 + 15   # placeholder; reposicionado no update()
        self.btn_toggle_static  = GuiButton(rx,     50, 20, 20, "", _S, _SH)
        self.btn_toggle_physics = GuiButton(rx,     80, 20, 20, "", _S, _SH)
        self.btn_vel_dec        = GuiButton(rx,    135, 38, 20, "−", _S, _SH)
        self.btn_vel_inc        = GuiButton(rx+145,135, 38, 20, "+", _S, _SH)

        self.btn_prev_script     = GuiButton(rx,      190, 28, 22, "<",  _S, _SH)
        self.btn_next_script     = GuiButton(rx + 177,190, 28, 22, ">",  _S, _SH)
        self.btn_new_script      = GuiButton(rx,      215, 194, 20, "+ Novo Script",      _P,  _PH)
        self.btn_edit_script     = GuiButton(rx,      238, 93,  20, "Editor Ext.",        T.BTN_CODE, T.BTN_CODE_HOVER)
        self.btn_internal_editor = GuiButton(rx + 110,238, 84,  20, "Editor Int.",        T.BTN_CODE, T.BTN_CODE_HOVER)
        self.btn_script_help     = GuiButton(rx,      261, 194, 20, "Guia de Comandos",   T.BTN_SPECIAL, T.BTN_SPECIAL_HOVER)
        self.btn_clone           = GuiButton(rx,      352, 194, 26, "⧉ Clonar Objeto",    T.BTN_SPECIAL, T.BTN_SPECIAL_HOVER)

        self.btn_prev_parent = GuiButton(rx,       385, 28, 22, "<", _S, _SH)
        self.btn_next_parent = GuiButton(rx + 177, 385, 28, 22, ">", _S, _SH)
        self.btn_prev_tag    = GuiButton(rx,       440, 28, 22, "<", _S, _SH)
        self.btn_next_tag    = GuiButton(rx + 177, 440, 28, 22, ">", _S, _SH)

        self.btn_colors = [
            GuiButton(rx + i * 32, 312, 26, 26, "", bg_color=c, hover_color=c)
            for i, c in enumerate(COLOR_PALETTE)
        ]

        # Templates modal
        self.showing_templates  = False
        self._template_list     = self._load_template_list()
        self.btn_template_items = []
        for i, tpl in enumerate(self._template_list):
            self.btn_template_items.append(
                GuiButton(280, 120 + i * 60, 440, 48,
                          tpl.get("_template_name", f"Template {i+1}"),
                          T.SURFACE, T.SURFACE_2)
            )
        self.btn_templates_close = GuiButton(660, 80, 80, 28, "Fechar",
                                             T.BTN_DANGER, T.BTN_DANGER_HOVER)

        # ── Câmera ──
        cam_obj = GameObject("EditorCamera")
        self.camera_comp = cam_obj.add_component(Camera3D(
            fov=60.0, near=0.1, far=100.0,
            viewport_x=232.0, viewport_y=30.0,
            viewport_width=940.0, viewport_height=770.0,
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
            count_map = {"Cube": "cube_count", "Pyramid": "pyramid_count",
                         "Sphere": "sphere_count", "Plane": "plane_count",
                         "Capsule": "capsule_count", "Camera": "camera_count", "Light": "light_count"}
            attr = count_map.get(go.mesh_type, "cube_count")
            setattr(self, attr, getattr(self, attr) + 1)
            color = tuple(item["color"])
            go.add_component(self._make_mesh(go.mesh_type, color))
            self._add_go(go)
            self.editable_objects.append(go)
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
        self._notify(f"Template '{tpl.get('_template_name', '')}' carregado!", "success")

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
        from editor.mesh_factory import create_plane_mesh, create_capsule_mesh
        if shape == "Cube":    return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)
        elif shape == "Pyramid": return MeshRenderer3D(create_pyramid_mesh(1.0), color=color)
        elif shape == "Sphere":  return MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=color)
        elif shape == "Plane":   return MeshRenderer3D(create_plane_mesh(size=2.0, subdivisions=2), color=color)
        elif shape == "Capsule": return MeshRenderer3D(create_capsule_mesh(radius=0.4, height=1.0, rings=8, sectors=10), color=color)
        elif shape == "Camera":  return MeshRenderer3D(create_pyramid_mesh(0.5), color=color)
        elif shape == "Light":   return MeshRenderer3D(create_sphere_mesh(radius=0.25, rings=6, sectors=6), color=color)
        else:                    return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)

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
            "Cube":    (  0, 110, 220), "Pyramid": (220,  60,  20),
            "Sphere":  (100,  40, 180), "Plane":   ( 60, 160,  80),
            "Capsule": (200, 140,   0), "Camera":  ( 50, 200, 200),
            "Light":   (255, 230,  50),
        }
        default_names = {
            "Cube":    "Bloco",   "Pyramid": "Piramide", "Sphere":  "Bolinha",
            "Plane":   "Plano",   "Capsule": "Capsula",  "Camera":  "Camera",
            "Light":   "Luz",
        }
        count_map = {
            "Cube": "cube_count", "Pyramid": "pyramid_count", "Sphere": "sphere_count",
            "Plane": "plane_count", "Capsule": "capsule_count",
            "Camera": "camera_count", "Light": "light_count",
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
        self._notify(f"{go.name} adicionado", "success")

    def delete_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self._cancel_rename()
        self.history.push(self)
        go = self.editable_objects.pop(self.selected_index)
        name = go.name
        self._remove_go(go)
        go.destroy()
        self.selected_index = -1 if not self.editable_objects else max(0, self.selected_index - 1)
        self._notify(f"'{name}' excluído", "info")

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
        self._notify(f"'{go.name}' clonado", "success")

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
        flat_objs = [f[0] for f in flat]
        for obj in self.editable_objects:
            if obj not in flat_objs:
                flat.append((obj, 0))
        return flat

    def _start_rename(self, idx: int) -> None:
        if not (0 <= idx < len(self.editable_objects)): return
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
        if idx < 0: return
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
            self._notify("Cena salva com sucesso!", "success")
        except Exception as e:
            self._notify(f"Erro ao salvar: {e}", "error")

    def load_scene(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        if not os.path.exists(path):
            self._notify("Nenhuma cena salva encontrada.", "error"); return
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            self._notify(f"Erro ao carregar: {e}", "error"); return
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
            count_map = {"Cube": "cube_count", "Pyramid": "pyramid_count", "Sphere": "sphere_count",
                         "Plane": "plane_count", "Capsule": "capsule_count",
                         "Camera": "camera_count", "Light": "light_count"}
            attr = count_map.get(go.mesh_type, "cube_count")
            setattr(self, attr, getattr(self, attr) + 1)
            color = tuple(item["color"])
            go.add_component(self._make_mesh(go.mesh_type, color))
            self._add_go(go)
            self.editable_objects.append(go)
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
        self._notify("Cena carregada!", "success")

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
        for x in range(-5, 6): verts += [[x, -0.5, -5.0], [x, -0.5, 5.0]]
        for z in range(-5, 6): verts += [[-5.0, -0.5, z], [5.0, -0.5, z]]
        verts = np.array(verts, np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
        vw, vh = self.camera_comp.viewport_width, self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x, self.camera_comp.viewport_y
        sx = vx + (ndc[:, 0] + 1) * vw / 2
        sy = vy + (-ndc[:, 1] + 1) * vh / 2
        near = self.camera_comp.near
        for i in range(0, len(verts), 2):
            if depths[i] > near and depths[i + 1] > near:
                p0 = (int(sx[i]),   int(sy[i]))
                p1 = (int(sx[i+1]), int(sy[i+1]))
                center = (
                    (abs(verts[i][0]) < 0.01 and abs(verts[i][2] - verts[i+1][2]) > 0.01) or
                    (abs(verts[i][2]) < 0.01 and abs(verts[i][0] - verts[i+1][0]) > 0.01)
                )
                pygame.draw.line(screen, T.grid_color(center), p0, p1, 2 if center else 1)

    # -----------------------------------------------------------------------
    def update(self, dt: float) -> None:
        # Status timer
        if self._status_timer > 0:
            self._status_timer -= dt

        screen_surf = pygame.display.get_surface()
        if screen_surf:
            width, height = screen_surf.get_size()
            left_w  = _LEFT_W
            right_x = width - 230
            vp_w    = right_x - left_w
            vp_h    = height - 30

            self.camera_comp.viewport_x      = float(left_w)
            self.camera_comp.viewport_y      = 30.0
            self.camera_comp.viewport_width  = float(vp_w // 2 if self.play_mode else vp_w)
            self.camera_comp.viewport_height = float(vp_h)

            # Reposicionar botões do inspetor direito
            for btn in [self.btn_toggle_static, self.btn_toggle_physics,
                        self.btn_vel_dec, self.btn_new_script,
                        self.btn_edit_script, self.btn_script_help,
                        self.btn_clone, self.btn_prev_parent, self.btn_prev_tag,
                        self.btn_prev_script, self.btn_new_script]:
                btn.x = right_x + 15
            self.btn_vel_inc.x        = right_x + 145
            self.btn_next_script.x    = right_x + 177
            self.btn_internal_editor.x = right_x + 110
            self.btn_next_parent.x    = right_x + 177
            self.btn_next_tag.x       = right_x + 177
            for i, btn in enumerate(self.btn_colors):
                btn.x = right_x + 15 + i * 32

            self.btn_play_pause.x = width // 2 - 44

            self._tree_h       = max(100, height - _TREE_Y - 180)
            self._tree_max_vis = self._tree_h // _TREE_ROW_H

            self.btn_tree_down.y      = _TREE_Y + self._tree_h - 2
            self.btn_undo.y           = _TREE_Y + self._tree_h + 22
            self.btn_redo.y           = _TREE_Y + self._tree_h + 22
            self.btn_delete.y         = _TREE_Y + self._tree_h + 54
            self._light_y             = _TREE_Y + self._tree_h + 110
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
                if   self.active_gizmo_axis == 'x': sel.transform.scale[0] = max(0.1, sel.transform.scale[0] + dx * 0.015)
                elif self.active_gizmo_axis == 'y': sel.transform.scale[1] = max(0.1, sel.transform.scale[1] - dy * 0.015)
                elif self.active_gizmo_axis == 'z': sel.transform.scale[2] = max(0.1, sel.transform.scale[2] - dy * 0.015)
                elif self.active_gizmo_axis == 'center':
                    ns = max(0.1, sel.transform.scale[0] + (dx - dy) * 0.015)
                    sel.transform.scale = np.array([ns, ns, ns], np.float32)
            elif self.gizmo_mode == "rotate":
                if   self.active_gizmo_axis == 'x': sel.transform.rotation[0] = (sel.transform.rotation[0] + dy * 0.5) % 360
                elif self.active_gizmo_axis == 'y': sel.transform.rotation[1] = (sel.transform.rotation[1] + dx * 0.5) % 360
                elif self.active_gizmo_axis == 'z': sel.transform.rotation[2] = (sel.transform.rotation[2] + dx * 0.5) % 360
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
                yr = np.radians(self.camera_controller.yaw)
                pr = np.radians(self.camera_controller.pitch)
                right = np.array([np.cos(yr), 0.0, -np.sin(yr)], np.float32)
                up    = np.array([np.sin(pr) * np.sin(yr), np.cos(pr), np.sin(pr) * np.cos(yr)], np.float32)
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
        width, height = screen.get_size()
        left_w  = _LEFT_W
        right_x = width - 230
        vp_w    = right_x - left_w
        vp_h    = height - 30

        if self.play_mode:
            pygame.draw.rect(screen, T.VIEWPORT_BG, (left_w, 30, vp_w // 2, vp_h))
            self._draw_floor_grid(screen)
            for go in self.game_objects:
                go.draw(screen)
                if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                    r = go.get_component(MeshRenderer3D)
                    if r:
                        ow, oc, olw = r.wireframe, r.color, r.line_width
                        r.wireframe, r.color, r.line_width = True, T.ACCENT, 3
                        r.draw(screen)
                        r.wireframe, r.color, r.line_width = ow, oc, olw
            self._draw_gizmo(screen)
            self._draw_game_view(screen, left_w, vp_w, vp_h, height)
            pygame.draw.line(screen, T.BORDER, (left_w + vp_w // 2, 30), (left_w + vp_w // 2, height), 2)
            self._draw_viewport_badge(screen, left_w + 8,          38, "EDIT MODE",      T.ACCENT)
            self._draw_viewport_badge(screen, left_w + vp_w//2 + 8, 38, "GAME VIEW (PLAY)", T.SUCCESS)
        else:
            pygame.draw.rect(screen, T.VIEWPORT_BG, (left_w, 30, vp_w, vp_h))
            self._draw_floor_grid(screen)
            for go in self.game_objects:
                go.draw(screen)
                if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                    r = go.get_component(MeshRenderer3D)
                    if r:
                        ow, oc, olw = r.wireframe, r.color, r.line_width
                        r.wireframe, r.color, r.line_width = True, T.ACCENT, 3
                        r.draw(screen)
                        r.wireframe, r.color, r.line_width = ow, oc, olw
            self._draw_gizmo(screen)
            self._draw_viewport_badge(screen, left_w + 8, 38, "EDIT MODE", T.ACCENT)

        self._draw_left_panel(screen)
        self._draw_top_bar(screen)
        self._draw_right_panel(screen)
        self._draw_xyz_widget(screen)
        self._draw_status_bar(screen)

        if self.showing_templates:
            self._draw_templates_modal(screen)
        elif self.code_editor.is_open:
            self.code_editor.draw(screen)
        elif self.showing_help_modal:
            self._draw_help_modal(screen)
        elif self.showing_welcome:
            self._draw_welcome_modal(screen)

        self._draw_dropdowns(screen)

        if self._is_dragging_tree and self._drag_tree_src:
            mx, my = pygame.mouse.get_pos()
            label = f"Mover {self._drag_tree_src.name} para..."
            pygame.draw.rect(screen, T.BTN_ACTIVE, (mx + 15, my + 5, 200, 24), border_radius=4)
            screen.blit(self.font_body.render(label, True, T.TEXT_PRIMARY), (mx + 22, my + 9))

    # -----------------------------------------------------------------------
    # Draw helpers
    # -----------------------------------------------------------------------
    def _draw_viewport_badge(self, screen, x, y, text, color):
        """Badge colorido sobre a viewport (EDIT MODE / GAME VIEW)."""
        surf = self.font_btn.render(text, True, color)
        w = surf.get_width() + 14
        pygame.draw.rect(screen, T.PANEL,  (x, y, w, 18), border_radius=3)
        pygame.draw.rect(screen, color,    (x, y, w, 18), 1, border_radius=3)
        screen.blit(surf, (x + 7, y + 2))

    def _draw_status_bar(self, screen: pygame.Surface) -> None:
        """Barra de status inferior com feedback das últimas ações."""
        width, height = screen.get_size()
        bar_h = 22
        pygame.draw.rect(screen, T.PANEL,  (0, height - bar_h, width, bar_h))
        pygame.draw.line(screen, T.BORDER, (0, height - bar_h), (width, height - bar_h), 1)

        # Objetos + modo snap
        info = f"  {len(self.editable_objects)} objeto(s)   Grade: {'ON' if self.snap_enabled else 'OFF'}   Hist: {len(self.history._undo)} undo / {len(self.history._redo)} redo"
        screen.blit(self.font_section.render(info, True, T.TEXT_MUTED), (8, height - bar_h + 4))

        # Mensagem de status (temporária)
        if self._status_timer > 0 and self._status_msg:
            alpha = min(1.0, self._status_timer)
            kind_colors = {"info": T.ACCENT, "success": T.SUCCESS, "error": T.ERROR}
            col = kind_colors.get(getattr(self, "_status_kind", "info"), T.ACCENT)
            # fade simples: cor mais clara quando quase sumindo
            faded = T.alpha_blend(col, alpha, T.PANEL)
            surf = self.font_section.render(f"● {self._status_msg}", True, faded)
            screen.blit(surf, (width // 2 - surf.get_width() // 2, height - bar_h + 4))

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
        if not all(d > near for d in depths): return
        vw, vh = self.camera_comp.viewport_width,  self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x,      self.camera_comp.viewport_y
        def ts(i): return int(vx + (ndc[i, 0] + 1) * vw / 2), int(vy + (-ndc[i, 1] + 1) * vh / 2)
        c, px, py, pz = ts(0), ts(1), ts(2), ts(3)
        self.gizmo_screen_points = {'x': px, 'y': py, 'z': pz}
        self.gizmo_screen_center = c

        def draw_triangle(surface, color, pt, center):
            dx = pt[0] - center[0]; dy = pt[1] - center[1]
            dist = np.hypot(dx, dy)
            if dist > 0:
                ux, uy = dx / dist, dy / dist
                px_, py_ = -uy, ux
                p1 = (pt[0] + ux * 8, pt[1] + uy * 8)
                p2 = (pt[0] - ux * 8 + px_ * 6, pt[1] - uy * 8 + py_ * 6)
                p3 = (pt[0] - ux * 8 - px_ * 6, pt[1] - uy * 8 - py_ * 6)
                pygame.draw.polygon(surface, color, [p1, p2, p3])

        if self.gizmo_mode == "rotate":
            for pts_fn, col in [
                (lambda t: P + np.array([0.8*np.cos(t), 0, 0.8*np.sin(t)], np.float32), T.GIZMO_Y),
                (lambda t: P + np.array([0, 0.8*np.cos(t), 0.8*np.sin(t)], np.float32), T.GIZMO_X),
                (lambda t: P + np.array([0.8*np.cos(t), 0.8*np.sin(t), 0], np.float32), T.GIZMO_Z),
            ]:
                ring = np.array([pts_fn(t) for t in np.linspace(0, 2*np.pi, 20)], np.float32)
                rn, rd = project_vertices(ring, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                pts = [(int(vx+(rn[k,0]+1)*vw/2), int(vy+(-rn[k,1]+1)*vh/2))
                       for k in range(len(ring)) if rd[k] > near]
                if len(pts) > 1: pygame.draw.lines(screen, col, True, pts, 2)
            draw_triangle(screen, T.GIZMO_X, px, c)
            draw_triangle(screen, T.GIZMO_Y, py, c)
            draw_triangle(screen, T.GIZMO_Z, pz, c)
        else:
            pygame.draw.line(screen, T.GIZMO_X, c, px, 3)
            pygame.draw.line(screen, T.GIZMO_Y, c, py, 3)
            pygame.draw.line(screen, T.GIZMO_Z, c, pz, 3)
            if self.gizmo_mode == "translate":
                for pt, col in [(px, T.GIZMO_X), (py, T.GIZMO_Y), (pz, T.GIZMO_Z)]:
                    pygame.draw.circle(screen, col, pt, 7)
            elif self.gizmo_mode == "scale":
                for pt, col in [(px, T.GIZMO_X), (py, T.GIZMO_Y), (pz, T.GIZMO_Z)]:
                    pygame.draw.rect(screen, col, (pt[0]-6, pt[1]-6, 12, 12))
                pygame.draw.circle(screen, T.GIZMO_W, c, 6)

    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        height = screen.get_height()
        # Fundo do painel
        pygame.draw.rect(screen, T.PANEL, (0, 30, _LEFT_W, height - 30))
        pygame.draw.line(screen, T.BORDER, (_LEFT_W, 30), (_LEFT_W, height), 1)

        # ── Seção: Formas ──
        SectionHeader(12, 36, _LEFT_W - 16, "Adicionar").draw(screen, self.font_section)
        for btn in [self.btn_add_cube, self.btn_add_pyramid, self.btn_add_sphere,
                    self.btn_add_plane, self.btn_add_capsule, self.btn_add_camera, self.btn_add_light]:
            btn.draw(screen, self.font_btn)

        # ── Seção: Gizmo ──
        SectionHeader(12, 128, _LEFT_W - 16, "Transformar").draw(screen, self.font_section)
        for btn, mode in [(self.btn_mode_translate, "translate"),
                          (self.btn_mode_rotate,    "rotate"),
                          (self.btn_mode_scale,     "scale")]:
            active = (self.gizmo_mode == mode)
            btn.bg_color    = T.BTN_ACTIVE      if active else T.BTN_GIZMO
            btn.hover_color = T.BTN_ACTIVE_HOVER if active else T.BTN_GIZMO_HOVER
            btn.draw(screen, self.font_btn)

        # ── Snap + Templates ──
        self.btn_snap.text      = f"Grade: {'ON  (G)' if self.snap_enabled else 'OFF (G)'}"
        self.btn_snap.bg_color  = (25, 90, 58) if self.snap_enabled else T.BTN_SECONDARY
        self.btn_snap.draw(screen, self.font_btn)
        self.btn_templates.draw(screen, self.font_btn)

        # ── Seção: Cena (Outliner) ──
        SectionHeader(12, _TREE_Y - 14, _LEFT_W - 16, "Objetos da Cena").draw(screen, self.font_section)

        # Caixa da tree
        tree_rect = pygame.Rect(12, _TREE_Y, 184, self._tree_h)
        pygame.draw.rect(screen, T.BG,     tree_rect, border_radius=4)
        pygame.draw.rect(screen, T.BORDER, tree_rect, 1, border_radius=4)

        flat_tree = self._build_flat_tree()
        total = len(flat_tree)
        max_s = self._max_scroll()
        self._tree_scroll = min(self._tree_scroll, max_s)

        for slot_i in range(self._tree_max_vis):
            obj_i = self._tree_scroll + slot_i
            if obj_i >= total: break
            obj, depth = flat_tree[obj_i]
            sel = (0 <= self.selected_index < len(self.editable_objects)
                   and self.editable_objects[self.selected_index] == obj)

            ry  = _TREE_Y + slot_i * _TREE_ROW_H
            row = pygame.Rect(13, ry, 182, _TREE_ROW_H - 1)

            if sel:
                pygame.draw.rect(screen, T.ACCENT_BG, row, border_radius=3)
                pygame.draw.rect(screen, T.ACCENT,    row, 1, border_radius=3)
            else:
                # hover sutil
                mx, my = pygame.mouse.get_pos()
                if row.collidepoint(mx, my):
                    pygame.draw.rect(screen, T.SURFACE, row, border_radius=3)

            indent = min(depth, 4) * 10
            icon   = _SHAPE_ICON.get(getattr(obj, "mesh_type", "Cube"), "▣")
            icon_col = T.ACCENT if sel else T.TEXT_MUTED
            screen.blit(self.font_section.render(icon, True, icon_col), (18 + indent, ry + 7))

            # Renomeação inline
            if self._rename_index >= 0 and self.editable_objects[self._rename_index] == obj:
                pygame.draw.rect(screen, T.SURFACE_2, (32 + indent, ry + 3, 152 - indent, _TREE_ROW_H - 6), border_radius=2)
                pygame.draw.rect(screen, T.ACCENT,    (32 + indent, ry + 3, 152 - indent, _TREE_ROW_H - 6), 1, border_radius=2)
                display = self._rename_text + ("|" if self._rename_cursor_on else "")
                screen.blit(self.font_body.render(display, True, T.TEXT_PRIMARY), (35 + indent, ry + 5))
            else:
                label   = obj.name
                max_len = 18 - (indent // 10) * 2
                if len(label) > max_len: label = label[:max(5, max_len-2)] + ".."
                name_col = T.TEXT_PRIMARY if sel else T.TEXT_PRIMARY
                tag      = getattr(obj, "tag", "")
                screen.blit(self.font_body.render(label, True, name_col), (32 + indent, ry + 5))
                if tag:
                    # mini badge de tag
                    ts = self.font_section.render(tag, True, T.WARNING)
                    screen.blit(ts, (155 - ts.get_width(), ry + 7))

        # Scrollbar
        if total > self._tree_max_vis:
            bar_h = max(16, self._tree_h * self._tree_max_vis // max(total, 1))
            bar_y = _TREE_Y + (self._tree_h - bar_h) * self._tree_scroll // max(max_s, 1)
            pygame.draw.rect(screen, T.BORDER, (196, bar_y, 4, bar_h), border_radius=2)
            self.btn_tree_up.draw(screen, self.font_btn)
            self.btn_tree_down.draw(screen, self.font_btn)

        # Undo/Redo/Delete
        Divider(12, _TREE_Y + self._tree_h + 8, _LEFT_W - 24).draw(screen)
        self.btn_undo.bg_color    = T.BTN_ACTIVE     if self.history.can_undo else T.BTN_SECONDARY
        self.btn_redo.bg_color    = T.BTN_ACTIVE     if self.history.can_redo else T.BTN_SECONDARY
        self.btn_undo.hover_color = T.BTN_ACTIVE_HOVER if self.history.can_undo else T.BTN_SECONDARY_HOVER
        self.btn_redo.hover_color = T.BTN_ACTIVE_HOVER if self.history.can_redo else T.BTN_SECONDARY_HOVER
        self.btn_undo.draw(screen, self.font_btn)
        self.btn_redo.draw(screen, self.font_btn)
        if 0 <= self.selected_index < len(self.editable_objects):
            self.btn_delete.draw(screen, self.font_btn)

        # ── Seção: Luz ──
        Divider(12, self._light_y - 18, _LEFT_W - 24).draw(screen)
        SectionHeader(12, self._light_y - 14, _LEFT_W - 16, "Direção da Luz").draw(screen, self.font_section)
        self.btn_light_angle_dec.draw(screen, self.font_btn)
        angle_surf = self.font_xyz.render(f"{int(self.light_angle)}°", True, T.TEXT_PRIMARY)
        screen.blit(angle_surf, (60 + (100 - angle_surf.get_width()) // 2, self._light_y + 2))
        self.btn_light_angle_inc.draw(screen, self.font_btn)

    def _draw_top_bar(self, screen: pygame.Surface) -> None:
        width = screen.get_width()
        pygame.draw.rect(screen, T.PANEL, (0, 0, width, 30))
        pygame.draw.line(screen, T.BORDER, (0, 30), (width, 30), 1)

        # Logo / nome
        logo = self.font_body.render("Zennity", True, T.ACCENT)
        screen.blit(logo, (8, 7))
        # linha separadora após logo
        pygame.draw.line(screen, T.BORDER, (70, 4), (70, 26), 1)

        self.btn_menu_file.draw(screen,   self.font_btn)
        self.btn_menu_view.draw(screen,   self.font_btn)
        self.btn_menu_window.draw(screen, self.font_btn)

        # PLAY / STOP
        if self.play_mode:
            self.btn_play_pause.bg_color    = T.BTN_DANGER
            self.btn_play_pause.hover_color = T.BTN_DANGER_HOVER
            self.btn_play_pause.text        = "■  STOP"
        else:
            self.btn_play_pause.bg_color    = T.BTN_PRIMARY
            self.btn_play_pause.hover_color = T.BTN_PRIMARY_HOVER
            self.btn_play_pause.text        = "▶  PLAY"
        self.btn_play_pause.draw(screen, self.font_btn)

        # Undo/Redo counter (canto direito)
        undo_col = T.ACCENT    if self.history.can_undo else T.TEXT_FAINT
        redo_col = T.ACCENT    if self.history.can_redo else T.TEXT_FAINT
        screen.blit(self.font_btn.render(f"↩ {len(self.history._undo)}", True, undo_col), (width - 120, 8))
        screen.blit(self.font_btn.render(f"↪ {len(self.history._redo)}", True, redo_col), (width -  68, 8))

    def _draw_dropdowns(self, screen: pygame.Surface) -> None:
        if not self._active_dropdown: return
        if self._active_dropdown == "file":
            opts = ["Novo Scene", "Salvar", "Carregar", "Sair"]
            rx, ry, rw = 10, 30, 130
        elif self._active_dropdown == "view":
            grade_str = "Desativar Grade" if self.snap_enabled else "Ativar Grade"
            opts = ["Camera: Persp", "Camera: Top", "Camera: Side", grade_str, "Templates"]
            rx, ry, rw = 66, 30, 155
        elif self._active_dropdown == "window":
            fs_str = "Modo Janela" if getattr(self.engine, "is_fullscreen", False) else "Tela Cheia"
            opts = [fs_str + " (F11)", "Guia de Ajuda"]
            rx, ry, rw = 122, 30, 165
        else:
            return
        rh = len(opts) * 28
        pygame.draw.rect(screen, T.SURFACE, (rx, ry, rw, rh), border_radius=4)
        pygame.draw.rect(screen, T.BORDER,  (rx, ry, rw, rh), 1, border_radius=4)
        mx, my = pygame.mouse.get_pos()
        for i, opt in enumerate(opts):
            row_rect = pygame.Rect(rx + 1, ry + i * 28 + 1, rw - 2, 26)
            if row_rect.collidepoint(mx, my):
                pygame.draw.rect(screen, T.BTN_ACTIVE, row_rect, border_radius=3)
            screen.blit(self.font_body.render(opt, True, T.TEXT_PRIMARY), (rx + 10, ry + i * 28 + 6))

    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        width, height = screen.get_size()
        right_x = width - 230
        pygame.draw.rect(screen, T.PANEL, (right_x, 30, 230, height - 30))
        pygame.draw.line(screen, T.BORDER, (right_x, 30), (right_x, height), 1)

        if not (0 <= self.selected_index < len(self.editable_objects)):
            # Empty state
            empty_surf = self.font_body.render("Nenhum objeto selecionado", True, T.TEXT_FAINT)
            screen.blit(empty_surf, (right_x + (230 - empty_surf.get_width()) // 2, 80))
            return

        sel = self.editable_objects[self.selected_index]
        pos, rot, sc = sel.transform.position, sel.transform.rotation, sel.transform.scale
        rx = right_x + 15

        # ── Cabeçalho do objeto ──
        name_surf = self.font_xyz.render(sel.name, True, T.TEXT_PRIMARY)
        icon      = _SHAPE_ICON.get(getattr(sel, "mesh_type", "Cube"), "▣")
        icon_surf = self.font_xyz.render(icon, True, T.ACCENT)
        screen.blit(icon_surf, (rx, 36))
        screen.blit(name_surf, (rx + 20, 36))
        Divider(rx, 56, 200).draw(screen)

        # ── Física ──
        SectionHeader(rx, 62, 200, "Física").draw(screen, self.font_section)
        self.btn_toggle_static.draw(screen, self.font_btn)
        cb_col = T.ACCENT if getattr(sel, "is_static", False) else T.BORDER
        pygame.draw.rect(screen, cb_col, (rx + 3, 53, 14, 14), border_radius=3 if not getattr(sel, "is_static", False) else 0)
        if getattr(sel, "is_static", False): pygame.draw.rect(screen, T.ACCENT, (rx + 3, 53, 14, 14))
        screen.blit(self.font_body.render("Estático", True, T.TEXT_PRIMARY), (rx + 28, 52))

        self.btn_toggle_physics.draw(screen, self.font_btn)
        if getattr(sel, "use_physics", True): pygame.draw.rect(screen, T.ACCENT, (rx + 3, 83, 14, 14))
        screen.blit(self.font_body.render("Gravidade", True, T.TEXT_PRIMARY), (rx + 28, 82))

        screen.blit(self.font_section.render("IMPULSO VERTICAL", True, T.TEXT_MUTED), (rx, 112))
        self.btn_vel_dec.draw(screen, self.font_btn)
        val_surf = self.font_xyz.render(f"{sel.initial_velocity_y:+.1f} m/s", True, T.TEXT_PRIMARY)
        screen.blit(val_surf, (rx + 48, 135))
        self.btn_vel_inc.draw(screen, self.font_btn)

        Divider(rx, 162, 200).draw(screen)

        # ── Scripts ──
        SectionHeader(rx, 168, 200, "Comportamento").draw(screen, self.font_section)
        self.btn_prev_script.draw(screen, self.font_btn)
        pygame.draw.rect(screen, T.BG, (rx + 34, 190, 138, 22), border_radius=3)
        pygame.draw.rect(screen, T.BORDER, (rx + 34, 190, 138, 22), 1, border_radius=3)
        sn = os.path.basename(getattr(sel, "script_path", "")) or "Nenhum"
        if len(sn) > 14: sn = sn[:12] + ".."
        screen.blit(self.font_body.render(sn, True, T.TEXT_PRIMARY), (rx + 40, 193))
        self.btn_next_script.draw(screen, self.font_btn)
        for btn in [self.btn_new_script, self.btn_edit_script,
                    self.btn_internal_editor, self.btn_script_help]:
            btn.draw(screen, self.font_btn)

        Divider(rx, 282, 200).draw(screen)

        # ── Cor ──
        SectionHeader(rx, 288, 200, "Cor").draw(screen, self.font_section)
        renderer = sel.get_component(MeshRenderer3D)
        for i, btn in enumerate(self.btn_colors):
            btn.draw(screen, self.font_btn)
            if renderer and tuple(renderer.color) == tuple(COLOR_PALETTE[i]):
                pygame.draw.rect(screen, T.TEXT_PRIMARY,
                                 (btn.rect.x - 2, btn.rect.y - 2, btn.rect.w + 4, btn.rect.h + 4), 2, border_radius=6)

        Divider(rx, 344, 200).draw(screen)

        # ── Clone ──
        self.btn_clone.draw(screen, self.font_btn)

        # ── Hierarquia ──
        Divider(rx, 378, 200).draw(screen)
        SectionHeader(rx, 382, 200, "Hierarquia").draw(screen, self.font_section)
        self.btn_prev_parent.draw(screen, self.font_btn)
        parent_name = sel.parent.name if getattr(sel, "parent", None) else "(raiz)"
        pygame.draw.rect(screen, T.BG, (rx + 34, 385, 138, 22), border_radius=3)
        pygame.draw.rect(screen, T.BORDER, (rx + 34, 385, 138, 22), 1, border_radius=3)
        screen.blit(self.font_body.render(parent_name, True, T.TEXT_MUTED), (rx + 40, 388))
        self.btn_next_parent.draw(screen, self.font_btn)

        # ── Tag ──
        Divider(rx, 412, 200).draw(screen)
        SectionHeader(rx, 418, 200, "Tag").draw(screen, self.font_section)
        self.btn_prev_tag.draw(screen, self.font_btn)
        tag_val = getattr(sel, "tag", "") or "(sem tag)"
        tag_col  = T.WARNING if getattr(sel, "tag", "") else T.TEXT_FAINT
        pygame.draw.rect(screen, T.BG, (rx + 34, 440, 138, 22), border_radius=3)
        pygame.draw.rect(screen, T.BORDER, (rx + 34, 440, 138, 22), 1, border_radius=3)
        screen.blit(self.font_body.render(tag_val, True, tag_col), (rx + 40, 443))
        self.btn_next_tag.draw(screen, self.font_btn)

        # ── Transform (posição / rotação / escala) ──
        Divider(rx, 470, 200).draw(screen)
        SectionHeader(rx, 476, 200, "Transform").draw(screen, self.font_section)
        for label, vec, y0 in [("Pos", pos, 492), ("Rot", rot, 520), ("Esc", sc, 548)]:
            screen.blit(self.font_section.render(label, True, T.TEXT_MUTED), (rx, y0))
            for j, (axis, col) in enumerate([("X", T.GIZMO_X), ("Y", T.GIZMO_Y), ("Z", T.GIZMO_Z)]):
                screen.blit(self.font_section.render(axis, True, col), (rx + 30 + j * 58, y0))
                val_s = self.font_section.render(f"{vec[j]:.2f}", True, T.TEXT_PRIMARY)
                screen.blit(val_s, (rx + 40 + j * 58, y0))
