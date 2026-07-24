"""
tests/conftest.py

Os stubs de pygame (pygame.Surface = _FakeSurface, pygame.draw.rect = MagicMock)
estão no conftest.py da RAIZ do projeto, que o pytest carrega antes
deste arquivo e antes de qualquer módulo de teste.

Este arquivo existe apenas para fornecer fixtures específicas do subdiretório
tests/ que não sejam necessárias globalmente.
"""
# Nenhuma fixture adicional necessária no momento.
# Fixtures globais estão em conftest.py na raiz.
