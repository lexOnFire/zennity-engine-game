# 🎮 Zennity Engine - Editor Visual

> **Zennity é um motor de jogo 100% visual.** Crie jogos inteiros sem escrever código - use o editor gráfico!

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x%20%2F%20CE-green?logo=pygame)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-darkgreen?logo=qt)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## 🎯 O Que é Zennity?

Zennity é uma engine 2D/3D com um **Editor Visual Profissional** que permite:

- ✅ **Criar cenas** arrastando e soltando objetos
- ✅ **Programar lógica** conectando nós visualmente (sem código)
- ✅ **Desenhar interfaces** construindo UIs no editor
- ✅ **Controlar NPCs** com árvores de comportamento visuais
- ✅ **Testar imediatamente** clicando em Play

**Não é necessário saber programar!** 🎉

---

## 📚 Documentação Visual

### Para Iniciantes
Comece aqui: **[VISUAL_EDITOR_GUIDE.md](./VISUAL_EDITOR_GUIDE.md)**
- O que é cada ferramenta
- Como criar seu primeiro projeto
- Exemplos passo a passo

### Guias Específicos
- **[STATIC_UI_WORKFLOW.md](./STATIC_UI_WORKFLOW.md)** - Criar UIs estáticas 100% visual (novo!)
- **[UI_BUILDER_GUIDE.md](./UI_BUILDER_GUIDE.md)** - Criar interfaces de usuário
- **[BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md)** - Controlar NPCs e comportamentos
- **[DEPRECATION_NOTICE.md](./DEPRECATION_NOTICE.md)** - Migrar de projetos antigos em código

---

## 📦 Instalação

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
python -m zennity_run
```

Ou use o atalho (se instalado como pacote):
```bash
zennity-editor
```

---

## 🎨 Fluxo de Trabalho Visual

### Passo 1: Criar Cena
1. Menu → File → New Scene
2. Nomeie como "level_1.zscene"
3. Adicione GameObjects (Sprite, Tilemap, UI Canvas)

### Passo 2: Criar UI
1. Menu → File → New UI Layout
2. Arraste widgets (Label, Button, ProgressBar)
3. Configure posição, tamanho, cores
4. Salve como "hud.zui"

### Passo 3: Criar Comportamento
1. Menu → File → New Behavior Tree
2. Conecte nós (Condition, Action, Decorator)
3. Defina lógica visualmente
4. Salve como "enemy_ai.zbehavior"

### Passo 4: Conectar Tudo
1. GameObject → Component → Behavior
2. Configure `controller_path` = "enemy_ai.zbehavior"
3. Clique Play para testar

### Resultado
✅ Jogo completo, 100% visual, pronto para jogar!

---

## 🖥️ Interface do Editor

```
┌─────────────────────────────────────────┐
│  Zennity Studio                    ⚙️   │
├───────────────────────────────────────── ┤
│ File  Edit  View  Tools  Help            │
├──────────┬──────────────────┬───────────┤
│          │                  │           │
│ Outliner │  Viewport        │ Inspector │
│          │  (Preview)       │           │
│          │                  │           │
├──────────┼──────────────────┼───────────┤
│ Assets Browser       │ Behavior Tree    │
│                      │ ou UI Builder    │
└──────────────────────┴──────────────────┘
```

### Painéis Principais

| Painel | Função |
|--------|--------|
| **Outliner** | Hierarquia de objetos da cena |
| **Viewport** | Visualizar e editar a cena |
| **Inspector** | Editar propriedades |
| **Assets** | Navegador de arquivos do projeto |
| **Graph Editor** | Editar Behavior Trees e Logic Graphs |
| **UI Builder** | Criar interfaces |

---

## 📂 Estrutura de Pasta

```
Assets/
├── Scenes/
│   ├── level_1.zscene
│   └── menu.zscene
├── UI/
│   ├── hud.zui
│   └── main_menu.zui
├── Behaviors/
│   ├── enemy_patrol.zbehavior
│   └── player_controller.zbehavior
├── Logic/
│   ├── game_events.zlogic
│   └── ui_controls.zlogic
├── Sprites/
│   ├── player.png
│   └── enemy.png
└── Audio/
    ├── bgm_level1.mp3
    └── sfx_jump.wav
```

---

## 🎮 Exemplo Rápido: Jogo de Coleta

### 1. Cena Base
- Background (Sprite)
- Player (Sprite + Physics)
- Food items (Sprite + Trigger Collider)

### 2. HUD
- Score label: "Score: 0"
- HP bar: 100/100

### 3. Comportamento Food (NPC)
```
Repeat (infinito)
└─ Patrol entre dois pontos
```

### 4. Lógica Player (interação)
```
On Collision (Food)
  ├─ Destroy Food
  ├─ Increment Score
  └─ Play Sound
```

### 5. Play!
Clique Play, teste o jogo, ajuste conforme necessário.

---

## 🐛 Troubleshooting

### Editor não abre
```bash
python -m zennity_run --debug
```
Verifique saída do console para erro específico.

### Cena não carrega
- Verifique se arquivo `.zscene` existe em `Assets/Scenes/`
- Verifique permissões de leitura/escrita

### Comportamento não funciona
- Verifique se `controller_path` está correto
- Verifique se arquivo `.zbehavior` existe
- Veja console para erros de execução

---

## 📖 Próximos Passos

1. **Leia** [VISUAL_EDITOR_GUIDE.md](./VISUAL_EDITOR_GUIDE.md)
2. **Crie** seu primeiro projeto
3. **Explore** os exemplos em `Assets/Scenes/`
4. **Compartilhe** sua criação! 🎉

---

## 🆘 Precisa de Ajuda?

- 📖 Documentação: [VISUAL_EDITOR_GUIDE.md](./VISUAL_EDITOR_GUIDE.md)
- 🌳 Behavior Trees: [BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md)
- 🎨 UI Builder: [UI_BUILDER_GUIDE.md](./UI_BUILDER_GUIDE.md)
- ⚠️ Migrando de código: [DEPRECATION_NOTICE.md](./DEPRECATION_NOTICE.md)

---

**Zennity: Crie Jogos Visualmente!** 🎮✨

Feito com ❤️ por Alex
