# Contributing to Zennity Engine

Obrigado pelo interesse em contribuir! Este guia descreve como configurar o
ambiente, as convenções de código e o processo de contribuição.

---

## Configuração do Ambiente

```bash
# 1. Clone o repositório
git clone https://github.com/lexOnFire/zennity-engine-game.git
cd zennity-engine-game

# 2. Crie e ative um virtualenv
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt   # lint + testes
```

---

## Coding Standards

### Regras gerais
- Python 3.10+ obrigatório
- Type hints em todas as assinaturas públicas
- Docstrings em classes e métodos públicos (Google style)
- Máximo 100 caracteres por linha
- Imports ordenados: stdlib → third-party → local

### Ferramentas

| Ferramenta | Uso | Comando |
|---|---|---|
| `ruff` | Lint + formatação | `ruff check . && ruff format .` |
| `mypy` | Type checking | `mypy engine/` |
| `pytest` | Testes | `pytest tests/` |

### Onde o código novo vai

> **Regra absoluta:** toda evolução do núcleo ocorre em `engine/core/`.
> Os arquivos em `engine/*.py` são shims de retrocompat — não os evolua.

```
Novo sistema de núcleo     → engine/core/meu_sistema.py
Novo módulo (física, etc)  → engine/physics/meu_modulo.py
Novo componente visual     → engine/graphics/meu_componente.py
Nova janela do editor      → editor/meu_painel.py
```

### Imports

```python
# ✅ Correto — sempre importar do pacote canônico
from engine.core import Scene, GameObject, Component, Transform
from engine.core import Application, SceneManager, EventBus

# ❌ Legado — ainda funciona mas emite DeprecationWarning
from engine.component import Component
from engine.scene_manager import SceneManager
```

---

## Estrutura de um Componente

```python
from engine.core import Component

class MeuComponente(Component):
    """Descrição curta do que este componente faz."""

    def __init__(self, valor: int = 10) -> None:
        super().__init__()
        self.valor = valor

    def start(self) -> None:
        """Chamado uma vez quando o GO entra na cena."""

    def update(self, dt: float) -> None:
        """Chamado todo frame."""

    def destroy(self) -> None:
        """Limpeza quando o GO é destruído."""
```

---

## Estrutura de uma Scene

```python
from engine.core import Scene, GameObject
from engine.core import Component  # ou seu componente

class MinhaScene(Scene):
    def __init__(self):
        super().__init__(name="MinhaScene")

    def start(self) -> None:
        go = GameObject("Player", tag="Player")
        go.add_component(MeuComponente(valor=42))
        self.add_game_object(go)

    def update(self, dt: float) -> None:
        super().update(dt)   # propaga para todos os GOs

    def draw(self, screen) -> None:
        screen.fill((30, 30, 30))
        super().draw(screen)
```

---

## Convenções de Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(core): adiciona suporte a tags em GameObject
fix(physics): corrige depenetração MTV no BoxCollider
refactor(core): extrai Scene para engine/core/scene.py
docs(adr): ADR-005 — sistema de partículas
test(core): testes de ciclo de vida do Component
chore: atualiza requirements.txt
```

### Tipos válidos

| Tipo | Uso |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem mudança de comportamento |
| `docs` | Documentação |
| `test` | Testes |
| `chore` | Manutenção (deps, CI, scripts) |
| `perf` | Melhoria de performance |

---

## Testes

Todo novo código deve ter testes em `tests/`.

```bash
# Rodar todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov=engine --cov-report=term-missing

# Apenas testes do core
pytest tests/core/
```

Os testes de `engine.core` não precisam de janela Pygame — use mocks se necessário.

---

## Pull Requests

1. Fork o repositório
2. Crie uma branch: `git checkout -b feat/meu-recurso`
3. Faça commits com mensagens convencionais
4. Rode `ruff check . && pytest tests/` antes de abrir o PR
5. Abra o PR para `main` com descrição clara do que foi feito e por quê

PRs sem testes para código novo serão solicitados a adicioná-los antes do merge.
