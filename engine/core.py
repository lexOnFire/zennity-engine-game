"""
engine/core.py
────────────────────────────────────────────────────────────────

Arquitetura:

    Application              ← dona de tudo
    └── Engine               ← executor de sistemas por frame
           │
           ├── UpdateSystems    (é chamado por SceneManager.update)
           └── RenderSystems    (é chamado por SceneManager.draw)

Responsabilidades da Engine:
  ✅ Executar a lista de UpdateSystems em ordem
  ✅ Executar a lista de RenderSystems em ordem
  ❌ Janela  → Window
  ❌ Clock   → Time
  ❌ Eventos → Application
  ❌ Cenas   → SceneManager

Retrocompatibilidade:
  Os atributos `screen`, `width`, `height`, `fps`, `is_running`,
  `_scene_manager`, `_current_scene`, `_next_scene` e o método
  `change_scene()` ainda existem para que demos antigas continuem
  funcionando sem alteração. Eles serão preenchidos pela Application
  após criar a Engine.
"""
from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Callable, List, Optional

import pygame

if TYPE_CHECKING:
    from engine.application import Application


# ============================================================== #
#  Scene — base de todas as cenas                                #
# ============================================================== #

class Scene:
    """Contrato mínimo de uma cena."""

    def __init__(self) -> None:
        self.engine: Optional["Engine"] = None
        self.game_objects: list = []

    def start(self)        -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, screen: pygame.Surface) -> None: ...
    def handle_event(self, event: pygame.event.Event) -> None: ...


# ============================================================== #
#  Tipos de sistema                                              #
# ============================================================== #

UpdateSystem = Callable[["Scene", float], None]
RenderSystem = Callable[["Scene", pygame.Surface], None]


# ============================================================== #
#  Engine                                                        #
# ============================================================== #

