"""Testes de ciclo de vida, ownership e robustez do _InspectorDropFilter (Pre-Phase 13 Sprint R1.5)."""
from __future__ import annotations

import gc
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

from PySide6.QtCore import QCoreApplication, QEvent, QMimeData, QObject, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from editor.core.theme_manager import ThemeManager
from editor.runtime.asset_drag_drop import (
    _ASSET_MIME,
    _InspectorDropFilter,
    install_asset_drag_drop,
)


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_inspector_drop_filter_single_ownership(qapp):
    """Valida que o _InspectorDropFilter possui parent correto e não é instalado recursivamente em filhos."""
    inspector = QWidget()
    editor = SimpleNamespace(
        inspector=inspector,
        resources=None,
        prefabs=None,
        viewport=None,
        hierarchy=None,
    )

    # Adiciona filhos iniciais no Inspector
    layout = QVBoxLayout(inspector)
    child_lbl = QLabel("Prop Label", inspector)
    child_btn = QPushButton("Click", inspector)
    layout.addWidget(child_lbl)
    layout.addWidget(child_btn)

    # Instala drag and drop
    install_asset_drag_drop(editor)

    filt = getattr(editor, "_asset_drop_filter_inspector", None)
    assert filt is not None
    assert filt.parent() is inspector

    # Invariante R1.5: Filhos NÃO recebem setAcceptDrops(True) forçado pelo instalador de drag/drop
    assert child_lbl.acceptDrops() is False
    assert child_btn.acceptDrops() is False


def test_inspector_rebuild_child_deletion_stress(qapp):
    """Stress test executando 150 ciclos de criação, deleteLater, recriação e aplicação de tema."""
    inspector = QWidget()
    editor = SimpleNamespace(
        inspector=inspector,
        resources=None,
        prefabs=None,
        viewport=None,
        hierarchy=None,
    )
    layout = QVBoxLayout(inspector)

    install_asset_drag_drop(editor)
    filt = editor._asset_drop_filter_inspector

    theme_mgr = ThemeManager.instance()

    for i in range(150):
        # 1. Cria filhos dinâmicos
        btn = QPushButton(f"DynamicBtn_{i}", inspector)
        lbl = QLabel(f"Label_{i}", inspector)
        layout.addWidget(btn)
        layout.addWidget(lbl)
        qapp.processEvents()

        # 2. Aplica tema (disparando cascata de polish/style events no Qt)
        theme_name = "light" if i % 2 == 0 else "dark"
        theme_mgr.apply_theme(theme_name, inspector)

        # 3. Deleta filhos dinâmicos via deleteLater
        layout.removeWidget(btn)
        layout.removeWidget(lbl)
        btn.deleteLater()
        lbl.deleteLater()
        qapp.processEvents()

    # Filtro principal continua 100% válido e anexado ao Inspector
    assert filt.parent() is inspector


def test_inspector_drop_filter_event_handling(qapp):
    """Valida que o container do Inspector ainda processa eventos sintéticos de drag/drop após o endurecimento."""
    inspector = QWidget()
    editor = SimpleNamespace(
        inspector=inspector,
        resources=None,
        prefabs=None,
        viewport=None,
        hierarchy=None,
        editor_context=SimpleNamespace(
            selection=SimpleNamespace(selected=MagicMock())
        ),
    )
    install_asset_drag_drop(editor)
    filt = editor._asset_drop_filter_inspector

    mime = QMimeData()
    mime.setData(_ASSET_MIME, b"Assets/Sprites/player.png")

    enter_event = QDragEnterEvent(
        QPoint(10, 10),
        Qt.CopyAction,
        mime,
        Qt.LeftButton,
        Qt.NoModifier,
    )

    consumed = filt.eventFilter(inspector, enter_event)
    assert consumed is True
    assert enter_event.isAccepted()


def test_inspector_destruction_cleans_filter(qapp):
    """Valida que ao destruir o Inspector, o filtro associado também é desalocado pelo QObject ownership."""
    inspector = QWidget()
    editor = SimpleNamespace(
        inspector=inspector,
        resources=None,
        prefabs=None,
        viewport=None,
        hierarchy=None,
    )

    install_asset_drag_drop(editor)
    filt = editor._asset_drop_filter_inspector
    assert filt is not None

    # Destrói o Inspector
    inspector.deleteLater()
    qapp.processEvents()
    gc.collect()
