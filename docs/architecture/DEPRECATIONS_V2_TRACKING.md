# Deprecations Tracking for v2.0 Sunset

Data de criação: 1 de Agosto de 2026  
Release Alvo para Remoção Completa: **v2.0.0**  
Estratégia Oficial: Conforme [`docs/architecture/EDITOR_ENTRYPOINT_MIGRATION.md`](EDITOR_ENTRYPOINT_MIGRATION.md).

## Módulos Marcados com `DeprecationWarning` no v1.0.0

| Módulo / Interface Legada | Substituição Canônica (v1.0+) | Data-Alvo Remoção (v2.0) |
|---|---|---|
| `editor.phase1_editor` | `editor.phase1_main` / `isolated_editor_main` | Release v2.0.0 |
| `editor.windows.main_window.MainWindow` | `isolated_editor_main` | Release v2.0.0 |
| `editor.widgets.inspector_dock.InspectorDock` | `isolated_editor_main` Inspector Dock | Release v2.0.0 |
| `editor.premium_panels` | `editor.phase1_editor_mixins` | Release v2.0.0 |
| `editor.inspector` (Inspector Plugin System) | `editor/inspector_controller_*.py` | Release v2.0.0 |
| `engine.graphics.renderer2d` | `engine.graphics.renderer` | Release v2.0.0 |
| `engine.graphics.tilemap` | `engine.tilemap.tilemap` | Release v2.0.0 |
| `engine.component` | `engine.core` | Release v2.0.0 |

---

## Monitoramento Pós-Release (Long-Running Editor Soak Test)

- **Objetivo**: Monitorar a estabilidade de memória em sessões contínuas do editor de longa duração (nightly build).
- **Escopo**: Executar 5.000 ciclos de Play/Stop e edição de cena em um worker isolado para simular o uso diário sem reiniciar o processo.
