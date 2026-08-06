# Script de Validação: Node Database

Script Python para validar consistência do Logic Graph node database.

## Uso

```bash
python scripts/validate_node_database.py
```

## O que é validado

### 1. NODE_DEFINITIONS vs NODE_GROUPS

- ✓ Todos os nós em NODE_GROUPS existem em NODE_DEFINITIONS
- ✓ Categorias em NODE_GROUPS correspondem a NODE_DEFINITIONS
- ⚠ Nós não agrupados (fora de NODE_GROUPS)

### 2. NODE_DESCRIPTIONS

- ✓ Cobertura de documentação (quantos nós têm descrição)
- ⚠ Nós sem descrição (fará parte de CI/CD futuro)

## Saída

```
[OK]     - Verificação passou
[WARNING] - Aviso (geralmente não-crítico)
[ERROR]  - Erro que deve ser corrigido
[FAIL]   - Validação geral falhou
```

## Interpretando Erros

### "nós órfãos em NODE_GROUPS"

**Problema:** NODE_GROUPS referencia nós que não existem em NODE_DEFINITIONS.

**Solução:**
1. Remover nó de NODE_GROUPS (se foi deletado)
2. Ou adicionar nó a NODE_DEFINITIONS (se é novo)

Exemplo:
```python
# ANTES (erro): nó não existe
NODE_GROUPS = {
    "Movement": {
        "Patrulha": ["patrol_path"]  # ❌ não existe
    }
}

# DEPOIS (corrigido): remover ou criar o nó
NODE_GROUPS = {
    "Movement": {
        "Patrulha": ["patrol"]  # ✓ existe em NODE_DEFINITIONS
    }
}
```

### "incompatibilidades de categoria"

**Problema:** Um nó está em NODE_DEFINITIONS com categoria A, mas NODE_GROUPS o agrupa na categoria B.

**Solução:** Sincronizar a categoria (escolher uma como autoridade, geralmente NODE_DEFINITIONS).

Exemplo:
```python
# ANTES (erro):
# NODE_DEFINITIONS: set_position → category: "Position"
# NODE_GROUPS:      set_position → agrupa em "Movement"

# DEPOIS (corrigido): usar a mesma categoria
# Opção 1: Mover nó para categoria certa em NODE_GROUPS
NODE_GROUPS = {
    "Position": {
        "Posição": ["set_position"]  # ✓ Agora em "Position"
    }
}

# Opção 2: Alterar categoria em NODE_DEFINITIONS (menos recomendado)
NODE_DEFINITIONS["set_position"]["category"] = "Movement"
```

### "nós não agrupados"

**Problema:** Nó existe em NODE_DEFINITIONS mas não está em NODE_GROUPS.

**Aviso:** Não é crítico, mas o nó não aparecerá no modo TreeWidget agrupado.

**Solução (opcional):** Adicionar nó a NODE_GROUPS na subcategoria apropriada.

```python
# Novo nó foi adicionado em NODE_DEFINITIONS
NODE_DEFINITIONS["new_ui_button"] = {...}

# Adiciona a NODE_GROUPS
NODE_GROUPS = {
    "UI": {
        "Botões": ["new_ui_button"]  # ✓ Agora agrupado
    }
}
```

## Exit Codes

- `0` — Passou com sucesso
- `1` — Passou com avisos
- `2` — Falhou (há erros críticos)

Use em CI/CD:

```bash
# Script vai falhar se houver erros
python scripts/validate_node_database.py || exit 1
```

## Roadmap

### Curto Prazo

- [x] Script de validação básico
- [ ] Auto-fix para categorias simples
- [ ] Integração com CI/CD (GitHub Actions)

### Médio Prazo

- [ ] Sincronizar NODE_GROUPS automaticamente
- [ ] Validar nomes de nós (snake_case, etc)
- [ ] Verificar propriedades de nós (inputs, outputs, properties)

### Longo Prazo

- [ ] Gerar documentação de nós automaticamente
- [ ] Validar descrições (comprimento mínimo, etc)
- [ ] Detectar código morto (nós nunca usados)

## Exemplos de Uso

### Validar antes de commit

```bash
# Rápido check local
python scripts/validate_node_database.py

# Se houver erros, não commit
if [ $? -ne 0 ]; then
    echo "Fixe os erros antes de fazer commit"
    exit 1
fi
```

### Integração com Git Hook

```bash
# .git/hooks/pre-commit (executável)
#!/bin/bash
python scripts/validate_node_database.py
exit $?
```

### CI/CD (GitHub Actions)

```yaml
- name: Validate Node Database
  run: python scripts/validate_node_database.py
```

## Notas

- Script roda offline (sem internet)
- Lê NODE_DEFINITIONS, NODE_GROUPS, NODE_DESCRIPTIONS direto do código
- Não faz mudanças automaticamente (exceto futuro auto-fix)
- Útil para catching bugs durante refactoring de nós
