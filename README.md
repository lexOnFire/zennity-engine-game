# 🎮 Zennity Engine & Editor

> Uma engine modular 2D/3D construída sobre o Pygame com arquitetura ECS (Entity Component System) inspirada em Unity, integrada a um **Editor Profissional em PySide6** com design moderno inspirado na Unreal Engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x%20%2F%20CE-green?logo=pygame)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-darkgreen?logo=qt)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## Beta 0.1

A Beta 0.1 estabiliza o fluxo principal da Zennity:

```text
Criar cena -> Criar GameObject -> Adicionar componentes -> Adicionar script -> Play -> Input -> Stop
```

O projeto exemplo oficial fica em `examples/GettingStarted`. Ele não depende de assets externos e demonstra `GameObject`, componentes, `ScriptBehaviour`, `Input` e Play Mode.

Limites da Beta: ainda não há Input Mapping, gamepad, touch, Physics avançada, áudio integrado ao Play Mode, animação, networking, Package Manager ou Build System final. Alguns módulos legados continuam presentes para compatibilidade.

## 🖥️ O Novo Zennity Editor (PySide6)

O Zennity Editor é um ambiente integrado de desenvolvimento rico, responsivo e desacoplado através de uma arquitetura **MVVM** e comunicação assíncrona por **EventBus**.

### ✨ Funcionalidades do Editor
* **Workspace Unreal-inspired:** Interface escura com destaque cobalto cobrindo painéis flexíveis acopláveis (Docks) com persistência automática de layout via `QSettings`.
* **Outliner de Hierarquia:** Árvore recursiva dinâmica com busca rápida de texto, duplicação rápida (`Ctrl+D`), exclusão (`Delete`) e renomeação instantânea com duplo clique.
* **Asset Browser:** Navegador de arquivos com histórico de pastas (Voltar/Avançar/Subir), breadcrumbs interativos e visualização em grade de recursos.
* **Inspector Profissional (Fase 8):** Exibição e edição dinâmica com suporte total a desfazer/refazer (Undo/Redo) via `CommandManager`, validação numérica de inputs e isolamento de commits interativos.
* **Component System (Fase 9):** Base oficial de componentes com UUID, `enabled`, registro central, serialização explícita e integração com `GameObject`, cenas, prefabs e Inspector.
* **Add/Remove Components (Fase 10):** O Inspector adiciona e remove componentes através do `ComponentRegistry`, sempre com comandos reversíveis no `CommandManager`.
* **Inspector Plugin System (Fase 11/11.1):** O Inspector é apenas um host desacoplado; todos os editores de componente são resolvidos via `InspectorPluginRegistry`.
* **Play Mode Foundation (Fase 12-15):** Play cria um Runtime World isolado; `RuntimeManager.tick(delta_time)` atualiza Input, lifecycle de componentes e scripts Python somente nessa cópia.
* **Viewport Acelerada (OpenGL):** Renderização direta do framebuffer do Pygame no Qt em 60 FPS com suporte a atalho de foco (`F`) e alternância em tempo real entre projeções 2D e 3D.
* **Terminal Python & Console:** Console de mensagens do sistema colorido por severidade com interpretador interativo integrado para executar scripts no contexto do editor.
* **Ferramentas da Fase 1:** Seleção centralizada, Move Tool funcional com gizmo de translação, Snap opcional e modos Rotate/Scale preparados para implementação futura.
* **Code Editor e Scripts:** Editor de código-fonte embutido com atalho de salvamento (`Ctrl+S`) para programar comportamentos dos objetos em tempo real.
* **Build Exporter:** Exportação automatizada da cena ativa `.zscene` para uma pasta autônoma contendo todas as dependências lógicas e launchers rápidos (`jogar.bat`).
* **Profiler Gráfico:** Gráficos nativos gerados via `QPainter` medindo FPS, consumo de RAM e física ativa.

---

## 📦 Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/lexOnFire/zennity-engine-game.git
cd zennity-engine-game
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar o Editor
```bash
python editor/main.py
```

Também é possível abrir o editor da Fase 1 diretamente:

