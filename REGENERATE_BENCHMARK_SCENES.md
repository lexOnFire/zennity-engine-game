# REGENERAR SCENES DO BENCHMARK

**Objetivo**: Criar todas as 5 cenas do benchmark usando o serializer canônico do editor.

**Status**: BLOCKER — Playtest impossível até cenas serem regeneradas.

---

## ESTRATÉGIA

Em vez de corrigir JSON manualmente, **usar o editor para criar e salvar cada cena corretamente**.

Isso garante:
- ✅ Schema canônico aplicado automaticamente
- ✅ Formato esperado pelo deserializer
- ✅ Sem erros de typo ou estrutura
- ✅ Roundtrip compatible (save → load → save)

---

## PASSO A PASSO

### SCENE 1: MainMenu

#### 1A: Criar nova scene

```
Zennity Editor
  → File
  → New Scene

```

#### 1B: Adicionar Camera

```
Hierarchy
  → Right-click
  → Add → Camera2D

```

Nome: `MainCamera`

Propriedades:
- Zoom: 1.0
- Viewport: 1280x720
- Clear Color: [0.1, 0.1, 0.1, 1.0]

#### 1C: Adicionar Canvas UI

```
Hierarchy
  → Right-click
  → Add → Canvas

```

Nome: `MenuUI`

Inspector:
- UI Asset: `Assets/UI/MainMenu.zui`
- Auto Load: true

#### 1D: Adicionar Logic Graph

```
Hierarchy
  → Select MenuUI (Canvas)
  → Inspector
  → Add Component
  → Logic Graph

```

Select: `Assets/Logic/MainMenuLogic.zlogic`

#### 1E: Adicionar Project Variables

```
Editor Menu
  → Tools / Window
  → Project Variables Panel

```

Adicionar:
```
coins: 0
score: 0
has_key: false
health: 100
current_level: 1
```

#### 1F: Salvar Scene

```
File
  → Save Scene As
  → Assets/Scenes/MainMenu.zscene

```

**Expected**: Editor saves with canonical format_version, scene_name, etc.

---

### SCENE 2: Level1

#### 2A: Criar nova scene

```
File → New Scene

```

#### 2B: Adicionar Player

```
Hierarchy
  → Right-click
  → Add → Prefab
  → Select: Assets/Prefabs/Player.zprfb

```

Position: [0, 0]

#### 2C: Adicionar Enemies (3x)

```
Hierarchy
  → Right-click
  → Add → Prefab
  → Select: Assets/Prefabs/Enemy.zprfb

```

Posições:
- Enemy 1: [300, 0]
- Enemy 2: [200, 150]
- Enemy 3: [400, -150]

#### 2D: Adicionar Coins (5x)

```
Hierarchy
  → Right-click
  → Add → Prefab
  → Select: Assets/Prefabs/Coin.zprfb

```

Posições (espalhadas na arena):
- Coin 1: [100, -50]
- Coin 2: [-100, 50]
- Coin 3: [150, 100]
- Coin 4: [-150, -100]
- Coin 5: [50, 0]

#### 2E: Adicionar Key

```
Hierarchy
  → Right-click
  → Add → Prefab
  → Select: Assets/Prefabs/Key.zprfb

```

Posição: [-200, 100]

#### 2F: Adicionar Guard

```
Hierarchy
  → Right-click
  → Add → Prefab
  → Select: Assets/Prefabs/Guard.zprfb

```

Posição: [600, 0]

#### 2G: Adicionar Door

```
Hierarchy
  → Right-click
  → Add → Prefab
  → Select: Assets/Prefabs/Door.zprfb

```

Posição: [650, 0]

#### 2H: Adicionar LevelExit Trigger

```
Hierarchy
  → Right-click
  → Add → GameObject
  → Name: LevelExit

```

Adicionar componente:
- BoxCollider2D (trigger)
- Posição: [700, 0]
- Size: [50, 50]

Adicionar Logic Graph:
- `Assets/Logic/LevelExitLogic.zlogic`

#### 2I: Adicionar Camera e HUD

Camera:
```
Hierarchy
  → Add → Camera2D
  → Follow Target: Player
  → Smooth Follow: true
  → Follow Speed: 5.0
```

HUD:
```
Hierarchy
  → Add → Canvas
  → UI Asset: Assets/UI/HUD.zui
```

#### 2J: Adicionar Walls (4x)

```
Hierarchy
  → Add → GameObject
  → Name: WallLeft
  → Add BoxCollider2D
  → Position: [-20, 0], Size: [2, 30]

Repeat para:
  → WallRight: [20, 0]
  → WallTop: [0, -15]
  → WallBottom: [0, 15]
```

#### 2K: Salvar Scene

```
File → Save Scene As
  → Assets/Scenes/Level1.zscene
```

---

### SCENE 3: Level2

#### 3A-3J: Repetir como Level1, MAS:

Substituir Enemies (3x) **POR**:
```
Add → Prefab → Boss.zprfb
Position: [300, 0]
```

**Não adicionar** Coins, Key, Guard, Door, LevelExit (apenas arena simples).

