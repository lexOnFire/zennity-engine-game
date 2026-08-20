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

SOLUÇÃO ANTERIOR (pragmática, substituída no item 13.1-A):
  - Suíte principal: ``--ignore=tests/integration/test_memory_leak.py``.
  - CI: job ``memory-stability`` separado.
  Isso funcionava no CI mas não estava replicado em ``pytest.ini``, então quem
  rodasse ``pytest tests`` localmente herdava o falso positivo.

SOLUÇÃO ADOTADA (item 13.1-A) -- a "definitiva pendente" descrita acima:
  A medição roda num subprocesso Python limpo (``python <este arquivo>``). O
  heap medido é sempre virgem, independentemente do que rodou antes, então o
  resultado é o mesmo isolado, na suíte completa e no CI. O limite de 1.200
  objetos NÃO foi alterado; o corpo da medição é o mesmo, só mudou onde ele
  executa. O job dedicado do CI continua válido e passa a ser redundante em vez
  de obrigatório.
===========================================================================
"""
from __future__ import annotations

import gc
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

#: Crescimento máximo de objetos aceito ao fim dos 500 ciclos. Inalterado.
GROWTH_THRESHOLD = 1200

#: Marca o processo filho. Presente, o teste mede; ausente, ele delega.
CHILD_MARKER = "ZENNITY_MEMORY_LEAK_CHILD"


@pytest.mark.xdist_group(name="memory_leak")
def test_editor_play_stop_cycle_memory_stability() -> None:
    """Mede num processo limpo, reentrando neste mesmo teste via pytest.

    O filho é lançado como ``pytest <este teste>``, não como ``python <este
    arquivo>``. O conftest da raiz chama ``pygame.init()`` e envolve
    ``pygame.draw`` em mocks; um filho lançado fora do pytest não recebe nada
    disso e passa a exercitar rasterização real -- os 500 ciclos saltaram de
    segundos para mais de 15 minutos, medindo algo que a suíte nunca mede.
    """
    if os.environ.get(CHILD_MARKER) == "1":
        growth = _measure_growth()
        assert growth < GROWTH_THRESHOLD, (
            f"Potencial vazamento de memória detectado: +{growth} objetos retidos."
        )
        return

    environment = dict(os.environ)
    environment.update(
        {
            CHILD_MARKER: "1",
            "SDL_VIDEODRIVER": "dummy",
            "SDL_AUDIODRIVER": "dummy",
            "PYGAME_HIDE_SUPPORT_PROMPT": "1",
            "QT_QPA_PLATFORM": "offscreen",
        }
    )
    target = f"{Path(__file__).name}::test_editor_play_stop_cycle_memory_stability"
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=short",
            str(Path(__file__).resolve().parent / target),
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True,
        text=True,
        env=environment,
        timeout=900,
    )
    assert result.returncode == 0, (
        "a medição de estabilidade de memória falhou num processo limpo, "
        "portanto não é contaminação de contexto:\n"
        f"{result.stdout[-3000:]}\n{result.stderr[-2000:]}"
    )


def _measure_growth() -> int:
    """Os 500 ciclos de Play/Stop. Só faz sentido num heap limpo."""
    from PySide6.QtWidgets import QApplication
    from editor.phase1_editor import ZennityPhase1Editor

    qapp = QApplication.instance() or QApplication([])
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
    if growth >= GROWTH_THRESHOLD:
        diff = {k: final_types[k] - initial_types[k] for k in final_types if final_types[k] > initial_types[k] and k not in mock_types}
        sorted_diff = sorted(diff.items(), key=lambda x: x[1], reverse=True)
        print("\nLEAKED TYPES:", sorted_diff[:15])

    editor.close()
    editor.deleteLater()
    qapp.processEvents()
    return growth
