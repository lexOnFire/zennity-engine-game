"""
engine/application.py
────────────────────────────────────────────────────────────────
Arquitetura:

    Application           ← única instância global da engine
    │
    ├── Window             gerencia janela Pygame
    ├── Engine             UpdateSystems + RenderSystems
    ├── SceneManager       pilha de cenas e transições
    ├── Input              snapshot de input por frame
    ├── Time               delta, fps, frame, elapsed
    ├── EventBus           pub/sub desacoplado
    └── AssetManager       cache e carregamento de assets

Contexto global:

    app = Application.current()         # acessa a instância ativa

Service Locator:

    win   = app.get(Window)             # retorna Window
    time  = app.get(Time)               # retorna Time
    bus   = app.get(EventBus)           # retorna EventBus
    input = app.get(Input)              # retorna a classe Input

    # Registro de serviço externo:
    app.register(MyPhysicsModule())
    physics = app.get(MyPhysicsModule)

Uso mínimo:

    from engine.application import Application
    from my_game.scenes import MenuScene

    app = Application(width=1280, height=720, title="Meu Jogo")
    app.run(MenuScene())
"""
from __future__ import annotations

import sys
import traceback
from typing import Optional, Type, TypeVar

import pygame

from .window        import Window
from .time          import Time
from .event_bus     import EventBus
from .input         import Input
from .assets        import Assets
from .core          import Scene, Engine, SceneManager

T = TypeVar("T")


