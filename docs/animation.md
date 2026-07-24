# 🎬 Sistema de Animação — Zennity Engine

## Visão Geral

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| `SpriteSheet` | `engine/animation/spritesheet.py` | Fatia spritesheet em frames individuais |
| `AnimationClip` | `engine/animation/clip.py` | Sequencia de frames + FPS + eventos |
| `Animator` | `engine/animation/animator.py` | Componente que gerencia clips e máquina de estados |

---

## Uso Rápido

```python
from engine.animation import SpriteSheet, AnimationClip, Animator
from engine.graphics.renderer2d import SpriteRenderer

# 1. Carregar spritesheet
sheet = SpriteSheet("assets/player.png", frame_width=32, frame_height=32)
sheet.load()

# 2. Criar clips
idle = AnimationClip("idle", sheet.get_range(0, 4),  fps=6)
run  = AnimationClip("run",  sheet.get_range(4, 10), fps=12)
jump = AnimationClip("jump", sheet.get_range(10, 13), fps=8, loop=False)

# 3. Adicionar componentes ao GameObject
sr   = player.add_component(SpriteRenderer(idle.frames[0]))
anim = player.add_component(Animator(default_clip="idle"))
anim.add_clip(idle).add_clip(run).add_clip(jump)

# 4. Transições automáticas
anim.add_transition("idle", "run",  lambda: abs(rb.velocity[0]) > 10)
anim.add_transition("run",  "idle", lambda: abs(rb.velocity[0]) < 10)
anim.add_transition("*",    "jump", lambda: not rb.grounded)  # global
anim.add_transition("jump", "idle", lambda: rb.grounded)
```

---

## SpriteSheet

```python
# Grade regular
sheet = SpriteSheet("tileset.png", 32, 32, spacing=2, margin=1, scale=2.0)
sheet.load()

# Strip horizontal
sheet = SpriteSheet.from_strip("run.png", frame_count=8)

# Acessar frames
frames       = sheet.get_range(0, 4)   # frames 0,1,2,3
row_frames   = sheet.get_row(1)        # linha 1 inteira
frames_left  = SpriteSheet.flip_h(frames)  # espelhado
```

---

## AnimationClip

```python
# Clip com loop
run = AnimationClip("run", frames, fps=12, loop=True)

# Clip sem loop (ex: morte)
die = AnimationClip("die", frames, fps=8, loop=False)

# Flip horizontal automático
run_left = AnimationClip("run_left", frames, fps=12, flip_h=True)

# Evento em frame específico
attack = AnimationClip("attack", frames, fps=10)
attack.add_event(frame_index=3, callback=lambda: apply_damage())
```

---

## Animator

### Controle manual

```python
anim.play("run")              # troca para o clip run
anim.play("jump", force=True) # força reiniciar mesmo se já tocando

anim.current_clip   # nome do clip atual
anim.current_frame  # índice do frame atual
anim.is_finished    # True se clip não-loop terminou
anim.is_playing("run")  # True/False
```

### Callback de fim

```python
anim.on_finish = lambda clip_name: print(f"{clip_name} terminou")

# Exemplo: voltar para idle após morrer
anim.on_finish = lambda name: anim.play("idle") if name == "die" else None
```

### Transições

```python
# from_state -> to_state quando condition() == True
anim.add_transition("idle", "run", lambda: speed > 10)

# "*" = qualquer estado
anim.add_transition("*", "hurt", lambda: self.is_hurt)
```

---

## Integração com SpriteRenderer

O `Animator` atualiza `SpriteRenderer.image` automaticamente a cada frame.
O `SpriteRenderer` cuida do draw (com suporte a câmera, zoom, rotação).

```
GameObject
  ├── Transform
  ├── RigidBody
  ├── BoxCollider
  ├── SpriteRenderer   ← Animator escreve .image aqui
  └── Animator         ← controla qual frame mostrar
```

---

## Rodar a Demo

```bash
python -m demos.demo_animator
```

Contrôles: `A/D` mover · `Space` pular · `F1` debug · `R` resetar
