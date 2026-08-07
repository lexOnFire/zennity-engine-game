# 🚀 Guia: UI Dinâmica 100% Visual

**Crie widgets em runtime usando nós visuais - sem código!**

---

## 📋 O Que É Possível?

Com os novos nós de UI dinâmica você pode:

- ✅ Criar Labels durante o jogo
- ✅ Criar ProgressBars dinamicamente
- ✅ Criar Buttons em runtime
- ✅ Criar Images dinamicamente
- ✅ Remover widgets quando necessário
- ✅ Modificar propriedades em tempo real
- ✅ Ler valores de widgets

**Tudo 100% visual, sem escrever código Python!**

---

## 🎯 Nós Disponíveis

### Criação de Widgets

| Nó | Descrição |
|---|---|
| **Criar Label Dinâmico** | Cria novo texto em runtime |
| **Criar ProgressBar Dinâmica** | Cria nova barra de progresso |
| **Criar Button Dinâmico** | Cria novo botão |
| **Criar Image Dinâmica** | Cria nova imagem |

### Modificação

| Nó | Descrição |
|---|---|
| **Remover Widget** | Deleta widget criado dinamicamente |
| **Atualizar Propriedade Widget** | Modifica text, value, visible, etc |
| **Ler Propriedade Widget** | Lê valor e salva em variável |

---

## 🛠️ Passo a Passo: Criar Labels Dinâmicos

### Cenário: Sistema de Dano Flutuante

Quando inimigo toma dano, mostrar número flutuante "-25" acima dele.

### 1️⃣ Preparar Cena

1. Crie um Canvas chamado **Panel_Flutuante** (na cena)
   - Render Mode: World Space (flutua sobre o inimigo)
   - Visível: true

2. Salve a cena

### 2️⃣ Criar Logic Graph

1. Novo → Logic Graph
2. Nó de entrada: **On Enemy Take Damage**
3. Conecte os nós:

```
On Enemy Take Damage (evento)
  ↓
Math Negate (damage * -1 para negativo)
  ↓
Converter para String (número → texto)
  ↓
Criar Label Dinâmico
├─ Parent: "Panel_Flutuante"
├─ Nome: "damage_label"
├─ Texto: [resultado do string]
├─ X: [posição X do inimigo]
└─ Y: [posição Y do inimigo]
  ↓
Delay (1.0 segundo)
  ↓
Remover Widget
├─ Parent: "Panel_Flutuante"
└─ Nome: "damage_label"
```

### 3️⃣ Resultado

Quando inimigo é atingido:
1. Label "-25" aparece acima dele
2. Fica visível por 1 segundo
3. Desaparece automaticamente

---

## 💡 Exemplo: Sistema de Aviso

**Cenário:** Mostrar mensagem dinâmica quando boss aparece.

### Logic Graph:

```
On Boss Spawn
  ↓
Criar Label Dinâmico
├─ Parent: "Panel_HUD"
├─ Nome: "boss_warning"
├─ Texto: "⚠️ BOSS APARECEU!"
├─ X: 960 (centro)
├─ Y: 100
└─ Font Size: 48
  ↓
Delay (3 segundos)
  ↓
Remover Widget
├─ Parent: "Panel_HUD"
└─ Nome: "boss_warning"
```

**Resultado:** Texto de aviso aparece por 3 segundos e desaparece.

---

## 🎨 Exemplo: Rating System

**Cenário:** Após ganhar, mostrar 5 estrelas e deixar clicar para avaliar.

### 1️⃣ Criar Painel Base (UI Builder)

```
Canvas (Screen Space)
├─ Panel_RatingPopup
│  ├─ Label_Title ("Quanto você gostou?")
│  ├─ Container_Stars (vazio, preenchido dinamicamente)
│  └─ Button_Submit ("Enviar Avaliação")
```

### 2️⃣ Logic Graph (criar estrelas dinamicamente)

