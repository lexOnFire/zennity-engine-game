# Tarefas — Inspector Profissional (Fase 8)

- [x] Ocultar handles legados permanentemente na nova viewport (`editor/widgets/phase1_viewport.py`)
- [x] Sincronizar e mapear `project_root` no `EditorContext` a partir do `AssetModel` do editor (`editor_context.py` & `main_window.py`)
- [x] Adicionar resolução automática do `project_root` a partir do caminho do arquivo no `prefab_loader.py`
- [x] Impedir criação de prefabs fora da pasta `Assets/` do projeto disparando `ValueError` (`prefab_loader.py`)
- [x] Definir o contrato oficial do formato `.zprefab` e documentá-lo em `docs/prefab-format.md`
- [x] Decidir sobre suporte recursivo futuro para `children: []` (estruturado no contrato, mas inicializado vazio por enquanto)
- [x] Validar que a instanciação do prefab adiciona exatamente uma única referência à cena ativa sem duplicações
- [x] Criar testes unitários e de integração cobrindo os cenários de prefabs em `tests/prefabs/`
- [x] Criar comandos reversíveis de alteração de propriedades `SetTransformPropertyCommand` e `SetPropertyCommand` (`editor/runtime/property_commands.py`)
- [x] Sincronizar o `CommandManager` e injetá-lo no `SceneViewModel` (`scene_viewmodel.py` e `main_window.py`)
- [x] Implementar `commit_transform_property` no `SceneViewModel` para disparar transações de modificação no histórico
- [x] Atualizar `TransformComponentWidget` para isolar modificações interativas (`valueChanged`) de commits de histórico (`editingFinished`)
- [x] Garantir que `on_property_changed` no `InspectorDock` não overwrite o valor original do spinbox durante a edição
- [x] Criar suíte completa de testes unitários e de integração para o Inspector em `tests/editor/test_phase1_inspector.py`
- [x] Atualizar a documentação de arquitetura e roadmap (`README.md`, `ROADMAP.md` e `ARCHITECTURE.md`)
- [x] Rodar e validar toda a suíte de testes (1508 testes passando)
- [x] Compactar o projeto atualizado e limpo em `zennity_engine.zip`
