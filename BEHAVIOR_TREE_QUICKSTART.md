# ⚡ BEHAVIOR TREE — INÍCIO RÁPIDO

**Seu novo sistema de IA está 100% pronto. Aqui está como usar em 5 minutos.**

---

## 🎬 Demo Rápida

```python
# 1. Criar uma árvore simples
tree = {
    "format": "zennity.behavior_tree",
    "version": 1,
    "start_node": "root",
    "nodes": {
        "root": {
            "type": "bt.selector",
            "children": ["attack", "patrol"]
        },
        "attack": {
            "type": "bt.target_in_range",
            "target": "Player",
            "distance": 200
        },
        "patrol": {
            "type": "bt.patrol",
            "point_a": [0, 0],
            "point_b": [300, 0],
            "speed": 80
        }
    }
}

# 2. Criar runtime
from engine.ai.behavior_tree_runtime import BehaviorTreeRuntime

class MyBT(BehaviorTreeRuntime):
    def _find_objects_by_tag(self, tag):
        if tag == "Player":
            return [game.player]
        return []
    
    def _get_position(self, obj):
        return obj.position

bt = MyBT(tree, game_object=my_enemy)

# 3. Executar a cada frame
while game_running:
    status = bt.update(dt=0.016)  # ✅ Pronto!
```

---

## 📚 Estrutura de Nós (Rápido)

### Composite (Fluxo)
| Nó | O Quê |
|---|---|
| **Sequence** | A→B→C (todos) |
| **Selector** | A∨B∨C (qualquer um) |

### Decorator (Modificar)
| Nó | O Quê |
|---|---|
| **Repeat** | Fazer N vezes |
| **Cooldown** | Aguardar depois |
| **Limiter** | Máximo N vezes |
| **Inverter** | Sucesso↔Falha |

### Condition (Decidir)
| Nó | O Quê |
|---|---|
| **Target In Range?** | Alvo perto? |
| **Health Check?** | Saúde OK? |
| **Parameter Check?** | Condição? |
| **Random Chance?** | Sorte? |

### Action (Fazer)
| Nó | O Quê |
|---|---|
| **Idle** | Esperar |
| **Patrol** | Patrulhar |
| **Chase** | Perseguir |
| **Move To** | Mover |
| **Attack** | Atacar |
| **Play Animation** | Animar |
| **Set Parameter** | Comunicar |

---

## 💡 Exemplo: Inimigo Inteligente

```json
{
  "start_node": "ai",
  "nodes": {
    "ai": {
      "type": "bt.selector",
      "children": ["se_ferido", "se_perto", "patrulhar"]
    },
    "se_ferido": {
      "type": "bt.sequence",
      "children": ["check_low_hp", "fugir"]
    },
    "check_low_hp": {
      "type": "bt.health_check",
      "min_health": 30
    },
    "fugir": {
      "type": "bt.move_to",
      "target_pos": [0, 0],
      "speed": 200
    },
    "se_perto": {
      "type": "bt.target_in_range",
      "target": "Player",
      "distance": 300
    },
    "patrulhar": {
      "type": "bt.patrol",
      "point_a": [0, 0],
      "point_b": [500, 0],
      "speed": 80
    }
  }
}
```

---

## 🔗 Próximos Passos

1. **Leia o Guia Completo:**
   ```
   cat BEHAVIOR_TREE_GUIDE.md
   ```

2. **Veja Exemplos:**
   ```
   python examples_behavior_tree.py
   ```

3. **Rode os Testes:**
   ```
   pytest tests/ai/test_behavior_tree_runtime.py -v
   ```

4. **Crie Sua Árvore:**
   - Copie estrutura JSON acima
   - Sobrescreva métodos de integração
   - Execute!

---

## 🎯 Padrões Prontos

### Patrulha + Ataque
```
Selector
├─ (Alvo perto? → Atacar)
└─ Patrulhar
```

### Ataque com Cooldown
```
Cooldown(1s)
└─ Attack
```

### Múltiplas Estratégias
```
Selector
├─ (Ferido? → Fugir)
├─ (Perto? → Atacar)
└─ Patrulhar
```

### Ataques Rápidos em Sequência
```
Repeat(3x)
└─ Attack
```

---

## ✅ Checklist

- [ ] Ler BEHAVIOR_TREE_GUIDE.md
- [ ] Rodar examples_behavior_tree.py
- [ ] Copiar classe MyBehaviorTree para seu projeto
- [ ] Criar arquivo .zbehavior com sua árvore
- [ ] Integrar em seu game loop
- [ ] Testar com pytest
- [ ] Celebrar! 🎉

---

## 🚀 Arquivos do Sistema

```
engine/ai/
├─ behavior_tree_nodes.py       ← Definições (20 nós)
└─ behavior_tree_runtime.py     ← Runtime (executa)

examples_behavior_tree.py        ← 3 exemplos prontos
BEHAVIOR_TREE_GUIDE.md           ← Guia completo
BEHAVIOR_TREE_IMPROVEMENTS.md    ← O que melhorou
BEHAVIOR_TREE_QUICKSTART.md      ← Este arquivo!

tests/ai/
└─ test_behavior_tree_runtime.py ← Testes
```

---

## 🎮 Integração com Pygame/Seu Engine

```python
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.position = [x, y]
        self.health = 100
        
        # Carregar árvore
        self.tree = MyBehaviorTree.from_file(
            "Assets/Behaviors/enemy.zbehavior",
            game_object=self
        )
    
    def update(self):
        self.tree.update(dt=1/60)  # 60 FPS
        # Position e Health são atualizados pela árvore!
```

---

## 🐛 Debug Rápido

```python
status = bt.update(dt=0.016)

# Ver o que aconteceu
for event in bt.events:
    print(event)
    # {'type': 'action_done', 'action_type': 'patrol', ...}
```

---

**Tudo pronto! Divirta-se criando IA inteligente! 🎮**

Dúvidas? Veja BEHAVIOR_TREE_GUIDE.md ou examples_behavior_tree.py