```bash
python -m editor.phase1_main
```

### 4. Abrir o Projeto Exemplo

No editor, use `File > Open Scene` e selecione:

```text
examples/GettingStarted/Assets/Scenes/GettingStarted.zscene
```

---

## 🚀 Uso Standalone (Engine Pura)

```python
from engine.core import Application, Scene
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider

class GameScene(Scene):
    def start(self):
        # Cria um player
        self.player = GameObject(name="Player")
        self.player.transform.position[0] = 400
        self.player.transform.position[1] = 300

        # Adiciona componentes
        self.player.add_component(RigidBody())
        self.player.add_component(BoxCollider(width=32, height=32))
        self.add_game_object(self.player)

if __name__ == "__main__":
    app = Application(800, 600, "Zennity Standalone Game")
    app.run(GameScene())
```

### Component System

Todo componente herda de `engine.core.Component` e pode ser registrado no `ComponentRegistry`:

```python
from engine.core import Component, register_component

class Health(Component):
    component_type = "Health"
    unique = True

    def __init__(self, value=100):
        super().__init__()
        self.value = value

    def serialize_properties(self):
        return {"value": self.value}

    def deserialize_properties(self, data):
        self.value = int(data.get("value", 100))

register_component(Health)
```

`Transform` continua sendo obrigatório e acessível por `game_object.transform`. Componentes opcionais como `RigidBody`, `BoxCollider`, `CircleCollider` e `ScriptComponent` são serializados em cenas e prefabs.

No editor, todo componente registrado aparece automaticamente no menu **Add Component** do Inspector. Adicionar e remover componentes opcionais passa por `AddComponentCommand` e `RemoveComponentCommand`, então Undo/Redo permanece consistente. Componentes `unique = True` não podem ser duplicados e componentes `required = True`, como `Transform`, não podem ser removidos.

Para fornecer uma interface própria no Inspector, registre também um plugin:

```python
from editor.inspector import InspectorPlugin, inspector_plugin_registry

class HealthInspectorPlugin(InspectorPlugin):
    component_type = "Health"

    def create_widget(self, component, command_manager, refresh=None):
        ...

inspector_plugin_registry.register(HealthInspectorPlugin)
```

O plugin deve aplicar alterações pelo `CommandManager`, normalmente usando `self.set_property(...)`.

`RealInspectorPanel` e `InspectorDock` seguem o mesmo fluxo oficial: percorrer componentes, resolver plugin no registry e hospedar o widget retornado. Novos componentes não exigem alteração do Inspector.

### Play Mode Foundation

O Play Mode separa dois mundos:

* `Editor World`: cena persistente editada pelo Inspector, salva em disco e usada por prefabs/assets.
* `Runtime World`: cópia profunda criada por `RuntimeManager.start_play(...)`, renderizada pela Viewport durante Play e destruída por `stop_play()`.

`RuntimeScene` clona `GameObject`, `Transform`, componentes e hierarquia sem compartilhar instâncias com a cena do editor. Alterações feitas durante Play desaparecem ao parar.

A Fase 13 adiciona o ciclo de vida básico de componentes:

```python
class MyComponent(Component):
    def on_runtime_start(self):
        ...

    def on_runtime_update(self, delta_time):
        ...

    def on_runtime_stop(self):
        ...
```

`RuntimeManager.tick(delta_time)` só executa quando o estado é `PLAYING`. Componentes desabilitados e objetos inativos não recebem lifecycle.

A Fase 14 adiciona o runtime oficial de scripts Python. Scripts de usuário herdam de `ScriptBehaviour` e são referenciados por `ScriptComponent`:

```python
from engine.runtime import ScriptBehaviour

class PlayerController(ScriptBehaviour):
    def on_awake(self):
        ...

    def on_start(self):
        ...

    def on_update(self, delta_time):
        self.transform.position[0] += 10 * delta_time

    def on_destroy(self):
        ...
```

`ScriptRuntime` carrega módulos apenas dentro do Runtime World. Cada `GameObject` recebe sua própria instância do script, mesmo quando usa o mesmo arquivo `.py`. Erros em um script são registrados e desabilitam somente aquele `ScriptComponent`, sem derrubar o Play Mode. O Editor World nunca executa scripts nem recebe mutações feitas por eles durante Play.

