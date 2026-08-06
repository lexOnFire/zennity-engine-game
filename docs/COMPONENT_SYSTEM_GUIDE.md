# Guia Completo: Sistema de Componentes de Alto Nível

A Zennity Engine agora oferece 4 componentes poderosos e amigáveis para criar games sem precisar de Logic Graph complexo ou scripts. Este guia mostra como usá-los.

---

## 📋 Índice

1. [UIBinder](#uibinder) — Sincronizar dados com UI
2. [DialogueManager](#dialoguemanager) — Sistema de diálogos
3. [AnimationController](#animationcontroller) — Máquina de estados
4. [MaterialPropertyAnimator](#materialpropertyanimator) — Animar propriedades
5. [Exemplos Práticos](#exemplos-práticos)

---

## UIBinder

### O que faz?
Sincroniza automaticamente propriedades de objetos com elementos UI (Labels, ProgressBars, etc).

### Modo Automático (Polling)
Atualiza a cada frame:
```python
go.add_component(UIBinder(
    source_path="player.health",
    ui_element_name="HealthLabel",
    bind_mode="auto",
    format_string="{value}/100"
))
```

Quando `player.health` mudar, `HealthLabel` atualiza automaticamente.

### Modo Event (Reativo)
Atualiza apenas quando evento é disparado:
```python
go.add_component(UIBinder(
    source_path="player.health",
    ui_element_name="HealthLabel",
    bind_mode="event",
    event_name="health_changed"
))
```

### Casos de Uso

**Contador Decrescente (999 → 0)**
```python
go.add_component(UIBinder(
    source_path="game.counter",
    ui_element_name="CounterLabel",
    bind_mode="auto",
    format_string="{value}"
))
```

**Vida com Máximo**
```python
go.add_component(UIBinder(
    source_path="player.health",
    ui_element_name="HealthText",
    format_string="{value}/100"
))
```

**Timer em Segundos**
```python
go.add_component(UIBinder(
    source_path="game.time_left",
    ui_element_name="TimerLabel",
    format_string="{value:.1f}s"
))
```

**ProgressBar**
```python
go.add_component(UIBinder(
    source_path="player.experience",
    ui_element_name="ExpBar",
    format_string="{value}%"
))
```

---

## DialogueManager

### O que faz?
Sistema completo de diálogos com ramificações, flags e escolhas.

### Setup Básico

```python
npc = GameObject("Merchant")
npc.add_component(DialogueManager(
    dialogue_file="Assets/Dialogues/merchant.zdialogue",
    speaker_name="Merchant",
    ui_text_element="DialogueText",
    auto_start=False
))
```

### Usar Diálogos

```python
manager = npc.get_component(DialogueManager)

# Iniciar diálogo
manager.begin_dialogue()

# Avançar para próxima fala
manager.advance()

# Escolher uma opção (índice 0, 1, 2...)
manager.choose_option(0)

# Verificar se ativo
if manager.is_active():
    print("Diálogo em progresso")
```

### Flags e Condições

```python
# Definir flag
manager.set_flag("has_quest", True)
manager.set_flag("player_level", 5)

# Usar em diálogo: [if player_level >= 5] mostra opção especial

# Recuperar flag
level = manager.get_flag("player_level", default=1)
```

### Callbacks

```python
# Quando diálogo inicia
manager.on_dialogue_start(lambda: print("Diálogo começou"))

# Quando escolhe opção
manager.on_dialogue_choice(lambda idx: print(f"Escolheu opção {idx}"))

# Quando diálogo termina
manager.on_dialogue_end(lambda: print("Diálogo acabou"))

# Quando evento é disparado
manager.on_event(lambda name, payload: print(f"Evento: {name}"))
```

### Criar Arquivo de Diálogo

Arquivo `.zdialogue` em `Assets/Dialogues/`:

```json
{
  "format": "zennity.generic_graph",
  "category": "Dialogue",
  "nodes": [
    {
      "id": "start",
      "type": "dialogue.speech",
      "inputs": {
        "speaker": "Merchant",
        "text": "Olá! Bem-vindo à minha loja!"
      }
    },
    {
      "id": "choices",
      "type": "dialogue.choice",
      "inputs": {
        "prompt": "O que você quer fazer?"
      }
    }
  ],
  "edges": [
    {
      "source_node": "start",
      "source_port": "out",
      "target_node": "choices",
      "target_port": "in"
    }
  ]
}
```

---

## AnimationController

### O que faz?
Máquina de estados que controla animações com transições automáticas.

### Setup

```python
player = GameObject("Player")
controller = player.add_component(AnimationController(
    default_state="idle",
    blend_duration=0.2
))

# Adicionar estados
controller.add_state("idle", "idle_clip")
controller.add_state("run", "run_clip")
controller.add_state("jump", "jump_clip")
```

### Transições Automáticas

```python
# De idle para run quando velocidade > 0.5
controller.add_transition(
    from_state="idle",
    to_state="run",
    condition=lambda params: params.get("speed", 0) > 0.5
)

# De run para idle quando velocidade <= 0.5
controller.add_transition(
    from_state="run",
    to_state="idle",
    condition=lambda params: params.get("speed", 0) <= 0.5
)

# De qualquer estado para jump
controller.add_transition(
    from_state="idle",
    to_state="jump",
    condition=lambda params: params.get("is_jumping", False)
)
```

### Usar Parâmetros

```python
# Definir parâmetro
controller.set_parameter("speed", 1.5)
controller.set_parameter("is_jumping", True)
controller.set_parameter("combo_count", 3)

# Recuperar parâmetro
speed = controller.get_parameter("speed", default=0)
```

### Transições Manuais

```python
# Mudar estado manualmente
controller.set_state("jump")

# Forçar reiniciar (mesmo que já esteja tocando)
controller.set_state("jump", force=True)

# Estado atual
current = controller.get_current_state()
```

### Callbacks

```python
# Ao entrar em estado
controller.on_state_enter("jump", lambda: print("Jumpando!"))

# Ao sair de estado
controller.on_state_exit("jump", lambda: print("Parou de pular"))
```

---

## MaterialPropertyAnimator

### O que faz?
Anima propriedades (cores, opacidade, números) com easing suave.

### Setup

```python
sprite = go.get_component(SpriteRenderer)
animator = go.add_component(MaterialPropertyAnimator())
```

### Animar Cor

```python
# Flash branco (dano)
animator.animate_color(
    sprite,
    target_color=(1.0, 1.0, 1.0, 1.0),
    duration=0.1,
    easing="ease_out"
)
```

### Animar Opacidade

```python
# Fade out
animator.animate_opacity(
    sprite,
    target_opacity=0.0,
    duration=1.0,
    easing="ease_in",
    on_complete=lambda: go.destroy()
)
```

### Animar Qualquer Propriedade

```python
# Propriedade numérica
animator.animate(
    sprite,
    property_name="brightness",
    target_value=1.5,
    duration=0.5,
    easing="bounce"
)

# Múltiplas simultâneas
animator.animate(sprite, "color", (0, 0, 0, 1), 0.3)
animator.animate(sprite, "opacity", 0.5, 0.5)
```

### Easing Disponível

- `linear` — velocidade constante
- `ease_in` — lento → rápido
- `ease_out` — rápido → lento
- `ease_in_out` — lento → rápido → lento
- `bounce` — ricochete
- `elastic` — elástico

### Callbacks

```python
def on_flash_done():
    print("Flash terminou!")

animator.animate_color(
    sprite,
    (1, 1, 1, 1),
    0.1,
    on_complete=on_flash_done
)
```

### Controle

```python
# Verificar se há animações em progresso
if animator.is_animating():
    print("Ainda tem animação rolando")

# Parar todas as animações
animator.stop_all()
```

---

## Exemplos Práticos

### 1. Jogo com Vida + UI

```python
# Player
player = GameObject("Player")
player.health = 100
player.max_health = 100

# UI
health_label = GameObject("HealthLabel")
health_label.add_component(UIBinder(
    source_path="player.health",
    ui_element_name="HealthText",
    format_string="{value}/100"
))

# Animation
sprite = player.get_component(SpriteRenderer)
animator = player.add_component(MaterialPropertyAnimator())

# Quando toma dano
def take_damage(amount):
    player.health -= amount
    # Flash branco
    animator.animate_color(sprite, (1, 1, 1, 1), 0.1, easing="ease_out")

take_damage(10)  # UI atualiza automaticamente!
```

### 2. Diálogo Interativo

```python
npc = GameObject("NPC")
manager = npc.add_component(DialogueManager(
    dialogue_file="Assets/Dialogues/npc.zdialogue",
    speaker_name="NPC",
    auto_start=False
))

# Quando clica em NPC
def interact():
    manager.begin_dialogue()

# Quando escolhe opção
def on_choice(idx):
    if idx == 0:
        manager.set_flag("quest_accepted", True)
    manager.advance()

manager.on_dialogue_choice(on_choice)
```

### 3. Animação com Estados

```python
player = GameObject("Player")
sprite = player.get_component(SpriteRenderer)
anim = player.add_component(AnimationController())

anim.add_state("idle", "idle_clip")
anim.add_state("run", "run_clip")

anim.add_transition("idle", "run", lambda p: p.get("speed") > 0.5)
anim.add_transition("run", "idle", lambda p: p.get("speed") <= 0.5)

# No update do jogo
def update_player(speed):
    anim.set_parameter("speed", speed)
    # Animação muda automaticamente!
```

### 4. Efeitos Visuais

```python
enemy = GameObject("Enemy")
sprite = enemy.get_component(SpriteRenderer)
animator = enemy.add_component(MaterialPropertyAnimator())

# Explosão com fade
animator.animate_color(sprite, (1, 1, 1, 1), 0.1, easing="ease_out")
animator.animate_opacity(sprite, 0.0, 0.5, easing="ease_in", 
    on_complete=lambda: enemy.destroy())
```

---

## 🎯 Padrão Recomendado

**Para iniciantes, use essa sequência:**

1. **UI com UIBinder** — sincroniza dados automaticamente
2. **DialogueManager** — para NPCs e histórias
3. **AnimationController** — para animações dinâmicas
4. **MaterialPropertyAnimator** — para efeitos visuais

**Resultado**: Game funcional **sem Logic Graph complexo**!

---

## 📚 Referência Rápida

| Componente | Problema que Resolve | Simplicidade |
|-----------|---------------------|-------------|
| UIBinder | Sincronizar dados ↔ UI | ⭐⭐⭐⭐⭐ |
| DialogueManager | Diálogos com ramificações | ⭐⭐⭐⭐ |
| AnimationController | Mudar animações dinamicamente | ⭐⭐⭐⭐ |
| MaterialPropertyAnimator | Efeitos visuais fluidos | ⭐⭐⭐ |

---

## ❓ FAQ

**P: Preciso usar Logic Graph?**
R: Não! Esses 4 componentes resolvem 80% dos casos.

**P: Posso combinar com Logic Graph?**
R: Sim! Use componentes para coisas comuns, Logic Graph para lógica complexa.

**P: E para controlar tudo via script?**
R: Pode também! Todos os componentes têm API Python.

**P: Qual é a performance?**
R: Otimizada — UIBinder usa polling eficiente, outros usam callbacks.

---

## 🚀 Próximos Passos

1. Veja o exemplo prático em `examples/ComponentDemo/`
2. Crie seu próprio jogo combinando os 4
3. Se precisar de lógica complexa, use Logic Graph + componentes

Boa sorte! 🎮
