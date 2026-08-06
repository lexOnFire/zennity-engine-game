# Logic Graph - Nós de UI (Fase 2)

Guia de uso dos 5 novos nós adicionados ao Logic Graph para trabalhar com elementos UI de forma simples.

## Novos Nós (5)

### 1. **Set UI Value** — Define Valor Numérico

Muda o valor de um elemento UI (como Progress Bar, Label, etc).

**Entradas:**
- `in` (flow) — Sinal para executar
- `element` (text) — Nome ou ID do elemento UI
- `value` (number) — Novo valor

**Saídas:**
- `next` (flow) — Executado após sucesso

**Propriedades:**
- `format` (string) — Formato para exibição (ex: "{value}/100")
- `max_value` (number) — Valor máximo permitido

**Exemplo:** Definir barra de vida a 75
```
Set UI Value
├─ element: "HealthBar"
├─ value: 75
└─ max_value: 100
```

---

### 2. **Increment UI Value** — Incrementa Valor

Adiciona um valor ao elemento UI.

**Entradas:**
- `in` (flow)
- `element` (text) — Nome do elemento
- `amount` (number) — Quanto incrementar

**Saídas:**
- `next` (flow)

**Propriedades:**
- `max_value` (number) — Limite máximo

**Exemplo:** Ganhar 10 de pontos
```
[Collider.on_trigger_enter] → Increment UI Value
├─ element: "ScoreCounter"
├─ amount: 10
└─ max_value: 9999
```

---

### 3. **Decrement UI Value** — Decrementa Valor

Remove um valor do elemento UI (oposto do Increment).

**Entradas:**
- `in` (flow)
- `element` (text)
- `amount` (number) — Quanto decrementar

**Saídas:**
- `next` (flow)

**Propriedades:**
- `min_value` (number) — Limite mínimo

**Exemplo:** Gastar 5 de mana
```
[Button.on_click] → Decrement UI Value
├─ element: "ManaBar"
├─ amount: 5
└─ min_value: 0
```

---

### 4. **Animate Material** — Anima Propriedade de Material

Suaviza a transição de uma propriedade de material (cor, opacidade, brilho, etc).

**Entradas:**
- `in` (flow)
- `target` (object) — Objeto que será animado
- `property` (text) — Nome da propriedade ("opacity", "color", "brightness")
- `target_value` (number) — Valor final
- `duration` (number) — Duração em segundos

**Saídas:**
- `next` (flow) — Chamado ao terminar

**Propriedades:**
- `easing` (string) — Tipo de suavização:
  - `linear` — Velocidade constante
  - `ease_in` — Começa lento
  - `ease_out` — Termina lento
  - `ease_in_out` — Começa e termina lento

**Exemplo:** Fazer NPC desaparecer gradualmente
```
[NPC.on_death] → Animate Material
├─ target: NPC
├─ property: "opacity"
├─ target_value: 0
├─ duration: 2.0
└─ easing: "ease_out"
```

---

### 5. **Format UI Text** — Formata Texto com Valores

Muda o texto de um Label com formatação automática.

**Entradas:**
- `in` (flow)
- `element` (text) — Nome do Label
- `format_string` (text) — Template ("Vida: {value}/{max}")
- `value` (number) — Valor a inserir

**Saídas:**
- `next` (flow)

**Propriedades:**
- `format` (string) — Fallback se não passado via entrada

**Exemplo:** Mostrar "Vida: 50/100"
```
[Update Health] → Format UI Text
├─ element: "HealthLabel"
├─ format_string: "Vida: {value}/100"
└─ value: 50
```

---

## Exemplos Práticos

### Contador Simples (Usar Increment/Decrement)

```
[Canvas - Contador]
├─ Label
│   ├─ text: "0"
│   └─ name: "CounterLabel"
├─ Button (+)
│   └─ on_click → Increment UI Value
│       ├─ element: "CounterLabel"
│       ├─ amount: 1
│       └─ max_value: 999
└─ Button (-)
    └─ on_click → Decrement UI Value
        ├─ element: "CounterLabel"
        ├─ amount: 1
        └─ min_value: 0
```