A Fase 15 adiciona o Input System oficial. Scripts usam apenas a API pública `Input`, sem acessar Qt/PySide ou Pygame diretamente:

```python
from engine.runtime import Input, ScriptBehaviour

class PlayerController(ScriptBehaviour):
    def on_update(self, delta_time):
        if Input.is_key_down("Space"):
            ...

        if Input.is_mouse_pressed("left"):
            print(Input.mouse_position(), Input.mouse_delta())
```

`Input.is_key_pressed(...)` e `Input.is_key_released(...)` duram apenas um frame. O mesmo vale para `is_mouse_pressed(...)` e `is_mouse_released(...)`. Ao sair do Play, todo estado de teclado e mouse é limpo.

A Fase 16 adiciona o Time System oficial. Scripts e sistemas runtime consultam `Time`; somente o `RuntimeManager` atualiza os valores a cada tick:

```python
from engine.runtime import ScriptBehaviour, Time

class PlayerController(ScriptBehaviour):
    def on_update(self, delta_time):
        print(Time.delta_time, Time.time, Time.frame_count)
```

`Time.delta_time` e `Time.time` respeitam `Time.time_scale`. `Time.unscaled_delta_time` e `Time.unscaled_time` continuam acumulando o tempo real recebido pelo runtime. `Time.fixed_delta_time` já existe como preparação para Physics futura, mas `FixedUpdate` ainda não foi implementado.

A Fase 17 adiciona a fundação oficial de física runtime. O `PhysicsWorld` é criado apenas dentro da `RuntimeScene`, registra `RigidBody`, `BoxCollider` e `CircleCollider` dos clones do Play Mode, integra corpos usando `Time.fixed_delta_time` e detecta contatos simples sem resolver interpenetração completa.

Scripts podem consultar a fachada pública:

```python
from engine.runtime import Physics

contacts = Physics.contacts()
```

O Editor World não participa da simulação física runtime, e o estado do `PhysicsWorld` é limpo no Stop.

A Fase 18 adiciona o Camera System oficial. O componente `Camera` gerencia a cor de limpeza de tela, o zoom 2D, a área da tela (`viewport_rect`) e a prioridade de renderização. O `CameraManager` localiza a câmera principal (`Camera.main`), a qual é usada isoladamente pelo Runtime para desenhar a cena durante o Play.

Scripts podem acessar a câmera principal a partir de:

```python
from engine.graphics.camera import Camera

main_camera = Camera.main
```

A Fase 19 adiciona o Audio Runtime oficial. O componente `AudioSource` gerencia a reprodução de clipes de áudio em runtime (`audio_clip`, `volume`, `pitch`, `loop`, `play_on_awake` e `mute`). O componente `AudioListener` representa o ponto receptor de áudio. O `AudioManager` gerencia todas as fontes e listeners ativos, garantindo isolamento total do Editor e a interrupção completa de qualquer reprodução ao parar o Play Mode.

Scripts podem manipular clipes de áudio obtendo o componente `AudioSource`:

```python
from engine.audio import AudioSource

source = self.game_object.get_component(AudioSource)
source.play()
```

A Fase 20 adiciona o sistema de Scene Gizmos Avançados. O `GizmoRegistry` centraliza o registro de renderizadores visuais exclusivos de editor para componentes específicos. Implementamos gizmos profissionais para `Camera` (retângulo de fov azul), `BoxCollider` e `CircleCollider` (bordas verdes de colisão físicas) e `AudioSource`/`AudioListener` (ícones amarelo e magenta com alcance sonoro). Esses gizmos são exibidos unicamente na Viewport do Editor em modo edição, garantindo total isolamento visual e zero impacto no Runtime World.

Para registrar um novo gizmo personalizado de componente:

```python
from editor.gizmos.gizmo_registry import GizmoRegistry

def draw_my_custom_gizmo(component, screen, scene):
    # Lógica de desenho com pygame.draw
    pass

GizmoRegistry.register("MyComponentType", draw_my_custom_gizmo)
```

