"""
editor/widgets/viewport_drop_mixin.py
======================================
Mixin que adiciona suporte a drop de assets do AssetBrowser
no ViewportWidget e no InspectorDock.

Uso no ViewportWidget::

    class ViewportWidget(ViewportDropMixin, QOpenGLWidget):
        ...
        def __init__(self):
            super().__init__()
            self.setup_drop()   # habilita accept drops

Uso no InspectorDock::

    class InspectorDock(ViewportDropMixin, QDockWidget):
        ...
"""
from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

_ASSET_MIME = "application/x-zennity-asset"
_IMG_EXTS   = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
_SCRIPT_EXT = ".py"


class ViewportDropMixin:
    """
    Mixin leve para aceitar drag-and-drop de assets Zennity.
    A classe host deve implementar `_on_asset_dropped(path, pos)`.
    """

    def setup_drop(self) -> None:
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------ #
    # Qt drag events                                                      #
    # ------------------------------------------------------------------ #

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(_ASSET_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(_ASSET_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if not mime.hasFormat(_ASSET_MIME):
            event.ignore()
            return
        raw = mime.data(_ASSET_MIME)
        path = raw.data().decode("utf-8") if raw else ""
        if path:
            self._on_asset_dropped(path, event.pos())
            event.acceptProposedAction()
        else:
            event.ignore()

    # ------------------------------------------------------------------ #
    # Helper: tipo do asset                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _asset_is_image(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in _IMG_EXTS

    @staticmethod
    def _asset_is_script(path: str) -> bool:
        return os.path.splitext(path)[1].lower() == _SCRIPT_EXT

    # ------------------------------------------------------------------ #
    # A implementar na classe host                                        #
    # ------------------------------------------------------------------ #

    def _on_asset_dropped(self, path: str, pos: QPoint) -> None:
        """Sobrescrever na classe concreta para tratar o drop."""
        raise NotImplementedError
