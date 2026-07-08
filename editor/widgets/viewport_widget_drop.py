"""
editor/widgets/viewport_widget_drop.py
========================================
Patch de drop no ViewportWidget.
Importe e chame `apply_drop_patch(ViewportWidget)` depois de definir a classe.

Alternativamente, coloque esta lógica diretamente no ViewportWidget.__init__.
Esse arquivo existe para não alterar o ViewportWidget original e evitar conflitos.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint

from editor.widgets.viewport_drop_mixin import ViewportDropMixin

if TYPE_CHECKING:
    from editor.widgets.viewport_widget import ViewportWidget

_IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}


def apply_drop_patch(cls) -> None:
    """
    Injeta suporte a drop de imagens (.png/.jpg) e scripts (.py) no ViewportWidget.
    - Imagem → cria novo SpriteRenderer no objeto selecionado ou cria objeto novo.
    - Script → associa script_path ao objeto selecionado.
    """

    original_init = cls.__init__

    def patched_init(self, parent=None):
        original_init(self, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-zennity-asset"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-zennity-asset"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()
        if not mime.hasFormat("application/x-zennity-asset"):
            event.ignore()
            return
        raw = mime.data("application/x-zennity-asset")
        path = raw.data().decode("utf-8") if raw else ""
        if not path:
            event.ignore()
            return

        ext = os.path.splitext(path)[1].lower()
        vm = getattr(self, "viewmodel", None)
        if vm is None:
            event.ignore()
            return

        if ext in _IMG_EXTS:
            _drop_sprite(self, vm, path, event.pos())
        elif ext == ".py":
            _drop_script(vm, path)

        event.acceptProposedAction()

    cls.__init__    = patched_init
    cls.dragEnterEvent = dragEnterEvent
    cls.dragMoveEvent  = dragMoveEvent
    cls.dropEvent      = dropEvent


def _drop_sprite(vp, vm, path: str, pos) -> None:
    """Atribui sprite ao objeto selecionado ou cria um novo."""
    obj = getattr(vm, "selected_object", None)
    if obj is None and hasattr(vm, "create_object"):
        # Cria objeto novo na posição do drop
        try:
            from editor.core.event_bus import EventBus
            name = os.path.splitext(os.path.basename(path))[0]
            obj = vm.create_object("sprite", name=name)
        except Exception:
            pass
    if obj is not None:
        obj.mesh_type = "sprite"
        obj.mesh_path = path
        # Tenta notificar Inspector via sinal
        try:
            vm.selection_changed.emit(obj)
        except Exception:
            pass


def _drop_script(vm, path: str) -> None:
    """Associa o script ao objeto selecionado."""
    obj = getattr(vm, "selected_object", None)
    if obj is not None:
        obj.script_path = path
        try:
            vm.selection_changed.emit(obj)
        except Exception:
            pass