Manter:
- Player
- Camera (com follow)
- HUD
- Walls (4x)

#### 3K: Salvar Scene

```
File → Save Scene As
  → Assets/Scenes/Level2.zscene
```

---

### SCENE 4: GameOver

#### 4A: Criar nova scene

```
File → New Scene
```

#### 4B: Adicionar Camera

```
Add → Camera2D
Clear Color: [0.4, 0.1, 0.1, 1.0]  (dark red)
```

#### 4C: Adicionar UI

```
Add → Canvas
UI Asset: Assets/UI/GameOver.zui
Add Logic Graph: Assets/Logic/GameOverLogic.zlogic
```

#### 4D: Salvar Scene

```
File → Save Scene As
  → Assets/Scenes/GameOver.zscene
```

---

### SCENE 5: Victory

#### 5A: Criar nova scene

```
File → New Scene
```

#### 5B: Adicionar Camera

```
Add → Camera2D
Clear Color: [0.1, 0.05, 0.2, 1.0]  (dark purple)
```

#### 5C: Adicionar UI

```
Add → Canvas
UI Asset: Assets/UI/Victory.zui
Add Logic Graph: Assets/Logic/VictoryLogic.zlogic
```

#### 5D: Salvar Scene

```
File → Save Scene As
  → Assets/Scenes/Victory.zscene
```

---

## VALIDAÇÃO PÓS-REGENERAÇÃO

### 1. Verificar Schema Canônico

Para cada `.zscene`:

```bash
cat Assets/Scenes/MainMenu.zscene | jq 'keys'
```

Expected output:
```json
[
  "format_version",
  "scene_name",
  "engine_version",
  "objects"
]
```

### 2. Verificar format_version

```bash
cat Assets/Scenes/MainMenu.zscene | jq '.format_version'
```

Expected: `2`

### 3. Verificar scene_name

```bash
cat Assets/Scenes/MainMenu.zscene | jq '.scene_name'
```

Expected: `"Main Menu"` (ou similar)

### 4. Verificar Transform Structure

```bash
cat Assets/Scenes/Level1.zscene | jq '.objects[0].transform'
```

Expected:
```json
{
  "position": [x, y, z],
  "rotation": [x, y, z],
  "rz": 0.0,
  "scale": [x, y, z]
}
```

### 5. Abrir cada Scene no Editor

```
Asset Browser
  → Assets/Scenes
  → Double-click MainMenu.zscene

Expected:
✅ Scene carrega
✅ Hierarchy se popula
✅ Viewport atualiza
✅ Sem erros no console
```

Repetir para:
- Level1.zscene
- Level2.zscene
- GameOver.zscene
- Victory.zscene

### 6. Testar Roundtrip

```
Load MainMenu.zscene (deve abrir)
  → File → Save Scene
  → Close
  → Reopen MainMenu.zscene

Expected:
✅ Abre novamente sem problema
✅ Sem dados perdidos
```

---

## CHECKLIST FINAL

### MainMenu
- [ ] Cena criada no editor
- [ ] Camera adicionada
- [ ] Canvas + UI Asset adicionada
- [ ] Logic Graph adicionada
- [ ] Project Variables definidas
- [ ] Salvo como MainMenu.zscene
- [ ] Abre no editor
- [ ] Schema canônico verificado

### Level1
- [ ] Player prefab adicionado
- [ ] 3x Enemies adicionados (posições corretas)
- [ ] 5x Coins adicionadas (espalhadas)
- [ ] Key adicionada ([-200, 100])
- [ ] Guard adicionado ([600, 0])
- [ ] Door adicionada ([650, 0])
- [ ] LevelExit trigger adicionado ([700, 0])
- [ ] Camera com follow adicionada
- [ ] HUD Canvas adicionada
- [ ] 4x Walls adicionadas
- [ ] Salvo como Level1.zscene
- [ ] Abre no editor

### Level2
- [ ] Player prefab adicionado
- [ ] Boss prefab adicionado ([300, 0])
- [ ] Camera com follow adicionada
- [ ] HUD Canvas adicionada
- [ ] 4x Walls adicionadas
- [ ] Salvo como Level2.zscene
- [ ] Abre no editor

### GameOver
- [ ] Camera adicionada (cor vermelha)
- [ ] Canvas + GameOver UI adicionada
- [ ] GameOverLogic adicionada
- [ ] Salvo como GameOver.zscene
- [ ] Abre no editor

### Victory
- [ ] Camera adicionada (cor roxa)
- [ ] Canvas + Victory UI adicionada
- [ ] VictoryLogic adicionada
- [ ] Salvo como Victory.zscene
- [ ] Abre no editor

---

## PRÓXIMO PASSO

Quando todas as 5 cenas abrirem no editor:

1. ✅ Commit das scenes regeneradas
2. ✅ Reabrir testes para validar schema
3. ✅ Fechar BUG-8A-001B
4. ✅ Prosseguir com PLAYTEST MANUAL

---

## ESTIMATIVA

**Tempo esperado**: 30-45 minutos (criação manual + validação)

Não é automatizável porque requer UI interaction no editor.
