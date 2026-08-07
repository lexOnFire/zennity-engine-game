# 🎮 Sistemas Avançados 100% Visual

**Zennity agora tem suporte COMPLETO para Diálogo, Partículas, Audio, Câmera e State Machine!**

---

## 🗣️ Sistema de Diálogo

Crie narrativas inteiras SEM CÓDIGO usando Logic Graph!

### Nós Disponíveis

#### 1. **Mostrar Diálogo**
Exibe um diálogo com opções de escolha.

**Entradas:**
- ID do Diálogo: ID único (ex: "dialog_choice_1")
- Personagem: Nome do NPC (ex: "Chefe")
- Texto: O que o NPC diz
- Opções: Array com as respostas (ex: ["Sim", "Não", "Talvez"])

**Saídas:**
- Mostrando: Diálogo exibido
- Falha: Erro ao exibir

**Exemplo:**
```
On Quest Start
  ↓
Mostrar Diálogo
├─ ID: "intro_dialog"
├─ Personagem: "Rei"
├─ Texto: "Bem-vindo ao meu reino!"
└─ Opções: ["Ajudar", "Recusar"]
  ↓
Aguardar Escolha
```

#### 2. **Aguardar Escolha**
Pausa execução até player escolher uma opção.

**Entradas:**
- ID do Diálogo: ID do diálogo que está mostrando

**Saídas:**
- Escolhido: Player fez uma escolha
- Aguardando: Ainda esperando
- Índice: Qual opção foi escolhida (0, 1, 2...)
- Texto Escolhido: Qual texto foi escolhido

**Exemplo:**
```
Aguardar Escolha
├─ ID: "intro_dialog"
  ↓ (escolhido)
  ├─ Se Índice == 0 → Dar missão
  └─ Se Índice == 1 → Recusar missão
```

#### 3. **Definir Escolha** (uso interno)
Para testar ou simular escolhas do player.

#### 4. **Fechar Diálogo**
Remove um diálogo ativo da tela.

---

## 🎵 Audio Avançado

Controle total sobre sons com fade e efeitos!

### Nós Disponíveis

#### 1. **Tocar Som com Fade**
Toca som com fade in e fade out suave.

**Entradas:**
- Arquivo: Caminho do som (ex: "assets/sounds/explosion.wav")
- Fade In: Tempo para suavizar entrada (segundos)
- Fade Out: Tempo para suavizar saída (segundos)
- Volume: Volume inicial (0.0 - 1.0)

**Exemplo:**
```
Tocar Som com Fade
├─ Arquivo: "sounds/music_boss.wav"
├─ Fade In: 2.0
├─ Fade Out: 1.0
└─ Volume: 0.8
```

#### 2. **Definir Volume**
Controla volume de um canal.

**Entradas:**
- Volume: 0.0 (silenciado) a 1.0 (máximo)
- Canal: "master" (tudo), "sfx" (efeitos), "music" (música)

**Exemplo:**
```
On Pause Menu Open
  ↓
Definir Volume
├─ Volume: 0.3
└─ Canal: "master"
```

#### 3. **Definir Pitch**
Muda velocidade/tom do som.

**Entradas:**
- Pitch: 1.0 = normal, 2.0 = dobrado, 0.5 = metade

**Exemplo:**
```
Definir Pitch
├─ Pitch: 1.2  (som mais agudo)
```

#### 4. **Parar Todos os Sons**
Para imediatamente todos os áudios.

---

## ✨ Sistema de Partículas

Crie efeitos visuais impressionantes!

### Nós Disponíveis

#### 1. **Criar Sistema de Partículas**
Cria um novo sistema de partículas em uma posição.

**Entradas:**
- X, Y: Posição
- Tipo: "spark", "smoke", "fire", "dust", "water" (ou customizado)
- Quantidade: Número de partículas
- Tempo de Vida: Quanto tempo cada partícula dura
- Velocidade: Quão rápido as partículas se movem

