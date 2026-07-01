"""
Cena principal do editor 3D da Zennity Engine.
Melhorias nesta versão:
  - Undo/Redo (Ctrl+Z / Ctrl+Shift+Z)
  - PhysicsSim integrado com RigidBody3D da engine
  - MOUSEWHEEL correto (pygame.MOUSEWHEEL)
  - Snap de grade configurável
  - Visualização de câmera secundária (Game View)
  - Arrastamento com Shift+drag
  - Gizmos de translação/rotação/escala com travamento de eixo
  - Sistema de templates de cena
  - Editor de código interno
  - Tag / Layer / Parent por ciclo de botão
  - Outliner com drag-and-drop de hierarquia
  - fix: TAG_OPTIONS global, _new_scene(), _hit_gizmo()
"""
from __future__ import annotations

import json
import os
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pygame

from engine.scene import Scene
from engine.game_object import GameObject
from engine.transform import Transform
from engine.components.mesh_renderer_3d import MeshRenderer3D
from engine.components.camera_3d import Camera3D
from engine.components.collider_3d import BoxCollider3D
from engine.components.rigidbody_3d import RigidBody3D
from engine.component import Component
from editor.camera_controller import OrbitCameraController
from editor.code_editor import CodeEditor
from editor.physics_sim import PhysicsSim
from editor.script_manager import ScriptManager
from editor.undo_history import UndoHistory
from editor.gui_button import GuiButton
from editor.layout import EditorLayout

# ── Constantes visuais ──────────────────────────────────────────────────────
TOP_BAR_H   = 36
STATUS_BAR_H = 22
TREE_Y      = TOP_BAR_H + 8
TREE_ROW_H  = 22

WELCOME_STEPS = [
    {
        "title": "Bem-vindo ao Zennity Editor 3D",
        "body": (
            "Este é o editor de cenas 3D da Zennity Engine.\n"
            "Navegue pelas abas para conhecer os recursos disponíveis."
        ),
    },
    {
        "title": "Adicionando objetos",
        "body": (
            "Use o painel esquerdo para adicionar formas à cena.\n"
            "Clique em 'Cubo', 'Pirâmide', 'Esfera', etc."
        ),
    },
    {
        "title": "Transformando objetos",
        "body": (
            "Selecione um objeto e use os gizmos coloridos para mover,\n"
            "rotacionar ou escalar. Segure Shift para arrastar livremente."
        ),
    },
    {
        "title": "Play Mode",
        "body": (
            "Clique em ▶ PLAY para simular física e scripts.\n"
            "Clique em ⏹ STOP para restaurar o estado original."
        ),
    },
]

# Paleta de cores disponível no inspector
COLOR_PALETTE = [
    (220,  80,  80),   # vermelho
    ( 80, 160, 220),   # azul
    ( 80, 200, 120),   # verde
    (230, 180,  50),   # amarelo
    (180,  80, 220),   # roxo
    (220, 130,  60),   # laranja
    (200, 200, 200),   # cinza
    ( 60,  60,  60),   # escuro
]

TAG_OPTIONS = ["", "Player", "Enemy", "Collectible", "Trigger", "Ground", "Wall", "Hazard", "Pickup"]

# ── Paleta de interface ──────────────────────────────────────────────────────
UI_BG        = ( 30,  30,  32)
UI_PANEL     = ( 40,  40,  44)
UI_PANEL2    = ( 50,  50,  55)
UI_ACCENT    = ( 70, 130, 180)
UI_ACCENT2   = ( 90, 160, 210)
UI_TEXT      = (220, 220, 225)
UI_TEXT_DIM  = (140, 140, 148)
UI_BORDER    = ( 60,  60,  68)
UI_SUCCESS   = ( 80, 200, 100)
UI_WARN      = (220, 160,  50)
UI_ERROR     = (220,  80,  80)
UI_GRID      = ( 55,  55,  60)


