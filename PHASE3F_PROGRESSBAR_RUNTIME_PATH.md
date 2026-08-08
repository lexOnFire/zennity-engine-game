# PHASE 3F: RASTREAMENTO REAL DA PROGRESSBAR

**Data**: 2026-08-08  
**Status**: ✅ COMPLETADO  
**Objetivo**: Mapear caminho completo da ProgressBar desde UI Builder até Logic Graph

---

## 1. UI BUILDER (EDITOR)

### Classe: UIBuilderDock
- **Arquivo**: `editor/ui_builder/ui_builder_dock.py`
- **Localização**: Linhas 135-517

### Criação de ProgressBar
```python
# Linha 160
("ProgressBar", lambda: self.add_widget(UIProgressBar(self._next_name("ProgressBar"))))
```

**Método**: `add_widget(widget: UIWidget)`
- Procura pai válido (UICanvas, UIPanel, etc)
- Define posição relativa (x += 24, y += 24)
- Chama `parent.add_child(widget)`

### Classe de UI Runtime
- **Classe**: `UIProgressBar`
- **Arquivo**: `engine/ui/runtime/widgets.py`
- **Localização**: Linhas 121-130

```python
class UIProgressBar(UIWidget):
    def __init__(self, name: str = "ProgressBar") -> None:
        super().__init__(name)
        self.value: float = 50.0
        self.max_value: float = 100.0
        self.fill_color: str = "#2ECC71"
        self.bg_color: str = "#1C2330"
        self.border_color: str = "#96AAC8"
```

### Propriedades Editáveis no Inspector
- **Nome**: `txt_name` (QLineEdit)
- **Posição**: `spin_x`, `spin_y` (QSpinBox)
- **Tamanho**: `spin_width`, `spin_height` (QSpinBox)
- **Valor**: `spin_value` (QSpinBox)
- **Valor Max**: `spin_max_value` (QSpinBox)
- **Visibilidade**: `check_visible` (QCheckBox)

**Método de aplicação**: `apply_inspector()` (linhas 387-412)

---

## 2. SERIALIZAÇÃO

### Formato .zui (JSON)

```json
{
  "format": "zennity.ui",
  "version": 1,
  "canvas": {
    "name": "MainCanvas",
    "type": "UICanvas",
    "x": 0.0,
    "y": 0.0,
    "width": 1920.0,
    "height": 1080.0,
    "visible": true,
    "render_mode": "Screen Space",
    "children": [
      {
        "name": "HealthBar",
        "type": "UIProgressBar",
        "x": 40.0,
        "y": 40.0,
        "width": 180.0,
        "height": 20.0,
        "visible": true,
        "value": 75.0,
        "max_value": 100.0,
        "fill_color": "#2ECC71",
        "bg_color": "#1C2330",
        "border_color": "#96AAC8",
        "children": []
      }
    ]
  }
}
```

### Método de Serialização
- **Classe**: `UIWidget` (base)
- **Método**: `serialize()` (linhas 28-45 em engine/ui/runtime/widgets.py)

```python
def serialize(self) -> dict:
    data = {
        "name": self.name,
        "type": getattr(self, "widget_type", self.__class__.__name__),
        "x": self.x,
        "y": self.y,
        "width": self.width,
        "height": self.height,
        "visible": self.visible,
        "children": [c.serialize() for c in self.children],
    }
    # Atributos especiais por widget type
    for key in ("bg_color", "text", "hover_color", "font_size", "text_color",
                "texture_path", "scroll_y", "placeholder", "layout_mode", "render_mode",
                "fill_color", "border_color", "value", "max_value"):
        if hasattr(self, key):
            data[key] = getattr(self, key)
    return data
```

### Salvamento
- **Arquivo**: `editor/ui_builder/ui_builder_dock.py` linhas 480-504
- **Função**: `save()`
- **Path**: Padrão `Assets/UI/*.zui`
- **Formato**: JSON com `ensure_ascii=False, indent=2`
- **Estratégia**: Write to .tmp, rename to .zui (atômico)

---

## 3. CAMINHOS DE PERSISTÊNCIA

### Onde o .zui é Armazenado
- **Padrão**: `Assets/UI/*.zui` (escolhido pelo usuário)
- **Cache Last**: `.zennity/last_ui.json`

### Recuperação
```python
def load_document(self, path: str | Path) -> bool:
    source = Path(path).resolve()
    data = json.loads(source.read_text(encoding="utf-8"))
    canvas = widget_from_dict(data.get("canvas", data))
```

