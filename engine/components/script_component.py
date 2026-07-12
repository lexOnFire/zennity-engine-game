from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Callable


class ScriptComponent:
    """Componente que associa um script Python a um GameObject.

    Formato esperado do script (simples, sem classe obrigatória):

        # meu_script.py
        speed = 200.0

        def on_start(go):
            go.vy = 0

        def on_update(go, dt):
            from engine.input import Input
            if Input.is_key_held("right"):
                go.x += speed * dt

        def on_stop(go):
            pass

    Também suporta o formato com classe (primeira classe concreta do módulo).
    """

    component_type: str = "Script"
    type_name: str = "Script"
    required: bool = False
    unique: bool = False

    def __init__(self, script_path: str = "") -> None:
        self.script_path: str = script_path
        self.properties: dict[str, Any] = {}
        self.enabled: bool = True
        self._module: Any = None
        self._instance: Any = None  # instância de classe, se houver
        if script_path:
            self._load_module()
            self._load_defaults()

    # ------------------------------------------------------------------
    # Carregamento do módulo
    # ------------------------------------------------------------------

    def _load_module(self) -> None:
        """Importa o módulo do script e guarda em self._module."""
        path = Path(self.script_path)
        if not path.exists():
            return
        module_name = f"_zen_script_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return
        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            self._module = module
        except Exception as exc:
            print(f"[ScriptComponent] Erro ao carregar '{self.script_path}': {exc}")

    def _resolve_class(self) -> type | None:
        """Retorna a primeira classe concreta definida no módulo, se houver."""
        if self._module is None:
            return None
        module_name = getattr(self._module, "__name__", "")
        for _name, obj in inspect.getmembers(self._module, inspect.isclass):
            if obj.__module__ == module_name:
                return obj
        return None

    def _get_fn(self, name: str) -> Callable | None:
        """Busca uma função de nível de módulo pelo nome."""
        if self._module is None:
            return None
        fn = getattr(self._module, name, None)
        return fn if callable(fn) else None

    # ------------------------------------------------------------------
    # Ciclo de vida — chamados pelo ScriptSystem
    # ------------------------------------------------------------------

    def call_start(self, go: Any) -> None:
        """Chama on_start(go) no script, se existir."""
        if not self.enabled:
            return
        if self._module is None:
            self._load_module()
        cls = self._resolve_class()
        if cls is not None:
            self._instance = cls()
            if hasattr(self._instance, "on_start"):
                self._instance.on_start(go)
        else:
            fn = self._get_fn("on_start")
            if fn is not None:
                try:
                    fn(go)
                except Exception as exc:
                    print(f"[ScriptComponent] on_start error: {exc}")

    def call_update(self, go: Any, dt: float) -> None:
        """Chama on_update(go, dt) no script, se existir."""
        if not self.enabled:
            return
        if self._instance is not None:
            if hasattr(self._instance, "on_update"):
                try:
                    self._instance.on_update(go, dt)
                except Exception as exc:
                    print(f"[ScriptComponent] on_update error: {exc}")
        else:
            fn = self._get_fn("on_update")
            if fn is not None:
                try:
                    fn(go, dt)
                except Exception as exc:
                    print(f"[ScriptComponent] on_update error: {exc}")

    def call_stop(self, go: Any) -> None:
        """Chama on_stop(go) no script, se existir."""
        if self._instance is not None:
            if hasattr(self._instance, "on_stop"):
                try:
                    self._instance.on_stop(go)
                except Exception as exc:
                    print(f"[ScriptComponent] on_stop error: {exc}")
        else:
            fn = self._get_fn("on_stop")
            if fn is not None:
                try:
                    fn(go)
                except Exception as exc:
                    print(f"[ScriptComponent] on_stop error: {exc}")
        self._instance = None

    # ------------------------------------------------------------------
    # Detecção de propriedades editáveis no Inspector
    # ------------------------------------------------------------------

    def _load_defaults(self) -> None:
        """Detecta propriedades públicas do script para exibir no Inspector.

        Suporta dois formatos:
        1. Variáveis de módulo (float, int, str, bool) — ex.: speed = 200.0
        2. Anotações de instância em classe (exceto ClassVar)
        """
        if self._module is None:
            return

        cls = self._resolve_class()
        if cls is not None:
            self._load_defaults_from_class(cls)
        else:
            self._load_defaults_from_module()

    def _load_defaults_from_module(self) -> None:
        """Lê variáveis de módulo públicas como propriedades editáveis."""
        _PRIMITIVE = (float, int, str, bool)
        for name, value in vars(self._module).items():
            if name.startswith("_"):
                continue
            if callable(value):
                continue
            if not isinstance(value, _PRIMITIVE):
                continue
            if name not in self.properties:
                self.properties[name] = value

    def _load_defaults_from_class(self, cls: type) -> None:
        hints: dict[str, Any] = {}
        for klass in reversed(cls.__mro__):
            hints.update(getattr(klass, "__annotations__", {}))
        for name, annotation in hints.items():
            if name.startswith("_"):
                continue
            if "ClassVar" in str(annotation):
                continue
            if name not in self.properties:
                try:
                    default = getattr(cls, name)
                except AttributeError:
                    default = self._default_for_annotation(annotation)
                self.properties[name] = default

    @staticmethod
    def _default_for_annotation(annotation: Any) -> Any:
        mapping = {float: 0.0, int: 0, str: "", bool: False}
        return mapping.get(annotation, None)

    # ------------------------------------------------------------------
    # Serialização
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
            self._load_module()
            self._load_defaults()
        self.properties.update(stored)

    # ------------------------------------------------------------------
    # Helpers públicos
    # ------------------------------------------------------------------

    def set_property(self, name: str, value: Any) -> None:
        self.properties[name] = value

    def get_property(self, name: str, default: Any = None) -> Any:
        return self.properties.get(name, default)

    def script_name(self) -> str:
        return Path(self.script_path).name if self.script_path else ""
