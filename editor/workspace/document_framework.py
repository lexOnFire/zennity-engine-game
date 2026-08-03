"""Document Framework — cada tipo de recurso abre como documento.

Aproxima a experiência do editor a uma IDE moderna, onde múltiplos
documentos podem estar abertos e alternados via abas.

Tipos suportados:
  Scene, Material, Animation, Dialogue, BehaviorTree, UI, VisualScript
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable


class DocumentType(str, Enum):
    SCENE          = "scene"
    MATERIAL       = "material"
    ANIMATION      = "animation"
    DIALOGUE       = "dialogue"
    BEHAVIOR_TREE  = "behavior_tree"
    UI             = "ui"
    VISUAL_SCRIPT  = "visual_script"
    UNKNOWN        = "unknown"

    @classmethod
    def from_extension(cls, path: str | Path) -> DocumentType:
        ext = Path(path).suffix.lower()
        return {
            ".zscene":  cls.SCENE,
            ".zmat":    cls.MATERIAL,
            ".zanim":   cls.ANIMATION,
            ".zdialogue": cls.DIALOGUE,
            ".zdlg":    cls.DIALOGUE,
            ".zbehavior": cls.BEHAVIOR_TREE,
            ".zbtree":  cls.BEHAVIOR_TREE,
            ".zui":     cls.UI,
            ".zlogic":  cls.VISUAL_SCRIPT,
            ".zvs":     cls.VISUAL_SCRIPT,
        }.get(ext, cls.UNKNOWN)


@dataclass
class EditorDocument:
    """Representa um documento aberto no editor.

    Cada documento tem seu tipo, caminho, estado de modificação
    e dados em memória. Pode ser serializado e restaurado.
    """
    doc_type: DocumentType
    path: Path | None = None
    title: str = "Sem título"
    data: Any = None
    is_modified: bool = False
    on_close: Callable | None = field(default=None, repr=False)

    def mark_modified(self) -> None:
        self.is_modified = True
        try:
            from editor.core.event_bus import EventBus
            EventBus.emit("Scene.object_modified", document=self)
        except Exception:
            pass

    def mark_saved(self, path: Path | None = None) -> None:
        if path:
            self.path = path
            self.title = path.stem
        self.is_modified = False

    @property
    def display_title(self) -> str:
        suffix = " *" if self.is_modified else ""
        return f"{self.title}{suffix}"


class DocumentManager:
    """Gerencia todos os documentos abertos no editor."""

    _instance: DocumentManager | None = None

    def __init__(self) -> None:
        self._documents: list[EditorDocument] = []
        self._active: EditorDocument | None = None
        self._on_active_changed: list[Callable] = []

    @classmethod
    def instance(cls) -> DocumentManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def open(self, doc_type: DocumentType, path: Path | None = None, data: Any = None) -> EditorDocument:
        # Verifica se já existe o documento aberto
        if path:
            for doc in self._documents:
                if doc.path == path:
                    self.set_active(doc)
                    return doc

        title = path.stem if path else f"Novo {doc_type.value.replace('_', ' ').title()}"
        doc = EditorDocument(doc_type=doc_type, path=path, title=title, data=data)
        self._documents.append(doc)
        self.set_active(doc)
        return doc

    def close(self, doc: EditorDocument) -> bool:
        if doc in self._documents:
            if doc.on_close:
                doc.on_close()
            self._documents.remove(doc)
            if self._active is doc:
                self._active = self._documents[-1] if self._documents else None
                self._notify_active()
            return True
        return False

    def set_active(self, doc: EditorDocument) -> None:
        self._active = doc
        self._notify_active()

    @property
    def active(self) -> EditorDocument | None:
        return self._active

    @property
    def all_documents(self) -> list[EditorDocument]:
        return list(self._documents)

    def subscribe_active(self, callback: Callable) -> None:
        if callback not in self._on_active_changed:
            self._on_active_changed.append(callback)

    def _notify_active(self) -> None:
        for cb in list(self._on_active_changed):
            try:
                cb(self._active)
            except Exception:
                pass
