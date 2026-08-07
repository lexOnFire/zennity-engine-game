# 🌳 Guia Completo: Behavior Tree (BT)

O **Behavior Tree** é onde você define o comportamento de NPCs e criaturas. Use a interface visual - não precisa de código!

---

## 📋 Categorias de Nós

### 🔀 **COMPOSITE** - Controlam Fluxo
Definem **como** os nós filhos são executados.

| Nó | Descrição | Uso |
|---|---|---|
| **Selector** | Tenta cada filho até um **ter sucesso** | Fallback: "tente A, se falhar tente B" |
| **Sequence** | Executa filhos **em ordem**. Falha se um falhar | Pipeline: "fazer A, depois B, depois C" |

**Exemplo: Selector (escolher ação)**
```
Selector
├─ Sequence (se comida perto)
│  ├─ Target In Range
│  └─ Chase
└─ Patrol (padrão, se nada)
```

---

### 🎯 **CONDITION** - Tomam Decisões
Retornam SUCCESS (sim) ou FAILURE (não).

| Nó | Entrada | Descrição |
|---|---|---|
| **Target In Range** | tag, distance | "Alvo está perto?" |
| **Health Check** | min_health | "Saúde está ok?" |
| **Parameter Check** | parameter, operator, value | "Variável tem valor X?" |
| **Random Chance** | chance (0-100) | "Sorte de X%?" |

**Exemplo: Verificar se comida está perto**
```
Target In Range
├─ Target: "Food" (tag do objeto)
├─ Distance: 400.0 (pixels)
→ Success se está perto, Failure se está longe
```

---

### ⚙️ **DECORATOR** - Modificam Comportamento
Alteram como o nó filho é executado.

| Nó | Entrada | Descrição |
|---|---|---|
| **Repeat** | count (0=infinito) | Repetir N vezes ou infinitamente |
| **Cooldown** | seconds | Aguardar N segundos entre execuções |
| **Limiter** | max_count | Executar no máximo N vezes |
| **Inverter** | - | Inverter resultado (sucesso→falha, falha→sucesso) |

**Exemplo: Atacar com cooldown**
```
Cooldown (2.0 segundos)
└─ Attack
```
*Não ataca mais de 1x a cada 2 segundos*

---

### 🎬 **ACTION** - Executam Ações Reais

#### Movimento
| Nó | Entradas | Descrição |
|---|---|---|
| **Idle** | duration | Esperar N segundos |
| **Move To** | target_pos, speed | Mover para posição fixa |
| **Chase** | target, speed, stop_distance | Perseguir alvo |
| **Patrol** | point_a, point_b, speed | Ir e vir entre dois pontos |

#### Combate
| Nó | Entradas | Descrição |
|---|---|---|
| **Attack** | target, damage, range | Atacar inimigo no alcance |
| **Play Animation** | animation | Tocar animação (ex: "jump", "hit") |

#### Variáveis
| Nó | Entradas | Descrição |
|---|---|---|
| **Set Parameter** | parameter, value | Guardar valor em variável |
| **Log** | message | Imprimir no console (debug) |

---

## 🎨 **UI ACTIONS** - Interagir com UI

| Nó | Widget | Descrição |
|---|---|---|
| **Set UI Text** | nome, texto | Mudar texto: `"100"` |
| **Set UI Progress** | nome, valor | Mudar barra: 75 de 100 |
| **Set UI Visible** | nome, true/false | Mostrar/ocultar widget |
| **Increment UI Value** | nome, quantidade | Aumentar: +10 moedas |
| **Decrement UI Value** | nome, quantidade | Diminuir: -5 HP |

**Exemplo: Reduzir HP ao tomar dano**
```
Nó: Decrementar Valor UI
├─ Widget: "hp_bar"
├─ Quantidade: 20.0
→ Remove 20 do valor atual da barra
```

---

## 🔗 Conectar Nós

1. **Clique no nó de saída** (porta inferior)
2. **Arraste até o nó de entrada** (porta superior)
3. **Solte para conectar**

### Tipos de Conexão

| Tipo | Cor | Significa |
|---|---|---|
| **Exec** (branco) | Fluxo de execução (A executa, depois B) |
| **Data** (azul) | Passagem de valor (A envia número, B recebe) |

---

## 📐 Estrutura Básica de uma BT

**Toda BT precisa ter:**
1. **Start Node** - Nó por onde começa (geralmente um Selector)
2. **Nós conectados** - Cada nó precisa de entrada e saída
3. **Folhas** (Leafs) - Nós sem filhos (Conditions ou Actions)

**Padrão recomendado:**
```
Selector (root)
├─ Sequence (se condição 1)
│  ├─ Condition 1
│  ├─ Action 1
│  └─ Action 2
├─ Sequence (se condição 2)
│  ├─ Condition 2
│  └─ Action 3
└─ Default Action
```

---

## 💾 Como Usar no Projeto

### 1. Criar Behavior Tree

1. Menu → New → Behavior Tree
2. Nó inicial aparece automaticamente
3. Adicione nós conforme necessário
4. Salve em `Assets/Behaviors/nome.zbehavior`

### 2. Usar em GameObject

1. Abra Scene
2. Selecione objeto (ex: "inimigo")
3. Inspector → Add Component → Behavior
4. Configure:
   - **Controller Path**: `Assets/Behaviors/nome.zbehavior`
   - **Auto Start**: Ativado (inicia ao carregar a cena)

### 3. Testar

1. Play (execute a cena)
2. Observe o objeto seguindo a lógica da BT

---

## 📋 Checklist: Criar Comportamento de NPC

- [ ] Identifique estados (idle, chase, attack, flee)
- [ ] Mapeie transições entre estados
- [ ] Crie nós Condition para cada transição
- [ ] Crie nós Action para cada estado
- [ ] Use Sequence para ações que devem acontecer juntas
- [ ] Use Selector para escolher entre alternativas
- [ ] Teste no Play mode
- [ ] Ajuste velocidades, distâncias, valores

---

## 🎯 Exemplos Práticos

### Exemplo 1: NPC Simples (Patrulhar)
```
Repeat (infinito)
└─ Patrol
   ├─ Point A: (-100, 100)
   ├─ Point B: (200, 0)
   └─ Speed: 80.0
```
*Vai e vem entre dois pontos forever*

---

### Exemplo 2: NPC com Perseguição
```
Selector
├─ Sequence (se joueur perto)
│  ├─ Target In Range (tag: "Player", distance: 300)
│  ├─ Chase (target: "Player", speed: 150)
│  └─ Attack (target: "Player", damage: 10)
└─ Patrol (padrão)
   ├─ Point A: (-100, 0)
   ├─ Point B: (100, 0)
   └─ Speed: 50.0
```
*Se vir joueur, chasa e ataca. Senão, patrulha normalmente.*

---

### Exemplo 3: NPC com Feedback Visual
```
Sequence (ao ataqe)
├─ Attack (target: "Player", damage: 20)
├─ Play Animation ("attack_swing")
├─ Set UI Progress (widget: "enemy_hp", value: 75)
└─ Idle (duration: 1.0)
```
*Ataca, anima, atualiza UI, espera 1s antes de repetir*

---

## 🐛 Debug

### Ver execução em tempo real

1. Play (execute cena)
2. Selecione objeto com BT
3. Verifique console para logs

### Adicionar debug

Adicione nó **Log** onde quiser ver mensagens:
```
Log (message: "Iniciando perseguição!")
```

Veja saída no Console do editor.

---

**Próximo:** Leia [UI_BUILDER_GUIDE.md](./UI_BUILDER_GUIDE.md) para trabalhar com UI! 🎨