```
On Level Complete
  ↓
Loop (5 vezes, criar 5 estrelas)
  ├─ Calcular posição X (i * 80)
  ├─ Criar Button Dinâmico
  │  ├─ Parent: "Container_Stars"
  │  ├─ Nome: "star_" + i
  │  ├─ Texto: "⭐"
  │  ├─ X: [posição calculada]
  │  └─ Y: 50
  └─ [próxima iteração]
  ↓
Mostrar Painel
├─ Widget: "Panel_RatingPopup"
└─ Visible: true
```

### 3️⃣ Resultado

5 estrelas aparecem dinamicamente, pronta para o jogador interagir.

---

## 📐 Parâmetros dos Nós

### Criar Label

```
Parent (string)       : Nome do Container pai
Nome do Widget        : Identificador único ("label_1", "damage_text")
Texto                 : O que mostrar ("Dinâmico", "25", etc)
X, Y                  : Posição no painel
Tamanho Fonte         : Tamanho em pixels (24, 32, 48, etc)
```

### Criar ProgressBar

```
Parent                : Nome do Container pai
Nome do Widget        : Identificador único
X, Y                  : Posição
Largura, Altura       : Dimensões (200x20 é padrão)
Valor Inicial         : 50 (para começar meio cheia)
Valor Max             : 100 (máximo possível)
```

### Remover Widget

```
Parent                : Nome do Container pai
Nome do Widget        : Qual widget remover (deve ser criado antes)
```

### Atualizar Propriedade

```
Parent                : Nome do Container pai
Nome do Widget        : Qual widget modificar
Propriedade           : "text", "value", "visible", "x", "y", etc
Novo Valor            : Qualquer coisa (string, número, true/false)
```

---

## 🎯 Casos de Uso Práticos

### 1. Tutorial com Dicas Dinâmicas
```
On Start Tutorial
  ├─ Criar Label ("Aperte ESPAÇO para pular")
  ├─ Delay (5 segundos)
  └─ Remover Label
```

### 2. Indicador de Cooldown
```
On Ability Use
  ├─ Criar Label ("Cooldown: 30s")
  ├─ Atualizar Propriedade (a cada 1s, reduzir)
  └─ Remover quando chegar a 0
```

### 3. Inventário Dinâmico
```
On Pick Item
  ├─ Criar Button ("Item_novo")
  ├─ Posicionar no próximo slot
  └─ Ao clicar, executar ação
```

### 4. Chat Dinâmico
```
On NPC Talk
  ├─ Loop para cada mensagem
  ├─ Criar Label com texto
  ├─ Delay
  ├─ Remover Label
  └─ Próxima mensagem
```

---

## 🐛 Troubleshooting

### Problema: Widget não aparece
- [ ] Verifique se Parent existe na cena
- [ ] Verifique se Panel_Parent está Visível
- [ ] Verifique X, Y (não estão fora da tela?)

### Problema: Widget não remove
- [ ] Verifique se Nome do Widget é **exato** (case-sensitive)
- [ ] Verifique se Parent está correto

### Problema: Texto não atualiza
- [ ] Verifique se Widget foi criado primeiro
- [ ] Verifique se propriedade é "text" (não "label" ou outro)

---

## 📋 Checklist: Implementar UI Dinâmica

- [ ] Criar Container pai no UI Builder (ex: Panel_HUD)
- [ ] Identificar quando criar widgets (evento, spawn, etc)
- [ ] Criar Logic Graph com nós de criação
- [ ] Definir Parent correto
- [ ] Definir Nome único para cada widget
- [ ] Testar em Play mode
- [ ] Adicionar remoção quando não mais necessário
- [ ] Testar limpeza de widgets

---

## ✨ Resultado

**UI 100% dinâmica, criada visualmente, sem código Python!**

Seus jogadores verão:
- Labels flutuantes ao tomar dano
- Avisos dinâmicos de eventos
- Sistemas de rating interativos
- HUDs adaptáveis
- Qualquer coisa que precise ser criada em runtime

---

**Próximo:** Combine com [STATIC_UI_WORKFLOW.md](./STATIC_UI_WORKFLOW.md) para UI estática + dinâmica! 🎮✨
