# 🎮 Zennity Engine

> Uma engine 2D modular construída em cima do Pygame, com arquitetura inspirada em Unity (ECS — Entity Component System).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green?logo=pygame)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## ✨ Funcionalidades

- **Engine Loop** com delta time e troca de cenas agendada
- **Sistema de Cenas** (`Scene`) com `start`, `update`, `draw`, `handle_event`
- **GameObject + Components** — arquitetura ECS inspirada em Unity
- **Transform** com posição, rotação e escala usando NumPy
- **Sistema de Física** com `RigidBody`, `BoxCollider` e detecção AABB
- **Sistema de Gráficos** com `Camera` e `SpriteRenderer`
- **Gerenciamento de Assets** (imagens, fontes, etc.)
- **Sistema de Áudio** (música e efeitos sonoros)
- **Input Manager** com suporte a teclado e mouse

---

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/lexOnFire/zennity-engine-game.git
cd zennity-engine-game

# Instale as dependências
pip install -r requirements.txt
```

---

## 🚀 Uso Rápido

```python
from engine.core import Engine, Scene
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
import pygame

class GameScene(Scene):
    def start(self):
        # Cria um player
        self.player = GameObject(name="Player")
        self.player.transform.x = 400
        self.player.transform.y = 300

        # Adiciona física
        rb = self.player.add_component(RigidBody())
        col = self.player.add_component(BoxCollider(width=32, height=32))

    def update(self, dt):
        self.player.update(dt)

    def draw(self, screen):
        self.player.draw(screen)
        screen.fill((30, 30, 30))  # fundo

if __name__ == "__main__":
    engine = Engine(width=800, height=600, title="Zennity Demo")
    engine.run(GameScene())
```

---

## 🗂️ Estrutura do Projeto

```
zennity-engine-game/
├── engine/
│   ├── core.py            # Engine principal + Sistema de Cenas
│   ├── game_object.py     # GameObject (container de componentes)
│   ├── component.py       # Component base + Transform
│   ├── assets.py          # Gerenciamento de assets
│   ├── audio.py           # Sistema de áudio
│   ├── input.py           # Input Manager
│   ├── physics/
│   │   ├── rigidbody.py   # Física e movimento
│   │   └── collider.py    # Detecção de colisão AABB
│   └── graphics/
│       ├── camera.py      # Sistema de câmera 2D
│       └── renderer.py    # SpriteRenderer
├── demos/                 # Demos e exemplos
├── scripts/               # Scripts utilitários
├── requirements.txt
└── README.md
```

---

## 🧩 Sistemas

### Physics

| Classe | Descrição |
|---|---|
| `RigidBody` | Aplica gravidade, velocidade e movimento baseado em dt |
| `BoxCollider` | Colisão AABB com callbacks `on_collision_enter` e `on_collision_exit` |

### Graphics

| Classe | Descrição |
|---|---|
| `Camera` | Câmera 2D com follow suave de target |
| `SpriteRenderer` | Renderiza sprites com suporte à câmera |

---

## 🛠️ Dependências

- `pygame >= 2.0`
- `numpy`

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

> Feito com 💙 por [lexOnFire](https://github.com/lexOnFire)
