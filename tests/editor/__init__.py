"""Editor test package.

The ``__init__.py`` matters: without it pytest imports ``tests/editor/conftest.py``
under the bare module name ``conftest``, which shadows the repository-root
``conftest.py`` for any module doing ``from conftest import ...``
(``tests/test_transitions.py`` does).  Marking the directory as a package makes
the module ``tests.editor.conftest`` instead.
"""
