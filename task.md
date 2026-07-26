# Tarefas — Validação Windows/Python 3.12 (v0.5.0-alpha RC)

> Objetivo: Validar o fluxo completo da engine e do editor no Windows com Python 3.12,
> garantindo que o Release Candidate da v0.5.0-alpha está pronto para publicação.

---

## 1. Ambiente

- [ ] Confirmar Python 3.12 instalado e ativo no PATH (`python --version`)
- [ ] Criar e ativar venv limpo: `python -m venv .venv && .venv\Scripts\activate`
- [ ] Instalar dependências: `pip install -r requirements.txt -r requirements-dev.txt`
- [ ] Confirmar que `pygame`, `PyQt6` e demais libs instalam sem erros no Windows
- [ ] Verificar que não há warnings de compatibilidade durante a instalação

---

## 2. Suíte de Testes

- [ ] Rodar suíte completa headless: `pytest --tb=short -q`
- [ ] Confirmar que **todos os 1508 testes passam** sem falhas
- [ ] Confirmar que não há warnings de depreciação do Python 3.12 nos testes
- [ ] Verificar que caminhos de arquivo (`pathlib.Path`, separadores `\\`) funcionam corretamente no Windows
- [ ] Verificar que `conftest.py` configura corretamente o ambiente headless no Windows

---

## 3. Editor Visual

- [ ] Iniciar o editor: `python -m editor` (ou entry point equivalente)
- [ ] Confirmar que a janela principal abre sem erros no console
- [ ] Verificar que o tema/UI carrega corretamente (tokens, ícones SVG)
- [ ] Testar abertura de uma cena existente (`Untitled.zscene`)
- [ ] Testar criação de novo GameObject na Hierarchy
- [ ] Testar adição de componente via Inspector
- [ ] Testar que o `TransformComponentWidget` responde a `valueChanged` e `editingFinished` sem erros
- [ ] Testar undo/redo (`Ctrl+Z` / `Ctrl+Y`) de propriedades do Inspector
- [ ] Testar salvamento atômico da cena (verificar que backup é criado)
- [ ] Testar drag & drop na Hierarchy
- [ ] Verificar que o Project Browser lista assets corretamente com caminhos Windows

---

## 4. Play / Pause / Stop

- [ ] Pressionar Play — confirmar que a cena inicia sem erros
- [ ] Confirmar que o físico roda com passo fixo durante o Play
- [ ] Pressionar Pause — confirmar que o jogo pausa e o áudio para
- [ ] Pressionar Stop — confirmar que a cena é restaurada ao estado original
- [ ] Confirmar que a seleção do objeto é restaurada após Stop
- [ ] Testar ciclo Play → Stop → Play sem crashes

---

## 5. Sistemas de Runtime

- [ ] **Física**: verificar que `BoxCollider` e `CircleCollider` detectam colisões corretamente
- [ ] **Áudio**: verificar que `AudioSource` toca e para via `AudioManager`
- [ ] **Animação**: verificar que `AnimationClip` roda via `Animator` durante o Play
- [ ] **UI Runtime**: verificar que `Canvas`, `Label`, `Button` renderizam no HUD
- [ ] **Logic Graph**: verificar que nós básicos executam (`Once`, `Cooldown`, `Prefab`)
- [ ] **Tilemap**: verificar que `TilemapRenderer` renderiza multicamadas sem artefatos

---

## 6. Prefabs

- [ ] Criar um prefab e salvar em `Assets/` — confirmar que `.zprefab` é gerado corretamente
- [ ] Confirmar que tentar salvar prefab fora de `Assets/` levanta `ValueError`
- [ ] Instanciar prefab na cena — confirmar que apenas **uma** referência é adicionada
- [ ] Verificar resolução automática de `project_root` a partir do caminho do arquivo

---

## 7. Export / Build

- [ ] Abrir Build Settings e configurar um `BuildConfig` para Desktop/Windows
- [ ] Executar validação do projeto — confirmar que erros bloqueiam a exportação
- [ ] Gerar exportação com perfil Debug — confirmar que o artefato é criado
- [ ] Executar o runtime exportado em processo separado — confirmar que a cena carrega
- [ ] Verificar que o Build Report exibe métricas e lista de arquivos corretamente

---

## 8. CI / Finalização

- [ ] Confirmar que o gate de CI Windows 3.12 passa no GitHub Actions
- [ ] Confirmar que não há arquivos de debug (`context_failures.txt`, `diff_stat.txt`, `diff_files.txt`, `*.png` de debug) commitados no branch principal
- [ ] Atualizar `CHANGELOG.md` com a entrada da v0.5.0-alpha
- [ ] Marcar milestone v0.5.0-alpha como concluída
- [ ] Criar tag `v0.5.0-alpha` no repositório