A Fase 21 adiciona a fundação oficial do Animation Runtime. `AnimationClip` passa a suportar `Keyframe` serializável para propriedades simples como `position`, `rotation` e `scale`, enquanto o componente `Animator` toca, pausa, para e atualiza clips durante o Play Mode usando exclusivamente `Time.delta_time`.

```python
from engine.animation import AnimationClip, Animator, Keyframe

clip = AnimationClip(
    "move",
    frames=[],
    duration=1.0,
    loop=True,
    keyframes=[
        Keyframe(0.0, "position", [0.0, 0.0, 0.0]),
        Keyframe(1.0, "position", [100.0, 0.0, 0.0]),
    ],
)

animator = game_object.add_component(Animator(default_clip="move"))
animator.add_clip(clip)
```

O `Animator` roda somente no Runtime World. Alterações feitas por animação durante Play não modificam a cena do Editor e são descartadas no Stop. Nesta fase ainda não há timeline visual, editor de keyframes, blend tree, state machine avançada ou importador de spritesheets.

### UI Runtime Foundation

A Fase 22 adiciona a base oficial de UI Runtime. `Canvas`, `Label`, `Image` e `Button` são componentes serializáveis, registrados no `ComponentRegistry` e editáveis pelo Inspector Plugin System.

```python
from engine.ui.runtime_components import Canvas, LabelComponent

canvas = game_object.add_component(Canvas())
label = game_object.add_component(LabelComponent(text="Start", x=24, y=20))
```

Durante Play, o `UIRenderer` desenha componentes de UI depois da cena e de forma independente da câmera. Elementos de UI pertencem ao Runtime World, são ocultos da renderização normal da cena e não modificam o Editor World. Nesta fase ainda não há editor visual, layout automático, eventos complexos, temas ou animações de UI.

### Criando Scripts

Crie um arquivo `.py` dentro de `Assets/Scripts` e anexe um `ScriptComponent` ao GameObject apontando para esse caminho. Um script mínimo:

```python
from engine.runtime import Input, ScriptBehaviour

class PlayerController(ScriptBehaviour):
    def on_update(self, delta_time):
        if Input.is_key_down("Space"):
            self.transform.position[0] += 120.0 * delta_time
```

Scripts rodam somente durante Play Mode e sempre sobre clones do Runtime World.

---

## 🗂️ Estrutura do Projeto

```
zennity-engine-game/
├── engine/                # Módulos canônicos da Zennity Engine (ECS)
│   ├── core/              # Engine principal, Cenas e EventBus
│   ├── runtime/           # RuntimeScene, RuntimeManager, ScriptRuntime, InputManager e clone profundo do Play Mode
│   ├── physics/           # RigidBody, Box/Circle Colliders
│   ├── ui/                # UI Runtime: Canvas, componentes básicos e UIRenderer
│   └── graphics/          # Renderers 3D, Câmera e Matrizes
├── editor/                # O Novo Zennity Editor modular (PySide6)
│   ├── core/              # EventBus do editor e exportador
│   ├── models/            # Scene e Asset Models
│   ├── runtime/           # EditorContext, seleção, ferramentas e comandos
│   ├── viewmodels/        # Apresentação e lógica de bindings
│   ├── widgets/           # Hierarchy, Inspector, Console, Docks, Viewport
│   ├── windows/           # MainWindow e Diálogos de Preferências
│   └── themes/            # dark_theme.qss e ícones
├── editor_legacy/         # Versão legada do editor Pygame (compatibilidade)
├── demos/                 # Exemplos práticos e demonstrativos
├── examples/              # Projetos exemplo oficiais da Beta
├── scripts/               # Scripts utilitários e de comportamento do usuário
└── tests/                 # Suites completas de testes unitários (pytest)
```

---

## 🛠️ Dependências Principais

* `pygame-ce` ou `pygame >= 2.5`
* `numpy`
* `PySide6 >= 6.5.0`

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

> Desenvolvido com 💙 por [lexOnFire](https://github.com/lexOnFire)
