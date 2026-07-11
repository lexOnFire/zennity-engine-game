# Relatorio de Auditoria: Necessidade do QTimer Durante o Drag

Gerado em: 2026-07-11 13:12:36

## 1. Código Completo de `_tick()`

Mapeado em [phase1_viewport.py:L695-716](file:///C:/Users/alexs/OneDrive/Documentos/meu projeto/pygame_engine/editor/widgets/phase1_viewport.py#L695-L716):
```python
    def _tick(self) -> None:
        now = time.time()
        dt = min(now - self._last_time, 0.1)
        self._last_time = now

        if self.active_scene:
            runtime_playing = (
                self.runtime_manager is not None
                and getattr(self.runtime_manager, "is_playing", False)
            )
            is_runtime_scene = (
                runtime_playing
                and getattr(self.runtime_manager, "runtime_scene", None) is self.active_scene
            )
            if is_runtime_scene:
                self.runtime_manager.tick(dt)
            elif not runtime_playing:
                # Disable scene.update in edit mode to prevent physics from falling
                self._sync_selection_to_model()

        self.update()
```

---

## 2. Operações Executadas pelo `_tick()`
1.  **Cálculo de delta tempo (`dt`):** Infraestrutura temporal.
2.  **`runtime_manager.tick(dt)`:** Executa scripts, animações e física (ativo apenas no Play Mode).
3.  **`_sync_selection_to_model()`:** Sincroniza a seleção do outliner/inspector com o objeto selecionado na cena legada do Pygame (ativo apenas no Edit Mode).
4.  **`self.update()`:** Agenda o redesenho do widget (`PaintEvent`).

---

## 3. Classificação das Operações
*   **Tempo / Delta:** *Infraestrutura*
*   **`runtime_manager.tick`:** *Física, Animação, Runtime, Atualização de cena*
*   **`_sync_selection_to_model`:** *Seleção, UI*
*   **`self.update()`:** *Renderização*

---

## 4. Análise de Necessidade no Drag
Durante a operação de drag:
*   **Nenhuma das operações de `_tick()` é necessária.** O loop de física/scripts está pausado no editor e o redesenho da tela já é impulsionado na taxa máxima pelo próprio evento `mouseMoveEvent` ao arrastar.

---

## 5. Operações que modificam variáveis de controle
*   **`transform.position`:** Nenhuma.
*   **`camera`:** Nenhuma.
*   **`gizmos`:** Nenhuma.
*   **`selection`:** Potencialmente `_sync_selection_to_model()`, mas como o arraste trava a seleção no objeto selecionado no início, nenhuma alteração de seleção ocorre no drag.

---

## 6. Impacto de Pausar o Timer Durante o Drag (Análise Item por Item)
*   **Física:** Sem impacto (já pausada no editor).
*   **Animação:** Sem impacto (já pausada no editor).
*   **Scripts:** Sem impacto (já pausados no editor).
*   **Movimento de Câmera (Pan/Zoom):** Sem impacto (controlados de forma síncrona nos eventos de mouse/roda).
*   **Seleção no Inspector/Outliner:** Sem impacto (a seleção do objeto a ser movido ocorre no `mousePressEvent` inicial e não muda no arraste).
*   **Atualização Visual do Arraste:** Sem impacto (o `mouseMoveEvent` chama `update()` a cada pixel movido, garantindo repaints em tempo real).

---

## 7. Dependências e Modos
*   **Dependência de Play Mode:** Sim. O `_tick` é obrigatório no Play Mode para rodar a simulação do jogo.
*   **Dependência da aba Game:** Não. O Game View roda sob um QTimer próprio.
*   **Dependência da aba Scene:** Sim. Controla a temporização da aba Scene em modo de repouso (Edit Mode).

---

## 8. Conclusão Final

O timer pode ser pausado durante o drag?
**SIM**

### Justificativa Técnica:
Durante o drag, o redesenho é gerado de forma síncrona pelos eventos de mouse (acoplado ao input). O timer de 16ms torna-se totalmente redundante e concorrente, competindo por ciclos de CPU no event loop do Qt e enviando requisições de repaints que interferem no fluxo linear do drag. 

Pausar temporariamente o timer no início do drag (`begin_move_drag`, `begin_scale_drag`) e retomá-lo no encerramento (`end_drag`/`mouseReleaseEvent`) elimina as disputas de renderização e estabiliza a atualização visual.