---

## 4. LOAD / HYDRATION (PLAY MODE)

### Arquivo Principal
- **Arquivo**: `engine/ui/runtime/widgets.py`
- **Função**: `widget_from_dict(data: dict[str, Any]) -> UIWidget`
- **Linhas**: 143-157

```python
def widget_from_dict(data: dict[str, Any]) -> UIWidget:
    """Rebuild a runtime widget hierarchy from serialized UI data."""
    widget_class = WIDGET_TYPES.get(str(data.get("type", "")), UIWidget)
    widget = widget_class(str(data.get("name", widget_class.__name__)))
    for key in ("x", "y", "width", "height", "visible", "bg_color", "text",
                "hover_color", "font_size", "text_color", "texture_path",
                "scroll_y", "placeholder", "layout_mode", "render_mode",
                "fill_color", "border_color", "value", "max_value"):
        if key in data and hasattr(widget, key):
            setattr(widget, key, data[key])
    for child_data in data.get("children", []):
        if isinstance(child_data, dict):
            widget.add_child(widget_from_dict(child_data))
    return widget
```

### Mapa de Tipos
```python
WIDGET_TYPES = {
    "RuntimeUICanvas": RuntimeUICanvas,
    "UICanvas": RuntimeUICanvas,
    "UIPanel": UIPanel,
    "UIButton": UIButton,
    "UILabel": UILabel,
    "RuntimeUIImage": RuntimeUIImage,
    "UIImage": RuntimeUIImage,
    "UIScrollView": UIScrollView,
    "UIInput": UIInput,
    "UIContainer": UIContainer,
    "UIProgressBar": UIProgressBar,
}
```

---

## 5. REPRESENTAÇÃO EM PLAY MODE

### Duas Implementações Distintas

#### A. UIProgressBar (Editor Runtime - runtime/widgets.py)
```python
class UIProgressBar(UIWidget):
    widget_type = "UIProgressBar"
    value: float = 50.0
    max_value: float = 100.0
    fill_color: str = "#2ECC71"
    bg_color: str = "#1C2330"
    border_color: str = "#96AAC8"
```

**Usado por**:
- UI Builder do editor (editor/ui_builder/ui_builder_dock.py)
- Renderizador do viewport isolado (editor/runtime/native_ui.py)

**Limitações**:
- Não é persistido em .zscene
- Não é componente do GameObject
- Apenas para edição/preview

#### B. ProgressBarComponent (Runtime Component - runtime_components.py)
```python
class ProgressBarComponent(RuntimeUIElement):
    component_type = "ProgressBar"
    value: float = 100.0
    max_value: float = 100.0
    fill_color: tuple[int, int, int] = (46, 204, 113)
    bg_color: tuple[int, int, int] = (28, 35, 48)
    
    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(self.max_value, float(value)))
    
    def serialize_properties(self) -> dict[str, Any]: ...
    def deserialize_properties(self, data: dict[str, Any]) -> None: ...
```

**Arquivo**: `engine/ui/runtime_components.py`  
**Localização**: Linhas 550-601

**Usado por**:
- Scenes (.zscene) — formato de persistência oficial
- Play Mode — componente de GameObject
- Build/Export — incluído no runtime

---

