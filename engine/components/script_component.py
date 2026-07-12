from __future__ import annotations

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any


class ScriptComponent:
    """Componente que associa um script Python a um GameObject.

    Armazena o caminho do script e um dicionário de propriedades
    publicadas. As propriedades são detectadas automaticamente a
    partir das anotações de instância da classe principal do script.
    """

    # component_type é usado pelo ComponentRegistry como chave canônica.
    # type_name é usado pelo InspectorPluginRegistry para resolver o plugin.
    # Ambos devem ser iguais.
    component_type: str = "Script"
    type_name: str = "Script"
    required: bool = False
    unique: bool = False

    def __init__(self, script_path: str = "") -> None:
        self.script_path: str = script_path
        self.properties: dict[str, Any] = {}
        self.enabled: bool = True
        self._module: Any = None
        if script_path:
            self._load_defaults()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def _load_defaults(self) -> None:
        """Carrega o módulo e detecta propriedades públicas da classe."""
        cls = self._resolve_class()
        if cls is None:
            return
        hints = {}
        for klass in reversed(cls.__mro__):
            hints.update(getattr(klass, "__annotations__", {}))
        for name, annotation in hints.items():
            if name.startswith("_"):
                continue
            if str(annotation).startswith("ClassVar") or "ClassVar" in str(annotation):
                continue
            if name not in self.properties:
                try:
                    default = getattr(cls, name)
                except AttributeError:
                    default = self._default_for_annotation(annotation)
                self.properties[name] = default

    def _resolve_class(self) -> type | None:
        """Importa o módulo do script e retorna a primeira classe concreta."""
        path = Path(self.script_path)
        if not path.exists():
            return None
        module_name = f"_zen_script_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None
        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            self._module = module
        except Exception:
            return None
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module_name:
                return obj
        return None

    @staticmethod
    def _default_for_annotation(annotation: Any) -> Any:
        mapping = {float: 0.0, int: 0, str: "", bool: False}
        return mapping.get(annotation, None)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.type_name,
            "enabled": self.enabled,
            "properties": {
                "script_path": self.script_path,
                "props": dict(self.properties),
            },
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.script_path = str(data.get("script_path", ""))
        stored = data.get("props", {})
        if self.script_path:
            self._load_defaults()
        self.properties.update(stored)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_property(self, name: str, value: Any) -> None:
        self.properties[name] = value

    def get_property(self, name: str, default: Any = None) -> Any:
        return self.properties.get(name, default)

    def script_name(self) -> str:
        return Path(self.script_path).name if self.script_path else ""
