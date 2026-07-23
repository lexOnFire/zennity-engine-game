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


def test_editor_play_stop_cycle_memory_stability(qapp: QApplication) -> None:
    """Valida a estabilidade de memória por 500 ciclos de Play/Stop."""
    editor = ZennityPhase1Editor()
    import pygame

    def _reset_pygame_mocks():
        # Limpa o histórico de chamadas acumulado nos mocks globais do pygame para não falsear o teste de memória
        for name in dir(pygame.draw):
            attr = getattr(pygame.draw, name)
            if hasattr(attr, "reset_mock"):
                attr.reset_mock()

    # Executa ciclos iniciais para aquecer caches e alocações internas estáveis
    for _ in range(10):
        editor.play()
        editor.stop()
        editor.console.log.clear()
        editor.editor_context.commands.clear()
        editor.editor_context.selection.clear()
        _reset_pygame_mocks()
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
        _reset_pygame_mocks()
        qapp.processEvents()

    # Coleta final e liberação
    for _ in range(5):
        gc.collect()
        _reset_pygame_mocks()
        qapp.processEvents()

    final_objects = gc.get_objects()
    final_types = Counter(type(obj).__name__ for obj in final_objects)

    # O crescimento de objetos na memória deve ser desprezível
    growth = len(final_objects) - len(initial_objects)
    
    # Se houver crescimento excessivo, imprime a diferença por tipo de objeto
    if growth >= 1200:
        diff = {k: final_types[k] - initial_types[k] for k in final_types if final_types[k] > initial_types[k]}
        sorted_diff = sorted(diff.items(), key=lambda x: x[1], reverse=True)
        print("\nLEAKED TYPES:", sorted_diff[:15])
        
    assert growth < 1200, f"Potencial vazamento de memória detectado: +{growth} objetos retidos."

    editor.close()
    editor.deleteLater()
    qapp.processEvents()