## 6. FLUXO CONCRETO: UI BUILDER → PLAY MODE

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EDITOR (UIBuilderDock)                                   │
│   Create ProgressBar                                        │
│   UIProgressBar(name="HealthBar")                           │
│   value=75, max_value=100                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SERIALIZE (.zui JSON)                                    │
│   widget.serialize()                                        │
│   → canvas.serialize() → children[].serialize()            │
│   {                                                         │
│     "name": "HealthBar",                                   │
│     "type": "UIProgressBar",                               │
│     "value": 75.0,                                         │
│     "max_value": 100.0,                                    │
│     ...                                                     │
│   }                                                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SAVE (Assets/UI/*.zui)                                   │
│   document_data() → json.dumps() → file write              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. LOAD (Play Mode)                                         │
│   scene_loader.load() → json.load(*.zui)                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. HYDRATE (widget_from_dict)                              │
│   Reconstrói hierarquia UIProgressBar                      │
│   (em memória apenas — não persistido em .zscene)         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. SCENE CONVERSION (native_ui.py)                         │
│   scene_item_to_ui() →  ui_to_scene_item()               │
│   UIProgressBar dict                                        │
│   → ProgressBarComponent serialization dict               │
│   → GameObject component                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. REGISTERED COMPONENT (game_object.components)           │
│   ProgressBarComponent                                      │
│   Attached to GameObject in Play Mode scene               │
│   value=75.0, max_value=100.0                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. LOGIC GRAPH ACCESS                                      │
│   get_progress_bar_value node                              │
│   _fetch_progress_bar_value()                              │
│   → Searches game._world, game.objects                    │
│   → Finds ProgressBarComponent                            │
│   → Returns value (75.0)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. CAMINHOS DE BUSCA EM PLAY MODE

### _fetch_progress_bar_value() — 4 Estratégias

**Arquivo**: `engine/logic/runtime/nodes/dynamic_ui_nodes.py`  
**Linhas**: 265-341

#### Estratégia 1: Árvores de Canvas (.zui) em game._world
```python
for wdict in world_dicts:  # game._world, game.objects
    for obj_name, obj in wdict.items():
        ui = obj.get("ui")  # UI dict
        if isinstance(ui, dict):
            overrides = ui.get("_widget_overrides", {})
            # Procura widget por nome
            matched_widget = _find_ui_widget_in_tree(ui, name)
            if "value" in matched_widget:
                return float(matched_widget["value"])
```

#### Estratégia 2: game.find() (objeto direto)
```python
if hasattr(game, "find"):
    target = game.find(name)  # Procura por tag/nome
    if hasattr(target, "value"):
        return float(target.value)
```

#### Estratégia 3: Componentes do GameObject
```python
comps = obj.get("components", [])
for comp in comps:
    if str(comp.get("type", "")).lower() in {"progressbar", "progress_bar"}:
        props = comp.get("properties", {})
        if "value" in props:
            return float(props["value"])
```

#### Estratégia 4: Blackboard/Runtime Variables
```python
if hasattr(runtime, "variables"):
    for key in (name, f"{name}.value", "value", "comida.value"):
        if key in runtime.variables:
            return float(runtime.variables[key])
```

---

## 8. PROBLEMA: DUPLICAÇÃO E INCONSISTÊNCIA

### Problema 1: Duas Hierarquias de Widget
```
UIProgressBar (engine.ui.runtime)
  └─ Só para editor/preview
  └─ Não serializado em .zscene
  └─ Sem ciclo de vida de Play Mode

ProgressBarComponent (engine.ui.runtime_components)
  └─ Componente oficial de GameObject
  └─ Serializado em .zscene
  └─ Tem ciclo de vida completo
```

**Impacto**: UIProgressBar é "decorativo" — não afeta Play Mode de verdade.

### Problema 2: Quatro Camadas de Busca
```
1. UI dict em game._world["..."].get("ui")
2. game.find(widget_name)
3. GameObject.components[].type == "ProgressBar"
4. runtime.variables[widget_name]
```

**Impacto**: 
- Lógica difícil de rastrear
- Fallbacks silenciosos
- Pode encontrar objeto errado
- "Funciona por acaso"

### Problema 3: Fonte de Verdade Incerta
- `.zui` → UIProgressBar (editor)
- `.zscene` → ProgressBarComponent (game)
- Runtime → Qual versão está sendo usada?

**Impacto**: 
- Alterações podem não sincronizar
- Debugging confuso
- get_progress_bar_value retorna valor "correto por acaso"

### Problema 4: Sem Type Safety
```python
getattr(child, property_name)  # arbitrary property access
```

Não há validação de qual propriedade existe em qual tipo de widget.

---

## 9. ARQUIVO ESTRUTURA DO COMPONENTE

### ProgressBarComponent Serialization

```json
{
  "type": "ProgressBar",
  "enabled": true,
  "properties": {
    "x": 40.0,
    "y": 40.0,
    "width": 180.0,
    "height": 18.0,
    "visible": true,
    "z_order": 0,
    "widget_name": "HealthBar",
    "value": 75.0,
    "max_value": 100.0,
    "fill_color": [46, 204, 113],
    "bg_color": [28, 35, 48],
    "anchor": "",
    "margin_x": 16.0,
    "margin_y": 16.0
  }
}
```

### Classe
```python
class ProgressBarComponent(RuntimeUIElement):
    component_type = "ProgressBar"
    
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 180.0,
        height: float = 18.0,
        value: float = 100.0,
        max_value: float = 100.0,
        fill_color: tuple[int, int, int] = (46, 204, 113),
        bg_color: tuple[int, int, int] = (28, 35, 48),
        visible: bool = True,
        z_order: int = 0,
    ) -> None: ...
```

---

## 10. DESSERIALIZAÇÃO (deserialize_properties)

```python
def deserialize_properties(self, data: dict[str, Any]) -> None:
    super().deserialize_properties(data)
    self.value = float(data.get("value", self.value))
    self.max_value = max(0.0001, float(data.get("max_value", self.max_value)))
    self.fill_color = tuple(data.get("fill_color", self.fill_color))
    self.bg_color = tuple(data.get("bg_color", self.bg_color))
```

---

## 11. LIFECYCLE EM PLAY MODE

```
1. Scene loads from .zscene
   └─ ComponentRegistry.resolve("ProgressBar")
   └─ ComponentRegistry.create("ProgressBar", **properties)

2. ProgressBarComponent instantiated
   └─ deserialize_properties() called
   └─ value = 75.0, max_value = 100.0

3. on_runtime_start() called
   └─ _owner_is_pure_ui() check
   └─ If pure UI: game_object.runtime_hidden = True

4. Render system draws (editor/runtime/native_ui.py)
   └─ NativeUIRenderer draws component
   └─ Fill ratio = value / max_value

5. Logic Graph queries
   └─ evaluate_get_progress_bar_value()
   └─ _fetch_progress_bar_value() searches
   └─ Returns value or None
```

---

## 12. LOOKUP MECHANISM

### widget_name (Desambiguação)

Problema: GameObject pode ter múltiplos ProgressBarComponents
```python
# Sem widget_name:
get_component(ProgressBarComponent)  # Sempre retorna PRIMEIRO

# Com widget_name:
for comp in game_object.components:
    if isinstance(comp, ProgressBarComponent) and comp.widget_name == "HealthBar":
        return comp.value
```

**Campo**: `RuntimeUIElement.widget_name` (string)  
**Setado em**: UI Builder Inspector ou programaticamente  
**Usado por**: `_find_widget()` em ui_nodes.py

---

## 13. TEMPO DE VIDA

### UIProgressBar (UIBuilder)
- **Criação**: Quando usuário clica "ProgressBar" no toolbar
- **Duração**: While editor is open
- **Destruição**: When document closed or widget deleted
- **Persistência**: .zui file only

### ProgressBarComponent (Play Mode)
- **Criação**: Scene load / deserialization
- **Duração**: Until scene unload or object destruction
- **Destruição**: GameObject destroyed or component removed
- **Persistência**: .zscene file

---

## 14. DUPLICAÇÕES ENCONTRADAS

### Duplicação 1: Widget Class Hierarchy
```
UIProgressBar (editor, runtime/widgets.py)
├─ Used by: UIBuilder, native_ui preview
├─ NOT persisted in .zscene
└─ Different properties (string colors)

ProgressBarComponent (engine, runtime_components.py)
├─ Used by: Play Mode, Scene persistence
├─ Persisted in .zscene
└─ Different properties (tuple colors)
```

**Resultado**: `UIProgressBar.fill_color = "#2ECC71"` mas `ProgressBarComponent.fill_color = (46, 204, 113)`

### Duplicação 2: Serialization Formats
```
.zui format (UIBuilder):
{
  "type": "UIProgressBar",
  "fill_color": "#2ECC71",
  "value": 75.0
}

.zscene format (Scene):
{
  "type": "ProgressBar",
  "properties": {
    "fill_color": [46, 204, 113],
    "value": 75.0
  }
}
```

### Duplicação 3: Lookup Logic
```
A. _fetch_progress_bar_value() (dynamic_ui_nodes.py)
   - 4 fallback strategies
   - Complex tree walking
   - Silent failures

B. _find_widget() (ui_nodes.py - impure)
   - Gets component directly
   - Simple, but no fallbacks

C. set_ui_progress_bar (ui_nodes.py)
   - Another implementation
```

### Duplicação 4: Property Names
```
UIProgressBar:
  .value
  .max_value
  .fill_color (string)
  .bg_color (string)
  .border_color (string)

ProgressBarComponent:
  .value
  .max_value
  .fill_color (tuple)
  .bg_color (tuple)
  No border_color
```

---

## 15. PROBLEMAS ENCONTRADOS

### Problema A: Silent Type Conversion
```python
# In native_ui.py:
"fill_color": [46, 204, 113],

# In UIProgressBar:
self.fill_color: str = "#2ECC71"

# Conversion happens where? No explicit adapter.
```

### Problema B: Bidirectional Sync Not Implemented
```
UIBuilder edits HealthBar
  → Saves to Assets/UI/hud.zui
  
But .zscene still has old version
  → Play Mode uses stale values
```

### Problema C: widget_name Not Always Set
```python
# UIProgressBar doesn't have widget_name field
class UIProgressBar(UIWidget):
    def __init__(self, name: str = "ProgressBar") -> None:
        super().__init__(name)
        # NO: self.widget_name = ...
```

**But ProgressBarComponent requires it**:
```python
class RuntimeUIElement(Component):
    self.widget_name = str(widget_name)  # REQUIRED for disambiguation
```

### Problema D: Conversion via native_ui.py
```
UIProgressBar (editor)
  → .zui (saved)
  → native_ui._flatten_zui_widget()
  → Snapshot dict
  → ui_to_scene_item()
  → ProgressBarComponent serialization
  → .zscene (saved)
```

**Missing**: Automatic .zui → .zscene sync

### Problema E: _fetch_progress_bar_value() Heuristics
```python
# Check 4 different locations, in order:
# 1. game._world["..."]["ui"] tree
# 2. game.find(name)
# 3. GameObject.components
# 4. runtime.variables

# What if object is in location 1 but named differently in location 3?
# What if two widgets exist with same name?
# Silent failure with None return.
```

---

## 16. ARQUITETURA RECOMENDADA

### Consolidação Proposta: UIRuntimeService

```python
class UIRuntimeService:
    """Única fonte de verdade para UI em Play Mode."""
    
    def resolve_widget(self, identifier: str) -> ProgressBarComponent | None:
        """Encontra widget por widget_name (ÚNICO lugar de busca)."""
        # Implementação determinística
        # Não heurística
        # Loga misses
        
    def get_property(self, identifier: str, property_name: str) -> Any:
        """Lê propriedade com type safety."""
        # Resolve widget
        # Valida property_name existe
        # Retorna typed value ou None
        
    def set_property(self, identifier: str, property_name: str, value: Any) -> bool:
        """Escreve propriedade com validação."""
        # Mesma lógica segura
```

### Adapters (se necessário)
```python
class WidgetAdapter:
    """Abstraction para diferentes representações de widget."""
    
    @property
    def value(self) -> float: ...
    
    @property
    def max_value(self) -> float: ...
    
    def set_value(self, v: float) -> None: ...
```

### Type Safety via Schema
```python
UI_SCHEMA = {
    "ProgressBar": {
        "value": (float, 0.0, 100.0),
        "max_value": (float, 1.0, 10000.0),
        "visible": bool,
        "fill_color": (tuple, int, int, int),
    }
}
```

---

## SUMMARY TABLE

| Item | Classe | Arquivo | Uso |
|------|--------|---------|-----|
| **Editor Widget** | UIProgressBar | engine/ui/runtime/widgets.py | UIBuilder preview |
| **Runtime Component** | ProgressBarComponent | engine/ui/runtime_components.py | Play Mode, .zscene |
| **Logic Node** | get_progress_bar_value | engine/logic/runtime/nodes/dynamic_ui_nodes.py | Pure data evaluator |
| **Serializer** | widget.serialize() | engine/ui/runtime/widgets.py | .zui export |
| **Deserializer** | widget_from_dict() | engine/ui/runtime/widgets.py | .zui load |
| **Converter** | native_ui functions | editor/runtime/native_ui.py | .zui ↔ .zscene |
| **Search Logic** | _fetch_progress_bar_value() | engine/logic/runtime/nodes/dynamic_ui_nodes.py | Play Mode lookup (HEURISTIC) |

---

## CONCLUSION

**ProgressBar percorre 3 sistemas distintos**:

1. **UIProgressBar** (editor runtime) — Apenas edição visual
2. **ProgressBarComponent** (engine component) — Representação real em Play Mode
3. **get_progress_bar_value node** (logic graph) — Busca heurística (problemática)

**Arquitetura atual funciona por acaso**:
- UIBuilder cria UIProgressBar
- native_ui converte para ProgressBarComponent
- _fetch_progress_bar_value() encontra via fallback
- Valor retornado é correto

**Mas sem**:
- Fonte de verdade clara
- Type safety
- Determinismo na busca
- Sincronização bidirecional

**Next Phase 3G**: UIRuntimeService consolidará tudo com APIs limpas e type-safe.