class EditorScene(Scene):
    """Cena principal do editor 3D — gerencia viewport, painéis e input."""

    # ──────────────────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()

        self._lay: EditorLayout = EditorLayout(800, 600)

        # Objetos editáveis
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        # Câmera
        self._cam_go: Optional[GameObject] = None
        self.camera_controller: Optional[OrbitCameraController] = None
        self._camera_modes = ["Perspective", "Orthographic", "Top", "Front", "Side"]
        self._camera_mode_index = 0

        # Gizmo
        self.gizmo_mode = "translate"          # translate | rotate | scale
        self.gizmo_screen_points: Dict[str, Optional[Tuple[int, int]]] = {}
        self.gizmo_screen_center: Optional[Tuple[int, int]] = None

        # Arrasto de gizmo
        self.is_dragging_gizmo  = False
        self.active_gizmo_axis  = ""
        self.gizmo_drag_last_mouse: Optional[Tuple[int, int]] = None

        # Arrasto livre (Shift+LMB)
        self.is_dragging_object = False
        self.drag_object_last_mouse: Optional[Tuple[int, int]] = None

        # Arrasto de árvore
        self._drag_tree_src: Optional[GameObject] = None
        self._drag_tree_y: int = 0
        self.click_start_pos: Optional[Tuple[int, int]] = None

        # Rename inline
        self._rename_index: int = -1
        self._rename_text: str = ""
        self._last_click_index: int = -1
        self._last_click_time: float = 0.0

        # Scroll do outliner
        self._tree_scroll: int = 0

        # Snap de grade
        self.snap_enabled: bool = False
        self.snap_size:    float = 0.5

        # Play mode
        self.play_mode: bool = False
        self.saved_scene_state: Optional[List[Dict]] = None

        # Luz direcional
        self.light_angle: float = 45.0

        # Dropdowns
        self._active_dropdown: Optional[str] = None

        # Notificações flutuantes
        self._notifs: List[Dict] = []

        # Modais
        self.showing_welcome:   bool = True
        self.welcome_step:      int  = 0
        self.showing_help_modal:  bool = False
        self.showing_templates: bool = False

        # Templates e scripts
        self._template_list: List[Dict] = []
        self.available_scripts: List[str] = []

        # Undo/redo
        self.history: UndoHistory = UndoHistory()

        # Editor de código interno
        self.code_editor: CodeEditor = CodeEditor()

        # Botões (criados em start())
        self.btn_play_pause:        GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_menu_file:         GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_menu_view:         GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_menu_window:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_cube:          GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_pyramid:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_sphere:        GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_plane:         GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_capsule:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_camera:        GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_add_light:         GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_mode_translate:    GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_mode_rotate:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_mode_scale:        GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_snap:              GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_templates:         GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_undo:              GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_redo:              GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_delete:            GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_clone:             GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_toggle_static:     GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_toggle_physics:    GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_vel_dec:           GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_vel_inc:           GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_prev_script:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_next_script:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_new_script:        GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_edit_script:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_internal_editor:   GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_script_help:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_prev_parent:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_next_parent:       GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_prev_tag:          GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_next_tag:          GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_light_angle_dec:   GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_light_angle_inc:   GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_tree_up:           GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_tree_down:         GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_welcome_close:     GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_welcome_next:      GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_welcome_prev:      GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_templates_close:   GuiButton = GuiButton(0, 0, 1, 1, "")
        self.btn_new_scene:         GuiButton = GuiButton(-200, -200, 10, 10, "Novo")
        self.btn_colors:            List[GuiButton] = []
        self.btn_template_items:    List[GuiButton] = []

    # ──────────────────────────────────────────────────────────────────────────
    def _notify(self, msg: str, kind: str = "info") -> None:
        color = {"info": UI_TEXT, "success": UI_SUCCESS, "warn": UI_WARN, "error": UI_ERROR}.get(kind, UI_TEXT)
        self._notifs.append({"msg": msg, "color": color, "t": 2.5})

    # ──────────────────────────────────────────────────────────────────────────
    def start(self) -> None:
        surf = pygame.display.get_surface()
        w, h = (surf.get_width(), surf.get_height()) if surf else (800, 600)
        self._lay = EditorLayout(w, h)

        # ── Câmera orbital ────────────────────────────────────────────────────
        cam_go = GameObject("EditorCamera")
        cam_go.transform.position = np.array([0.0, 3.0, 6.0], dtype=np.float32)
        cam_go.add_component(Camera3D(fov=60.0))
        ctrl = OrbitCameraController()
        cam_go.add_component(ctrl)
        self.camera_controller = ctrl
        self._cam_go = cam_go
        self.add_game_object(cam_go)

        # ── Formas padrão ─────────────────────────────────────────────────────
        self.spawn_object("Cube")
        self.spawn_object("Plane")

        # ── Templates e scripts ───────────────────────────────────────────────
        self._template_list = self._load_template_list()
        self.available_scripts = ScriptManager.list_scripts()

        # ── Botões ─────────────────────────────────────────────────────────────
        self._build_buttons()
        self._reposition_buttons()

    # ──────────────────────────────────────────────────────────────────────────
    def _build_buttons(self) -> None:
        G = GuiButton
        ph = -200

        self.btn_play_pause        = G(ph, ph, 90, 24, "▶  PLAY",   bg=(50, 120, 60), hover=(70, 150, 80))
        self.btn_menu_file         = G(ph, ph, 48, 24, "Arquivo")
        self.btn_menu_view         = G(ph, ph, 48, 24, "Exibir")
        self.btn_menu_window       = G(ph, ph, 56, 24, "Janela")

        self.btn_add_cube          = G(ph, ph, 110, 22, "🧊 Cubo")
        self.btn_add_pyramid       = G(ph, ph, 110, 22, "🔺 Pirâmide")
        self.btn_add_sphere        = G(ph, ph, 110, 22, "⚪ Esfera")
        self.btn_add_plane         = G(ph, ph, 110, 22, "▬ Plano")
        self.btn_add_capsule       = G(ph, ph, 110, 22, "💊 Cápsula")
        self.btn_add_camera        = G(ph, ph, 110, 22, "📷 Câmera")
        self.btn_add_light         = G(ph, ph, 110, 22, "💡 Luz")

        self.btn_mode_translate    = G(ph, ph, 34, 22, "T",  bg=(60, 100, 140))
        self.btn_mode_rotate       = G(ph, ph, 34, 22, "R",  bg=(60, 100, 140))
        self.btn_mode_scale        = G(ph, ph, 34, 22, "S",  bg=(60, 100, 140))

        self.btn_snap              = G(ph, ph, 110, 22, "Grade: OFF")
        self.btn_templates         = G(ph, ph, 110, 22, "📋 Templates")

        self.btn_undo              = G(ph, ph, 50, 22, "↩ Undo")
        self.btn_redo              = G(ph, ph, 50, 22, "↪ Redo")
        self.btn_delete            = G(ph, ph, 50, 22, "🗑 Del",  bg=(100, 40, 40), hover=(140, 50, 50))

        self.btn_tree_up           = G(ph, ph, 18, 14, "▲")
        self.btn_tree_down         = G(ph, ph, 18, 14, "▼")

        self.btn_light_angle_dec   = G(ph, ph, 24, 18, "◀")
        self.btn_light_angle_inc   = G(ph, ph, 24, 18, "▶")

        self.btn_clone             = G(ph, ph, 110, 22, "⎘ Clonar")
        self.btn_toggle_static     = G(ph, ph, 110, 22, "Estático: OFF")
        self.btn_toggle_physics    = G(ph, ph, 110, 22, "Física: OFF")
        self.btn_vel_dec           = G(ph, ph, 24, 18, "▼")
        self.btn_vel_inc           = G(ph, ph, 24, 18, "▲")
        self.btn_prev_script       = G(ph, ph, 18, 18, "◀")
        self.btn_next_script       = G(ph, ph, 18, 18, "▶")
        self.btn_new_script        = G(ph, ph, 110, 18, "+ Novo Script")
        self.btn_edit_script       = G(ph, ph, 110, 18, "✏ Editar Script")
        self.btn_internal_editor   = G(ph, ph, 110, 18, "📝 Abrir Editor")
        self.btn_script_help       = G(ph, ph, 18, 18, "?")
        self.btn_prev_parent       = G(ph, ph, 18, 18, "◀")
        self.btn_next_parent       = G(ph, ph, 18, 18, "▶")
        self.btn_prev_tag          = G(ph, ph, 18, 18, "◀")
        self.btn_next_tag          = G(ph, ph, 18, 18, "▶")

        self.btn_colors = [
            G(ph, ph, 18, 18, "", bg=c, hover=tuple(min(255, v + 40) for v in c))
            for c in COLOR_PALETTE
        ]

        self.btn_welcome_close     = G(ph, ph, 80, 26, "Fechar")
        self.btn_welcome_next      = G(ph, ph, 80, 26, "Próximo ▶")
        self.btn_welcome_prev      = G(ph, ph, 80, 26, "◀ Anterior")
        self.btn_templates_close   = G(ph, ph, 80, 26, "Fechar")
        self.btn_template_items    = [
            G(ph, ph, 200, 24, tpl.get("_template_name", f"Template {i}"))
            for i, tpl in enumerate(self._template_list)
        ]

    # ──────────────────────────────────────────────────────────────────────────
    def _load_template_list(self) -> List[Dict]:
        path = os.path.join(os.path.dirname(__file__), "templates")
        result: List[Dict] = []
        if not os.path.isdir(path):
            return result
        for fname in sorted(os.listdir(path)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(path, fname)) as f:
                        data = json.load(f)
                    if "_template_name" not in data:
                        data["_template_name"] = fname[:-5]
                    result.append(data)
                except Exception:
                    pass
        return result

    # ──────────────────────────────────────────────────────────────────────────
    def _load_template(self, tpl: Dict) -> None:
        for obj in list(self.editable_objects):
            self._remove_go(obj)
        self.editable_objects.clear()
        self.selected_index = -1

        for obj_data in tpl.get("objects", []):
            shape = obj_data.get("shape", "Cube")
            color = tuple(obj_data.get("color", [200, 200, 200]))
            go = self.spawn_object(shape, color=color, _register=False)
            pos = obj_data.get("position", [0, 0, 0])
            rot = obj_data.get("rotation", [0, 0, 0])
            sc  = obj_data.get("scale",    [1, 1, 1])
            go.transform.position = np.array(pos, dtype=np.float32)
            go.transform.rotation = np.array(rot, dtype=np.float32)
            go.transform.scale    = np.array(sc,  dtype=np.float32)
            self._add_go(go)

    # ──────────────────────────────────────────────────────────────────────────
    def _set_camera_mode(self, mode_name: str) -> None:
        self._camera_mode_index = self._camera_modes.index(mode_name) if mode_name in self._camera_modes else 0

    def _add_go(self, go: GameObject) -> None:
        self.add_game_object(go)
        if go not in self.editable_objects:
            self.editable_objects.append(go)

    def _remove_go(self, go: GameObject) -> None:
        self.remove_game_object(go)
        if go in self.editable_objects:
            self.editable_objects.remove(go)

    def _snap(self, v: np.ndarray) -> np.ndarray:
        if not self.snap_enabled:
            return v
        s = self.snap_size
        return np.round(v / s) * s

    def _make_mesh(self, shape: str, color: tuple):
        return MeshRenderer3D(shape=shape, color=color)

    # ──────────────────────────────────────────────────────────────────────────
    def spawn_object(self, shape: str, color: Optional[tuple] = None, _register: bool = True) -> GameObject:
        default_colors = {
            "Cube":     (180, 100, 100),
            "Pyramid":  (100, 180, 100),
            "Sphere":   (100, 100, 200),
            "Plane":    ( 80, 160,  80),
            "Capsule":  (180, 140,  80),
            "Camera":   (200, 200,  80),
            "Light":    (255, 220,  80),
        }
        c = color if color else default_colors.get(shape, (180, 180, 180))
        name = f"{shape}_{len(self.editable_objects) + 1}"
        go = GameObject(name)
        go.transform.position = self._snap(
            np.array([
                (len(self.editable_objects) % 5) * 1.5 - 3.0,
                0.5 if shape != "Plane" else 0.0,
                -(len(self.editable_objects) // 5) * 1.5,
            ], dtype=np.float32)
        )
        if shape not in ("Camera", "Light"):
            go.add_component(self._make_mesh(shape, c))
            go.add_component(BoxCollider3D())
        else:
            dummy = MeshRenderer3D(shape="Cube", color=c)
            dummy.visible = False
            go.add_component(dummy)
        self.history.push(self)
        if _register:
            self._add_go(go)
        return go

    # ──────────────────────────────────────────────────────────────────────────
    def delete_selected(self) -> None:
        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return
        self.history.push(self)
        go = self.editable_objects[self.selected_index]
        self._remove_go(go)
        self.selected_index = min(self.selected_index, len(self.editable_objects) - 1)

    def clone_selected(self) -> None:
        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return
        src = self.editable_objects[self.selected_index]
        r   = src.get_component(MeshRenderer3D)
        shape = getattr(r, "shape", "Cube") if r else "Cube"
        color = getattr(r, "color", (180, 180, 180)) if r else (180, 180, 180)
        clone = self.spawn_object(shape, color=color, _register=False)
        clone.transform.position = src.transform.position.copy() + np.array([0.5, 0.0, 0.0])
        clone.transform.rotation = src.transform.rotation.copy()
        clone.transform.scale    = src.transform.scale.copy()
        clone.name               = src.name + "_clone"
        self.history.push(self)
        self._add_go(clone)
        self.selected_index = len(self.editable_objects) - 1

    # ──────────────────────────────────────────────────────────────────────────
    def _build_flat_tree(self) -> List[Tuple[GameObject, int]]:
        roots = [o for o in self.editable_objects if getattr(o, "parent", None) is None]
        result: List[Tuple[GameObject, int]] = []

        def visit(go: GameObject, depth: int) -> None:
            result.append((go, depth))
            for child in getattr(go, "children", []):
                if child in self.editable_objects:
                    visit(child, depth + 1)

        for r in roots:
            visit(r, 0)
        return result

    def _start_rename(self, idx: int) -> None:
        if 0 <= idx < len(self.editable_objects):
            self._rename_index = idx
            self._rename_text  = self.editable_objects[idx].name

    def _commit_rename(self) -> None:
        if 0 <= self._rename_index < len(self.editable_objects) and self._rename_text.strip():
            self.editable_objects[self._rename_index].name = self._rename_text.strip()
        self._rename_index = -1
        self._rename_text  = ""

    def _cancel_rename(self) -> None:
        self._rename_index = -1
        self._rename_text  = ""

    def _tree_scroll_to(self, idx: int) -> None:
        lay = self._lay
        visible_rows = (lay.left_panel_h - TREE_Y - 30) // TREE_ROW_H
        if idx < self._tree_scroll:
            self._tree_scroll = idx
        elif idx >= self._tree_scroll + visible_rows:
            self._tree_scroll = idx - visible_rows + 1

    def _max_scroll(self) -> int:
        lay = self._lay
        visible_rows = max(1, (lay.left_panel_h - TREE_Y - 30) // TREE_ROW_H)
        return max(0, len(self.editable_objects) - visible_rows)

    # ──────────────────────────────────────────────────────────────────────────
    def save_scene(self) -> None:
        data: Dict = {"objects": []}
        for go in self.editable_objects:
            r = go.get_component(MeshRenderer3D)
            entry = {
                "name":     go.name,
                "shape":    getattr(r, "shape", "Cube") if r else "Cube",
                "color":    list(getattr(r, "color", (180, 180, 180))) if r else [180, 180, 180],
                "position": go.transform.position.tolist(),
                "rotation": go.transform.rotation.tolist(),
                "scale":    go.transform.scale.tolist(),
                "tag":      getattr(go, "tag", ""),
                "is_static":       getattr(go, "is_static", False),
                "physics_enabled": getattr(go, "physics_enabled", False),
                "script_path":     getattr(go, "script_path", ""),
                "parent":   (go.parent.name if getattr(go, "parent", None) else ""),
            }
            data["objects"].append(entry)
        path = os.path.join(os.getcwd(), "editor_scene.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self._notify(f"Cena salva em {path}", "success")

    def load_scene(self) -> None:
        path = os.path.join(os.getcwd(), "editor_scene.json")
        if not os.path.exists(path):
            self._notify("Arquivo editor_scene.json não encontrado", "error")
            return
        with open(path) as f:
            data = json.load(f)
        for obj in list(self.editable_objects):
            self._remove_go(obj)
        self.editable_objects.clear()
        self.selected_index = -1
        name_map: Dict[str, GameObject] = {}
        for entry in data.get("objects", []):
            shape = entry.get("shape", "Cube")
            color = tuple(entry.get("color", [180, 180, 180]))
            go = self.spawn_object(shape, color=color, _register=False)
            go.name = entry.get("name", go.name)
            go.transform.position = np.array(entry.get("position", [0, 0, 0]), dtype=np.float32)
            go.transform.rotation = np.array(entry.get("rotation", [0, 0, 0]), dtype=np.float32)
            go.transform.scale    = np.array(entry.get("scale",    [1, 1, 1]),  dtype=np.float32)
            go.tag               = entry.get("tag", "")
            go.is_static         = entry.get("is_static", False)
            go.physics_enabled   = entry.get("physics_enabled", False)
            go.script_path       = entry.get("script_path", "")
            self._add_go(go)
            name_map[go.name] = go
        for entry in data.get("objects", []):
            pname = entry.get("parent", "")
            if pname and entry["name"] in name_map and pname in name_map:
                child = name_map[entry["name"]]
                parent = name_map[pname]
                if hasattr(parent, "add_child"):
                    parent.add_child(child)
        self._notify("Cena carregada!", "success")

    # ──────────────────────────────────────────────────────────────────────────
    def _select_at(self, mx: int, my: int) -> None:
        lay = self._lay
        cam = self._cam_go.get_component(Camera3D) if self._cam_go else None
        if cam is None:
            return
        vp = lay.viewport_rect
        nx = (mx - vp.left) / vp.width  * 2 - 1
        ny = 1 - (my - vp.top) / vp.height * 2
        ctrl = self.camera_controller
        yr = np.radians(ctrl.yaw)
        pr = np.radians(ctrl.pitch)
        fwd = np.array([-np.sin(yr) * np.cos(pr), -np.sin(pr), -np.cos(yr) * np.cos(pr)], dtype=np.float32)
        right = np.array([np.cos(yr), 0, -np.sin(yr)], dtype=np.float32)
        up = np.cross(right, fwd)
        fov_rad = np.radians(60.0)
        aspect = vp.width / max(1, vp.height)
        ray_dir = (fwd + right * nx * np.tan(fov_rad / 2) * aspect + up * ny * np.tan(fov_rad / 2))
        ray_dir /= np.linalg.norm(ray_dir)
        ray_orig = self._cam_go.transform.position.copy()

        best_t = float("inf")
        best_i = -1
        for i, go in enumerate(self.editable_objects):
            half = go.transform.scale * 0.5
            pos  = go.transform.position
            t_min, t_max = -1e9, 1e9
            for axis in range(3):
                d = ray_dir[axis]
                if abs(d) < 1e-8:
                    if abs(ray_orig[axis] - pos[axis]) > half[axis]:
                        t_min, t_max = 1.0, -1.0
                        break
                    continue
                t1 = (pos[axis] - half[axis] - ray_orig[axis]) / d
                t2 = (pos[axis] + half[axis] - ray_orig[axis]) / d
                t_min = max(t_min, min(t1, t2))
                t_max = min(t_max, max(t1, t2))
            if t_min <= t_max and t_min > 0 and t_min < best_t:
                best_t = t_min
                best_i = i

        self.selected_index = best_i

    # ──────────────────────────────────────────────────────────────────────────
    def _draw_floor_grid(self, screen: pygame.Surface) -> None:
        lay     = self._lay
        ctrl    = self.camera_controller
        vp      = lay.viewport_rect
        cx, cy  = vp.centerx, vp.centery
        GRID_N  = 10
        CELL_PX = max(20, int(120 / max(1.0, ctrl.distance)))

        yr = np.radians(ctrl.yaw)
        pr = np.radians(ctrl.pitch)

        def world_to_screen(wx: float, wz: float) -> Tuple[int, int]:
            rx = wx * np.cos(yr) + wz * np.sin(yr)
            rz = -wx * np.sin(yr) + wz * np.cos(yr)
            sx = int(cx + rx * CELL_PX)
            sy = int(cy + rz * CELL_PX * np.sin(pr) + 0 * np.cos(pr))
            return sx, sy

        for i in range(-GRID_N, GRID_N + 1):
            p1 = world_to_screen(i, -GRID_N)
            p2 = world_to_screen(i,  GRID_N)
            p3 = world_to_screen(-GRID_N, i)
            p4 = world_to_screen( GRID_N, i)
            col = (70, 70, 75) if i != 0 else (90, 90, 100)
            pygame.draw.line(screen, col, p1, p2)
            pygame.draw.line(screen, col, p3, p4)

    # ──────────────────────────────────────────────────────────────────────────
    def _reposition_buttons(self) -> None:
        lay = self._lay
        w, h = lay.screen_w, lay.screen_h
        lw   = lay.left_panel_w
        rw   = lay.right_panel_w
        rx   = lay.right_panel_x

        cy = TOP_BAR_H // 2 - 12
        self.btn_menu_file.set_rect(10,  cy, 48, 24)
        self.btn_menu_view.set_rect(62,  cy, 48, 24)
        self.btn_menu_window.set_rect(114, cy, 56, 24)
        self.btn_play_pause.set_rect(w // 2 - 45, cy, 90, 24)

        bx = (lw - 110) // 2
        by = TOP_BAR_H + 30
        for btn, label in [
            (self.btn_add_cube,    "🧊 Cubo"),
            (self.btn_add_pyramid, "🔺 Pirâmide"),
            (self.btn_add_sphere,  "⚪ Esfera"),
            (self.btn_add_plane,   "▬ Plano"),
            (self.btn_add_capsule, "💊 Cápsula"),
            (self.btn_add_camera,  "📷 Câmera"),
            (self.btn_add_light,   "💡 Luz"),
        ]:
            btn.label = label
            btn.set_rect(bx, by, 110, 22)
            by += 26

        by += 8
        for i, btn in enumerate([self.btn_mode_translate, self.btn_mode_rotate, self.btn_mode_scale]):
            btn.set_rect(bx + i * 38, by, 34, 22)
        by += 28

        self.btn_snap.set_rect(bx, by, 110, 22);       by += 26
        self.btn_templates.set_rect(bx, by, 110, 22);  by += 26
        self.btn_undo.set_rect(bx,      by, 50, 22)
        self.btn_redo.set_rect(bx + 54, by, 50, 22);   by += 26
        self.btn_delete.set_rect(bx, by, 110, 22);     by += 26

        self.btn_tree_up.set_rect(lw - 22, TOP_BAR_H + 4, 18, 14)
        self.btn_tree_down.set_rect(lw - 22, h - STATUS_BAR_H - 18, 18, 14)

        lx = bx
        self.btn_light_angle_dec.set_rect(lx,      h - STATUS_BAR_H - 26, 24, 18)
        self.btn_light_angle_inc.set_rect(lx + 86, h - STATUS_BAR_H - 26, 24, 18)

        ix = rx + 8
        iy = TOP_BAR_H + 8

        self.btn_clone.set_rect(ix, iy, rw - 16, 22);           iy += 26
        self.btn_toggle_static.set_rect(ix, iy, rw - 16, 22);   iy += 26
        self.btn_toggle_physics.set_rect(ix, iy, rw - 16, 22);  iy += 26

        self.btn_vel_dec.set_rect(ix,      iy, 24, 18)
        self.btn_vel_inc.set_rect(ix + rw - 40, iy, 24, 18);    iy += 24

        iy += 8
        for i, btn in enumerate(self.btn_colors):
            btn.set_rect(ix + i * 20, iy, 18, 18)
        iy += 26

        iy += 8
        self.btn_prev_script.set_rect(ix, iy, 18, 18)
        self.btn_next_script.set_rect(ix + rw - 26, iy, 18, 18);  iy += 22
        self.btn_new_script.set_rect(ix, iy, rw - 16, 18);         iy += 22
        self.btn_edit_script.set_rect(ix, iy, rw - 16, 18);        iy += 22
        self.btn_internal_editor.set_rect(ix, iy, rw - 16, 18);    iy += 22
        self.btn_script_help.set_rect(ix + rw - 26, iy - 22, 18, 18)

        iy += 8
        self.btn_prev_parent.set_rect(ix, iy, 18, 18)
        self.btn_next_parent.set_rect(ix + rw - 26, iy, 18, 18);  iy += 22

        self.btn_prev_tag.set_rect(ix, iy, 18, 18)
        self.btn_next_tag.set_rect(ix + rw - 26, iy, 18, 18);     iy += 22

        mx_c, my_c = w // 2, h // 2
        self.btn_welcome_close.set_rect(mx_c + 60, my_c + 80, 80, 26)
        self.btn_welcome_prev.set_rect(mx_c - 160, my_c + 80, 80, 26)
        self.btn_welcome_next.set_rect(mx_c + 60, my_c + 80, 80, 26)
        self.btn_templates_close.set_rect(mx_c + 110, my_c - 120, 80, 26)
        for i, btn in enumerate(self.btn_template_items):
            btn.set_rect(mx_c - 110, my_c - 100 + i * 28, 220, 24)

    # ──────────────────────────────────────────────────────────────────────────
    def update(self, dt: float) -> None:
        surf = pygame.display.get_surface()
        if surf:
            sw, sh = surf.get_size()
            if sw != self._lay.screen_w or sh != self._lay.screen_h:
                self._lay = EditorLayout(sw, sh)
                self._reposition_buttons()

        if self._cam_go and self.camera_controller:
            self.camera_controller.update(dt)

        if self.play_mode:
            PhysicsSim.step(self.editable_objects, dt)
            ScriptManager.update_all(self.editable_objects, dt)

        if self.is_dragging_gizmo and self.gizmo_drag_last_mouse:
            mx, my = pygame.mouse.get_pos()
            if not pygame.mouse.get_pressed()[0]:
                self.is_dragging_gizmo = False
                self.active_gizmo_axis = ""
            elif self.selected_index >= 0:
                dx = mx - self.gizmo_drag_last_mouse[0]
                dy = my - self.gizmo_drag_last_mouse[1]
                sel = self.editable_objects[self.selected_index]
                speed = 0.01 * self.camera_controller.distance
                axis_map = {"x": 0, "y": 1, "z": 2}
                a = axis_map.get(self.active_gizmo_axis, -1)
                delta2d = dx - dy
                if a >= 0:
                    if self.gizmo_mode == "translate":
                        sel.transform.position[a] += delta2d * speed
                        sel.transform.position = self._snap(sel.transform.position)
                    elif self.gizmo_mode == "rotate":
                        sel.transform.rotation[a] = (sel.transform.rotation[a] + delta2d * 0.5) % 360
                    elif self.gizmo_mode == "scale":
                        sel.transform.scale[a] = max(0.05, sel.transform.scale[a] + delta2d * speed)
                elif self.active_gizmo_axis == "center":
                    if self.gizmo_mode == "translate":
                        ctrl = self.camera_controller
                        yr = np.radians(ctrl.yaw)
                        right = np.array([np.cos(yr), 0, -np.sin(yr)], dtype=np.float32)
                        sel.transform.position += right * dx * speed
                        sel.transform.position[1] -= dy * speed
                        sel.transform.position = self._snap(sel.transform.position)
                self.gizmo_drag_last_mouse = (mx, my)

        if self.is_dragging_object and self.drag_object_last_mouse:
            mx, my = pygame.mouse.get_pos()
            if not pygame.mouse.get_pressed()[0]:
                self.is_dragging_object = False
            elif self.selected_index >= 0:
                dx = mx - self.drag_object_last_mouse[0]
                dy = my - self.drag_object_last_mouse[1]
                sel = self.editable_objects[self.selected_index]
                speed = 0.008 * self.camera_controller.distance
                ctrl = self.camera_controller
                yr = np.radians(ctrl.yaw)
                right = np.array([np.cos(yr), 0, -np.sin(yr)], dtype=np.float32)
                sel.transform.position += right * dx * speed
                sel.transform.position[1] -= dy * speed
                sel.transform.position = self._snap(sel.transform.position)
                self.drag_object_last_mouse = (mx, my)

        for n in self._notifs:
            n["t"] -= dt
        self._notifs = [n for n in self._notifs if n["t"] > 0]

    # ──────────────────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface) -> None:
        lay = self._lay
        screen.fill(UI_BG)

        vp = lay.viewport_rect
        pygame.draw.rect(screen, (22, 22, 26), vp)
        self._draw_floor_grid(screen)
        self._render_3d(screen)
        if self.selected_index >= 0:
            self._draw_gizmo(screen)

        pygame.draw.rect(screen, UI_PANEL,  pygame.Rect(0, TOP_BAR_H, lay.left_panel_w, lay.screen_h - TOP_BAR_H))
        pygame.draw.rect(screen, UI_PANEL,  pygame.Rect(lay.right_panel_x, TOP_BAR_H, lay.right_panel_w, lay.screen_h - TOP_BAR_H))
        pygame.draw.rect(screen, UI_PANEL2, pygame.Rect(0, 0, lay.screen_w, TOP_BAR_H))

        self._draw_top_bar(screen)
        self._draw_left_panel(screen)
        self._draw_right_panel(screen)
        self._draw_status_bar(screen)
        self._draw_dropdowns(screen)

        if lay.game_view_rect:
            self._draw_game_view(screen)

        self._draw_xyz_widget(screen)

        font = pygame.font.SysFont("segoeui", 13)
        ny = lay.screen_h - STATUS_BAR_H - 28
        for n in sorted(self._notifs, key=lambda x: -x["t"])[:4]:
            surf  = font.render(n["msg"], True, n["color"])
            screen.blit(surf, (lay.left_panel_w + 10, ny))
            ny -= 20

        if self.showing_welcome:
            self._draw_welcome_modal(screen)
        if self.showing_help_modal:
            self._draw_help_modal(screen)
        if self.showing_templates:
            self._draw_templates_modal(screen)

        if self.code_editor.is_open:
            self.code_editor.draw(screen)

    # ──────────────────────────────────────────────────────────────────────────
    def _draw_viewport_badge(self, screen, x, y, text, color):
        font = pygame.font.SysFont("segoeui", 11)
        surf = font.render(text, True, color)
        screen.blit(surf, (x, y))

    def _draw_game_view(self, screen: pygame.Surface) -> None:
        lay = self._lay
        gv  = lay.game_view_rect
        pygame.draw.rect(screen, (15, 15, 18), gv)
        pygame.draw.rect(screen, UI_BORDER, gv, 1)
        self._draw_viewport_badge(screen, gv.x + 4, gv.y + 4, "GAME VIEW", UI_ACCENT2)

    def _draw_status_bar(self, screen: pygame.Surface) -> None:
        lay = self._lay
        bar = pygame.Rect(0, lay.screen_h - STATUS_BAR_H, lay.screen_w, STATUS_BAR_H)
        pygame.draw.rect(screen, UI_PANEL2, bar)
        font = pygame.font.SysFont("segoeui", 12)

        mode   = self._camera_modes[self._camera_mode_index]
        objs   = len(self.editable_objects)
        sel    = self.editable_objects[self.selected_index].name if 0 <= self.selected_index < objs else "—"
        verts  = sum(
            len(getattr(go.get_component(MeshRenderer3D), "vertices", [])) // 3
            for go in self.editable_objects
            if go.get_component(MeshRenderer3D)
        )
        snap_s = f"Snap {self.snap_size}u" if self.snap_enabled else "Snap OFF"
        parts  = [f"Câmera: {mode}", f"Objetos: {objs}", f"Selecionado: {sel}", f"Verts ~{verts}", snap_s]
        x = 8
        for p in parts:
            s = font.render(p, True, UI_TEXT_DIM)
            screen.blit(s, (x, lay.screen_h - STATUS_BAR_H + 4))
            x += s.get_width() + 20

    # ──────────────────────────────────────────────────────────────────────────
    def _draw_gizmo(self, screen: pygame.Surface) -> None:
        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return

        lay  = self._lay
        vp   = lay.viewport_rect
        ctrl = self.camera_controller
        sel  = self.editable_objects[self.selected_index]

        def project(wp: np.ndarray) -> Optional[Tuple[int, int]]:
            yr = np.radians(ctrl.yaw)
            pr = np.radians(ctrl.pitch)
            cam_pos = ctrl.transform.position
            d = wp - cam_pos
            cy2, sy2 = np.cos(-yr), np.sin(-yr)
            dx, dz = d[0] * cy2 - d[2] * sy2, d[0] * sy2 + d[2] * cy2
            d = np.array([dx, d[1], dz])
            cp, sp = np.cos(-np.radians(ctrl.pitch)), np.sin(-np.radians(ctrl.pitch))
            dy2, dz2 = d[1] * cp - d[2] * sp, d[1] * sp + d[2] * cp
            d = np.array([d[0], dy2, dz2])
            if d[2] >= -0.01:
                return None
            fov_h = np.tan(np.radians(30))
            fov_v = fov_h * vp.height / max(1, vp.width)
            sx = int(vp.centerx - d[0] / (-d[2]) * vp.width  / (2 * fov_h))
            sy = int(vp.centery - d[1] / (-d[2]) * vp.height / (2 * fov_v))
            return sx, sy

        pos = sel.transform.position
        GIZMO_LEN = 0.6
        axes = {
            "x": (pos + np.array([GIZMO_LEN, 0, 0]), (220, 80, 80)),
            "y": (pos + np.array([0, GIZMO_LEN, 0]), (80, 200, 80)),
            "z": (pos + np.array([0, 0, GIZMO_LEN]), (80, 80, 220)),
        }
        center_pt = project(pos)
        self.gizmo_screen_center = center_pt
        self.gizmo_screen_points = {}

        if center_pt:
            for axis, (tip_wp, col) in axes.items():
                tip_sp = project(tip_wp)
                self.gizmo_screen_points[axis] = tip_sp
                if tip_sp:
                    pygame.draw.line(screen, col, center_pt, tip_sp, 2)
                    pygame.draw.circle(screen, col, tip_sp, 5)
            pygame.draw.circle(screen, (255, 255, 255), center_pt, 5)
            pygame.draw.circle(screen, (0, 0, 0),       center_pt, 3)

    # ──────────────────────────────────────────────────────────────────────────
    def _render_3d(self, screen: pygame.Surface) -> None:
        lay = self._lay
        vp  = lay.viewport_rect
        ctrl = self.camera_controller
        if ctrl is None:
            return

        rad = np.radians(self.light_angle)
        light_dir = np.array([np.cos(rad), 1.0, np.sin(rad)], dtype=np.float32)
        norm = np.linalg.norm(light_dir)
        if norm > 0:
            light_dir /= norm

        for i, go in enumerate(self.editable_objects):
            r = go.get_component(MeshRenderer3D)
            if r is None or not getattr(r, "visible", True):
                continue
            r.light_dir = light_dir
            r.draw(screen, go.transform, ctrl, vp, selected=(i == self.selected_index))

    # ──────────────────────────────────────────────────────────────────────────
    def _draw_xyz_widget(self, screen: pygame.Surface) -> None:
        lay  = self._lay
        ctrl = self.camera_controller
        if ctrl is None:
            return
        cx   = lay.left_panel_w + 48
        cy   = TOP_BAR_H + 48
        R    = 28
        yr   = np.radians(ctrl.yaw)
        pr   = np.radians(ctrl.pitch)

        axes_w = {
            "X": np.array([ 1.0,  0.0,  0.0]),
            "Y": np.array([ 0.0,  1.0,  0.0]),
            "Z": np.array([ 0.0,  0.0,  1.0]),
        }
        colors = {"X": (220, 80, 80), "Y": (80, 200, 80), "Z": (80, 80, 220)}

        def w2s(v):
            x2 = v[0] * np.cos(yr) - v[2] * np.sin(yr)
            z2 = v[0] * np.sin(yr) + v[2] * np.cos(yr)
            y2 = v[1] * np.cos(pr) - z2 * np.sin(pr)
            return int(cx + x2 * R), int(cy - y2 * R)

        font = pygame.font.SysFont("segoeui", 11, bold=True)
        for label, aw in axes_w.items():
            sp = w2s(aw)
            pygame.draw.line(screen, colors[label], (cx, cy), sp, 2)
            pygame.draw.circle(screen, colors[label], sp, 4)
            screen.blit(font.render(label, True, colors[label]), (sp[0] + 4, sp[1] - 6))

    # ──────────────────────────────────────────────────────────────────────────
    def _modal_overlay(self, screen: pygame.Surface, w: int, h: int) -> pygame.Rect:
        lay = self._lay
        overlay = pygame.Surface((lay.screen_w, lay.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(lay.screen_w // 2 - w // 2, lay.screen_h // 2 - h // 2, w, h)
        pygame.draw.rect(screen, UI_PANEL2, rect, border_radius=8)
        pygame.draw.rect(screen, UI_BORDER, rect, 1, border_radius=8)
        return rect

    def _draw_welcome_modal(self, screen: pygame.Surface) -> None:
        rect = self._modal_overlay(screen, 380, 220)
        step = WELCOME_STEPS[min(self.welcome_step, len(WELCOME_STEPS) - 1)]
        font_t = pygame.font.SysFont("segoeui", 16, bold=True)
        font_b = pygame.font.SysFont("segoeui", 13)

        t = font_t.render(step["title"], True, UI_TEXT)
        screen.blit(t, (rect.x + 20, rect.y + 20))

        y = rect.y + 50
        for line in step["body"].split("\n"):
            s = font_b.render(line, True, UI_TEXT_DIM)
            screen.blit(s, (rect.x + 20, y))
            y += 20

        pg = font_b.render(f"{self.welcome_step + 1}/{len(WELCOME_STEPS)}", True, UI_TEXT_DIM)
        screen.blit(pg, (rect.x + rect.w // 2 - pg.get_width() // 2, rect.y + rect.h - 40))

        bw, bh = 80, 26
        bcy = rect.y + rect.h - 30
        self.btn_welcome_close.set_rect(rect.x + rect.w - 90, bcy, bw, bh)
        self.btn_welcome_next.set_rect(rect.x + rect.w - 90, bcy, bw, bh)
        self.btn_welcome_prev.set_rect(rect.x + 10, bcy, bw, bh)

        if self.welcome_step > 0:
            self.btn_welcome_prev.draw(screen)
        if self.welcome_step < len(WELCOME_STEPS) - 1:
            self.btn_welcome_next.draw(screen)
        else:
            self.btn_welcome_close.draw(screen)

    def _draw_help_modal(self, screen: pygame.Surface) -> None:
        rect = self._modal_overlay(screen, 400, 300)
        font_t = pygame.font.SysFont("segoeui", 15, bold=True)
        font_b = pygame.font.SysFont("segoeui", 12)
        screen.blit(font_t.render("Atalhos de Script", True, UI_TEXT), (rect.x + 16, rect.y + 14))
        tips = [
            "self.transform.position += np.array([0,0,1]) * dt * 3",
            "self.transform.rotation[1] += 45 * dt",
            "self.transform.scale = np.array([1,1,1]) * (1 + 0.1*math.sin(t))",
            "",
            "Variáveis disponíveis:",
            "  self — o próprio GameObject",
            "  dt   — delta time em segundos",
            "  t    — tempo acumulado em segundos",
            "  keys — pygame.key.get_pressed()",
            "  np   — numpy",
            "  math — módulo math",
        ]
        y = rect.y + 44
        for tip in tips:
            s = font_b.render(tip, True, UI_TEXT_DIM if not tip.endswith(":") else UI_TEXT)
            screen.blit(s, (rect.x + 16, y))
            y += 18

    def _draw_templates_modal(self, screen: pygame.Surface) -> None:
        rect = self._modal_overlay(screen, 260, max(160, 60 + len(self._template_list) * 28))
        font_t = pygame.font.SysFont("segoeui", 15, bold=True)
        screen.blit(font_t.render("Templates de Cena", True, UI_TEXT), (rect.x + 16, rect.y + 14))

        bw = 220
        for i, (btn, tpl) in enumerate(zip(self.btn_template_items, self._template_list)):
            bx = rect.x + (rect.w - bw) // 2
            by = rect.y + 46 + i * 28
            btn.set_rect(bx, by, bw, 24)
            btn.label = tpl.get("_template_name", f"Template {i+1}")
            btn.draw(screen)

        self.btn_templates_close.set_rect(rect.x + rect.w - 90, rect.y + 10, 80, 24)
        self.btn_templates_close.draw(screen)

        if not self._template_list:
            font_b = pygame.font.SysFont("segoeui", 12)
            s = font_b.render("Nenhum template encontrado.", True, UI_TEXT_DIM)
            screen.blit(s, (rect.x + 16, rect.y + 50))

    # ──────────────────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event) -> None:  # noqa: C901
        lay = self._lay

        # ── Scroll do mouse — zoom da câmera ────────────────────────────────
        if event.type == pygame.MOUSEWHEEL:
            if self.code_editor.is_open:
                self.code_editor.handle_event(event)
            else:
                self.camera_controller.target_distance = max(
                    1.0, self.camera_controller.target_distance - event.y * 0.5
                )
            return

        # ── Teclado ──────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                if event.mod & pygame.KMOD_SHIFT:
                    self.history.redo(self)
                    self._notify("Refazer", "info")
                else:
                    self.history.undo(self)
                    self._notify("Desfazer", "info")
                return

            if event.key == pygame.K_ESCAPE:
                if self.code_editor.is_open:
                    self.code_editor.close()
                elif self.showing_help_modal:
                    self.showing_help_modal = False
                elif self.showing_templates:
                    self.showing_templates = False
                elif self.showing_welcome:
                    self.showing_welcome = False
                return

            if self._rename_index >= 0:
                if event.key == pygame.K_RETURN:
                    self._commit_rename()
                elif event.key == pygame.K_BACKSPACE:
                    self._rename_text = self._rename_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self._rename_text += event.unicode
                return

            if self.code_editor.is_open:
                self.code_editor.handle_event(event)
                return

            if event.key == pygame.K_DELETE and self.selected_index >= 0:
                self.delete_selected()

        # ── Clique esquerdo ──────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            self.click_start_pos = (mx, my)

            if self.showing_welcome:
                if self.btn_welcome_close.is_clicked(event):
                    self.showing_welcome = False
                elif self.btn_welcome_next.is_clicked(event):
                    if self.welcome_step < len(WELCOME_STEPS) - 1:
                        self.welcome_step += 1
                elif self.btn_welcome_prev.is_clicked(event):
                    if self.welcome_step > 0:
                        self.welcome_step -= 1
                return

            if self.showing_help_modal:
                self.showing_help_modal = False
                return

            if self.showing_templates:
                if self.btn_templates_close.is_clicked(event):
                    self.showing_templates = False
                else:
                    for btn, tpl in zip(self.btn_template_items, self._template_list):
                        if btn.is_clicked(event):
                            self._load_template(tpl)
                            self.showing_templates = False
                            self._notify(f"Template '{tpl.get('_template_name','?')}' carregado", "success")
                            break
                return

            if self.code_editor.is_open:
                self.code_editor.handle_event(event)
                return

            # ── Barra superior ───────────────────────────────────────────────
            if self.btn_play_pause.is_clicked(event):
                if not self.play_mode:
                    self.play_mode = True
                    self.saved_scene_state = []
                    for obj in self.editable_objects:
                        self.saved_scene_state.append({
                            "obj": obj,
                            "pos": obj.transform.position.copy(),
                            "rot": obj.transform.rotation.copy(),
                            "sc":  obj.transform.scale.copy(),
                        })
                        PhysicsSim.attach_rigidbody(obj)
                        ScriptManager.load(obj)
                    self.btn_play_pause.label = "⏹  STOP"
                    self._notify("Play iniciado", "success")
                else:
                    self.play_mode = False
                    if self.saved_scene_state:
                        for state in self.saved_scene_state:
                            o = state["obj"]
                            o.transform.position = state["pos"]
                            o.transform.rotation = state["rot"]
                            o.transform.scale    = state["sc"]
                            PhysicsSim.detach_rigidbody(o)
                            ScriptManager.unload(o)
                    self.saved_scene_state = None
                    PhysicsSim.clear_registries()
                    self.btn_play_pause.label = "▶  PLAY"
                    self._notify("Play encerrado", "info")
                return

            if self.btn_menu_file.is_clicked(event):
                self._active_dropdown = "file" if self._active_dropdown != "file" else None
                return
            if self.btn_menu_view.is_clicked(event):
                self._active_dropdown = "view" if self._active_dropdown != "view" else None
                return
            if self.btn_menu_window.is_clicked(event):
                self._active_dropdown = "window" if self._active_dropdown != "window" else None
                return

            if self._active_dropdown:
                if self._active_dropdown == "file":
                    rx_d, ry_d = 10, TOP_BAR_H
                    for i, (label, action) in enumerate([
                        ("Novo",     self._new_scene),
                        ("Salvar",   self.save_scene),
                        ("Carregar", self.load_scene),
                    ]):
                        r = pygame.Rect(rx_d + 2, ry_d + 2 + i * 26, 116, 24)
                        if r.collidepoint(mx, my):
                            action()
                            self._active_dropdown = None
                            return
                self._active_dropdown = None

            # ── Painel esquerdo ──────────────────────────────────────────────
            if self.btn_add_cube.is_clicked(event):    self.spawn_object("Cube");    return
            if self.btn_add_pyramid.is_clicked(event): self.spawn_object("Pyramid"); return
            if self.btn_add_sphere.is_clicked(event):  self.spawn_object("Sphere");  return
            if self.btn_add_plane.is_clicked(event):   self.spawn_object("Plane");   return
            if self.btn_add_capsule.is_clicked(event): self.spawn_object("Capsule"); return
            if self.btn_add_camera.is_clicked(event):  self.spawn_object("Camera");  return
            if self.btn_add_light.is_clicked(event):   self.spawn_object("Light");   return

            if self.btn_mode_translate.is_clicked(event): self.gizmo_mode = "translate"; return
            if self.btn_mode_rotate.is_clicked(event):    self.gizmo_mode = "rotate";    return
            if self.btn_mode_scale.is_clicked(event):     self.gizmo_mode = "scale";     return

            if self.btn_snap.is_clicked(event):
                self.snap_enabled = not self.snap_enabled
                self.btn_snap.label = f"Grade: {'ON' if self.snap_enabled else 'OFF'}"
                return
            if self.btn_templates.is_clicked(event):
                self.showing_templates = True
                return

            if self.btn_undo.is_clicked(event):
                self.history.undo(self); self._notify("Desfazer", "info"); return
            if self.btn_redo.is_clicked(event):
                self.history.redo(self); self._notify("Refazer",  "info"); return
            if self.btn_delete.is_clicked(event):
                self.delete_selected(); return

            if self.btn_tree_up.is_clicked(event):
                self._tree_scroll = max(0, self._tree_scroll - 1); return
            if self.btn_tree_down.is_clicked(event):
                self._tree_scroll = min(self._max_scroll(), self._tree_scroll + 1); return

            if self.btn_light_angle_dec.is_clicked(event) or self.btn_light_angle_inc.is_clicked(event):
                delta = -15.0 if self.btn_light_angle_dec.is_clicked(event) else 15.0
                self.light_angle = (self.light_angle + delta) % 360
                rad = np.radians(self.light_angle)
                ld = np.array([np.cos(rad), 1.0, np.sin(rad)], np.float32)
                ld /= np.linalg.norm(ld)
                for obj in self.editable_objects:
                    r = obj.get_component(MeshRenderer3D)
                    if r:
                        r.light_dir = ld
                return

            # ── Viewport — gizmo hit-test → drag → seleção ──────────────────
            vp = lay.viewport_rect
            if vp.collidepoint(mx, my) and not self.play_mode:
                hit = self._hit_gizmo(mx, my)
                if hit and self.selected_index >= 0:
                    self.is_dragging_gizmo    = True
                    self.active_gizmo_axis    = hit
                    self.gizmo_drag_last_mouse = (mx, my)
                    return
                keys = pygame.key.get_pressed()
                if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.selected_index >= 0:
                    self.is_dragging_object   = True
                    self.drag_object_last_mouse = (mx, my)
                    return

        # ── Soltar botão esquerdo ─────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos

            if self._drag_tree_src is not None:
                tree = self._build_flat_tree()
                target_parent: Optional[GameObject] = None
                for vis_i, (obj, depth) in enumerate(tree):
                    row_i = vis_i - self._tree_scroll
                    if row_i < 0:
                        continue
                    row_rect = pygame.Rect(0, TREE_Y + row_i * TREE_ROW_H, lay.left_panel_w, TREE_ROW_H)
                    if row_rect.collidepoint(mx, my) and obj is not self._drag_tree_src:
                        target_parent = obj
                        break

                if target_parent is not None:
                    loop = False
                    curr = target_parent
                    while curr is not None:
                        if curr is self._drag_tree_src:
                            loop = True
                            break
                        curr = getattr(curr, "parent", None)
                    if not loop:
                        self.history.push(self)
                        self._drag_tree_src.parent = target_parent
                else:
                    self.history.push(self)
                    self._drag_tree_src.parent = None

                if self.click_start_pos:
                    import math as _math
                    dx = mx - self.click_start_pos[0]
                    dy = my - self.click_start_pos[1]
                    if _math.hypot(dx, dy) < 4.0:
                        real_idx = self.editable_objects.index(self._drag_tree_src)
                        now = pygame.time.get_ticks() / 1000.0
                        if real_idx == self._last_click_index and (now - self._last_click_time) < 0.4:
                            self._start_rename(real_idx)
                        else:
                            self.selected_index = real_idx
                        self._last_click_index = real_idx
                        self._last_click_time = now
                self._drag_tree_src = None
                self.click_start_pos = None
                return

            if self.click_start_pos:
                import math as _math
                dx = mx - self.click_start_pos[0]
                dy = my - self.click_start_pos[1]
                vp = lay.viewport_rect
                if _math.hypot(dx, dy) < 4.0 and not self.play_mode:
                    if not self.is_dragging_gizmo and not self.is_dragging_object:
                        # Tenta clicar na árvore primeiro
                        tree = self._build_flat_tree()
                        clicked_tree = False
                        for vis_i, (obj, depth) in enumerate(tree):
                            row_i = vis_i - self._tree_scroll
                            if row_i < 0:
                                continue
                            rr = pygame.Rect(0, TREE_Y + row_i * TREE_ROW_H, lay.left_panel_w, TREE_ROW_H)
                            if rr.collidepoint(mx, my):
                                actual_i = self.editable_objects.index(obj)
                                now = pygame.time.get_ticks() / 1000.0
                                if actual_i == self._last_click_index and (now - self._last_click_time) < 0.4:
                                    self._start_rename(actual_i)
                                else:
                                    self.selected_index = actual_i
                                self._last_click_index = actual_i
                                self._last_click_time = now
                                clicked_tree = True
                                break
                        if not clicked_tree and vp.collidepoint(mx, my):
                            self._select_at(mx, my)

            self.is_dragging_gizmo  = False
            self.is_dragging_object = False
            self.click_start_pos    = None

        # ── Drag da árvore — rastreamento ─────────────────────────────────────
        if event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            mx, my = event.pos
            if self.click_start_pos and self._drag_tree_src is None:
                import math as _math
                dx = mx - self.click_start_pos[0]
                dy = my - self.click_start_pos[1]
                if _math.hypot(dx, dy) > 6:
                    scx, scy = self.click_start_pos
                    tree = self._build_flat_tree()
                    for vis_i, (obj, depth) in enumerate(tree):
                        row_i = vis_i - self._tree_scroll
                        if row_i < 0:
                            continue
                        rr = pygame.Rect(0, TREE_Y + row_i * TREE_ROW_H, lay.left_panel_w, TREE_ROW_H)
                        if rr.collidepoint(scx, scy):
                            self._drag_tree_src = obj
                            break

        # ── Inspector ────────────────────────────────────────────────────────
        if 0 <= self.selected_index < len(self.editable_objects):
            sel = self.editable_objects[self.selected_index]

            if self.btn_toggle_static.is_clicked(event):
                self.history.push(self)
                sel.is_static = not getattr(sel, "is_static", False); return
            if self.btn_toggle_physics.is_clicked(event):
                self.history.push(self)
                sel.physics_enabled = not getattr(sel, "physics_enabled", False); return
            if self.btn_vel_dec.is_clicked(event):
                self.history.push(self)
                sel.initial_velocity_y = getattr(sel, "initial_velocity_y", 0.0) - 1.0
                if hasattr(sel, "_velocity"):
                    sel._velocity[1] = sel.initial_velocity_y
                return
            if self.btn_vel_inc.is_clicked(event):
                self.history.push(self)
                sel.initial_velocity_y = getattr(sel, "initial_velocity_y", 0.0) + 1.0
                if hasattr(sel, "_velocity"):
                    sel._velocity[1] = sel.initial_velocity_y
                return
            if self.btn_clone.is_clicked(event):
                self.clone_selected(); return
            if self.btn_prev_script.is_clicked(event) or self.btn_next_script.is_clicked(event):
                cur = getattr(sel, "script_path", "")
                idx = self.available_scripts.index(cur) if cur in self.available_scripts else 0
                delta = -1 if self.btn_prev_script.is_clicked(event) else 1
                ni = (idx + delta) % len(self.available_scripts)
                sel.script_path = self.available_scripts[ni] if ni > 0 else ""; return
            if self.btn_new_script.is_clicked(event):
                path = ScriptManager.create_template(sel)
                self.available_scripts = ScriptManager.list_scripts()
                sel.script_path = path; return
            if self.btn_edit_script.is_clicked(event):
                p = getattr(sel, "script_path", "")
                if p and os.path.exists(p):
                    try:
                        os.startfile(p)
                    except Exception:
                        import subprocess
                        subprocess.Popen(["notepad.exe", p])
                return
            if self.btn_internal_editor.is_clicked(event):
                p = getattr(sel, "script_path", "")
                if p and os.path.exists(p):
                    self.code_editor.open(p)
                return
            if self.btn_script_help.is_clicked(event):
                self.showing_help_modal = True; return

            if self.btn_prev_parent.is_clicked(event) or self.btn_next_parent.is_clicked(event):
                def is_descendant(p, child):
                    if p is child: return True
                    if p.parent is None: return False
                    return is_descendant(p.parent, child)
                candidates = [None] + [o for o in self.editable_objects if o is not sel and not is_descendant(o, sel)]
                cur_parent = getattr(sel, "parent", None)
                try:
                    pi = candidates.index(cur_parent)
                except ValueError:
                    pi = 0
                delta = -1 if self.btn_prev_parent.is_clicked(event) else 1
                pi = (pi + delta) % len(candidates)
                new_parent = candidates[pi]
                self.history.push(self)
                if cur_parent and hasattr(cur_parent, "remove_child"):
                    cur_parent.remove_child(sel)
                if new_parent and hasattr(new_parent, "add_child"):
                    new_parent.add_child(sel)
                return

            if self.btn_prev_tag.is_clicked(event) or self.btn_next_tag.is_clicked(event):
                cur_tag = getattr(sel, "tag", "")
                try:
                    ti = TAG_OPTIONS.index(cur_tag)
                except ValueError:
                    ti = 0
                delta = -1 if self.btn_prev_tag.is_clicked(event) else 1
                ti = (ti + delta) % len(TAG_OPTIONS)
                sel.tag = TAG_OPTIONS[ti]; return

            for i, btn in enumerate(self.btn_colors):
                if btn.is_clicked(event):
                    self.history.push(self)
                    r = sel.get_component(MeshRenderer3D)
                    if r:
                        r.color = COLOR_PALETTE[i]
                    return

    # ──────────────────────────────────────────────────────────────────────────
    def _new_scene(self) -> None:
        """Limpa todos os objetos da cena e reseta o histórico."""
        for obj in list(self.editable_objects):
            self._remove_go(obj)
        self.editable_objects.clear()
        self.selected_index = -1
        if hasattr(self.history, "clear"):
            self.history.clear()
        self._notify("Nova cena criada", "success")

    def _hit_gizmo(self, mx: int, my: int) -> Optional[str]:
        """Retorna o eixo do gizmo clicado ('x','y','z','center'), ou None."""
        RADIUS = 10
        for axis, pt in getattr(self, "gizmo_screen_points", {}).items():
            if pt and abs(mx - pt[0]) < RADIUS and abs(my - pt[1]) < RADIUS:
                return axis
        center = getattr(self, "gizmo_screen_center", None)
        if center:
            cx, cy = center
            if abs(mx - cx) < RADIUS and abs(my - cy) < RADIUS:
                return "center"
        return None

    # ──────────────────────────────────────────────────────────────────────────
    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        lay  = self._lay
        font = pygame.font.SysFont("segoeui", 12)
        lw   = lay.left_panel_w

        # Título do Outliner
        tsurf = font.render("OUTLINER", True, UI_TEXT_DIM)
        screen.blit(tsurf, (8, TOP_BAR_H + 6))

        # Botões de forma
        self.btn_add_cube.draw(screen)
        self.btn_add_pyramid.draw(screen)
        self.btn_add_sphere.draw(screen)
        self.btn_add_plane.draw(screen)
        self.btn_add_capsule.draw(screen)
        self.btn_add_camera.draw(screen)
        self.btn_add_light.draw(screen)

        # Gizmo modes
        for btn, label, mode in [
            (self.btn_mode_translate, "T", "translate"),
            (self.btn_mode_rotate,    "R", "rotate"),
            (self.btn_mode_scale,     "S", "scale"),
        ]:
            btn.bg_color = (80, 140, 200) if self.gizmo_mode == mode else (60, 100, 140)
            btn.draw(screen)

        self.btn_snap.draw(screen)
        self.btn_templates.draw(screen)
        self.btn_undo.draw(screen)
        self.btn_redo.draw(screen)
        self.btn_delete.draw(screen)
        self.btn_tree_up.draw(screen)
        self.btn_tree_down.draw(screen)

        # Luz direcional
        font_sm = pygame.font.SysFont("segoeui", 11)
        lx = self.btn_light_angle_dec.rect.x
        ly = self.btn_light_angle_dec.rect.y - 16
        screen.blit(font_sm.render(f"Luz: {int(self.light_angle)}°", True, UI_TEXT_DIM), (lx, ly))
        self.btn_light_angle_dec.draw(screen)
        self.btn_light_angle_inc.draw(screen)

        # Árvore de objetos
        tree = self._build_flat_tree()
        font_tree = pygame.font.SysFont("segoeui", 12)
        for vis_i, (obj, depth) in enumerate(tree):
            row_i = vis_i - self._tree_scroll
            if row_i < 0:
                continue
            ry = TREE_Y + row_i * TREE_ROW_H
            if ry + TREE_ROW_H > lay.screen_h - STATUS_BAR_H - 30:
                break
            actual_i = self.editable_objects.index(obj)
            is_sel = (actual_i == self.selected_index)
            bg = UI_ACCENT if is_sel else (UI_PANEL if row_i % 2 == 0 else UI_PANEL2)
            pygame.draw.rect(screen, bg, pygame.Rect(0, ry, lw - 22, TREE_ROW_H))

            # Rename inline
            if self._rename_index == actual_i:
                name_str = self._rename_text + "|"
                col = (255, 220, 80)
            else:
                name_str = ("  " * depth) + obj.name
             