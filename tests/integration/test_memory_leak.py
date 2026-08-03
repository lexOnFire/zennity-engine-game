"""Integration test: editor memory stability over 500 Play/Stop cycles.

===========================================================================
POR QUE ESTE TESTE ESTÁ FORA DA SUÍTE PRINCIPAL
===========================================================================

SITUAÇÃO:
  Este teste passa quando executado isoladamente (≈ 9,7 s, crescimento < 200
  objetos). Falha com +9.054 objetos quando roda após a suíte completa (~2.200
  testes).

CAUSA RAIZ:
  Os ≈ 2.200 testes anteriores acumulam mocks do ``unittest.mock`` no heap do
  interpretador Python (sobretudo ``_Call``, ``_CallList`` e ``MagicMock``).
  A função ``_reset_all_mocks`` do próprio teste limpa o histórico dos mocks
  que consegue alcançar via ``gc.get_objects()``, mas não consegue liberar
  os objetos já referenciados internamente pelos frames de teste ainda vivos no
  stack de pytest.  O resultado é um "baseline" inflado que distorce a medição.
  O problema é de contaminação de contexto, não de vazamento real no editor.

EVIDÊNCIA:
  - Suíte principal (após ~2.200 testes): falha com +9.054 objetos retidos.
  - Processo isolado (``pytest tests/integration/test_memory_leak.py``): passa
    consistentemente (crescimento < 200 objetos, limite = 1.200).

SOLUÇÃO ADOTADA (pragmática):
  - Suíte principal: usa ``--ignore=tests/integration/test_memory_leak.py``.
  - CI: job ``memory-stability`` separado roda este arquivo em processo limpo
    e é a fonte de verdade para regressões de memória.

SOLUÇÃO DEFINITIVA PENDENTE (próxima sessão de manutenção):
  Reescrever o corpo do teste para executar os 500 ciclos num subprocesso
  Python separado via ``subprocess.run([sys.executable, ...])``. Isso garante
  um heap limpo independentemente do que rodou antes, e resolve o problema
  de forma definitiva tanto no CI quanto localmente.
  Ver: https://github.com/<org>/zennity-engine-game/issues/<N>
  (ou buscar "test_memory_leak subprocess" em PRE_V1_FINAL_AUDIT.md)
===========================================================================
"""
from __future__ import annotations

import gc
from collections import Counter
import pytest
from PySide6.QtWidgets import QApplication
from editor.phase1_editor import ZennityPhase1Editor


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.xdist_group(name="memory_leak")
def test_editor_play_stop_cycle_memory_stability(qapp: QApplication) -> None:
    """Valida a estabilidade de memória por 500 ciclos de Play/Stop."""
    editor = ZennityPhase1Editor()
    import pygame

    def _reset_all_mocks():
        # Limpa o histórico de chamadas acumulado em todos os mocks para isolar a medição de memória
        import sys
        for mod_name in list(sys.modules.keys()):
            if "pygame" in mod_name or "editor" in mod_name or "engine" in mod_name:
                mod = sys.modules[mod_name]
                for name in dir(mod):
                    attr = getattr(mod, name, None)
                    if hasattr(attr, "reset_mock"):
                        try:
                            attr.reset_mock()
                        except Exception:
                            pass
        for obj in gc.get_objects():
            if type(obj).__name__ in ("Mock", "MagicMock", "NonCallableMagicMock", "_CallList"):
                if hasattr(obj, "reset_mock"):
                    try:
                        obj.reset_mock()
                    except Exception:
                        pass

    # Executa ciclos iniciais para aquecer caches e alocações internas estáveis
    for _ in range(10):
        editor.play()
        editor.stop()
        editor.console.log.clear()
        editor.editor_context.commands.clear()
        editor.editor_context.selection.clear()
        _reset_all_mocks()
        qapp.processEvents()

    # Coleta inicial
    gc.collect()
    initial_objects = gc.get_objects()
    initial_types = Counter(type(obj).__name__ for obj in initial_objects)

    # Executa 500 ciclos de Play/Stop com liberação e coleta de eventos Qt
    for _ in range(500):
        editor.play()
        editor.stop()
        editor.console.log.clear()
        editor.editor_context.commands.clear()
        editor.editor_context.selection.clear()
        _reset_all_mocks()
        qapp.processEvents()

    # Coleta final e liberação
    for _ in range(5):
        gc.collect()
        _reset_all_mocks()
        qapp.processEvents()

    final_objects = gc.get_objects()
    final_types = Counter(type(obj).__name__ for obj in final_objects)

    # O crescimento de objetos na memória deve ser desprezível, mas descontamos overhead do unittest.mock
    mock_types = {"_Call", "_CallList", "MagicMock", "Mock"}
    growth = sum(count for type_name, count in final_types.items() if type_name not in mock_types) - sum(count for type_name, count in initial_types.items() if type_name not in mock_types)
    
    # Se houver crescimento excessivo, imprime a diferença por tipo de objeto
    if growth >= 1200:
        diff = {k: final_types[k] - initial_types[k] for k in final_types if final_types[k] > initial_types[k] and k not in mock_types}
        sorted_diff = sorted(diff.items(), key=lambda x: x[1], reverse=True)
        print("\nLEAKED TYPES:", sorted_diff[:15])
        
    assert growth < 1200, f"Potencial vazamento de memória detectado: +{growth} objetos retidos."

    editor.close()
    editor.deleteLater()
    qapp.processEvents()