class Application:
    """
    Raiz da Zennity Engine.

    Cria, conecta e orquestra todos os subsistemas.
    Deve ser instanciada exatamente uma vez por processo.
    """

    _instance: Optional["Application"] = None

    # ------------------------------------------------------------------ #
    # Inicialização                                                       #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        width:  int   = 800,
        height: int   = 600,
        title:  str   = "Zennity Engine",
        fps:    int   = 60,
        dt_cap: float = 0.1,
    ) -> None:
        if Application._instance is not None:
            raise RuntimeError(
                "Application já foi instanciada. "
                "Use Application.current() para acessar a instância existente."
            )

        pygame.init()
        pygame.mixer.init()

        # ── Subsistemas ──────────────────────────────────────────────
        self.window:        Window       = Window(width, height, title)
        self.time:          Time         = Time(fps, dt_cap)
        self.event_bus:     EventBus     = EventBus()
        self.scene_manager: SceneManager = SceneManager.instance()
        self.assets                      = Assets   # namespace estático

        # Engine (retrocompat) — reutiliza a janela já criada
        self.engine: Engine = Engine.__new__(Engine)
        self.engine.screen         = self.window.screen
        self.engine.width          = self.window.width
        self.engine.height         = self.window.height
        self.engine.fps            = fps
        self.engine.is_fullscreen  = False
        self.engine.saved_w        = width
        self.engine.saved_h        = height
        self.engine.clock          = pygame.time.Clock()
        self.engine.is_running     = False
        self.engine._scene_manager = self.scene_manager
        self.engine._current_scene = None
        self.engine._next_scene    = None
        self.engine._app           = self
        self.engine._update_systems = []
        self.engine._render_systems = []

        self.scene_manager.bind(self.engine)

        # ── Service Locator registry ─────────────────────────────────
        # Mapeia tipo → instância (ou classe, para singletons estáticos)
        self._services: dict = {}
        self._register_builtins()

        self._is_running = False

        # Registra como instância global
        Application._instance = self

    def _register_builtins(self) -> None:
        """Registra automaticamente todos os subsistemas built-in."""
        self._services[Window]       = self.window
        self._services[Time]         = self.time
        self._services[EventBus]     = self.event_bus
        self._services[SceneManager] = self.scene_manager
        self._services[Engine]       = self.engine
        self._services[Input]        = Input   # classe estática
        self._services[Assets]       = Assets  # classe estática

    # ------------------------------------------------------------------ #
    # Context global                                                      #
    # ------------------------------------------------------------------ #

    @classmethod
    def current(cls) -> "Application":
        """
        Retorna a instância ativa da Application.

        Lança RuntimeError se nenhuma Application foi criada ainda.
        Use este método em qualquer sistema que precise acessar
        subsistemas sem receber a Application por parâmetro.

        Exemplo:
            app   = Application.current()
            scene = app.scene_manager.current
            delta = app.time.delta
        """
        if cls._instance is None:
            raise RuntimeError(
                "Nenhuma Application foi criada. "
                "Instancie Application(...) antes de chamar current()."
            )
        return cls._instance

    # ------------------------------------------------------------------ #
    # Service Locator                                                     #
    # ------------------------------------------------------------------ #

    def register(self, service: object) -> None:
        """
        Registra um serviço externo no locator.

        O serviço é indexado pelo seu tipo exato (type(service)).
        Para recuperar: app.get(MinhaClasse)

        Exemplo:
            app.register(MyPhysicsModule())
            physics = app.get(MyPhysicsModule)
        """
        self._services[type(service)] = service

    def register_as(self, service_type: Type, service: object) -> None:
        """
        Registra um serviço sob um tipo específico (interface ou classe base).

        Útil para registrar implementações diferentes sob o mesmo contrato:
            app.register_as(PhysicsSystem, Box2DPhysics())
            physics = app.get(PhysicsSystem)
        """
        self._services[service_type] = service

    def get(self, service_type: Type[T]) -> T:  # type: ignore[return]
        """
        Recupera um serviço pelo tipo.

        Lança KeyError se o serviço não estiver registrado.

        Exemplo:
            win   = app.get(Window)
            time  = app.get(Time)
            bus   = app.get(EventBus)
            input = app.get(Input)
        """
        try:
            return self._services[service_type]
        except KeyError:
            raise KeyError(
                f"Serviço '{service_type.__name__}' não registrado. "
                f"Use app.register() ou app.register_as() para cadastrá-lo."
            ) from None

    def has(self, service_type: Type) -> bool:
        """Verifica se um serviço está registrado sem lançar excessão."""
        return service_type in self._services

    # ------------------------------------------------------------------ #
    # Loop principal                                                      #
    # ------------------------------------------------------------------ #

    def run(self, initial_scene: Scene) -> None:
        """Inicia o loop principal da aplicação."""
        self._is_running = True
        self.engine.is_running = True

        self.scene_manager.load(initial_scene)

        while self._is_running:
            dt = self.time.tick()

            # Sync window → engine (retrocompat)
            self.engine.screen = self.window.screen
            self.engine.width  = self.window.width
            self.engine.height = self.window.height

            # Input
            Input.update()

            # Eventos
            for event in pygame.event.get():
                self._handle_system_event(event)
                try:
                    self.scene_manager.handle_event(event)
                except Exception:
                    traceback.print_exc()

            # Update
            try:
                self.scene_manager.update(dt)
            except Exception:
                traceback.print_exc()

            # Draw
            try:
                self.scene_manager.draw(self.window.screen)
            except Exception:
                traceback.print_exc()

            self.window.flip()

        self._shutdown()

    # ------------------------------------------------------------------ #
    # Eventos de sistema                                                  #
    # ------------------------------------------------------------------ #

    def _handle_system_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit()
        elif event.type == pygame.VIDEORESIZE and not self.window.is_fullscreen:
            self.window.on_resize(event.w, event.h)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.window.toggle_fullscreen()

        self.event_bus.publish("pygame_event", event=event)

    # ------------------------------------------------------------------ #
    # Controle de ciclo                                                   #
    # ------------------------------------------------------------------ #

    def quit(self) -> None:
        """Sinaliza o encerramento do loop na próxima iteração."""
        self.event_bus.publish("app.quit")
        self._is_running = False
        self.engine.is_running = False

    def _shutdown(self) -> None:
        """Finaliza Pygame, limpa a instância global e encerra."""
        Application._instance = None
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------ #
    # Propriedades de conveniência                                        #
    # ------------------------------------------------------------------ #

    @property
    def screen(self) -> pygame.Surface:
        return self.window.screen

    @property
    def current_scene(self) -> Optional[Scene]:
        return self.scene_manager.current

    def __repr__(self) -> str:
        scene = self.current_scene
        return (
            f"<Application scene={scene.__class__.__name__ if scene else 'None'} "
            f"fps={self.time.fps_target} services={len(self._services)}>"
        )
