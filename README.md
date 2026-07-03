# 🎮 Zennity Engine & Editor

> Uma engine modular 2D/3D construída sobre o Pygame com arquitetura ECS (Entity Component System) inspirada em Unity, integrada a um **Editor Profissional em PySide6** com design moderno inspirado na Unreal Engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x%20%2F%20CE-green?logo=pygame)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-darkgreen?logo=qt)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## 🖥️ O Novo Zennity Editor (PySide6)

O Zennity Editor é um ambiente integrado de desenvolvimento rico, responsivo e desacoplado através de uma arquitetura **MVVM** e comunicação assíncrona por **EventBus**.

### ✨ Funcionalidades do Editor
* **Workspace Unreal-inspired:** Interface escura com destaque cobalto cobrindo painéis flexíveis acopláveis (Docks) com persistência automática de layout via `QSettings`.
* **Outliner de Hierarquia:** Árvore recursiva dinâmica com busca rápida de texto, duplicação rápida (`Ctrl+D`), exclusão (`Delete`) e renomeação instantânea com duplo clique.
* **Asset Browser:** Navegador de arquivos com histórico de pastas (Voltar/Avançar/Subir), breadcrumbs interativos e visualização em grade de recursos.
* **Inspector Colapsável:** Exibição e edição dinâmica de propriedades de componentes (`Transform`, `RigidBody`, `Colliders`) e scripts.
* **Viewport Acelerada (OpenGL):** Renderização direta do framebuffer do Pygame no Qt em 60 FPS com suporte a atalho de foco (`F`) e alternância em tempo real entre projeções 2D e 3D.
* **Terminal Python & Console:** Console de mensagens do sistema colorido por severidade com interpretador interativo integrado para executar scripts no contexto do editor.
* **Gizmos de Transformação:** Handles visuais e binding bidirecional para translação, rotação e escala.
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

---

## 🗂️ Estrutura do Projeto

```
zennity-engine-game/
├── engine/                # Módulos canônicos da Zennity Engine (ECS)
│   ├── core/              # Engine principal, Cenas e EventBus
│   ├── physics/           # RigidBody, Box/Circle Colliders
│   └── graphics/          # Renderers 3D, Câmera e Matrizes
├── editor/                # O Novo Zennity Editor modular (PySide6)
│   ├── core/              # EventBus do editor e exportador
│   ├── models/            # Scene e Asset Models
│   ├── viewmodels/        # Apresentação e lógica de bindings
│   ├── widgets/           # Hierarchy, Inspector, Console, Docks, Viewport
│   ├── windows/           # MainWindow e Diálogos de Preferências
│   └── themes/            # dark_theme.qss e ícones
├── editor_legacy/         # Versão legada do editor Pygame (compatibilidade)
├── demos/                 # Exemplos práticos e demonstrativos
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
