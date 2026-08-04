# 🗑️ GUIA: Como Deletar/Destruir Objetos Corretamente

## ❌ O Problema

Você provavelmente está tentando fazer:

```python
enemy = GameObject("Enemy")
scene.add_game_object(enemy)

# ❌ ERRADO! Isso não funciona:
del enemy
```

**Por que não funciona?**
- `del enemy` apenas remove a referência Python
- O objeto **continua ativo na Scene**
- Continua recebendo update/draw
- Continua gastando memória
- É um **memory leak**

---

## ✅ A Solução Correta

### **Método 1: Usar `destroy()`** (Recomendado)

```python
enemy = GameObject("Enemy")
scene.add_game_object(enemy)

# ✅ CORRETO:
enemy.destroy()
```

**O que `destroy()` faz:**
1. Marca o objeto como inativo (`active = False`)
2. Chama `destroy()` em todos os componentes
3. Limpa lista de filhos
4. Remove da cena
5. Limpa referências

---

### **Método 2: Remover da Cena**

```python
enemy = GameObject("Enemy")
scene.add_game_object(enemy)

# ✅ Remover da scene (mas não destroi componentes):
scene.remove_game_object(enemy)

# Depois destruir:
enemy.destroy()
```

**Diferença:**
- `scene.remove_game_object()` → Remove referência da Scene
- `destroy()` → Limpa tudo completamente

---

## 📋 Ciclo Completo: Criar → Usar → Destruir

```python
from engine.core import Scene, GameObject, Engine
from engine.core.component import SpriteRenderer, Collider

class GameScene(Scene):
    def start(self):
        # 1. CRIAR
        self.enemy = GameObject("Enemy", tag="Enemy")
        self.enemy.transform.position = (100, 100)
        
        # Adicionar componentes
        sprite = SpriteRenderer("Assets/enemy.png")
        self.enemy.add_component(sprite)
        
        # Adicionar à cena
        self.add_game_object(self.enemy)
    
    def update(self, dt):
        super().update(dt)
        
        # 2. USAR
        self.enemy.transform.position[0] += 5
        
        # 3. DESTRUIR (quando necessário)
        if self.enemy.transform.position[0] > 1000:
            self.enemy.destroy()  # ✅ CORRETO
```

---

## 🎯 Exemplos Práticos

### Exemplo 1: Inimigo Desaparece ao Sair da Tela

```python
class GameScene(Scene):
    def update(self, dt):
        super().update(dt)
        
        # Destruir inimigos que saíram da tela
        for enemy in self.find_by_tag("Enemy"):
            if enemy.transform.position[0] > 1280:  # fora da tela
                enemy.destroy()  # ✅ Certo
```

### Exemplo 2: Destruir ao Receber Dano

```python
class Enemy(GameObject):
    def __init__(self):
        super().__init__("Enemy", tag="Enemy")
        self.health = 100
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.destroy()  # ✅ Destruir quando morre
```

### Exemplo 3: Destruir ao Coletar Item

```python
class GameScene(Scene):
    def update(self, dt):
        super().update(dt)
        
        # Detectar coleta de items
        player = self.find("Player")
        items = self.find_by_tag("Item")
        
        for item in items:
            if colliding(player, item):
                self.score += 10
                item.destroy()  # ✅ Item desaparece
```

### Exemplo 4: Destruir Múltiplos Objetos

```python
class GameScene(Scene):
    def clear_all_enemies(self):
        # ✅ Correto: usar list() para copiar antes de iterar
        for enemy in list(self.find_by_tag("Enemy")):
            enemy.destroy()
        
        # ❌ Errado: modificar lista enquanto itera
        # for enemy in self.find_by_tag("Enemy"):
        #     enemy.destroy()  # Pode pular itens!
```

---

## ⚠️ Armadilhas Comuns

### Armadilha 1: Tentar usar objeto destruído

```python
enemy = GameObject("Enemy")
scene.add_game_object(enemy)

enemy.destroy()

# ❌ Erro! Objeto já foi destruído
enemy.transform.position = (100, 100)  # Pode causar erro
```

**Solução:** Verificar antes de usar
```python
if enemy.active:
    enemy.transform.position = (100, 100)  # ✅ Seguro
```

### Armadilha 2: Modificar lista enquanto itera

```python
# ❌ Errado:
for enemy in self.find_by_tag("Enemy"):
    enemy.destroy()  # Modifica a lista durante iteração!

# ✅ Correto:
for enemy in list(self.find_by_tag("Enemy")):
    enemy.destroy()  # Usa cópia da lista
```

### Armadilha 3: Esquecer de remover da Scene

