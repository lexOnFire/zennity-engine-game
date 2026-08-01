# Deprecations Tracking for v2.0 Sunset

Data de Criação: **1 de Agosto de 2026**  
Milestone Alvo para Remoção Completa: **v2.0.0 (Previsão: Q1 2027 / 15 de Fevereiro de 2027)**  
Estratégia Oficial: Conforme [`docs/architecture/EDITOR_ENTRYPOINT_MIGRATION.md`](EDITOR_ENTRYPOINT_MIGRATION.md).

---

## Módulos Marcados com `DeprecationWarning` no v1.0.0

| Módulo / Interface Legada | Substituição Canônica (v1.0+) | Milestone Remoção | Data Limite (Sunset) |
|---|---|---|---|
| `editor.phase1_editor` | `editor.phase1_main` / `isolated_editor_main` | Milestone v2.0-Alpha1 | 15/12/2026 |
| `editor.windows.main_window.MainWindow` | `isolated_editor_main` | Milestone v2.0-Alpha1 | 15/12/2026 |
| `editor.widgets.inspector_dock.InspectorDock` | `isolated_editor_main` Inspector Dock | Milestone v2.0-Alpha1 | 15/12/2026 |
| `editor.premium_panels` | `editor.phase1_editor_mixins` | Milestone v2.0-Alpha2 | 15/01/2027 |
| `editor.inspector` (Inspector Plugin System) | `editor/inspector_controller_*.py` | Milestone v2.0-Alpha2 | 15/01/2027 |
| `engine.graphics.renderer2d` | `engine.graphics.renderer` | Milestone v2.0.0 Final | 15/02/2027 |
| `engine.graphics.tilemap` | `engine.tilemap.tilemap` | Milestone v2.0.0 Final | 15/02/2027 |
| `engine.component` | `engine.core` | Milestone v2.0.0 Final | 15/02/2027 |

---

## Monitoramento Pós-Release (Long-Running Editor Soak Test)

- **Objetivo**: Monitorar a estabilidade de memória em sessões contínuas do editor de longa duração (nightly build).
- **Frequência**: Nightly (Job agendado no GitHub Actions via cron `0 2 * * *`).
- **Escopo**: Executar 5.000 ciclos de Play/Stop e edição de cena em um worker isolado para simular o uso diário sem reiniciar o processo.
