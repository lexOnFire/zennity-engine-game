# 🎬 SceneManager — Zennity Engine

## Arquitetura

```
Engine
  └── SceneManager (opt-in via engine.use_scene_manager())
        ├── Stack de Cenas  [cena0, cena1, ...]  ← topo = ativa
        └── Transition      (FadeTransition, SlideTransition, ...)

Transition
  ├── Phase: OUT → SWAP → IN → DONE
  └── snapshot_out / snapshot_in  (capturas das cenas)
```

---

## Início Rápido

```python
from engine import Engine, Scene, SceneManager
from engine.transitions import FadeTransition, SlideTransition, SlideDirection

engine = Engine(800, 600, "Meu Jogo")
sm = engine.use_scene_manager()   # ← ativa; retrocompatível
engine.run(MenuScene())
```

---

## API

### `sm.load(scene, transition=None)`
Substitui toda a pilha pela nova cena.
```python
sm.load(GameScene(), FadeTransition(color=(0,0,0), duration_out=0.4))
```

### `sm.push(scene, transition=None)`
Empilha uma cena por cima (pausa a atual).
```python
sm.push(PauseScene(), SlideTransition(SlideDirection.UP, duration_in=0.35))
```

### `sm.pop(transition=None)`
Remove a cena do topo e retorna à anterior.
```python
sm.pop(SlideTransition(SlideDirection.DOWN, duration_in=0.3))
```

---

## Transições

| Classe | Efeito | Parâmetros principais |
|---|---|---|
| `FadeTransition` | Fade para cor sólida | `color`, `duration_out`, `duration_in` |
| `SlideTransition` | Nova cena desliza por cima | `direction` (LEFT/RIGHT/UP/DOWN), `duration_in` |
| `WipeTransition` | Varredura horizontal/vertical | `horizontal`, `duration_out`, `duration_in` |
| `CrossfadeTransition` | Cross-dissolve entre screenshots | `duration` |

### Easing disponível
`"linear"` · `"ease_in"` · `"ease_out"` · `"ease_in_out"` (padrão)

```python
FadeTransition(duration_out=0.5, easing="ease_in")
```

---

## Fluxo de Transição

```
  Frame N       Frame N+1 ... N+k    Frame N+k+1     Frame N+k+2 ... N+m
 ┌──────────┐   ┌──────────────────┐ ┌────────────┐  ┌──────────────────┐
 │  Fase OUT │→ │ cobre cena atual │→│ SWAP cenas │→ │  Fase IN         │
 │  (0→1.0) │   │ progress: 0→1.0  │ │ cena.start │  │  revela nova cena│
 └──────────┘   └──────────────────┘ └────────────┘  └──────────────────┘
```

- **Durante transição**: input bloqueado (evita double-click)
- **Snapshot automático**: cada fase captura a tela atual para o efeito visual
- **UIManager.reset()** chamado no swap → UI da cena anterior não vaza

---

## Callbacks

```python
sm.on_transition_start = lambda scene_name: print(f"→ indo para {scene_name}")
sm.on_transition_end   = lambda scene_name: print(f"✓ chegou em {scene_name}")
```

---

## Integração com Cenas Antigas

Cenas que usam `self.engine.change_scene(nova)` continuam funcionando —
o SceneManager faz patch de `engine.change_scene` para `sm.load` automaticamente.

---

## Rodar a Demo

```bash
python -m demos.demo_scene_manager
```

Controles: `Enter/Space` avançar · `H` reduzir HP · `Esc` pausar · `F11` fullscreen
