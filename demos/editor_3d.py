import pygame
import sys
import os
import numpy as np
from typing import List, Optional, Tuple

# Ajustar caminho para importar a engine da pasta superior
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.core import Engine, Scene
from engine.game_object import GameObject
from engine.component import Component
from engine.input import Input
from engine.graphics.renderer3d import Camera3D, MeshRenderer3D
from engine.graphics.renderer2d import TextRenderer
from engine.assets import Assets, Mesh
from engine.graphics.math3d import project_vertices

# ---------------------------------------------------------
# Algoritmo de Verificação: Ponto Dentro do Polígono (2D)
# ---------------------------------------------------------
def point_in_polygon(x: float, y: float, poly: List[Tuple[int, int]]) -> bool:
    """Verifica se o ponto (x, y) está dentro do polígono 2D (lista de pontos)."""
    n = len(poly)
    inside = False
    if n < 3:
        return False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


# ---------------------------------------------------------
# Geradores Procedurais de Formas 3D
# ---------------------------------------------------------
def create_pyramid_mesh(size: float = 1.0) -> Mesh:
    """Cria uma malha 3D de Pirâmide (triângulo)."""
    s = size / 2.0
    vertices = np.array([
        [-s, -0.4 * size, -s],  # 0: base esquerda-trás
        [ s, -0.4 * size, -s],  # 1: base direita-trás
        [ s, -0.4 * size,  s],  # 2: base direita-frente
        [-s, -0.4 * size,  s],  # 3: base esquerda-frente
        [0.0, 0.6 * size, 0.0]  # 4: topo (ápice)
    ], dtype=np.float32)
    
    faces = [
        [0, 1, 4],     # Trás
        [1, 2, 4],     # Direita
        [2, 3, 4],     # Frente
        [3, 0, 4],     # Esquerda
        [3, 2, 1, 0]   # Base (quadrado)
    ]
    return Mesh(vertices, faces)

def create_sphere_mesh(radius: float = 0.5, rings: int = 12, sectors: int = 12) -> Mesh:
    """Cria uma malha 3D de Esfera UV (bolinha)."""
    vertices = []
    for r in range(rings + 1):
        theta = r * np.pi / rings
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        
        for s in range(sectors):
            phi = s * 2 * np.pi / sectors
            x = radius * np.cos(phi) * sin_theta
            y = radius * cos_theta
            z = radius * np.sin(phi) * sin_theta
            vertices.append([x, y, z])
            
    faces = []
    for r in range(rings):
        for s in range(sectors):
            p0 = r * sectors + s
            p1 = r * sectors + (s + 1) % sectors
            p2 = (r + 1) * sectors + (s + 1) % sectors
            p3 = (r + 1) * sectors + s
            faces.append([p0, p1, p2, p3])
            
    return Mesh(np.array(vertices, dtype=np.float32), faces)


# ---------------------------------------------------------
# Botão Simples de Interface Gráfica (GUI)
# ---------------------------------------------------------
class GuiButton:
    def __init__(self, x: int, y: int, w: int, h: int, text: str, 
                 bg_color: Tuple[int, int, int] = (60, 70, 90), 
                 hover_color: Tuple[int, int, int] = (80, 95, 120), 
                 text_color: Tuple[int, int, int] = (240, 245, 255)) -> None:
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_pos = pygame.mouse.get_pos()
        c = self.hover_color if self.rect.collidepoint(mouse_pos) else self.bg_color
        pygame.draw.rect(screen, c, self.rect, border_radius=4)
        pygame.draw.rect(screen, (95, 110, 135), self.rect, 1, border_radius=4)
        
        txt_surf = font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


# ---------------------------------------------------------
# Controlador de Câmera Orbital com Mouse
# ---------------------------------------------------------
class OrbitCameraController(Component):
    """Controla a câmera orbitando ao redor do objeto ativo de forma suave com amortecimento."""
    def __init__(self, target: np.ndarray = None, distance: float = 4.5, 
                 yaw: float = 0.0, pitch: float = 15.0) -> None:
        super().__init__()
        self.target = target if target is not None else np.array([0.0, 0.0, 1.5], dtype=np.float32)
        self.distance = distance
        self.yaw = yaw
        self.pitch = pitch
        self.is_dragging = False
        
        # Alvos suavizados (para interpolação)
        self.target_yaw = yaw
        self.target_pitch = pitch
        self.target_distance = distance
        
        # Rastreamento de mouse absoluto e bloqueio de eixos
        self.last_mouse_pos: Optional[Tuple[int, int]] = None
        self.drag_start_pos: Optional[Tuple[int, int]] = None
        self.orbit_lock: Optional[str] = None  # None, 'h' (horizontal), ou 'v' (vertical)

    def update(self, dt: float) -> None:
        # 1. Suavizar foco da câmera no objeto selecionado (caso exista)
        desired_focus = np.array([0.0, 0.0, 1.5], dtype=np.float32)
        if self.game_object and self.game_object.scene:
            scene = self.game_object.scene
            if scene.selected_index >= 0 and scene.selected_index < len(scene.editable_objects):
                desired_focus = scene.editable_objects[scene.selected_index].transform.position
        
        # Interpolação suave do ponto de foco (Lerp)
        self.target += (desired_focus - self.target) * 8.0 * dt

        # 2. Detectar clique e arrasto do botão direito para atualizar os ângulos alvo
        mouse_pos = pygame.mouse.get_pos()
        rmb_held = pygame.mouse.get_pressed()[2]
        
        if rmb_held:
            if self.last_mouse_pos is None:
                # Só inicia o arrasto se começar dentro da área 3D
                if 230 <= mouse_pos[0] <= 770:
                    self.last_mouse_pos = mouse_pos
                    self.drag_start_pos = mouse_pos
                    self.orbit_lock = None
            else:
                # Se já iniciou o arrasto, continua mesmo se o mouse se mover para fora dos 250px (sem pulos!)
                if self.orbit_lock is None and self.drag_start_pos is not None:
                    total_dx = mouse_pos[0] - self.drag_start_pos[0]
                    total_dy = mouse_pos[1] - self.drag_start_pos[1]
                    dist = np.sqrt(total_dx**2 + total_dy**2)
                    if dist > 8.0:
                        if abs(total_dx) > abs(total_dy):
                            self.orbit_lock = 'h'
                        else:
                            self.orbit_lock = 'v'

                dx = mouse_pos[0] - self.last_mouse_pos[0]
                dy = mouse_pos[1] - self.last_mouse_pos[1]
                
                if dx != 0 or dy != 0:
                    # Aplicar rotações respeitando o travamento de eixo
                    if self.orbit_lock == 'h' or self.orbit_lock is None:
                        self.target_yaw = (self.target_yaw - dx * 0.20)
                    if self.orbit_lock == 'v' or self.orbit_lock is None:
                        self.target_pitch = max(-85.0, min(85.0, self.target_pitch + dy * 0.20))
                    self.is_dragging = True
                self.last_mouse_pos = mouse_pos
        else:
            self.last_mouse_pos = None
            self.drag_start_pos = None
            self.orbit_lock = None
            self.is_dragging = False

        # 3. Interpolar suavemente os ângulos e distância atuais para os alvos
        # Evita giros secos e adiciona sensação de inércia física
        self.yaw += (self.target_yaw - self.yaw) * 12.0 * dt
        self.pitch += (self.target_pitch - self.pitch) * 12.0 * dt
        self.distance += (self.target_distance - self.distance) * 10.0 * dt

        # 4. Calcular posição esférica baseada nos valores atuais suavizados (foco 100% centralizado)
        yaw_rad = np.radians(self.yaw)
        pitch_rad = np.radians(self.pitch)
        
        # Correção matemática do sinal para manter o objeto perfeitamente fixo no centro da tela ao orbitar
        ox = -self.distance * np.cos(pitch_rad) * np.sin(yaw_rad)
        oy = self.distance * np.sin(pitch_rad)
        oz = -self.distance * np.cos(pitch_rad) * np.cos(yaw_rad)
        
        self.transform.position = self.target + np.array([ox, oy, oz], dtype=np.float32)
        self.transform.ry = self.yaw
        self.transform.rx = self.pitch
        self.transform.rz = 0.0


