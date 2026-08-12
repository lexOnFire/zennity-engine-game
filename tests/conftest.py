"""
tests/conftest.py

Os stubs de pygame (pygame.Surface = _FakeSurface, pygame.draw.rect = MagicMock)
estão no conftest.py da RAIZ do projeto, que o pytest carrega antes
deste arquivo e antes de qualquer módulo de teste.

Este arquivo fornece dois contratos válidos para toda a suíte:

* nenhum teste pode abrir um diálogo modal do Qt
  (ver tests/_headless_dialogs.py);
* nenhum teste pode deixar estado do editor dentro do repositório
  (ver tests/_isolated_project_state.py).
"""

from tests._headless_dialogs import (  # noqa: F401
    HeadlessDialogRecorder,
    _headless_dialog_dir,
    _headless_dialog_guard,
    headless_dialogs,
)
from tests._headless_dialogs import pytest_configure as _configure_headless_dialogs
from tests._isolated_project_state import (  # noqa: F401
    _isolated_project_state,
)
from tests._isolated_project_state import pytest_configure as _configure_project_state


def pytest_configure(config):
    """Compose both contracts.

    Each module registers its own opt-out marker. Importing both names as
    ``pytest_configure`` would silently keep only the last one -- and the
    marker it failed to register would then be reported as unknown.
    """
    _configure_headless_dialogs(config)
    _configure_project_state(config)
