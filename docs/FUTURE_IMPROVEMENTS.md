# Melhorias Futuras - Roadmap de Componentes

Documento que registra sugestões e melhorias planejadas para o sistema de componentes de alto nível.

---

## 🎯 Melhorias de Curto Prazo (Próximas 2-4 semanas)

### 1. Presets Visuais no Inspector para UIBinder

**Problema Atual:**
- Usuário precisa digitar manualmente `source_path` como string
- Fácil fazer erros de digitação ("player.healt" vs "player.health")
- Sem autocomplete visual

**Solução Proposta:**
- Adicionar **dropdown interativo** no Inspector
- Quando clica em `source_path`, mostra tree de objetos disponíveis
- Seleciona via interface gráfica, gera path automaticamente
- Exemplo: `Player → health` gera `"player.health"`

**Benefício:**
- Zero erros de digitação
- Mais intuitivo para iniciantes
- Visual discovery of available properties

**Arquivo a Modificar:**
- `editor/inspector_plugins/ui_binder_plugin.py` (novo)

**Esforço Estimado:** 3-4 horas

---

### 2. Visualizador de Parâmetros do AnimationController

**Problema Atual:**
- Parâmetros são invisíveis durante Play Mode
- Difícil debugar transições que não acontecem
- Não sabe se parâmetro foi atualizado corretamente

**Solução Proposta:**
- Mini-aba no Inspector durante Play Mode
- Mostra todos os parâmetros em tempo real:
  ```
  AnimationController (Play Mode)
  ┌─ Parâmetros ─────────────────┐
  │ speed: 1.5 (float)            │
  │ is_jumping: true (bool)       │
  │ combo_count: 3 (int)          │
  │ current_state: run            │
  └───────────────────────────────┘
  ```
- Permite editar parâmetros in-place (para teste)
- Mostra estado atual e próximas transições possíveis

**Benefício:**
- Debugging muito mais fácil
- Entender fluxo de transições
- Testar comportamentos sem recompilar

**Arquivo a Modificar:**
- `editor/animation_controller_inspector_plugin.py` (novo)

**Esforço Estimado:** 4-5 horas

---

### 3. Gerador de Diálogos Inteligente

**Problema Atual:**
- Arquivo `.zdialogue` é manual e complexo (JSON puro)
- Não há ferramenta visual para criar diálogos
- Usuários precisam entender estrutura de nós e edges

**Solução Proposta:**
- **Dialog Builder Visual** (ferramenta no editor)
- Permite:
  - Arrastar nós de fala na tela
  - Conectar com clique
  - Editar texto inline
  - Preview do fluxo
  - Exportar para `.zdialogue`
- **Importador CSV/JSON** para `DialogueManager`:
  ```csv
  speaker,text,next_node,condition
  Merchant,Olá!,choices,
  Merchant,Qual você quer?,option_1,has_quest=true
  Merchant,Você precisa fazer a quest.,intro,has_quest=false
  ```

**Benefício:**
- Non-linear story creation
- Documentação visual de diálogos
- Rápido prototipar conversas

**Arquivo a Criar:**
- `editor/dialogue_builder/dialog_builder_dock.py` (novo)
- `editor/dialogue_builder/csv_importer.py` (novo)

**Esforço Estimado:** 6-8 horas

---

## 📈 Melhorias de Médio Prazo (1-2 meses)

### 4. Prefabs de Padrões Comuns

Criar prefabs prontos para:
- **Player com Sistema de Vida**
  - Player GameObject pré-configurado
  - UIBinder → Health Bar
  - MaterialPropertyAnimator → Flash ao tomar dano
  - AnimationController → idle/run/jump/hurt/death

- **NPC Interativo**
  - NPC GameObject
  - DialogueManager pré-configurado
  - Trigger para começar diálogo
  - Animations sincronizadas

- **UI Completa de Game**
  - Health Bar + Mana Bar + Stamina
  - Score Display
  - Timer
  - Status Effects
  Tudo com UIBinder pronto

**Arquivo a Criar:**
- `examples/Prefabs/PlayerCharacter.prefab`
- `examples/Prefabs/NPCCharacter.prefab`
- `examples/Prefabs/GameHUD.prefab`

---

### 5. Macros do Logic Graph para Componentes

Agrupar nós comuns em macros:

```
Macro: "Animar Dano"
├─ Animate Color (branco)
├─ Wait (0.1s)
└─ Restore Color
```

```
Macro: "Iniciar Diálogo Completo"
├─ Start Dialogue
├─ Wait por input
├─ Handle Choice
└─ Continue
```

Resultado: Logic Graph mais limpo, reutilizável

---

### 6. Sistema de Eventos Simplificado

Adicionar `EventBus` simples para componentes se comunicarem:

```python
# Disparar evento
EventBus.emit("player_took_damage", {"amount": 10})

# Escutar
manager.on_event("player_took_damage", lambda data: flash())
```

Benefício: Componentes desacoplados, fácil integração

---

## 🔮 Melhorias de Longo Prazo (2-3 meses)

### 7. UI Binder Pro (Vinculação Bidirecional)

Atualmente é unidirecional (dados → UI).

Fazer bidirecional:
- Usuário edita valor na UI → atualiza dados
- Útil para: RPG inventory, upgrade menus, settings

```python
ui_binder = UIBinder(
    source_path="player.health",
    format_string="{value}",
    bidirectional=True,  # Novo
    on_user_change=lambda new_val: player.heal(new_val)
)
```

---

### 8. Animation State Machine Avançada

Adicionar suporte para:
- **Sub-states** (hierarchical FSM)
- **Layered animations** (upper body vs lower body)
- **Animation blending** (smooth transitions)
- **Animation events** (callbacks em frames específicos)

---

### 9. Dialogue Branching Avançado

Adicionar suporte para:
- **Dynamic dialogue** (gera opções baseado em flags)
- **Dialogue priorities** (escolhe automaticamente a melhor opção)
- **Conversation memory** (lembra escolhas passadas)
- **NPC reactions** (diferentes respostas baseado em relacionamento)

---

### 10. Performance Profiling para Componentes

Adicionar ferramenta para:
- Medir tempo gasto em UIBinder updates
- Verificar quantas animações estão ativas
- Detectar memory leaks em diálogos

```
Performance Profiler
├─ UIBinder: 0.5ms (12 updates)
├─ AnimationController: 0.2ms (24 updates)
├─ MaterialPropertyAnimator: 0.3ms (8 animations)
└─ DialogueManager: 0.1ms (idle)
```

---

## 📋 Checklist para Implementação

### Curto Prazo
- [ ] UIBinder Inspector Preset
- [ ] AnimationController Parameter Viewer
- [ ] Dialogue Generator/Importer

### Médio Prazo
- [ ] Character Prefabs
- [ ] Logic Graph Macros
- [ ] EventBus System

### Longo Prazo
- [ ] UIBinder Bidirectional
- [ ] Advanced Animation FSM
- [ ] Advanced Dialogue System
- [ ] Performance Profiling

---

## 🎓 Como Contribuir

Se você quer trabalhar em uma dessas melhorias:

1. Escolha uma melhoria acima
2. Crie uma branch: `feature/improvement-name`
3. Implemente seguindo padrões existentes
4. Adicione testes
5. Crie PR com documentação

Todas essas ideias são **bem-vindas**! 🚀

---

## 📞 Feedback

Se você tem ideias adicionais ou sugestões, abra uma issue com label `enhancement`!

**Criado em:** 2026-08-06
**Última atualização:** 2026-08-06
