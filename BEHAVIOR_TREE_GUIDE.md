# 🎮 GUIA COMPLETO: SISTEMA DE BEHAVIOR TREE MELHORADO

## 📋 O Que É Uma Behavior Tree?

Uma **Behavior Tree** é um diagrama que descreve **como um personagem/inimigo se comporta**:
- ¿Deve patrulhar ou atacar?
- ¿Deve fugir ou perseguir?
- ¿Qual ação fazer em cada situação?

É como um **flowchart inteligente** que o jogo executa frame a frame.

---

## 🏗️ Estrutura: 3 Tipos de Nós

### 1️⃣ **COMPOSITE** — Controlam o fluxo

#### `Sequence` (Sequência)
```
fazer A → depois B → depois C
Falha se qualquer um falhar
```
**Quando usar:** "atacar DEPOIS esperar DEPOIS vencer"

#### `Selector` (Seletor)
```
tentar A → se falhar tenta B → se falhar tenta C
Sucesso se qualquer um tiver sucesso
```
**Quando usar:** "se alvo está perto, perseguir, SENÃO patrulhar"

---

### 2️⃣ **DECORATOR** — Modificam o filho

#### `Repeat` (Repetir)
```
Executa o filho N vezes (0 = infinito)
```
**Quando usar:** Patrulha contínua, loops

#### `Cooldown` (Aguardar)
```
Espera N segundos antes de deixar filho executar novamente
```
**Quando usar:** Limitar ataques (um por segundo)

#### `Limiter` (Limitador)
```
Executa até N vezes, depois falha sempre
```
**Quando usar:** "tente 3 vezes, se não conseguir desista"

#### `Inverter` (Inversor)
```
Sucesso vira falha, falha vira sucesso
```
**Quando usar:** "fazer enquanto NÃO tiver condição"

---

### 3️⃣ **CONDITION** — Checam situações

#### `Target In Range?` (Alvo no Alcance?)
Verifica se alvo (por tag) está perto.

```
Sucesso: alvo encontrado e dentro da distância
Falha: alvo não existe ou está longe
```

#### `Health Check?` (Saúde OK?)
Verifica se health > valor.

```
Sucesso: vida acima do limite
Falha: vida baixa
```

#### `Parameter Check?` (Parâmetro OK?)
Compara um parâmetro com um valor.

```
Operadores: ==, !=, <, ≤, >, ≥
```

#### `Random Chance?` (Sorte?)
Sucesso com X% de probabilidade.

---

### 4️⃣ **ACTION** — Fazem coisas reais

#### `Idle` / `Wait` (Esperar)
Fica parado N segundos.

#### `Patrol` (Patrulhar)
Alterna entre ponto A e B.

#### `Chase` (Perseguir)
Vai em direção ao alvo.

#### `Move To` (Mover Para)
Move para uma posição específica.

#### `Attack` (Atacar)
Aplica dano se alvo está no alcance.

#### `Play Animation` (Animar)
Toca uma animação.

#### `Set Parameter` (Definir Parâmetro)
Muda um parâmetro (comunica com o jogo).

#### `Log` (Debug)
Imprime mensagem (para testes).

---

## 📐 Exemplo Prático: Inimigo Inteligente

### Comportamento Desejado:
```
1. Se alvo está perto E tem saúde OK:
   → Perseguir e atacar
2. Se alvo está perto MAS baixa saúde:
   → Fugir e patrulhar
3. Se alvo não está perto:
   → Patrulhar normalmente
```

### Árvore Resultante:

```
                    [ROOT]
                      |
                  [SELECTOR]
                  /    |    \
                /      |      \
        [Seq 1]    [Seq 2]   [PATROL]
         /  \       /  \
   [Check  [Chase] [Check [FLEE]
    Range]         Health]
```

---

## 💾 Formato JSON da Behavior Tree

```json
{
  "format": "zennity.behavior_tree",
  "version": 1,
  "name": "EnemyBT",
  "start_node": "root",
  "nodes": {
    "root": {
      "type": "bt.selector",
      "children": ["attack_if_near", "patrol"]
    },
    "attack_if_near": {
      "type": "bt.sequence",
      "children": ["check_range", "attack_action"]
    },
    "check_range": {
      "type": "bt.target_in_range",
      "target": "Player",
      "distance": 200.0
    },
    "attack_action": {
      "type": "bt.attack",
      "target": "Player",
      "damage": 10.0,
      "range": 64.0
    },
    "patrol": {
      "type": "bt.patrol",
      "point_a": [0, 0],
      "point_b": [300, 0],
      "speed": 80.0
    }
  }
}
```

---

## 🎬 Como Executar em Código

### Integração Básica:

```python
from engine.ai.behavior_tree_runtime import BehaviorTreeRuntime
import json

# 1. Carregar a árvore
with open("Assets/Behaviors/EnemyBT.zbehavior") as f:
    tree_data = json.load(f)

# 2. Criar runtime
class MyEnemy:
    def __init__(self):
        self.position = [100, 100]
        self.health = 50
        
    def update(self):
        self.tree_runtime.update(dt=0.016)

enemy = MyEnemy()
enemy.tree_runtime = BehaviorTreeRuntime(tree_data, game_object=enemy)

# 3. A cada frame, chamar update()
enemy.tree_runtime.update(dt=0.016)

# 4. Definir parâmetros baseado no jogo
player_distance = distance_to_player(enemy)
enemy.tree_runtime.set_parameter("player_distance", player_distance)
```

### Sobrescrever Métodos para Integração:

```python
class MyBehaviorTree(BehaviorTreeRuntime):
    def _find_objects_by_tag(self, tag):
        """Encontrar objetos no seu jogo"""
        if tag == "Player":
            return [game.player]
        return []
    
    def _get_position(self, obj):
        """Pegar posição"""
        return obj.position
    
    def _move_towards_target(self, obj, target_pos, speed):
        """Mover objeto"""
        obj.velocity = self._direction_to(obj.position, target_pos) * speed
    
    def _apply_damage(self, obj, damage):
        """Aplicar dano"""
        obj.health -= damage
    
    @staticmethod
    def _direction_to(from_pos, to_pos):
        """Helper"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        dist = (dx*dx + dy*dy) ** 0.5
        if dist == 0: return (0, 0)
        return (dx/dist, dy/dist)
```

---

## 🎯 Padrões Comuns

### Padrão 1: Patrulhar OU Perseguir

```
[SELECTOR]
  ├─ [CHECK RANGE] → [CHASE]
  └─ [PATROL]
```

### Padrão 2: Atacar com Cooldown

```
[SEQUENCE]
  ├─ [COOLDOWN 1s]
  └─ [ATTACK]
```

Vai dentro de um SELECTOR/SEQUENCE maior.

### Padrão 3: Comportamento Alternado

```
[SELECTOR]
  ├─ [SEQUENCE]
  │   ├─ [CHECK LOW HEALTH]
  │   └─ [FLEE]
  ├─ [SEQUENCE]
  │   ├─ [CHECK IN RANGE]
  │   └─ [CHASE]
  └─ [PATROL]
```

### Padrão 4: Repetição com Limite

```
[SEQUENCE]
  ├─ [LIMITER 3x]
  │   └─ [JUMP ATTACK]
  └─ [WAIT 2s]
```

---

## 🐛 Debug e Teste

### Ver Eventos:

```python
runtime = BehaviorTreeRuntime(tree_data)
status = runtime.update(dt=0.016)

for event in runtime.events:
    print(event)
    # {"type": "node_success", "node_id": "root", ...}
    # {"type": "action_done", "node_id": "patrol", ...}
```

### Nó Log para Teste:

```json
{
  "type": "bt.log",
  "message": "Iniciando ataque!"
}
```

---

## ⚡ Dicas de Performance

1. **Reutilize Runtime:** Crie uma vez, update sempre (não recrie a cada frame)
2. **Cache Positions:** Calcule distâncias uma vez por frame
3. **Limpe Eventos:** Chame `clear_events()` se não precisar deles
4. **Use Cooldown:** Limite checagens custosas (pathfinding, raycast)

---

## 🔧 Próximas Melhorias Possíveis

- [ ] Editor visual para montar árvores (drag-and-drop)
- [ ] Blackboard compartilhado entre nós
- [ ] Estados paralelos (executa 2 nós ao mesmo tempo)
- [ ] Scripting customizado de nós
- [ ] Visualização ao vivo durante gameplay
- [ ] Profiler de performance

---

## 📚 Resumo Rápido

| Nó | O Quê | Quando |
|---|---|---|
| **Sequence** | Faz A depois B depois C | "atacar E esperar E vencer" |
| **Selector** | Tenta A, se falha B | "perseguir OU patrulhar" |
| **Repeat** | Faz N vezes | Loops infinitos |
| **Cooldown** | Aguarda tempo | Limitar frequência |
| **Limiter** | Máximo N vezes | Evitar loops infinitos |
| **Inverter** | Sucesso ↔ Falha | "enquanto NÃO..." |
| **Target In Range?** | Alvo perto? | Decisões de combate |
| **Health Check?** | Vida OK? | Fuga inteligente |
| **Parameter Check?** | Parâmetro == valor? | Estados customizados |
| **Idle** | Espera | Pausas naturais |
| **Patrol** | Alterna A↔B | Patrulha |
| **Chase** | Vai pro alvo | Perseguição |
| **Attack** | Ataca | Combate |

---

Qualquer dúvida? Verifique os exemplos em `Assets/Behaviors/` ou abra um issue! 🚀
