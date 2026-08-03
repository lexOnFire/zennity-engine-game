"""
engine/component_registry.py
────────────────────────────────────────────────────────────────
Registro central de componentes da Zennity Engine.

Permite:
  - Registrar qualquer classe Component por nome/alias
  - Instanciar um componente pelo nome (usado pela deserialização de cenas)
  - Listar todos os tipos registrados

Uso:
    from engine.component_registry import ComponentRegistry

    # Registro manual
    ComponentRegistry.register(MyComponent)
    ComponentRegistry.register(MyComponent, alias="my_component")

    # Resolução por nome
    cls = ComponentRegistry.resolve("MyComponent")
    instance = ComponentRegistry.create("MyComponent", hp=100)

    # Decorador
    @ComponentRegistry.component
    class Bullet(Component):
        ...
"""
from __future__ import annotations

from typing import Dict, Optional, Type, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.core.component import Component


class _ComponentRegistryMeta(type):
    """Metaclass que cria a tabela de registro como atributo de classe."""
    pass


class StaticComponentRegistry(metaclass=_ComponentRegistryMeta):
    """
    Registro singleton de componentes.
    Todos os métodos são @classmethod — não instancie esta classe.
    """

    _registry: Dict[str, Type["Component"]] = {}

    # ------------------------------------------------------------------ #
    # Registro                                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def register(
        cls,
        component_class: Type["Component"],
        alias: Optional[str] = None,
    ) -> Type["Component"]:
        """
        Registra *component_class* sob ``component_class.__name__`` e,
        opcionalmente, sob *alias* adicional.

        Retorna a própria classe para uso como decorador.
        """
        key = component_class.__name__
        cls._registry[key] = component_class
        if alias and alias != key:
            cls._registry[alias] = component_class
        return component_class

    @classmethod
    def component(
        cls,
        _cls: Optional[Type["Component"]] = None,
        *,
        alias: Optional[str] = None,
    ):
        """
        Decorador de registro.

            @ComponentRegistry.component
            class Health(Component): ...

            @ComponentRegistry.component(alias="hp")
            class Health(Component): ...
        """
        def _decorator(klass: Type["Component"]) -> Type["Component"]:
            return cls.register(klass, alias=alias)

        if _cls is not None:
            return _decorator(_cls)
        return _decorator

    # ------------------------------------------------------------------ #
    # Resolução                                                           #
    # ------------------------------------------------------------------ #

    @classmethod
    def resolve(cls, name: str) -> Type["Component"]:
        """
        Retorna a classe registrada sob *name*.
        Levanta KeyError se não encontrada.
        """
        try:
            return cls._registry[name]
        except KeyError:
            registered = list(cls._registry.keys())
            raise KeyError(
                f"Componente '{name}' não registrado. "
                f"Registrados: {registered}"
            ) from None

    @classmethod
    def get(cls, name: str, default=None) -> Optional[Type["Component"]]:
        """Versão segura de resolve() — retorna *default* se não encontrado."""
        return cls._registry.get(name, default)

    # ------------------------------------------------------------------ #
    # Instanciação                                                        #
    # ------------------------------------------------------------------ #

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> "Component":
        """
        Instancia e retorna um componente pelo nome registrado.

        Todos os kwargs são repassados ao ``__init__`` da classe.
        """
        klass = cls.resolve(name)
        return klass(**kwargs)

    # ------------------------------------------------------------------ #
    # Listagem                                                            #
    # ------------------------------------------------------------------ #

    @classmethod
    def all_names(cls) -> list:
        """Retorna lista de todos os nomes registrados (sem duplicatas de alias)."""
        seen: set = set()
        result = []
        for name, klass in cls._registry.items():
            if klass not in seen:
                seen.add(klass)
                result.append(name)
        return result

    @classmethod
    def all_classes(cls) -> list:
        """Retorna lista de classes únicas registradas."""
        return list(dict.fromkeys(cls._registry.values()))

    # ------------------------------------------------------------------ #
    # Limpeza (testes)                                                    #
    # ------------------------------------------------------------------ #

    @classmethod
    def clear(cls) -> None:
        """Remove todos os registros. Usado apenas em testes."""
        cls._registry.clear()

    # ------------------------------------------------------------------ #
    # Repr                                                                #
    # ------------------------------------------------------------------ #

    def __repr__(cls) -> str:  # type: ignore[override]
        return f"<ComponentRegistry [{len(cls._registry)} entries]>"


ComponentRegistry = StaticComponentRegistry