```python
# ❌ Errado (memory leak):
enemy = GameObject("Enemy")
scene.add_game_object(enemy)
del enemy  # Apenas remove referência, NÃO remove da Scene

# ✅ Correto:
enemy = GameObject("Enemy")
scene.add_game_object(enemy)
enemy.destroy()  # Remove de tudo
# ou
scene.remove_game_object(enemy)
enemy.destroy()
```

---

## 📊 Resumo das Opções

| Ação | O Que Faz | Quando Usar |
|------|-----------|-----------|
| `del enemy` | ❌ Só remove referência Python | NUNCA! |
| `enemy.active = False` | Desativa mas continua na Scene | Pausar/esconder temporário |
| `scene.remove_game_object(enemy)` | Remove da Scene (não destroi) | Mover para outra Scene |
| `enemy.destroy()` | Limpa tudo completamente | Deletar permanentemente ✅ |
| `scene.remove_game_object(enemy)` + `enemy.destroy()` | Remove + limpa | Máximo cuidado |

---

## 🔍 Checklist: Destruição Segura

```python
# 1. Objeto já está na Scene?
if enemy in scene.game_objects:
    # ✅ Sim, destruir é seguro
    enemy.destroy()

# 2. Iterando sobre lista?
for enemy in list(scene.find_by_tag("Enemy")):  # ✅ Use list()
    enemy.destroy()

# 3. Não reutilizar depois?
enemy.destroy()
# ✅ NÃO tentar usar enemy depois

# 4. Remover do Scene primeiro (opcional mas seguro)
scene.remove_game_object(enemy)
enemy.destroy()
```

---

## 🆚 Comparação: `del` vs `destroy()`

### `del` (Python padrão)
```python
del enemy
# Apenas remove referência Python
# Objeto ainda existe na Scene
# ❌ Não limpa nada
```

### `destroy()` (Engine)
```python
enemy.destroy()
# 1. Marca como inativo (active = False)
# 2. Chama destroy() em todos os componentes
# 3. Remove filhos
# 4. Remove da Scene
# 5. Limpa referências
# ✅ Limpa tudo
```

---

## 💡 Dicas Profissionais

### Dica 1: Marcar para Destruição
```python
# Se você quer destruir no próximo frame:
enemy.active = False  # Desativa imediatamente
# Depois em update:
scene.game_objects = [go for go in scene.game_objects if go.active]
```

### Dica 2: Pool de Objetos
```python
# Para muitos inimigos, reusar objetos:
class EnemyPool:
    def __init__(self, size=100):
        self.available = [GameObject("Enemy") for _ in range(size)]
        self.active = []
    
    def spawn(self, pos):
        if self.available:
            enemy = self.available.pop()
            enemy.active = True
            enemy.transform.position = pos
            self.active.append(enemy)
            return enemy
    
    def despawn(self, enemy):
        enemy.active = False
        self.active.remove(enemy)
        self.available.append(enemy)
```

### Dica 3: Evento de Destruição
```python
class GameObject:
    def __init__(self):
        self.on_destroy = []  # Lista de callbacks
    
    def destroy(self):
        # Chamar callbacks antes de destruir
        for callback in self.on_destroy:
            callback()
        # Depois destruir normalmente
        super().destroy()

# Uso:
enemy = GameObject("Enemy")
enemy.on_destroy.append(lambda: play_death_sound())
enemy.on_destroy.append(lambda: drop_loot())
enemy.destroy()  # Chama callbacks, depois destrói
```

---

## ❓ FAQ

### P: Posso usar `del` depois de `destroy()`?
```python
enemy.destroy()
del enemy  # Sim, mas redundante e desnecessário
```

### P: O que acontece se chamar `destroy()` duas vezes?
```python
enemy.destroy()
enemy.destroy()  # Seguro - já está inativo, nada acontece
```

### P: Como verificar se um objeto foi destruído?
```python
if enemy.active:
    print("Vivo")
else:
    print("Destruído")
```

### P: Preciso remover da Scene antes de destruir?
```python
enemy.destroy()  # NÃO precisa - destroy() faz tudo

# Mas se quiser ser explícito:
scene.remove_game_object(enemy)
enemy.destroy()
```

---

## 🚀 Resumo Final

```
❌ ERRADO:
  del enemy

✅ CORRETO:
  enemy.destroy()

EXPLICAÇÃO:
  destroy() é o método correto para deletar objetos
  do Zennity Engine. Ele:
  • Marca como inativo
  • Limpa componentes
  • Remove da Scene
  • Libera memória
```

---

**Sempre use `destroy()`, nunca use `del` para objetos de jogo!** 🎮

Dúvidas? Veja exemplos em `demos/` ou pergunte!
