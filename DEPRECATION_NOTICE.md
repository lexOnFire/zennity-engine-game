# ⚠️ Aviso de Descontinuação: Scripting em Python

**Data:** Agosto 2026  
**Status:** ❌ DESCONTINUADO

---

## 📌 Importantes

**Zennity é agora 100% VISUAL.** Código Python para criar lógica foi descontinuado.

### O que foi descontinuado:

- ❌ Criação de comportamento com `script_manager.py`
- ❌ Exemplos em código (`demos/`, `examples_*.py`)
- ❌ Scripts hardcoded (`scripts/`)
- ❌ Editor legado baseado em código

### O que continua funcionando:

- ✅ **Behavior Tree** (visual)
- ✅ **Logic Graph** (visual)
- ✅ **UI Builder** (visual)
- ✅ **Scene Editor** (visual)
- ✅ Runtime que executa arquivos visuais (`.zbehavior`, `.zlogic`, `.zui`, `.zscene`)

---

## 🎯 Migração de Projetos Antigos

### Se você tinha código em `script_manager.py`:

**Antes (❌ Não funciona mais):**
```python
class PlayerController(Script):
    def update(self):
        if input.is_pressed("space"):
            self.jump()
```

**Depois (✅ Novo sistema):**
1. Abra **Logic Graph**
2. Nó: `On Key Down` (SPACE)
3. Nó: `Jump` (Physics action)
4. Conecte → pronto!

---

## 📁 Arquivos Descontinuados

| Arquivo | Razão | Ação |
|---------|-------|------|
| `demos/` | Exemplos em código | Remover |
| `examples_*.py` | Exemplos em código | Remover |
| `scripts/` | Scripts hardcoded | Remover |
| `editor_legacy/` | Editor antigo | Remover |
| `editor/core/script_manager.py` | Gerenciador de scripts | Deprecado (keep for now) |

---

## 📚 Novo Fluxo de Trabalho

### Antes (Código):
```
Escrever Python → Compilar → Testar → Deploy
```

### Depois (Visual):
```
Editar no Editor → Play → Deploy
```

**Vantagens:**
- ✅ Nenhuma compilação necessária
- ✅ Feedback imediato (hot reload)
- ✅ Não precisa saber programação
- ✅ Colaboração mais fácil (arquivos `.zlogic` são JSON)

---

## 📖 Documentação

Leia os novos guias:

1. **[VISUAL_EDITOR_GUIDE.md](./VISUAL_EDITOR_GUIDE.md)** - Visão geral completa
2. **[BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md)** - Como criar comportamentos
3. **[UI_BUILDER_GUIDE.md](./UI_BUILDER_GUIDE.md)** - Como criar interfaces

---

## 🆘 Precisa de Ajuda?

Se você tinha um projeto baseado em código:

1. Abra um `.zscene` existente
2. Remova components que referenciam scripts
3. Crie equivalentes em Logic Graph ou Behavior Tree
4. Teste no Play mode

---

**Zennity: 100% Visual, Zero Código!** 🎮✨
