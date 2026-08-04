# 🗑️ DELETAR OBJETOS NO EDITOR VISUAL

## ✅ Como Deletar (3 Formas)

### Método 1: Tecla Delete (Recomendado)
```
1. Selecione um objeto na viewport ou hierarquia
2. Pressione "Delete" ou "Del" no teclado
3. Objeto é removido imediatamente
```

### Método 2: Menu de Contexto
```
1. Clique com BOTÃO DIREITO no objeto (hierarquia)
2. Selecione "Delete" ou "Remover"
3. Objeto é removido
```

### Método 3: Hierarquia (Tree Panel)
```
1. Selecione o objeto na árvore hierárquica (esquerda)
2. Pressione Delete
3. Objeto é removido
```

---

## ⚠️ Quando Delete NÃO Funciona

### ❌ Problema 1: Jogo está rodando
```
Você está em PLAY mode (play/pause)
→ Delete está desativado para evitar acidentes
→ Pressione "Stop" para voltar ao edit mode
→ Aí sim delete funciona
```

**Solução:**
```
[Stop] no editor para voltar ao modo EDIT
```

### ❌ Problema 2: Viewport não tem foco
```
Você clicou em outro painel (inspector, hierarchy, etc)
→ Delete pode ir para esse painel em vez de deletar o objeto
→ Clique na viewport para dar foco a ela
```

**Solução:**
```
1. Clique na viewport (área cinza com objetos)
2. Aí sim pressione Delete
```

### ❌ Problema 3: Objeto não está selecionado
```
Nenhum objeto está selecionado
→ Delete não tem nada para deletar
→ Clique no objeto para selecioná-lo
```

**Solução:**
```
1. Clique no objeto na viewport
2. (Deve ficar com borda branca/amarela)
3. Aí sim pressione Delete
```

### ❌ Problema 4: Viewport desconectada
```
A viewport não está respondendo aos comandos
→ Pode ser que a janela de viewport tenha travado
→ Feche e reabra
```

**Solução:**
```
1. Clique em "Editor" menu
2. Escolha "Reiniciar Viewport"
OU
1. Feche o editor completamente
2. Abra novamente
```

---

## 🎯 Checklist: Deletar com Sucesso

```
✅ Modo EDIT (não Play)?
   Se não: Clique [Stop]

✅ Objeto está selecionado?
   Se não: Clique nele na viewport

✅ Viewport tem foco (clicou nela)?
   Se não: Clique na viewport

✅ Objeto existe?
   Se não: Selecione outro objeto

→ AGORA sim: Pressione Delete
```

---

## 🔍 Como Saber se Funciona

### Antes (Objeto selecionado)
```
Viewport: objeto tem uma borda colorida (branca/amarela)
Hierarquia: objeto está destacado
Inspector: mostra propriedades do objeto
```

### Depois (Após pressionar Delete)
```
Viewport: objeto desapareceu
Hierarquia: objeto saiu da lista
Inspector: limpo (sem properties)
```

---

## 💡 Dicas Profissionais

### Dica 1: Atalho Rápido
```
Delete → Remove objeto selecionado
Ctrl+Z → Desfaz a deleção
```

### Dica 2: Deletar Vários
```
❌ Não há seleção múltipla
✅ Delete um por um:
   1. Selecione objeto A
   2. Pressione Delete
   3. Selecione objeto B
   4. Pressione Delete
   5. Etc...
```

### Dica 3: Restaurar Acidentalmente Deletado
```
❌ Deletou sem querer?
✅ Pressione Ctrl+Z (Undo) imediatamente
   (Funciona enquanto não fechar o editor)
```

### Dica 4: Limpar Cena Inteira
```
❌ Delete um por um é lento
✅ Use: File → New Scene
   Cria cena vazia e limpa
```

---

## 🖱️ Tipos de Delete

### Delete via Keyboard
```
✅ Delete         (tecla Delete)
✅ Backspace      (tecla Backspace)
❌ Remove         (NÃO funciona)
❌ Fn+Delete      (alguns teclados)
```

### Delete na Hierarquia
```
✅ Clique direito → Delete
✅ Selecione + Delete
✅ Selecione + Backspace
```

### Delete na Viewport
```
✅ Selecione objeto
✅ Pressione Delete
✅ Objeto desaparece
```

---

## ❓ FAQ

### P: Por que Delete não funciona?
A: Verifique se:
- Modo é EDIT (não Play)
- Objeto está selecionado
- Viewport tem foco
- Jogo não está rodando

### P: Posso deletar enquanto está rodando?
A: Não. Delete é desativado em Play mode para segurança.
Solução: Pressione Stop, aí delete.

### P: Como deletar sem perder o histórico?
A: Delete automático faz undo (Ctrl+Z).
Nenhuma perda permanente enquanto não fechar.

### P: Qual é o botão correto?
A: Delete (a tecla grande acima das setas do teclado).
Backspace também funciona.

### P: Posso deletar múltiplos objetos?
A: Não há seleção múltipla no editor atual.
Delete um por um.

---

## 📊 Comparação: Onde Deletar

| Local | Método | Funciona? |
|-------|--------|-----------|
| Viewport | Selecionar + Delete | ✅ Sim |
| Hierarquia | Selecionar + Delete | ✅ Sim |
| Hierarquia | Clique direito → Delete | ✅ Sim |
| Durante Play | Delete | ❌ Não |
| Sem seleção | Delete | ❌ Não |
| Inspector | Delete | ❌ Não (vai deletar texto) |

---

## 🆘 Se Delete Não Funciona Mesmo

### Passo 1: Verificar Estado
```
Verificar se está em EDIT mode:
  Canto inferior direito deve dizer "EDIT"
  Se disser "PLAY", pressione [Stop]
```

### Passo 2: Verificar Seleção
```
Verificar se objeto está selecionado:
  Deve haver borda colorida no objeto
  Hierarquia deve ter destaque
  Inspector deve mostrar properties
```

### Passo 3: Dar Foco à Viewport
```
Clique na viewport (área dos objetos)
Aí sim pressione Delete
```

### Passo 4: Usar Menu
```
Se teclado não funciona:
  Hierarquia → Clique direito
  → Delete (opção do menu)
```

### Passo 5: Reiniciar
```
Se nada funcionar:
  Feche o editor
  Abra novamente
  Tente de novo
```

---

## ⚙️ Sistema Interno

**Como funciona:**

1. Você pressiona Delete na viewport
2. Viewport captura a tecla
3. Envia mensagem: `delete_selected_requested`
4. Editor recebe a mensagem
5. Verifica se está em EDIT (não Play)
6. Verifica se objeto existe
7. Remove da cena
8. Atualiza hierarquia

**Se falhar em qualquer passo → Delete não funciona**

---

## 🎯 Resumo Rápido

```
PARA DELETAR:
1. Modo EDIT ✅
2. Objeto selecionado ✅
3. Viewport tem foco ✅
4. Pressione Delete ✅

E PRONTO!
```

---

**Delete deveria funcionar do jeito padrão!** Se não funcionar, verifique a checklist acima. 🎮

Ainda tendo problemas? Confira:
- Está em PLAY? → Pressione [Stop]
- Objeto selecionado? → Clique nele
- Viewport ativa? → Clique nela