### Barra de Vida com Dano (Animate)

```
[Enemy.on_hit]
    ↓
    Decrement UI Value
    ├─ element: "HealthBar"
    ├─ amount: 25
    └─ min_value: 0
    ↓
    Branch (Health == 0?)
    ├─ true  → Play Animation ("death") → Destroy Object
    └─ false → Animate Material
        ├─ target: Enemy
        ├─ property: "color"
        ├─ target_value: 255  (white flash)
        └─ duration: 0.2
```

### Chaves de Tesouro Coletáveis

```
[Player.on_collide_treasure]
    ↓
    Sequence
    ├─ Increment UI Value
    │  ├─ element: "KeyCounter"
    │  └─ amount: 1
    ├─ Play Sound ("key_collect")
    └─ Destroy Object (self)
```

---

## Ações do Behavior Tree (BT) — Novas

Além dos nós de Logic Graph, há 3 ações novas para Behavior Trees que trabalham com UI:

### `bt.set_ui_value`
Define um valor em elemento UI (sucesso/falha).

```bt
├─ Condition: Player Hit
└─ Set UI Value
   ├─ element: "DamageCounter"
   └─ value: 25
```

### `bt.increment_ui_value`
Incrementa valor em UI (sucesso/falha).

```bt
├─ Patrol
├─ [on_collect_item] → Increment UI Value
   ├─ element: "ItemCount"
   └─ amount: 1
```

### `bt.animate_ui_value`
Anima transição suave (retorna `running` enquanto anima, `success` ao terminar).

```bt
├─ Selector
   ├─ Animate UI Value (barra de vida)
   │  ├─ element: "HealthBar"
   │  ├─ target_value: 50
   │  ├─ duration: 0.5
   │  └─ easing: "ease_in_out"
   └─ ...
```

---

## Categorização Hierárquica

Os nós estão organizados em grupos para descoberta fácil:

```
UI (categoria)
├─ Texto
│  ├─ Set UI Text (existente)
│  └─ Format UI Text (novo)
├─ Valores
│  ├─ Set UI Value (novo)
│  ├─ Increment UI Value (novo)
│  └─ Decrement UI Value (novo)
├─ Diálogos
│  ├─ Start Dialogue
│  └─ Dialogue Choose
└─ Animação
   ├─ Animate UI Value (existente)
   └─ Animate Material (novo)
```

Na paleta do Logic Graph, buscar por "ui" mostra todos esses nós agrupados.

---

## Comparação com Código Manual

### Antes (sem nós específicos):
```csharp
// Seria necessário montar Logic Graph complexo com:
// - Get Property → Increment Number → Set Property
// - Para cada UI element
```

### Agora (com nós de UI):
```
Increment UI Value
├─ element: "ScoreLabel"
└─ amount: 10
// Pronto!
```

### Transição Suave:
```
Animate Material
├─ target: Enemy
├─ property: "opacity"
├─ target_value: 0
└─ duration: 2.0
// Sem precisa de Tween library manual
```

---

## Tips & Tricks

1. **Vincular UI a Lógica Complexa:** Use `UIBinder` (componente) para sincronização automática, ou combine `Set UI Value` com lógica condicional.

2. **Animações Encadeadas:** Use `Animate Material` com delay para criar efeitos como "damage flash" → "heal glow".

3. **Contadores com Limite:** Use `max_value` em `Increment UI Value` para evitar ultrapassa 100% de barra.

4. **BT + UI:** Combine ações BT novas para criar NPCs que atualizam UI (ex: "Fase 2 desbloqueada").

---

## Roadmap Futuro

- [ ] Visual property picker na paleta (clique para selecionar elemento)
- [ ] Presets (botões pré-configurados: "+1", "+10", "Reset")
- [ ] Editor visual para easing curves
- [ ] Suporte para animações em paralelo (coroutines)
