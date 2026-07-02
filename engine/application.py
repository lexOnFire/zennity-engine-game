"""
Application — raiz da arquitetura da Zennity Engine.

Hierarquia de propriedade:

    Application
    │
    ├── Window          gerencia janela Pygame (surface, resize, fullscreen)
    ├── Engine          loop interno + retrocompat de cena
    ├── SceneManager    pilha de cenas, transições
    ├── Input           estado do teclado/mouse por frame
    ├── Time            delta-time, clock, fps
    ├── EventBus        pub/sub desacoplado entre sistemas
    └── AssetManager    carregamento e cache de assets (Assets)

Uso mínimo:

    from engine.application import Application
    from my_game.scenes import MenuScene

    app = Application(width=1280, height=720, title="Meu Jogo")
    app.run(MenuScene())

A Application permanece retrocompatível: `Engine` ainda funciona
isoladamente, mas ao criar uma `Application` ela torna-se a proprietária
do loop e dos subsistemas.
"""
from __future__ import annotations

import sys
import traceback
from typing import Optional

import pygame

from .window       import Window
from .time         import Time
from .event_bus    import EventBus
from .input        import Input
from .assets       import Assets
from .core         import Scene, Engine
from .scene_manager import SceneManager


class Application:
    """
    Dono de todos os subsistemas da engine.

    Cria, conecta e orquestra:
      - Window   : janela Pygame
      - Time     : clock e delta-time
      - EventBus : comunicação pub/sub interna
      - Input    : snapshot de input por frame
      - Assets   : cache de assets (wraps Assets estático)
      - Engine   : loop + retrocompat de cenas
      - SceneManager : pilha de cenas com transições
    """

    # Instância global opcional (singleton fraco — sem forçar)
    _instance: Optional["Application"] = None

    def __init__(
        self,
        width:  int   = 800,
        height: int   = 600,
        title:  str   = "Zennity Engine",
        fps:    int   = 60,
        dt_cap: float = 0.1,
    ) -> None:
        pygame.init()
        pygame.mixer.init()

        # ── Subsistemas ──────────────────────────────────────────────
        self.window:       Window        = Window(width, height, title)
        self.time:         Time          = Time(fps, dt_cap)
        self.event_bus:    EventBus      = EventBus()
        self.scene_manager: SceneManager = SceneManager.instance()
        self.assets:       Assets        = Assets  # classe-namespace estática

        # Engine (retrocompat) — reutiliza a janela já criada
        self.engine: Engine = Engine.__new__(Engine)
        self.engine.screen         = self.window.screen
        self.engine.width          = self.window.width
        self.engine.height         = self.window.height
        self.engine.fps            = fps
        self.engine.is_fullscreen  = False
        self.engine.saved_w        = width
        self.engine.saved_h        = height
        self.engine.clock          = pygame.time.Clock()  # não usada pelo loop da Application
        self.engine.is_running     = False
        self.engine._scene_manager = self.scene_manager
        self.engine._current_scene = None
        self.engine._next_scene    = None

        self.scene_manager.bind(self.engine)

        self._is_running = False
        Application._instance = self

    # ------------------------------------------------------------------ #
    # Acesso global (opcional)
    # ------------------------------------------------------------------ #

    @classmethod
    def get(cls) -> Optional["Application"]:
        """Retorna a instância global, se existir."""
        return cls._instance

    # ------------------------------------------------------------------ #
    # Loop principal
    # ------------------------------------------------------------------ #

    def run(self, initial_scene: Scene) -> None:
        """Inicia o loop principal da aplicação."""
        self._is_running = True
        self.engine.is_running = True

        self.scene_manager.load(initial_scene)

        while self._is_running:
            dt = self.time.tick()

            # ── Sync window → engine (resize pode alterar screen) ────
            self.engine.screen = self.window.screen
            self.engine.width  = self.window.width
            self.engine.height = self.window.height

            # ── Input ───────────────────────────────────────────────
            Input.update()

            # ── Eventos ─────────────────────────────────────────────
            for event in pygame.event.get():
                self._handle_system_event(event)
                try:
                    self.scene_manager.handle_event(event)
                except Exception:
                    traceback.print_exc()

            # ── Update ──────────────────────────────────────────────
            try:
                self.scene_manager.update(dt)
            except Exception:
                traceback.print_exc()

            # ── Draw ────────────────────────────────────────────────
            try:
                self.scene_manager.draw(self.window.screen)
            except Exception:
                traceback.print_exc()

            self.window.flip()

        self._shutdown()

    # ------------------------------------------------------------------ #
    # Eventos de sistema
    # ------------------------------------------------------------------ #

    def _handle_system_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit()

        elif event.type == pygame.VIDEORESIZE and not self.window.is_fullscreen:
            self.window.on_resize(event.w, event.h)

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.window.toggle_fullscreen()

        # Publica evento raw no EventBus para sistemas externos
        self.event_bus.publish("pygame_event", event=event)

    # ------------------------------------------------------------------ #
    # Controle de ciclo
    # ------------------------------------------------------------------ #

    def quit(self) -> None:
        """Sinaliza o encerramento do loop na próxima iteração."""
        self._is_running = False
        self.engine.is_running = False

    def _shutdown(self) -> None:
        """Finaliza Pygame e encerra o processo."""
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------ #
    # Propriedades de conveniência
    # ------------------------------------------------------------------ #

    @property
    def screen(self) -> pygame.Surface:
        return self.window.screen

    @property
    def current_scene(self) -> Optional[Scene]:
        return self.scene_manager.current