class Engine:
    """
    Executor de sistemas por frame.

    A Engine não cria janela, não gerencia clock nem eventos.
    Ela recebe uma cena ativa (via SceneManager) e aplica
    os UpdateSystems e RenderSystems cadastrados.

    Uso direto (sem Application — retrocompat):

        engine = Engine(800, 600, "Meu Jogo")
        engine.run(MenuScene())

    Uso moderno (com Application):

        app = Application(800, 600, "Meu Jogo")
        app.engine.add_update_system(physics_system)
        app.run(MenuScene())
    """

    def __init__(
        self,
        width:  int = 800,
        height: int = 600,
        title:  str = "Zennity Engine",
        fps:    int = 60,
    ) -> None:
        # Apenas quando Engine é instanciada diretamente (sem Application)
        import sys
        pygame.init()
        pygame.mixer.init()

        info = pygame.display.Info()
        dw, dh = info.current_w, info.current_h
        if width >= dw or height >= dh:
            width  = int(dw * 0.9)
            height = int(dh * 0.85)

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)

        self.width  = width
        self.height = height
        self.fps    = fps
        self.is_fullscreen = False
        self.saved_w = width
        self.saved_h = height
        self.clock   = pygame.time.Clock()
        self.is_running = False

        # Retrocompat
        self._scene_manager  = None
        self._current_scene: Optional[Scene] = None
        self._next_scene:    Optional[Scene] = None

        # Referência fraca à Application dona (preenchida por Application)
        self._app: Optional["Application"] = None

        # Sistemas
        self._update_systems: List[UpdateSystem] = [_builtin_physics_system]
        self._render_systems: List[RenderSystem] = []

    # ------------------------------------------------------------------ #
    # Registro de sistemas                                               #
    # ------------------------------------------------------------------ #

    def add_update_system(self, system: UpdateSystem) -> None:
        """
        Adiciona um UpdateSystem ao final da fila.

        Um UpdateSystem é qualquer callable com assinatura:
            def my_system(scene: Scene, dt: float) -> None: ...
        """
        if system not in self._update_systems:
            self._update_systems.append(system)

    def remove_update_system(self, system: UpdateSystem) -> None:
        try:
            self._update_systems.remove(system)
        except ValueError:
            pass

    def add_render_system(self, system: RenderSystem) -> None:
        """
        Adiciona um RenderSystem ao final da fila.

        Um RenderSystem é qualquer callable com assinatura:
            def my_system(scene: Scene, screen: pygame.Surface) -> None: ...
        """
        if system not in self._render_systems:
            self._render_systems.append(system)

    def remove_render_system(self, system: RenderSystem) -> None:
        try:
            self._render_systems.remove(system)
        except ValueError:
            pass

    # ------------------------------------------------------------------ #
    # Execução de sistemas (chamada pelo SceneManager)                   #
    # ------------------------------------------------------------------ #

    def run_update_systems(self, scene: Scene, dt: float) -> None:
        """Executa todos os UpdateSystems cadastrados na ordem de registro."""
        for system in list(self._update_systems):
            try:
                system(scene, dt)
            except Exception:
                traceback.print_exc()

    def run_render_systems(self, scene: Scene, screen: pygame.Surface) -> None:
        """Executa todos os RenderSystems cadastrados na ordem de registro."""
        for system in list(self._render_systems):
            try:
                system(scene, screen)
            except Exception:
                traceback.print_exc()

    # ------------------------------------------------------------------ #
    # Retrocompat: API de cena direta (sem Application / SceneManager)   #
    # ------------------------------------------------------------------ #

    @property
    def current_scene(self) -> Optional[Scene]:
        if self._scene_manager:
            return self._scene_manager.current
        return self._current_scene

    def use_scene_manager(self):
        from .scene_manager import SceneManager
        sm = SceneManager.instance()
        sm.bind(self)
        self._scene_manager = sm
        return sm

    def change_scene(self, new_scene: Scene) -> None:
        if self._scene_manager:
            self._scene_manager.load(new_scene)
        else:
            self._next_scene = new_scene

    def _perform_scene_change(self) -> None:
        if self._next_scene is not None:
            try:
                from engine.physics.collider import BoxCollider, CircleCollider
                if self._current_scene:
                    BoxCollider.invalidate_tilemap_cache(self._current_scene)
                BoxCollider._registry.clear()
                CircleCollider._registry.clear()
                BoxCollider._scene_tilemap_components.clear()
                BoxCollider._scene_tilemaps.clear()
            except Exception:
                pass
            self._current_scene = self._next_scene
            self._current_scene.engine = self
            self._current_scene.start()
            self._next_scene = None

    def toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.saved_w, self.saved_h = self.width, self.height
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.FULLSCREEN
            )
        else:
            self.width, self.height = self.saved_w, self.saved_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.RESIZABLE
            )

    # ------------------------------------------------------------------ #
    # Loop standalone (retrocompat sem Application)                       #
    # ------------------------------------------------------------------ #

    def run(self, initial_scene: Scene) -> None:
        """
        Loop principal standalone — mantido para retrocompatibilidade.
        Quando usado com Application, este método não é chamado.
        """
        import sys
        from .input import Input

        self.is_running = True

        if self._scene_manager:
            self._scene_manager.load(initial_scene)
        else:
            self.change_scene(initial_scene)
            self._perform_scene_change()

        while self.is_running:
            Input.update()
            dt = min(self.clock.tick(self.fps) / 1000.0, 0.1)

            sm = self._scene_manager

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                try:
                    if sm:
                        sm.handle_event(event)
                    elif self._current_scene:
                        self._current_scene.handle_event(event)
                except Exception:
                    traceback.print_exc()

            try:
                if sm:
                    sm.update(dt)
                else:
                    if self._next_scene:
                        self._perform_scene_change()
                    if self._current_scene:
                        self._current_scene.update(dt)
                        self.run_update_systems(self._current_scene, dt)
            except Exception:
                traceback.print_exc()

            try:
                if sm:
                    sm.draw(self.screen)
                elif self._current_scene:
                    self._current_scene.draw(self.screen)
                    self.run_render_systems(self._current_scene, self.screen)
            except Exception:
                traceback.print_exc()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ============================================================== #
#  Sistemas builtin                                              #
# ============================================================== #

def _builtin_physics_system(scene: Scene, dt: float) -> None:
    """
    UpdateSystem builtin: roda BoxCollider.check_all() e
    CircleCollider.check_all() após scene.update(dt).

    Registrado automaticamente na Engine. Remova com:
        engine.remove_update_system(_builtin_physics_system)
    """
    try:
        from engine.physics.collider import BoxCollider, CircleCollider
        BoxCollider.check_all()
        CircleCollider.check_all()
    except Exception:
        traceback.print_exc()
