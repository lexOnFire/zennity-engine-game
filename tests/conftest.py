"""
tests/conftest.py

Os stubs de pygame (pygame.Surface = _FakeSurface, pygame.draw.rect = MagicMock)
estão no conftest.py da RAIZ do projeto, que o pytest carrega antes
deste arquivo e antes de qualquer módulo de teste.

Este arquivo fornece o contrato headless de toda a suíte: nenhum teste pode
abrir um diálogo modal do Qt. Ver tests/_headless_dialogs.py para o porquê.
"""

from tests._headless_dialogs import (  # noqa: F401
    HeadlessDialogRecorder,
    pytest_configure,
    _headless_dialog_dir,
    _headless_dialog_guard,
    headless_dialogs,
)
