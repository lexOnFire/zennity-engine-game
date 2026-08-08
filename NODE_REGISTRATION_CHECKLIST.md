# 📋 Protocolo de Registro de Nós - OBRIGATÓRIO

## ⚠️ ANTES DE CRIAR UM NÓ, SIGA ESTE CHECKLIST:

### 1️⃣ Criar o Executor
- [ ] Arquivo: `engine/logic/runtime/nodes/CATEGORY_nodes.py`
- [ ] Usar `@registry.register_executor('node_id')`
- [ ] Retornar list[str] com status válido
- [ ] Testar compilação: `python -m py_compile`

### 2️⃣ Criar a Definição
- [ ] Arquivo: `engine/logic/node_definitions/CATEGORY_nodes.py`
- [ ] Usar `NodeDefinition(id="node_id", title="Título", ...)`
- [ ] ID deve BATER com executor ID
- [ ] Usar `pins_input` e `pins_output` (não `inputs`/`outputs`)
- [ ] Usar strings para tipos: "EXEC", "STRING", "FLOAT" (não PinType enums)
- [ ] Testar compilação: `python -m py_compile`

### 3️⃣ Registrar no Provider
- [ ] `engine/logic/provider.py` - adicionar import de runtime
- [ ] `engine/logic/provider.py` - adicionar import de definição
- [ ] `engine/logic/provider.py` - adicionar `manager.register(NodeDef)`
- [ ] **Verificação crítica**: contar registrations = contar definições

### 4️⃣ Verificação Final (OBRIGATÓRIA)
```bash
# Executar ANTES de commitar
python -c "
import os, re

# Contar definições
defs = len([f for f in os.listdir('engine/logic/node_definitions') 
            if f.endswith('.py') and f != '__init__.py'])

# Contar registrations no provider  
with open('engine/logic/provider.py') as f:
    regs = len(re.findall(r'manager\.register', f.read()))

print(f'Definições: {defs} arquivos')
print(f'Registrations: {regs} nós')
print('OK!' if regs > 0 else 'ERRO!')
"
```

### 5️⃣ Teste no Editor
- [ ] Reabra a engine COMPLETAMENTE
- [ ] Procure pelo nó na categoria correta
- [ ] **SE NÃO APARECER = ERRO CRÍTICO**

---

## 🔴 SE UM NÓ NÃO APARECE:

1. **Verificar erro de importação**: `python -m py_compile engine/logic/provider.py`
2. **Verificar se está registrado**: grep `node_id` `engine/logic/provider.py`
3. **Verificar se ID bate**: executor ID == definição ID == no título
4. **Verificar se tem __node_definition__**: `grep __node_definition__` na definição

---

## 📊 TABELA DE VERIFICAÇÃO - PRÓXIMA AUDITORIA

| Nó | Executor | Definição | Importado | Registrado | Aparece |
|----|----------|-----------|-----------|------------|---------|
| bind_ui_to_variable | ✓ | ✓ | ✓ | ✓ | ? |
| update_ui_binding | ✓ | ✓ | ✓ | ✓ | ? |

---

**NÃO COMMITE SEM VERIFICAR!**
