# Diretrizes de Teste & Cobertura (CI / Quality Gate)

A **Zennity Engine** adota o `pytest` e `pytest-cov` como base para integração contínua (CI).

## Execução dos Testes com Cobertura

Para rodar todos os testes com medição de cobertura do pacote `engine`:

```bash
pytest --cov=engine --cov-report=term-missing --cov-fail-under=80
```

## Diretrizes de Qualidade
1. **Nenhum teste quebrado em `main`:** Todos os PRs e merges devem ter testes 100% verdes.
2. **Limite de Cobertura Mínima (Quality Gate):** Módulos do `engine/core/` e `engine/animation/` devem manter cobertura igual ou superior a 80%.
3. **Artefatos de CI:** Os diretórios `htmlcov/`, `.pytest_cache/` e `.coverage` são ignorados no versionamento pelo `.gitignore`.