**Saídas:**
- ID do Sistema: Guarde para usar em emitir/parar

**Exemplo:**
```
On Bomb Explodes
  ↓
Criar Sistema de Partículas
├─ X: position.x
├─ Y: position.y
├─ Tipo: "explosion"
├─ Quantidade: 50
├─ Tempo de Vida: 2.0
└─ Velocidade: 300.0
  ↓
Armazenar ID em variável (ex: "explosion_id")
```

#### 2. **Emitir Partículas**
Emite mais partículas de um sistema existente.

**Entradas:**
- ID do Sistema: ID retornado ao criar
- Quantidade: Quantas partículas emitir agora

**Exemplo:**
```
Emitir Partículas
├─ ID: variável("explosion_id")
└─ Quantidade: 20
```

#### 3. **Parar Partículas**
Para a emissão (partículas existentes continuam, novas não saem).

**Entradas:**
- ID: ID do sistema
- Destruir Imediatamente: Se true, remove todas as partículas agora

---

## 📹 Câmera Avançada

Câmera cinematográfica sem código!

### Nós Disponíveis

#### 1. **Câmera Sacode**
Cria efeito de impacto/explosão.

**Entradas:**
- Duração: Quanto tempo sacodeja
- Intensidade: Quão forte
- Frequência: Quantas vezes por segundo

**Exemplo:**
```
On Player Hit
  ↓
Câmera Sacode
├─ Duração: 0.3
├─ Intensidade: 10.0
└─ Frequência: 15.0
```

#### 2. **Câmera Segue**
Câmera segue suavemente um objeto (geralmente o player).

**Entradas:**
- Alvo: Nome do objeto (ex: "player")
- Suavidade: 0.3 = muito suave, 0.1 = mais rápido

**Exemplo:**
```
On Game Start
  ↓
Câmera Segue
├─ Alvo: "player"
└─ Suavidade: 0.3
```

#### 3. **Câmera Parar de Seguir**
Desativa o seguimento automático.

#### 4. **Câmera Olha Para**
Move câmera para uma posição específica.

**Entradas:**
- X, Y: Posição alvo
- Duração: Tempo para alcançar (segundos)

**Exemplo:**
```
On Boss Appears
  ↓
Câmera Olha Para
├─ X: boss.x
├─ Y: boss.y
└─ Duração: 2.0
```

#### 5. **Câmera Zoom**
Zoom suave com Lerp.

**Entradas:**
- Zoom: 1.0 = normal, 2.0 = 2x mais zoom, 0.5 = afastado
- Duração: Tempo da animação

**Exemplo:**
```
Câmera Zoom
├─ Zoom: 1.5
└─ Duração: 1.0
```

---

## 🎭 State Machine

Máquina de estados para comportamentos complexos!

### Nós Disponíveis

#### 1. **Criar State Machine**
Cria uma nova máquina de estados.

**Entradas:**
- ID da Máquina: ID único (ex: "player_sm")
- Estado Inicial: Estado que começa (ex: "idle")

**Saídas:**
- ID da Máquina: Guarde para usar depois

**Exemplo:**
```
On Game Start
  ↓
Criar State Machine
├─ ID: "enemy_sm"
└─ Estado Inicial: "idle"
```

#### 2. **Adicionar Transição**
Define como passar de um estado para outro.

**Entradas:**
- ID da Máquina: Qual máquina
- De: Estado inicial
- Para: Estado final
- Condição: "always" (sempre permitido), "on_key", "on_event"

**Exemplo:**
```
Adicionar Transição
├─ ID: "enemy_sm"
├─ De: "idle"
├─ Para: "walking"
└─ Condição: "always"

Adicionar Transição
├─ ID: "enemy_sm"
├─ De: "walking"
├─ Para: "attacking"
└─ Condição: "on_key"  (quando player se aproxima)

Adicionar Transição
├─ ID: "enemy_sm"
├─ De: "attacking"
├─ Para: "idle"
└─ Condição: "always"
```