# ---------------------------------------------------------
# Cena Principal do Editor
# ---------------------------------------------------------
class EditorScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1
        
        self.font_title = None
        self.font_body = None
        self.font_btn = None
        self.font_xyz = None
        
        self.buttons: List[GuiButton] = []
        self.click_start_pos: Optional[Tuple[int, int]] = None
        self.camera_comp: Optional[Camera3D] = None
        self.camera_controller: Optional[OrbitCameraController] = None
        
        # Arrasto de objetos com mouse (translação)
        self.is_dragging_object = False
        self.drag_object_last_mouse = (0, 0)
        
        # Modo do Gizmo e estados de arrasto de alças
        self.gizmo_mode = "translate"  # "translate", "rotate", "scale"
        self.is_dragging_gizmo = False
        self.active_gizmo_axis = None  # "x", "y" ou "z"
        self.gizmo_drag_last_mouse = (0, 0)
        self.gizmo_screen_points = {}  # Coordenadas projetadas das extremidades {'x': (x,y), ...}
        
        # Modo Play (Física 3D)
        self.play_mode = False
        self.saved_scene_state = None  # Cópia para restaurar após o STOP
        
        self.cube_count = 0
        self.pyramid_count = 0
        self.sphere_count = 0
        
        self.light_angle = 45.0
        self.available_scripts = ["Nenhum"]
        
        # Estado do Editor de Código Interno e Guia de Ajuda
        self.editing_script_path = None
        self.script_editor_lines = []
        self.editor_cursor_row = 0
        self.editor_cursor_col = 0
        self.editor_scroll_y = 0
        self.showing_help_modal = False

    def start(self) -> None:
        print("Editor de Cena 3D Iniciado!")
        self.font_title = Assets.get_font(None, 18)
        self.font_body = Assets.get_font(None, 15)
        self.font_btn = Assets.get_font(None, 14)
        self.font_xyz = Assets.get_font(None, 16)
        
        # Rastrear scripts disponíveis
        self.available_scripts = ["Nenhum"]
        if os.path.exists("scripts"):
            for f in os.listdir("scripts"):
                if f.endswith(".py"):
                    self.available_scripts.append(os.path.join("scripts", f))
                    
        # Botões de criação de formas (Compactados na linha Y = 45 para caber em 230)
        self.btn_add_cube = GuiButton(15, 45, 62, 26, "+ Cubo", bg_color=(40, 100, 60), hover_color=(50, 130, 80))
        self.btn_add_pyramid = GuiButton(82, 45, 62, 26, "+ Pirâm", bg_color=(40, 100, 60), hover_color=(50, 130, 80))
        self.btn_add_sphere = GuiButton(149, 45, 62, 26, "+ Esf", bg_color=(40, 100, 60), hover_color=(50, 130, 80))
        
        # Botões de seleção do Modo de Gizmo (Linha Y = 80)
        self.btn_mode_translate = GuiButton(15, 80, 62, 26, "Mover", bg_color=(80, 60, 120), hover_color=(100, 80, 150))
        self.btn_mode_rotate = GuiButton(82, 80, 62, 26, "Girar", bg_color=(80, 60, 120), hover_color=(100, 80, 150))
        self.btn_mode_scale = GuiButton(149, 80, 62, 26, "Escalar", bg_color=(80, 60, 120), hover_color=(100, 80, 150))
        
        # Botões superiores do Viewport (X >= 230, Y = 15)
        self.btn_play_pause = GuiButton(245, 15, 80, 26, "PLAY", bg_color=(40, 100, 40), hover_color=(50, 130, 50))
        self.btn_save = GuiButton(335, 15, 70, 26, "Salvar", bg_color=(100, 70, 40), hover_color=(130, 90, 50))
        self.btn_load = GuiButton(415, 15, 70, 26, "Carregar", bg_color=(100, 70, 40), hover_color=(130, 90, 50))
        
        # Botões de controle de ângulo da luz (Y = 365)
        self.btn_light_angle_dec = GuiButton(15, 365, 40, 22, " < ", bg_color=(60, 65, 78), hover_color=(75, 80, 95))
        self.btn_light_angle_inc = GuiButton(165, 365, 40, 22, " > ", bg_color=(60, 65, 78), hover_color=(75, 80, 95))
        
        # Botões do Inspetor Lateral Direito (X >= 770)
        self.btn_toggle_static = GuiButton(785, 50, 20, 20, "", bg_color=(45, 49, 58), hover_color=(70, 76, 90))
        self.btn_toggle_physics = GuiButton(785, 80, 20, 20, "", bg_color=(45, 49, 58), hover_color=(70, 76, 90))
        
        self.btn_vel_dec = GuiButton(785, 135, 40, 20, " - ", bg_color=(60, 65, 78), hover_color=(75, 80, 95))
        self.btn_vel_inc = GuiButton(915, 135, 40, 20, " + ", bg_color=(60, 65, 78), hover_color=(75, 80, 95))
        
        self.btn_prev_script = GuiButton(785, 190, 30, 22, " < ", bg_color=(60, 65, 78), hover_color=(75, 80, 95))
        self.btn_next_script = GuiButton(945, 190, 30, 22, " > ", bg_color=(60, 65, 78), hover_color=(75, 80, 95))
        self.btn_new_script = GuiButton(785, 215, 190, 20, "+ Novo Script", bg_color=(40, 100, 60), hover_color=(50, 130, 80))
        self.btn_edit_script = GuiButton(785, 238, 93, 20, "Editor Ext.", bg_color=(0, 100, 160), hover_color=(0, 130, 200))
        self.btn_internal_editor = GuiButton(882, 238, 93, 20, "Editor Int.", bg_color=(0, 100, 160), hover_color=(0, 130, 200))
        self.btn_script_help = GuiButton(785, 261, 190, 20, "Guia de Comandos", bg_color=(120, 80, 40), hover_color=(150, 100, 50))
        
        # Botoes auxiliares para os modais (nao entram na lista geral de botoes da cena)
        self.btn_editor_save = GuiButton(700, 46, 70, 22, "Salvar", bg_color=(40, 100, 60), hover_color=(50, 130, 80))
        self.btn_editor_close = GuiButton(785, 46, 70, 22, "Fechar", bg_color=(140, 40, 40), hover_color=(175, 50, 50))
        self.btn_help_close = GuiButton(785, 46, 70, 22, "Fechar", bg_color=(140, 40, 40), hover_color=(175, 50, 50))
        
        self.color_palette = [
            (200, 200, 200),  # Cinza/Branco
            (220, 50, 50),    # Vermelho
            (50, 170, 50),    # Verde
            (50, 100, 220),   # Azul
            (240, 200, 0),    # Amarelo
            (200, 50, 200)    # Roxo
        ]
        self.btn_colors = []
        for col_idx, col in enumerate(self.color_palette):
            self.btn_colors.append(GuiButton(785 + col_idx * 32, 312, 24, 24, "", bg_color=col, hover_color=col))
            
        self.btn_clone = GuiButton(785, 352, 190, 26, "Clonar Objeto", bg_color=(80, 60, 120), hover_color=(100, 75, 150))
        
        self.buttons.extend([
            self.btn_add_cube, self.btn_add_pyramid, self.btn_add_sphere,
            self.btn_mode_translate, self.btn_mode_rotate, self.btn_mode_scale,
            self.btn_play_pause, self.btn_save, self.btn_load,
            self.btn_light_angle_dec, self.btn_light_angle_inc,
            self.btn_toggle_static, self.btn_toggle_physics,
            self.btn_vel_dec, self.btn_vel_inc,
            self.btn_prev_script, self.btn_next_script,
            self.btn_new_script, self.btn_edit_script, self.btn_internal_editor,
            self.btn_script_help, self.btn_clone
        ])
        self.buttons.extend(self.btn_colors)
        
        # Câmera 3D para a Viewport Central (X: 230 a 770)
        camera_obj = GameObject("EditorCamera")
        self.camera_comp = camera_obj.add_component(Camera3D(
            fov=60.0, near=0.1, far=100.0,
            viewport_x=230.0, viewport_y=0.0,
            viewport_width=540.0, viewport_height=600.0
        ))
        self.camera_controller = camera_obj.add_component(OrbitCameraController())
        self.add_game_object(camera_obj)

        # Objeto inicial padrão
        self.spawn_object("Cube")

    def spawn_object(self, shape_type: str) -> None:
        go = GameObject()
        go.transform.position = np.array([0.0, 0.0, 1.5])
        go.mesh_type = shape_type
        go.is_static = False
        go.use_physics = True
        go.initial_velocity_y = 0.0
        go.script_path = ""
        
        if shape_type == "Cube":
            self.cube_count += 1
            go.name = f"Bloco_{self.cube_count}"
            mesh = Assets.create_cube_mesh(1.0)
            go.add_component(MeshRenderer3D(mesh, color=(0, 110, 220)))  # Azul escuro contrastante
        elif shape_type == "Pyramid":
            self.pyramid_count += 1
            go.name = f"Piramide_{self.pyramid_count}"
            mesh = create_pyramid_mesh(1.0)
            go.add_component(MeshRenderer3D(mesh, color=(220, 60, 20)))  # Vermelho/Laranja
        elif shape_type == "Sphere":
            self.sphere_count += 1
            go.name = f"Bolinha_{self.sphere_count}"
            mesh = create_sphere_mesh(radius=0.6, rings=10, sectors=10)
            go.add_component(MeshRenderer3D(mesh, color=(100, 40, 180)))  # Roxo
            
        self.add_game_object(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1

    def delete_selected(self) -> None:
        if 0 <= self.selected_index < len(self.editable_objects):
            go = self.editable_objects.pop(self.selected_index)
            self.remove_game_object(go)
            go.destroy()
            self.selected_index = -1 if not self.editable_objects else 0

    def clone_selected(self) -> None:
        if 0 <= self.selected_index < len(self.editable_objects):
            src = self.editable_objects[self.selected_index]
            go = GameObject()
            go.mesh_type = getattr(src, "mesh_type", "Cube")
            go.name = src.name + "_Clone"
            go.is_static = getattr(src, "is_static", False)
            go.use_physics = getattr(src, "use_physics", True)
            go.initial_velocity_y = getattr(src, "initial_velocity_y", 0.0)
            go.script_path = getattr(src, "script_path", "")
            
            go.transform.position = src.transform.position + np.array([0.5, 0.0, 0.5], dtype=np.float32)
            go.transform.rotation = src.transform.rotation.copy()
            go.transform.scale = src.transform.scale.copy()
            
            renderer = src.get_component(MeshRenderer3D)
            color = renderer.color if renderer else (200, 200, 200)
            
            if go.mesh_type == "Cube":
                mesh = Assets.create_cube_mesh(1.0)
                go.add_component(MeshRenderer3D(mesh, color=color))
            elif go.mesh_type == "Pyramid":
                mesh = create_pyramid_mesh(1.0)
                go.add_component(MeshRenderer3D(mesh, color=color))
            elif go.mesh_type == "Sphere":
                mesh = create_sphere_mesh(radius=0.6, rings=10, sectors=10)
                go.add_component(MeshRenderer3D(mesh, color=color))
                
            self.add_game_object(go)
            self.editable_objects.append(go)
            self.selected_index = len(self.editable_objects) - 1
            print("Objeto clonado com sucesso!")

    def save_scene(self) -> None:
        data = {
            "objects": []
        }
        for obj in self.editable_objects:
            shape_type = "Cube"
            if "Piramide" in obj.name:
                shape_type = "Pyramid"
            elif "Bolinha" in obj.name:
                shape_type = "Sphere"
                
            renderer = obj.get_component(MeshRenderer3D)
            color = list(renderer.color) if renderer else [200, 200, 200]
            
            data["objects"].append({
                "name": obj.name,
                "shape": shape_type,
                "position": obj.transform.position.tolist(),
                "rotation": obj.transform.rotation.tolist(),
                "scale": obj.transform.scale.tolist(),
                "color": color,
                "is_static": getattr(obj, "is_static", False),
                "use_physics": getattr(obj, "use_physics", True),
                "initial_velocity_y": getattr(obj, "initial_velocity_y", 0.0),
                "script_path": getattr(obj, "script_path", "")
            })
        
        try:
            import json
            filepath = os.path.join(os.path.dirname(__file__), 'scene.json')
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            print("Cena salva com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar cena: {e}")

    def load_scene(self) -> None:
        filepath = os.path.join(os.path.dirname(__file__), 'scene.json')
        if not os.path.exists(filepath):
            print("Nenhuma cena salva encontrada!")
            return
            
        try:
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            for obj in list(self.editable_objects):
                self.remove_game_object(obj)
                obj.destroy()
            self.editable_objects.clear()
            self.selected_index = -1
            
            self.cube_count = 0
            self.pyramid_count = 0
            self.sphere_count = 0
            
            for item in data.get("objects", []):
                go = GameObject()
                go.name = item["name"]
                go.transform.position = np.array(item["position"], dtype=np.float32)
                go.transform.rotation = np.array(item["rotation"], dtype=np.float32)
                go.transform.scale = np.array(item["scale"], dtype=np.float32)
                
                go.mesh_type = item.get("shape", "Cube")
                go.is_static = item.get("is_static", False)
                go.use_physics = item.get("use_physics", True)
                go.initial_velocity_y = item.get("initial_velocity_y", 0.0)
                go.script_path = item.get("script_path", "")
                
                shape = item["shape"]
                color = tuple(item["color"])
                
                if shape == "Cube":
                    self.cube_count += 1
                    mesh = Assets.create_cube_mesh(1.0)
                    go.add_component(MeshRenderer3D(mesh, color=color))
                elif shape == "Pyramid":
                    self.pyramid_count += 1
                    mesh = create_pyramid_mesh(1.0)
                    go.add_component(MeshRenderer3D(mesh, color=color))
                elif shape == "Sphere":
                    self.sphere_count += 1
                    mesh = create_sphere_mesh(radius=0.6, rings=10, sectors=10)
                    go.add_component(MeshRenderer3D(mesh, color=color))
                    
                self.add_game_object(go)
                self.editable_objects.append(go)
                
            if self.editable_objects:
                self.selected_index = len(self.editable_objects) - 1
            print("Cena carregada com sucesso!")
        except Exception as e:
            print(f"Erro ao carregar cena: {e}")

    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        go._propagate_scene(self)

    def remove_game_object(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)

    def select_object_at_screen_pos(self, mouse_pos: Tuple[int, int]) -> None:
        """Verifica se o clique do mouse intersectou alguma face projetada de algum objeto."""
        mx, my = mouse_pos
        closest_obj_idx = -1
        closest_depth = float('inf')
        
        for idx, obj in enumerate(self.editable_objects):
            renderer = obj.get_component(MeshRenderer3D)
            if renderer and renderer.last_screen_coords is not None:
                coords = renderer.last_screen_coords
                # Loop por todas as faces do modelo
                for face in renderer.mesh.faces:
                    # Obter coordenadas de tela da face
                    poly = [tuple(coords[v_idx]) for v_idx in face]
                    # Verificar se o mouse está dentro deste polígono projetado
                    if point_in_polygon(mx, my, poly):
                        # Calcular a profundidade média do objeto para culling de profundidade do clique
                        obj_pos_cam = (self.camera_comp.view_matrix @ np.append(obj.transform.position, 1.0))
                        depth = -obj_pos_cam[2]  # Z na câmera
                        if depth < closest_depth:
                            closest_depth = depth
                            closest_obj_idx = idx
                            
        if closest_obj_idx != -1:
            self.selected_index = closest_obj_idx

    def draw_floor_grid(self, screen: pygame.Surface) -> None:
        """Projeta e desenha uma grade/régua no chão (Y = -0.5) com linhas cinzas."""
        verts = []
        # Criar linhas horizontais e verticais da grade (de -5.0 a 5.0 com passo de 1.0)
        for x in range(-5, 6):
            verts.append([x, -0.5, -5.0])
            verts.append([x, -0.5, 5.0])
        for z in range(-5, 6):
            verts.append([-5.0, -0.5, z])
            verts.append([5.0, -0.5, z])
            
        verts = np.array(verts, dtype=np.float32)
        
        m_matrix = np.eye(4, dtype=np.float32)
        v_matrix = self.camera_comp.view_matrix
        p_matrix = self.camera_comp.projection_matrix
        
        # Projetar os pontos usando o pipeline 3D da engine
        ndc_coords, depths = project_vertices(verts, m_matrix, v_matrix, p_matrix)
        
        width, height = screen.get_size()
        v_x = self.camera_comp.viewport_x
        v_y = self.camera_comp.viewport_y
        v_w = self.camera_comp.viewport_width
        v_h = self.camera_comp.viewport_height
        
        w_half = v_w / 2.0
        h_half = v_h / 2.0
        
        screen_x = v_x + (ndc_coords[:, 0] + 1.0) * w_half
        screen_y = v_y + (-ndc_coords[:, 1] + 1.0) * h_half
        
        grid_color = (220, 222, 226)
        near = self.camera_comp.near
        
        for i in range(0, len(verts), 2):
            # Desenhar linha apenas se ambos os pontos estiverem à frente da câmera
            if depths[i] > near and depths[i+1] > near:
                p0 = (int(screen_x[i]), int(screen_y[i]))
                p1 = (int(screen_x[i+1]), int(screen_y[i+1]))
                
                # Eixos centrais (X=0 ou Z=0) desenhados em cinza mais escuro (régua principal)
                is_center = (abs(verts[i][0]) < 0.01 and abs(verts[i][2] - verts[i+1][2]) > 0.01) or \
                            (abs(verts[i][2]) < 0.01 and abs(verts[i][0] - verts[i+1][0]) > 0.01)
                            
                color = (170, 175, 185) if is_center else grid_color
                pygame.draw.line(screen, color, p0, p1, 2 if is_center else 1)
 
    def update(self, dt: float) -> None:
        # Executar scripts comportamentais vinculados durante a simulação (PLAY)
        if self.play_mode:
            for obj in self.editable_objects:
                if hasattr(obj, "script_module") and hasattr(obj.script_module, "update"):
                    try:
                        obj.script_module.update(obj, dt)
                    except Exception as run_err:
                        print(f"Erro ao rodar update do script no objeto {obj.name}: {run_err}")

        # 1. Simulação Física (se estiver em Modo Play)
        if self.play_mode:
            sim_dt = min(0.05, dt)
            
            # Gravidade e translação simples (apenas se não for estático)
            for obj in self.editable_objects:
                if getattr(obj, "is_static", False):
                    continue
                if not hasattr(obj, "physics_velocity"):
                    obj.physics_velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                
                # Aplicar gravidade apenas se usar física
                if getattr(obj, "use_physics", True):
                    obj.physics_velocity[1] -= 9.8 * sim_dt
                obj.transform.position += obj.physics_velocity * sim_dt
                
            # Colisão com o chão (Y = -0.5, apenas se não for estático)
            for obj in self.editable_objects:
                if getattr(obj, "is_static", False):
                    continue
                bottom_y = obj.transform.position[1] - obj.transform.scale[1] * 0.5
                if bottom_y < -0.5:
                    obj.transform.position[1] = -0.5 + obj.transform.scale[1] * 0.5
                    obj.physics_velocity[1] = -obj.physics_velocity[1] * 0.4  # Elasticidade
                    obj.physics_velocity[0] *= 0.9  # Fricção lateral
                    obj.physics_velocity[2] *= 0.9  # Fricção lateral
 
            # Colisão entre objetos (Esfera vs Esfera aproximada)
            n_objs = len(self.editable_objects)
            for i in range(n_objs):
                for j in range(i + 1, n_objs):
                    obj1 = self.editable_objects[i]
                    obj2 = self.editable_objects[j]
                    
                    if getattr(obj1, "is_static", False) and getattr(obj2, "is_static", False):
                        continue
                        
                    pos1 = obj1.transform.position
                    pos2 = obj2.transform.position
                    
                    r1 = np.mean(obj1.transform.scale) * 0.5
                    r2 = np.mean(obj2.transform.scale) * 0.5
                    min_dist = r1 + r2
                    
                    diff = pos1 - pos2
                    dist = np.linalg.norm(diff)
                    if dist < min_dist:
                        # Resolver sobreposição
                        overlap = min_dist - dist
                        normal = diff / max(1e-5, dist)
                        
                        if getattr(obj1, "is_static", False):
                            obj2.transform.position -= normal * overlap
                            v2 = getattr(obj2, "physics_velocity", np.zeros(3, dtype=np.float32))
                            vel_along_normal = np.dot(v2, normal)
                            if vel_along_normal > 0:
                                restitution = 0.5
                                obj2.physics_velocity -= normal * (1.0 + restitution) * vel_along_normal
                        elif getattr(obj2, "is_static", False):
                            obj1.transform.position += normal * overlap
                            v1 = getattr(obj1, "physics_velocity", np.zeros(3, dtype=np.float32))
                            vel_along_normal = np.dot(v1, normal)
                            if vel_along_normal < 0:
                                restitution = 0.5
                                obj1.physics_velocity -= normal * (1.0 + restitution) * vel_along_normal
                        else:
                            obj1.transform.position += normal * (overlap * 0.5)
                            obj2.transform.position -= normal * (overlap * 0.5)
                            
                            v1 = getattr(obj1, "physics_velocity", np.zeros(3, dtype=np.float32))
                            v2 = getattr(obj2, "physics_velocity", np.zeros(3, dtype=np.float32))
                            
                            rel_vel = v1 - v2
                            vel_along_normal = np.dot(rel_vel, normal)
                            
                            if vel_along_normal < 0:
                                restitution = 0.5
                                impulse = -(1.0 + restitution) * vel_along_normal / 2.0
                                
                                obj1.physics_velocity += normal * impulse
                                obj2.physics_velocity -= normal * impulse
                            
        # 2. Arrasto do Gizmo Interativo (Mover, Girar, Escalar)
        elif self.is_dragging_gizmo and 0 <= self.selected_index < len(self.editable_objects):
            selected_obj = self.editable_objects[self.selected_index]
            mouse_pos = pygame.mouse.get_pos()
            dx = mouse_pos[0] - self.gizmo_drag_last_mouse[0]
            dy = mouse_pos[1] - self.gizmo_drag_last_mouse[1]
            self.gizmo_drag_last_mouse = mouse_pos
            
            if self.gizmo_mode == "translate":
                if self.active_gizmo_axis == 'x':
                    selected_obj.transform.position[0] += dx * 0.015
                elif self.active_gizmo_axis == 'y':
                    selected_obj.transform.position[1] -= dy * 0.015
                elif self.active_gizmo_axis == 'z':
                    selected_obj.transform.position[2] -= dy * 0.015
            elif self.gizmo_mode == "scale":
                if self.active_gizmo_axis == 'x':
                    selected_obj.transform.scale[0] = max(0.1, selected_obj.transform.scale[0] + dx * 0.015)
                elif self.active_gizmo_axis == 'y':
                    selected_obj.transform.scale[1] = max(0.1, selected_obj.transform.scale[1] - dy * 0.015)
                elif self.active_gizmo_axis == 'z':
                    selected_obj.transform.scale[2] = max(0.1, selected_obj.transform.scale[2] - dy * 0.015)
                elif self.active_gizmo_axis == 'center':
                    ds = (dx - dy) * 0.015
                    new_s = max(0.1, selected_obj.transform.scale[0] + ds)
                    selected_obj.transform.scale = np.array([new_s, new_s, new_s], dtype=np.float32)
            elif self.gizmo_mode == "rotate":
                if self.active_gizmo_axis == 'x':
                    selected_obj.transform.rotation[0] = (selected_obj.transform.rotation[0] + dy * 0.5) % 360
                elif self.active_gizmo_axis == 'y':
                    selected_obj.transform.rotation[1] = (selected_obj.transform.rotation[1] + dx * 0.5) % 360
                elif self.active_gizmo_axis == 'z':
                    selected_obj.transform.rotation[2] = (selected_obj.transform.rotation[2] + dx * 0.5) % 360
        else:
            # Segurança do mouse para o Gizmo
            if not pygame.mouse.get_pressed()[0]:
                self.is_dragging_gizmo = False
                self.active_gizmo_axis = None
                
            # 3. Arrasto livre antigo (LMB + X/Z) - Desativado em Modo Play
            if self.is_dragging_object and 0 <= self.selected_index < len(self.editable_objects):
                selected_obj = self.editable_objects[self.selected_index]
                mouse_pos = pygame.mouse.get_pos()
                dx = mouse_pos[0] - self.drag_object_last_mouse[0]
                dy = mouse_pos[1] - self.drag_object_last_mouse[1]
                self.drag_object_last_mouse = mouse_pos
                
                yaw_rad = np.radians(self.camera_controller.yaw)
                pitch_rad = np.radians(self.camera_controller.pitch)
                right_vec = np.array([np.cos(yaw_rad), 0.0, -np.sin(yaw_rad)], dtype=np.float32)
                up_vec = np.array([
                    np.sin(pitch_rad) * np.sin(yaw_rad),
                    np.cos(pitch_rad),
                    np.sin(pitch_rad) * np.cos(yaw_rad)
                ], dtype=np.float32)
                
                if pygame.key.get_pressed()[pygame.K_x]:
                    selected_obj.transform.position -= up_vec * (dy * 0.015)
                elif pygame.key.get_pressed()[pygame.K_z]:
                    selected_obj.transform.position += right_vec * (dx * 0.015)
            else:
                if not pygame.mouse.get_pressed()[0]:
                    self.is_dragging_object = False

        for go in self.game_objects:
            go.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        # 1. Limpar área 3D (Viewport) com FUNDO BRANCO
        pygame.draw.rect(screen, (255, 255, 255), (250, 0, 550, 600))
        
        # 2. Desenhar a Grade (Régua) no chão
        self.draw_floor_grid(screen)
        
        # 3. Desenhar todos os objetos 3D da cena
        for go in self.game_objects:
            go.draw(screen)
            
            # Se for o objeto selecionado, desenhar contorno em aramado vermelho com borda grossa (3px)
            if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                renderer = go.get_component(MeshRenderer3D)
                if renderer:
                    orig_wireframe = renderer.wireframe
                    orig_color = renderer.color
                    orig_line_width = renderer.line_width
                    
                    renderer.wireframe = True
                    renderer.color = (255, 0, 0)   # Vermelho brilhante
                    renderer.line_width = 3        # Bordas destacadas com 3px de espessura!
                    renderer.draw(screen)
                    
                    renderer.wireframe = orig_wireframe
                    renderer.color = orig_color
                    renderer.line_width = orig_line_width

        # Desenhar o Gizmo 3D Interativo do objeto selecionado na Viewport (somente se não estiver jogando e se estiver ativo)
        if self.selected_index >= 0 and not self.play_mode and self.gizmo_mode is not None:
            selected_obj = self.editable_objects[self.selected_index]
            P = selected_obj.transform.position
            
            # Projetar alças de acordo com o modo do Gizmo
            if self.gizmo_mode == "rotate":
                # Alças localizadas exatamente sobre a borda dos anéis de raio 0.8
                E_x = P + np.array([0.0, 0.8, 0.0], dtype=np.float32)  # Alça do anel X (Vermelho)
                E_y = P + np.array([0.0, 0.0, 0.8], dtype=np.float32)  # Alça do anel Y (Verde)
                E_z = P + np.array([0.8, 0.0, 0.0], dtype=np.float32)  # Alça do anel Z (Azul)
            else:
                # Eixos de comprimento 1.2 para Mover/Escalar
                E_x = P + np.array([1.2, 0.0, 0.0], dtype=np.float32)
                E_y = P + np.array([0.0, 1.2, 0.0], dtype=np.float32)
                E_z = P + np.array([0.0, 0.0, 1.2], dtype=np.float32)
            
            verts = np.array([P, E_x, E_y, E_z], dtype=np.float32)
            ndc_coords, depths = project_vertices(verts, np.eye(4, dtype=np.float32), self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
            
            near = self.camera_comp.near
            if depths[0] > near and depths[1] > near and depths[2] > near and depths[3] > near:
                w_half = self.camera_comp.viewport_width / 2.0
                h_half = self.camera_comp.viewport_height / 2.0
                v_x = self.camera_comp.viewport_x
                v_y = self.camera_comp.viewport_y
                
                c_x = int(v_x + (ndc_coords[0, 0] + 1.0) * w_half)
                c_y = int(v_y + (-ndc_coords[0, 1] + 1.0) * h_half)
                
                px_x = int(v_x + (ndc_coords[1, 0] + 1.0) * w_half)
                px_y = int(v_y + (-ndc_coords[1, 1] + 1.0) * h_half)
                
                py_x = int(v_x + (ndc_coords[2, 0] + 1.0) * w_half)
                py_y = int(v_y + (-ndc_coords[2, 1] + 1.0) * h_half)
                
                pz_x = int(v_x + (ndc_coords[3, 0] + 1.0) * w_half)
                pz_y = int(v_y + (-ndc_coords[3, 1] + 1.0) * h_half)
                
                self.gizmo_screen_points = {
                    'x': (px_x, px_y),
                    'y': (py_x, py_y),
                    'z': (pz_x, pz_y)
                }
                self.gizmo_screen_center = (c_x, c_y)
                
                # Se for modo Rotação (Girar), desenhar anéis/arcos de órbita
                if self.gizmo_mode == "rotate":
                    # Anel Y (Verde)
                    ring_pts = []
                    for t in np.linspace(0, 2*np.pi, 20):
                        ring_pts.append(P + np.array([0.8*np.cos(t), 0.0, 0.8*np.sin(t)], dtype=np.float32))
                    ring_pts = np.array(ring_pts, dtype=np.float32)
                    ndc_r, depths_r = project_vertices(ring_pts, np.eye(4, dtype=np.float32), self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                    scr_r = []
                    for idx in range(len(ring_pts)):
                        if depths_r[idx] > near:
                            rx = int(v_x + (ndc_r[idx, 0] + 1.0) * w_half)
                            ry = int(v_y + (-ndc_r[idx, 1] + 1.0) * h_half)
                            scr_r.append((rx, ry))
                    if len(scr_r) > 1:
                        pygame.draw.lines(screen, (50, 170, 50), True, scr_r, 1)
                        
                    # Anel X (Vermelho)
                    ring_pts = []
                    for t in np.linspace(0, 2*np.pi, 20):
                        ring_pts.append(P + np.array([0.0, 0.8*np.cos(t), 0.8*np.sin(t)], dtype=np.float32))
                    ring_pts = np.array(ring_pts, dtype=np.float32)
                    ndc_r, depths_r = project_vertices(ring_pts, np.eye(4, dtype=np.float32), self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                    scr_r = []
                    for idx in range(len(ring_pts)):
                        if depths_r[idx] > near:
                            rx = int(v_x + (ndc_r[idx, 0] + 1.0) * w_half)
                            ry = int(v_y + (-ndc_r[idx, 1] + 1.0) * h_half)
                            scr_r.append((rx, ry))
                    if len(scr_r) > 1:
                        pygame.draw.lines(screen, (220, 50, 50), True, scr_r, 1)

                    # Anel Z (Azul)
                    ring_pts = []
                    for t in np.linspace(0, 2*np.pi, 20):
                        ring_pts.append(P + np.array([0.8*np.cos(t), 0.8*np.sin(t), 0.0], dtype=np.float32))
                    ring_pts = np.array(ring_pts, dtype=np.float32)
                    ndc_r, depths_r = project_vertices(ring_pts, np.eye(4, dtype=np.float32), self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                    scr_r = []
                    for idx in range(len(ring_pts)):
                        if depths_r[idx] > near:
                            rx = int(v_x + (ndc_r[idx, 0] + 1.0) * w_half)
                            ry = int(v_y + (-ndc_r[idx, 1] + 1.0) * h_half)
                            scr_r.append((rx, ry))
                    if len(scr_r) > 1:
                        pygame.draw.lines(screen, (50, 100, 220), True, scr_r, 1)

                # Desenhar as linhas de haste do Gizmo (apenas nos modos Mover/Escalar, ocultando na rotação)
                if self.gizmo_mode != "rotate":
                    pygame.draw.line(screen, (220, 50, 50), (c_x, c_y), (px_x, px_y), 3)
                    pygame.draw.line(screen, (50, 170, 50), (c_x, c_y), (py_x, py_y), 3)
                    pygame.draw.line(screen, (50, 100, 220), (c_x, c_y), (pz_x, pz_y), 3)
                
                # Desenhar as extremidades/handles interativos
                if self.gizmo_mode == "translate":
                    pygame.draw.circle(screen, (220, 50, 50), (px_x, px_y), 7)
                    pygame.draw.circle(screen, (50, 170, 50), (py_x, py_y), 7)
                    pygame.draw.circle(screen, (50, 100, 220), (pz_x, pz_y), 7)
                elif self.gizmo_mode == "scale":
                    # Alças quadradas para Escala
                    pygame.draw.rect(screen, (220, 50, 50), (px_x - 6, px_y - 6, 12, 12))
                    pygame.draw.rect(screen, (50, 170, 50), (py_x - 6, py_y - 6, 12, 12))
                    pygame.draw.rect(screen, (50, 100, 220), (pz_x - 6, pz_y - 6, 12, 12))
                    # Alça central amarela no pivô para Escala Uniforme
                    pygame.draw.circle(screen, (240, 200, 0), (c_x, c_y), 6)
                elif self.gizmo_mode == "rotate":
                    # Desenhar pequenos triângulos coloridos apontando para cima nas bordas dos anéis
                    for tx, ty, col in [(px_x, px_y, (220, 50, 50)), (py_x, py_y, (50, 170, 50)), (pz_x, pz_y, (50, 100, 220))]:
                        pygame.draw.polygon(screen, col, [
                            (tx, ty - 8),
                            (tx - 6, ty + 4),
                            (tx + 6, ty + 4)
                        ])

        # 4. Desenhar Painel Lateral de UI Esquerdo (Cinza escuro, largura 230)
        pygame.draw.rect(screen, (38, 42, 50), (0, 0, 230, 600))
        pygame.draw.line(screen, (55, 60, 72), (230, 0), (230, 600), 2)
        
        # Cabeçalhos e textos da UI
        screen.blit(self.font_title.render("ADICIONAR FORMAS", True, (0, 200, 255)), (15, 18))
        self.btn_add_cube.draw(screen, self.font_btn)
        self.btn_add_pyramid.draw(screen, self.font_btn)
        self.btn_add_sphere.draw(screen, self.font_btn)
        
        # Desenhar e destacar botões do Gizmo Mode na barra lateral
        self.btn_mode_translate.bg_color = (0, 150, 220) if self.gizmo_mode == "translate" else (80, 60, 120)
        self.btn_mode_rotate.bg_color = (0, 150, 220) if self.gizmo_mode == "rotate" else (80, 60, 120)
        self.btn_mode_scale.bg_color = (0, 150, 220) if self.gizmo_mode == "scale" else (80, 60, 120)
        
        self.btn_mode_translate.draw(screen, self.font_btn)
        self.btn_mode_rotate.draw(screen, self.font_btn)
        self.btn_mode_scale.draw(screen, self.font_btn)
        
        # Desenhar botões superiores do Viewport (PLAY, Salvar, Carregar)
        self.btn_play_pause.bg_color = (180, 40, 40) if self.play_mode else (40, 120, 60)
        self.btn_play_pause.hover_color = (220, 50, 50) if self.play_mode else (50, 150, 80)
        self.btn_play_pause.text = "STOP" if self.play_mode else "PLAY"
        
        self.btn_play_pause.draw(screen, self.font_btn)
        self.btn_save.draw(screen, self.font_btn)
        self.btn_load.draw(screen, self.font_btn)
        
        screen.blit(self.font_title.render("OBJETOS DA CENA", True, (0, 200, 255)), (15, 125))
        
        # Lista dos últimos 5 objetos
        y_offset = 150
        for idx, obj in enumerate(self.editable_objects[-5:]):
            actual_idx = self.editable_objects.index(obj)
            is_selected = (actual_idx == self.selected_index)
            
            slot_rect = pygame.Rect(15, y_offset, 200, 22)
            bg_color = (60, 80, 110) if is_selected else (45, 49, 58)
            border_color = (0, 200, 255) if is_selected else (70, 76, 90)
            
            pygame.draw.rect(screen, bg_color, slot_rect, border_radius=3)
            pygame.draw.rect(screen, border_color, slot_rect, 1, border_radius=3)
            
            name_text = self.font_body.render(obj.name, True, (255, 255, 255))
            screen.blit(name_text, (25, y_offset + 4))
            y_offset += 26
            
        # Desenhar o botão de excluir objeto posicionado em Y = 300 (Largura 200)
        if 0 <= self.selected_index < len(self.editable_objects):
            self.btn_delete.draw(screen, self.font_btn)
            
        # Desenhar controles de Direção da Luz no painel esquerdo
        screen.blit(self.font_title.render("DIREÇÃO DA LUZ", True, (0, 200, 255)), (15, 340))
        self.btn_light_angle_dec.draw(screen, self.font_btn)
        angle_text = self.font_body.render(f"Sol: {int(self.light_angle)}\u00b0", True, (255, 255, 255))
        screen.blit(angle_text, (65, 368))
        self.btn_light_angle_inc.draw(screen, self.font_btn)
            
        # 4.5. Desenhar overlay de status do objeto selecionado na parte inferior da Viewport 3D (Compactado e Centrado)
        if 0 <= self.selected_index < len(self.editable_objects):
            selected_obj = self.editable_objects[self.selected_index]
            pos = selected_obj.transform.position
            rot = selected_obj.transform.rotation
            scale = selected_obj.transform.scale
            
            # Criar superfície com canal alpha para o fundo semi-transparente
            overlay_surf = pygame.Surface((480, 42), pygame.SRCALPHA)
            overlay_surf.fill((30, 34, 42, 200))  # Cinza escuro semi-transparente
            screen.blit(overlay_surf, (260, 545))
            pygame.draw.rect(screen, (0, 200, 255), (260, 545, 480, 42), 1, border_radius=4)
            
            # Textos de informações do status do objeto (Compactados em duas linhas)
            name_lbl = self.font_xyz.render(f"OBJETO: {selected_obj.name.upper()}", True, (0, 200, 255))
            info_lbl = self.font_body.render(f"Pos: X:{pos[0]:.1f} Y:{pos[1]:.1f} Z:{pos[2]:.1f} | Tam: X:{scale[0]:.1f} Y:{scale[1]:.1f} Z:{scale[2]:.1f} | Rot: X:{int(rot[0])}\u00b0 Y:{int(rot[1])}\u00b0 Z:{int(rot[2])}\u00b0", True, (240, 240, 240))
            
            screen.blit(name_lbl, (270, 548))
            screen.blit(info_lbl, (270, 566))

        # 4.8. Desenhar Painel Lateral de UI Direito (Inspetor - Cinza escuro, largura 230)
        pygame.draw.rect(screen, (38, 42, 50), (770, 0, 230, 600))
        pygame.draw.line(screen, (55, 60, 72), (770, 0), (770, 600), 2)
        
        if 0 <= self.selected_index < len(self.editable_objects):
            selected_obj = self.editable_objects[self.selected_index]
            
            # Título do painel de propriedades
            screen.blit(self.font_title.render("PROPRIEDADES 3D", True, (0, 200, 255)), (785, 18))
            
            # Checkbox Estático
            self.btn_toggle_static.draw(screen, self.font_btn)
            if getattr(selected_obj, "is_static", False):
                pygame.draw.rect(screen, (0, 200, 255), (789, 54, 12, 12))
            screen.blit(self.font_body.render("Estático (Piso/Parede)", True, (240, 240, 240)), (815, 52))
            
            # Checkbox Simular Física
            self.btn_toggle_physics.draw(screen, self.font_btn)
            if getattr(selected_obj, "use_physics", True):
                pygame.draw.rect(screen, (0, 200, 255), (789, 84, 12, 12))
            screen.blit(self.font_body.render("Simular Gravidade", True, (240, 240, 240)), (815, 82))
            
            # Controles de Velocidade Inicial
            screen.blit(self.font_body.render("Impulso Inicial Vertical:", True, (220, 220, 220)), (785, 115))
            self.btn_vel_dec.draw(screen, self.font_btn)
            vy_text = self.font_body.render(f"{selected_obj.initial_velocity_y:+.1f} m/s", True, (255, 255, 255))
            screen.blit(vy_text, (835, 137))
            self.btn_vel_inc.draw(screen, self.font_btn)
            
            # Controles de Script comportamental
            screen.blit(self.font_body.render("Comportamento (Script):", True, (220, 220, 220)), (785, 170))
            self.btn_prev_script.draw(screen, self.font_btn)
            
            # Caixa do nome do script
            pygame.draw.rect(screen, (45, 49, 58), (820, 190, 120, 22), border_radius=3)
            pygame.draw.rect(screen, (70, 76, 90), (820, 190, 120, 22), 1, border_radius=3)
            script_path = getattr(selected_obj, "script_path", "")
            script_name = os.path.basename(script_path) if script_path else "Nenhum"
            # Cortar texto se for muito longo
            if len(script_name) > 13:
                script_name = script_name[:11] + ".."
            screen.blit(self.font_body.render(script_name, True, (255, 255, 255)), (826, 194))
            self.btn_next_script.draw(screen, self.font_btn)
            self.btn_new_script.draw(screen, self.font_btn)
            self.btn_edit_script.draw(screen, self.font_btn)
            self.btn_internal_editor.draw(screen, self.font_btn)
            self.btn_script_help.draw(screen, self.font_btn)
            
            # Cores (Paleta)
            screen.blit(self.font_body.render("Cor do Objeto:", True, (220, 220, 220)), (785, 292))
            for btn in self.btn_colors:
                btn.draw(screen, self.font_btn)
                
            # Clonar Objeto
            self.btn_clone.draw(screen, self.font_btn)
        else:
            # Mensagem quando nenhum objeto está selecionado
            screen.blit(self.font_body.render("Selecione um objeto para", True, (140, 145, 155)), (785, 50))
            screen.blit(self.font_body.render("ver suas propriedades.", True, (140, 145, 155)), (785, 75))

        # 5. Desenhar Widget xyz estático no canto superior direito da Viewport (C centralizado em X=710)
        C = (710, 60)
        v_rot = self.camera_comp.view_matrix[:3, :3]
        
        dir_x = v_rot @ np.array([0.0, 0.0, -1.0], dtype=np.float32)
        dir_y = v_rot @ np.array([0.0, 1.0, 0.0], dtype=np.float32)
        dir_z = v_rot @ np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        axis_len = 35.0
        E_x = np.array([C[0] + axis_len * dir_x[0], C[1] - axis_len * dir_x[1]], dtype=np.float32)
        E_y = np.array([C[0] + axis_len * dir_y[0], C[1] - axis_len * dir_y[1]], dtype=np.float32)
        E_z = np.array([C[0] + axis_len * dir_z[0], C[1] - axis_len * dir_z[1]], dtype=np.float32)
        
        self.gizmo_ex = E_x
        self.gizmo_ey = E_y
        self.gizmo_ez = E_z
        
        p_x = (int(E_x[0]), int(E_x[1]))
        p_y = (int(E_y[0]), int(E_y[1]))
        p_z = (int(E_z[0]), int(E_z[1]))
        
        pygame.draw.line(screen, (220, 50, 50), C, p_x, 2)
        pygame.draw.line(screen, (50, 170, 50), C, p_y, 2)
        pygame.draw.line(screen, (50, 100, 220), C, p_z, 2)
        pygame.draw.circle(screen, (120, 125, 135), C, 4)
        
        for pt, label, col in [(E_x, "X", (220, 50, 50)), (E_y, "Y", (50, 170, 50)), (E_z, "Z", (50, 100, 220))]:
            ix, iy = int(pt[0]), int(pt[1])
            pygame.draw.circle(screen, col, (ix, iy), 9)
            txt = self.font_xyz.render(label, True, (255, 255, 255))
            txt_rect = txt.get_rect(center=(ix, iy))
            screen.blit(txt, txt_rect)
            
        # Desenhar Editor Interno se estiver ativo
        if self.editing_script_path is not None:
            self.draw_internal_editor(screen)
            
        # Desenhar Guia de Comandos se estiver ativo
        elif self.showing_help_modal:
            self.draw_help_modal(screen)

    def draw_internal_editor(self, screen: pygame.Surface) -> None:
        # Fundo escuro semi-transparente
        overlay = pygame.Surface((1000, 600), pygame.SRCALPHA)
        overlay.fill((20, 24, 30, 230))
        screen.blit(overlay, (0, 0))
        
        # Painel central
        modal_rect = pygame.Rect(120, 40, 760, 520)
        pygame.draw.rect(screen, (30, 34, 42), modal_rect, border_radius=8)
        pygame.draw.rect(screen, (0, 200, 255), modal_rect, 2, border_radius=8)
        
        # Barra de titulo
        title_rect = pygame.Rect(120, 40, 760, 35)
        pygame.draw.rect(screen, (42, 47, 57), title_rect, border_radius=8)
        pygame.draw.line(screen, (55, 60, 72), (120, 75), (880, 75), 2)
        
        fname = os.path.basename(self.editing_script_path)
        screen.blit(self.font_title.render(f"Zennity Code Editor - {fname}", True, (0, 200, 255)), (140, 48))
        
        # Instrucoes
        screen.blit(self.font_body.render("Ctrl+S: Salvar  |  Esc: Fechar  |  Use as setas para navegar", True, (150, 155, 165)), (140, 535))
        
        # Botoes
        self.btn_editor_save.draw(screen, self.font_btn)
        self.btn_editor_close.draw(screen, self.font_btn)
        
        # Area de texto
        text_bg = pygame.Rect(140, 90, 720, 430)
        pygame.draw.rect(screen, (22, 25, 30), text_bg, border_radius=4)
        pygame.draw.rect(screen, (55, 60, 72), text_bg, 1, border_radius=4)
        
        # Renderizar linhas visiveis
        visible_lines = 20
        y_pos = 100
        for i in range(self.editor_scroll_y, min(len(self.script_editor_lines), self.editor_scroll_y + visible_lines)):
            line_str = self.script_editor_lines[i]
            
            # Numero da linha
            num_lbl = self.font_body.render(f"{i+1:3d} |", True, (90, 95, 105))
            screen.blit(num_lbl, (150, y_pos))
            
            # Texto da linha
            txt_lbl = self.font_body.render(line_str, True, (240, 240, 240))
            screen.blit(txt_lbl, (200, y_pos))
            
            # Cursor
            if i == self.editor_cursor_row:
                sub_str = line_str[:self.editor_cursor_col]
                text_width = self.font_body.size(sub_str)[0]
                cursor_x = 200 + text_width
                pygame.draw.line(screen, (0, 200, 255), (cursor_x, y_pos), (cursor_x, y_pos + 14), 2)
                
            y_pos += 20

    def draw_help_modal(self, screen: pygame.Surface) -> None:
        # Fundo escuro semi-transparente
        overlay = pygame.Surface((1000, 600), pygame.SRCALPHA)
        overlay.fill((20, 24, 30, 230))
        screen.blit(overlay, (0, 0))
        
        # Painel central
        modal_rect = pygame.Rect(120, 40, 760, 520)
        pygame.draw.rect(screen, (30, 34, 42), modal_rect, border_radius=8)
        pygame.draw.rect(screen, (0, 200, 255), modal_rect, 2, border_radius=8)
        
        # Barra de titulo
        title_rect = pygame.Rect(120, 40, 760, 35)
        pygame.draw.rect(screen, (42, 47, 57), title_rect, border_radius=8)
        pygame.draw.line(screen, (55, 60, 72), (120, 75), (880, 75), 2)
        
        screen.blit(self.font_title.render("Guia de Comandos Scripting (Zennity Engine Game)", True, (0, 200, 255)), (140, 48))
        
        self.btn_help_close.draw(screen, self.font_btn)
        
        # Area de texto (Leitura)
        text_bg = pygame.Rect(140, 90, 720, 430)
        pygame.draw.rect(screen, (22, 25, 30), text_bg, border_radius=4)
        pygame.draw.rect(screen, (55, 60, 72), text_bg, 1, border_radius=4)
        
        help_lines = [
            "Os scripts controlam o comportamento dos objetos durante a simulacao (PLAY).",
            "Cada script deve conter as funcoes 'start(obj)' e 'update(obj, dt)'.",
            "",
            "1. LER ENTRADAS DE TECLADO (Input):",
            "   Importe a classe Input e o Pygame:",
            "   -------------------------------------------------",
            "   from engine.input import Input",
            "   import pygame",
            "   ",
            "   # Mover no eixo X usando as teclas 'A' e 'D':",
            "   if Input.get_key(pygame.K_d):",
            "       obj.transform.position[0] += 2.0 * dt",
            "   if Input.get_key(pygame.K_a):",
            "       obj.transform.position[0] -= 2.0 * dt",
            "   -------------------------------------------------",
            "",
            "2. PULOS E FISICA (Impulso):",
            "   Se o objeto tiver a opcao 'Simular Gravidade' ligada:",
            "   -------------------------------------------------",
            "   # Aplicar impulso vertical ao pressionar ESPACO:",
            "   if Input.get_key_down(pygame.K_SPACE):",
            "       if hasattr(obj, 'physics_velocity'):",
            "           obj.physics_velocity[1] = 6.0  # Velocidade de pulo",
            "   -------------------------------------------------",
            "",
            "3. ROTACAO E ESCALA:",
            "   Edite obj.transform.rotation (graus) ou obj.transform.scale:",
            "   -------------------------------------------------",
            "   # Rotacionar no eixo Y continuamente:",
            "   obj.transform.rotation[1] = (obj.transform.rotation[1] + 45.0 * dt) % 360",
            "   ",
            "   # Pulsar escala periodicamente (usando numpy ou math):",
            "   import numpy as np",
            "   fator = 1.0 + 0.2 * np.sin(obj.script_time * 5.0)",
            "   obj.transform.scale = np.array([fator, fator, fator])",
            "   -------------------------------------------------"
        ]
        
        y_pos = 105
        for line in help_lines:
            color = (0, 200, 255) if line.startswith("   ") else (220, 222, 226)
            screen.blit(self.font_body.render(line, True, color), (160, y_pos))
            y_pos += 18

    def setup_inspector_buttons(self) -> None:
        self.btn_delete = GuiButton(15, 300, 200, 26, "Excluir Objeto", bg_color=(140, 40, 40), hover_color=(175, 50, 50))

    def open_internal_editor(self, path: str) -> None:
        self.editing_script_path = path
        self.script_editor_lines = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.script_editor_lines = f.read().splitlines()
            except Exception as e:
                print(f"Erro ao ler arquivo: {e}")
        if not self.script_editor_lines:
            self.script_editor_lines = [""]
        self.editor_cursor_row = 0
        self.editor_cursor_col = 0
        self.editor_scroll_y = 0
        pygame.key.set_repeat(300, 30)

    def save_internal_script(self) -> None:
        if self.editing_script_path:
            try:
                content = "\n".join(self.script_editor_lines)
                with open(self.editing_script_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Script salvo com sucesso: {self.editing_script_path}")
            except Exception as e:
                print(f"Erro ao salvar arquivo: {e}")

    def handle_event(self, event: pygame.event.Event) -> None:
        # 1. Se o Editor Interno estiver ativo, desviar todos os eventos para ele
        if self.editing_script_path is not None:
            if self.btn_editor_save.is_clicked(event):
                self.save_internal_script()
                return
            elif self.btn_editor_close.is_clicked(event):
                self.editing_script_path = None
                pygame.key.set_repeat(0, 0)
                return
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.editing_script_path = None
                    pygame.key.set_repeat(0, 0)
                    return
                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.save_internal_script()
                    return
                elif event.key == pygame.K_UP:
                    if self.editor_cursor_row > 0:
                        self.editor_cursor_row -= 1
                        self.editor_cursor_col = min(self.editor_cursor_col, len(self.script_editor_lines[self.editor_cursor_row]))
                        if self.editor_cursor_row < self.editor_scroll_y:
                            self.editor_scroll_y = self.editor_cursor_row
                    return
                elif event.key == pygame.K_DOWN:
                    if self.editor_cursor_row < len(self.script_editor_lines) - 1:
                        self.editor_cursor_row += 1
                        self.editor_cursor_col = min(self.editor_cursor_col, len(self.script_editor_lines[self.editor_cursor_row]))
                        if self.editor_cursor_row >= self.editor_scroll_y + 20:
                            self.editor_scroll_y = self.editor_cursor_row - 19
                    return
                elif event.key == pygame.K_LEFT:
                    if self.editor_cursor_col > 0:
                        self.editor_cursor_col -= 1
                    elif self.editor_cursor_row > 0:
                        self.editor_cursor_row -= 1
                        self.editor_cursor_col = len(self.script_editor_lines[self.editor_cursor_row])
                        if self.editor_cursor_row < self.editor_scroll_y:
                            self.editor_scroll_y = self.editor_cursor_row
                    return
                elif event.key == pygame.K_RIGHT:
                    if self.editor_cursor_col < len(self.script_editor_lines[self.editor_cursor_row]):
                        self.editor_cursor_col += 1
                    elif self.editor_cursor_row < len(self.script_editor_lines) - 1:
                        self.editor_cursor_row += 1
                        self.editor_cursor_col = 0
                        if self.editor_cursor_row >= self.editor_scroll_y + 20:
                            self.editor_scroll_y = self.editor_cursor_row - 19
                    return
                elif event.key == pygame.K_BACKSPACE:
                    row = self.editor_cursor_row
                    col = self.editor_cursor_col
                    if col > 0:
                        line = self.script_editor_lines[row]
                        self.script_editor_lines[row] = line[:col-1] + line[col:]
                        self.editor_cursor_col -= 1
                    elif row > 0:
                        prev_line = self.script_editor_lines[row-1]
                        cur_line = self.script_editor_lines[row]
                        self.editor_cursor_col = len(prev_line)
                        self.script_editor_lines[row-1] = prev_line + cur_line
                        self.script_editor_lines.pop(row)
                        self.editor_cursor_row -= 1
                        if self.editor_cursor_row < self.editor_scroll_y:
                            self.editor_scroll_y = self.editor_cursor_row
                    return
                elif event.key == pygame.K_RETURN:
                    row = self.editor_cursor_row
                    col = self.editor_cursor_col
                    line = self.script_editor_lines[row]
                    self.script_editor_lines[row] = line[:col]
                    self.script_editor_lines.insert(row + 1, line[col:])
                    self.editor_cursor_row += 1
                    self.editor_cursor_col = 0
                    if self.editor_cursor_row >= self.editor_scroll_y + 20:
                        self.editor_scroll_y = self.editor_cursor_row - 19
                    return
                elif event.key == pygame.K_TAB:
                    row = self.editor_cursor_row
                    col = self.editor_cursor_col
                    line = self.script_editor_lines[row]
                    self.script_editor_lines[row] = line[:col] + "    " + line[col:]
                    self.editor_cursor_col += 4
                    return
                else:
                    if event.unicode and ord(event.unicode) >= 32:
                        row = self.editor_cursor_row
                        col = self.editor_cursor_col
                        line = self.script_editor_lines[row]
                        self.script_editor_lines[row] = line[:col] + event.unicode + line[col:]
                        self.editor_cursor_col += 1
                    return
            return

        # 2. Se o Guia de Ajuda estiver ativo, desviar todos os eventos para ele
        if self.showing_help_modal:
            if self.btn_help_close.is_clicked(event):
                self.showing_help_modal = False
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.showing_help_modal = False
                return
            return

        # Clicks na GUI de adicionar formas
        if self.btn_add_cube.is_clicked(event):
            self.spawn_object("Cube")
        elif self.btn_add_pyramid.is_clicked(event):
            self.spawn_object("Pyramid")
        elif self.btn_add_sphere.is_clicked(event):
            self.spawn_object("Sphere")

        # Clicks na seleção do Gizmo Mode (com alternância Liga/Desliga)
        elif self.btn_mode_translate.is_clicked(event):
            self.gizmo_mode = None if self.gizmo_mode == "translate" else "translate"
        elif self.btn_mode_rotate.is_clicked(event):
            self.gizmo_mode = None if self.gizmo_mode == "rotate" else "rotate"
        elif self.btn_mode_scale.is_clicked(event):
            self.gizmo_mode = None if self.gizmo_mode == "scale" else "scale"
 
        # Clicks na Simulação Física e Arquivo
        elif self.btn_play_pause.is_clicked(event):
            if not self.play_mode:
                self.play_mode = True
                self.saved_scene_state = []
                import importlib.util
                for obj in self.editable_objects:
                    self.saved_scene_state.append({
                        "obj_ref": obj,
                        "position": obj.transform.position.copy(),
                        "rotation": obj.transform.rotation.copy(),
                        "scale": obj.transform.scale.copy()
                    })
                    vy = getattr(obj, "initial_velocity_y", 0.0)
                    obj.physics_velocity = np.array([0.0, vy, 0.0], dtype=np.float32)
                    
                    # Carregar script dinamicamente
                    path = getattr(obj, "script_path", "")
                    if path and os.path.exists(path):
                        try:
                            spec = importlib.util.spec_from_file_location("user_script_" + str(id(obj)), path)
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            obj.script_module = module
                            if hasattr(module, "start"):
                                module.start(obj)
                        except Exception as script_err:
                            print(f"Erro ao carregar script {path}: {script_err}")
            else:
                self.play_mode = False
                if self.saved_scene_state:
                    for state in self.saved_scene_state:
                        obj = state["obj_ref"]
                        obj.transform.position = state["position"]
                        obj.transform.rotation = state["rotation"]
                        obj.transform.scale = state["scale"]
                        if hasattr(obj, "physics_velocity"):
                            delattr(obj, "physics_velocity")
                        if hasattr(obj, "script_module"):
                            delattr(obj, "script_module")
                        
                        # Limpar atributos temporários criados por scripts (como 'time')
                        for key in list(obj.__dict__.keys()):
                            if key not in ["name", "transform", "components", "scene", "mesh_type", "is_static", "use_physics", "initial_velocity_y", "script_path", "active", "parent", "children"]:
                                delattr(obj, key)
                    self.saved_scene_state = None
        elif self.btn_save.is_clicked(event):
            self.save_scene()
        elif self.btn_load.is_clicked(event):
            self.load_scene()

        # Clicks na rotação de ângulo da luz (Sol)
        elif self.btn_light_angle_dec.is_clicked(event) or self.btn_light_angle_inc.is_clicked(event):
            delta = -15.0 if self.btn_light_angle_dec.is_clicked(event) else 15.0
            self.light_angle = (self.light_angle + delta) % 360
            rad = np.radians(self.light_angle)
            light_dir = np.array([np.cos(rad), 1.0, np.sin(rad)], dtype=np.float32)
            light_dir /= np.linalg.norm(light_dir)
            for obj in self.editable_objects:
                renderer = obj.get_component(MeshRenderer3D)
                if renderer:
                    renderer.light_dir = light_dir

        # Clicks no Inspetor Lateral Direito
        elif 0 <= self.selected_index < len(self.editable_objects):
            selected_obj = self.editable_objects[self.selected_index]
            
            # Checkbox estático
            if self.btn_toggle_static.is_clicked(event):
                selected_obj.is_static = not getattr(selected_obj, "is_static", False)
                
            # Checkbox física
            elif self.btn_toggle_physics.is_clicked(event):
                selected_obj.use_physics = not getattr(selected_obj, "use_physics", True)
                
            # Velocidade Inicial
            elif self.btn_vel_dec.is_clicked(event):
                selected_obj.initial_velocity_y = getattr(selected_obj, "initial_velocity_y", 0.0) - 1.0
            elif self.btn_vel_inc.is_clicked(event):
                selected_obj.initial_velocity_y = getattr(selected_obj, "initial_velocity_y", 0.0) + 1.0
                
            # Scripts de Comportamento
            elif self.btn_prev_script.is_clicked(event) or self.btn_next_script.is_clicked(event):
                cur_script = getattr(selected_obj, "script_path", "")
                if cur_script not in self.available_scripts:
                    cur_idx = 0
                else:
                    cur_idx = self.available_scripts.index(cur_script)
                delta = -1 if self.btn_prev_script.is_clicked(event) else 1
                new_idx = (cur_idx + delta) % len(self.available_scripts)
                selected_obj.script_path = self.available_scripts[new_idx] if new_idx > 0 else ""
                
            # Criar novo Script personalizado para o objeto
            elif self.btn_new_script.is_clicked(event):
                script_name = f"behavior_{selected_obj.name.lower().replace(' ', '_')}.py"
                os.makedirs("scripts", exist_ok=True)
                script_path = os.path.join("scripts", script_name)
                
                template_content = f"""# Script de Comportamento para o objeto: {selected_obj.name}
# Voce pode editar este arquivo para programar o comportamento do objeto em tempo de execucao.

def start(obj):
    # Executado uma unica vez ao iniciar a simulacao (PLAY)
    print(f"Iniciando comportamento de {{obj.name}}!")
    obj.start_pos = obj.transform.position.copy()
    obj.script_time = 0.0

def update(obj, dt):
    # Executado a cada frame durante a simulacao (PLAY)
    obj.script_time = getattr(obj, "script_time", 0.0) + dt
    
    # Exemplo: Rotacao suave no eixo Y
    obj.transform.rotation[1] = (obj.transform.rotation[1] + 45.0 * dt) % 360
"""
                if not os.path.exists(script_path):
                    with open(script_path, "w", encoding="utf-8") as f_script:
                        f_script.write(template_content)
                    print(f"Novo script criado em: {script_path}")
                
                # Recarregar lista de scripts
                self.available_scripts = ["Nenhum"]
                for f in os.listdir("scripts"):
                    if f.endswith(".py"):
                        self.available_scripts.append(os.path.join("scripts", f))
                
                # Auto-vincular
                selected_obj.script_path = script_path
                
            # Abrir o script para edicao no editor padrao do sistema
            elif self.btn_edit_script.is_clicked(event):
                script_path = getattr(selected_obj, "script_path", "")
                if script_path and os.path.exists(script_path):
                    try:
                        os.startfile(script_path)
                    except Exception as open_err:
                        print(f"Erro ao abrir script: {open_err}. Tentando Bloco de Notas...")
                        try:
                            import subprocess
                            subprocess.Popen(["notepad.exe", script_path])
                        except Exception as np_err:
                            print(f"Erro ao abrir Bloco de Notas: {np_err}")
                            
            # Abrir o script para edicao no editor interno modal
            elif self.btn_internal_editor.is_clicked(event):
                script_path = getattr(selected_obj, "script_path", "")
                if script_path and os.path.exists(script_path):
                    self.open_internal_editor(script_path)
                    
            # Mostrar Guia de Ajuda de Comandos
            elif self.btn_script_help.is_clicked(event):
                self.showing_help_modal = True
                            
            # Clonar Objeto
            elif self.btn_clone.is_clicked(event):
                self.clone_selected()
                
            # Cores
            else:
                for c_idx, btn in enumerate(self.btn_colors):
                    if btn.is_clicked(event):
                        renderer = selected_obj.get_component(MeshRenderer3D)
                        if renderer:
                            renderer.color = self.color_palette[c_idx]
                        break

        # Atalho de teclado para clonar (Ctrl + D)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.clone_selected()
 
        # Clicks no Widget XYZ do Canto Superior Direito
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if hasattr(self, 'gizmo_ex') and self.gizmo_ex is not None:
                d_x = np.linalg.norm(np.array([mx, my]) - self.gizmo_ex)
                d_y = np.linalg.norm(np.array([mx, my]) - self.gizmo_ey)
                d_z = np.linalg.norm(np.array([mx, my]) - self.gizmo_ez)
                
                if d_x < 12.0:
                    self.camera_controller.target_yaw = 0.0
                    self.camera_controller.target_pitch = 0.0
                    return
                elif d_y < 12.0:
                    self.camera_controller.target_yaw = 0.0
                    self.camera_controller.target_pitch = 85.0
                    return
                elif d_z < 12.0:
                    self.camera_controller.target_yaw = 0.0
                    self.camera_controller.target_pitch = -85.0
                    return
 
        # Clicks nas extremidades do Gizmo do objeto selecionado na tela
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.selected_index >= 0 and not self.play_mode and self.gizmo_mode is not None and hasattr(self, 'gizmo_screen_points'):
                # Verificar clique na alça central de escala uniforme
                if self.gizmo_mode == "scale" and hasattr(self, 'gizmo_screen_center'):
                    cx, cy = self.gizmo_screen_center
                    d_center = np.linalg.norm(np.array([mx, my]) - np.array([cx, cy]))
                    if d_center < 10.0:
                        self.is_dragging_gizmo = True
                        self.active_gizmo_axis = 'center'
                        self.gizmo_drag_last_mouse = event.pos
                        return
                        
                for axis, pt in self.gizmo_screen_points.items():
                    d = np.linalg.norm(np.array([mx, my]) - pt)
                    if d < 12.0:
                        self.is_dragging_gizmo = True
                        self.active_gizmo_axis = axis
                        self.gizmo_drag_last_mouse = event.pos
                        return

        # Controle de cliques de mouse para seleção (distinguindo arrasto de clique rápido)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click_start_pos = event.pos
            mx, my = event.pos
            # Verificar se clicou no objeto selecionado para iniciar arrasto
            if 230 <= mx <= 770 and 0 <= self.selected_index < len(self.editable_objects):
                selected_obj = self.editable_objects[self.selected_index]
                renderer = selected_obj.get_component(MeshRenderer3D)
                if renderer and renderer.last_screen_coords is not None:
                    coords = renderer.last_screen_coords
                    for face in renderer.mesh.faces:
                        poly = [tuple(coords[v_idx]) for v_idx in face]
                        if point_in_polygon(mx, my, poly):
                            self.is_dragging_object = True
                            self.drag_object_last_mouse = event.pos
                            break
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_object = False
            self.is_dragging_gizmo = False
            self.active_gizmo_axis = None
            if self.click_start_pos is not None:
                dx = event.pos[0] - self.click_start_pos[0]
                dy = event.pos[1] - self.click_start_pos[1]
                dist = np.sqrt(dx*dx + dy*dy)
                
                # Se o mouse moveu menos de 4 pixels, foi um CLIQUE (seleção)
                if dist < 4.0:
                    mx, my = event.pos
                    if mx < 230:
                        # Clique na lista lateral do painel
                        y_offset = 150
                        for idx, obj in enumerate(self.editable_objects[-5:]):
                            slot_rect = pygame.Rect(15, y_offset, 200, 22)
                            if slot_rect.collidepoint((mx, my)):
                                self.selected_index = self.editable_objects.index(obj)
                            y_offset += 26
                    elif mx <= 770:
                        # Clique na tela 3D
                        self.select_object_at_screen_pos(event.pos)
                        
                self.click_start_pos = None

        # Zoom de câmera com scroll suavizado
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll Up
                self.camera_controller.target_distance = max(1.5, self.camera_controller.target_distance - 0.3)
            elif event.button == 5:  # Scroll Down
                self.camera_controller.target_distance = min(15.0, self.camera_controller.target_distance + 0.3)

        # Modificação de transform no Inspetor (apenas exclusão)
        if 0 <= self.selected_index < len(self.editable_objects):
            if self.btn_delete.is_clicked(event):
                self.delete_selected()


if __name__ == '__main__':
    engine = Engine(width=1000, height=600, title="Zennity Engine Game - 3D Editor de Cenas")
    scene = EditorScene()
    scene.setup_inspector_buttons()
    engine.run(scene)