#### 3. **Mudar Estado**
Muda para um novo estado.

**Entradas:**
- ID: Qual máquina
- Novo Estado: Para qual estado ir
- Forçar: Se true, ignora verificação de transição válida

**Saídas:**
- Mudado: Mudança foi bem-sucedida
- Transição Inválida: Essa mudança não é permitida
- Estado Anterior: Qual era o estado anterior

**Exemplo:**
```
Mudar Estado
├─ ID: "enemy_sm"
├─ Novo Estado: "walking"
└─ Forçar: false
```

#### 4. **Obter Estado**
Retorna o estado atual.

**Entradas:**
- ID: Qual máquina

**Saídas:**
- Estado Atual: Nome do estado

#### 5. **Está em Estado?**
Verifica se está em um estado específico (condicional).

**Entradas:**
- ID: Qual máquina
- Estado a Verificar: Qual estado verificar

**Saídas:**
- Está: Sim, está nesse estado
- Não Está: Não está nesse estado

**Exemplo:**
```
Está em Estado?
├─ ID: "enemy_sm"
└─ Estado: "idle"
  ↓ (se sim)
  └─ Animar para posição idle
  ↓ (se não)
  └─ Aguardar transição
```

---

## 🎯 Exemplo Completo: Boss Inteligente

```
On Game Start
  ↓
Criar State Machine
├─ ID: "boss_sm"
└─ Estado Inicial: "idle"
  ↓
Adicionar Transição (idle → chase)
Adicionar Transição (chase → attack)
Adicionar Transição (attack → idle)
  ↓
Criar Particle System (para efeitos)
├─ Tipo: "boss_aura"
└─ ID: armazenar em "boss_particles"
  ↓
Loop Principal
├─ Aguardar Distância < 200
├─ Mudar Estado (boss_sm → chase)
├─ Câmera Segue (boss)
│
├─ Aguardar Distância < 50
├─ Mudar Estado (boss_sm → attack)
├─ Câmera Sacode
├─ Tocar Som com Fade (boss_attack.wav, fade_in: 0.2)
├─ Emitir Partículas (boss_particles, quantidade: 30)
│
├─ Aguardar 2 segundos
├─ Mudar Estado (boss_sm → idle)
```

---

## 📊 Resumo Completo: 100% Visual Agora!

| Sistema | Nós | Status |
|---------|-----|--------|
| **Diálogo** | Mostrar, Aguardar, Fechar | ✅ 5 nós |
| **Audio** | Play Fade, Volume, Pitch, Stop All | ✅ 4 nós |
| **Partículas** | Criar, Emitir, Parar | ✅ 3 nós |
| **Câmera** | Shake, Follow, Look At, Zoom | ✅ 5 nós |
| **State Machine** | Criar, Transição, Mudar, Obter, Verificar | ✅ 5 nós |

**Total: 22 nós novos adicionados!**

---

## 🎉 Resultado

**Você pode agora criar jogos COMPLETAMENTE VISUAIS:**
- ✅ Narrativas com diálogos e escolhas
- ✅ Efeitos sonoros e música cinematográfica
- ✅ Efeitos visuais com partículas
- ✅ Câmera profissional
- ✅ Comportamentos complexos com state machine
- ✅ Tudo SEM ESCREVER UMA LINHA DE CÓDIGO PYTHON!

---

## 📚 Próximas Leituras

- [README_VISUAL.md](./README_VISUAL.md) - Visão geral do Zennity visual
- [LOGIC_GRAPH_COMPLETE.md](./LOGIC_GRAPH_COMPLETE.md) - Nós essenciais de Logic Graph
- [BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md) - AI e comportamentos
- [UI_BUILDER_GUIDE.md](./UI_BUILDER_GUIDE.md) - Interface do usuário

---

**Zennity é 100% visual agora! Crie seus melhores jogos! 🚀✨**
