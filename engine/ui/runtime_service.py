"""
engine/ui/runtime_service.py
─────────────────────────────────────────────────────────────
UIRuntimeService — Registro centralizado de widgets em Play Mode.

Responsabilidade:
  - Registro determinístico de componentes UI em tempo de execução
  - Resolução de widgets por identificador único
  - Acesso type-safe a propriedades
  - Detecção de duplicatas e ambiguidades
  - Diagnostics e logging

Princípios:
  - Fonte de verdade única: ProgressBarComponent, LabelComponent, etc
  - Sem heurísticas silenciosas
  - Sem fallbacks invisíveis
  - Debug-friendly
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Tuple
from enum import Enum


class UIPropertyType(Enum):
    """Tipos de propriedade permitidos em UI widgets."""
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"
    TUPLE_INT = "tuple[int, int, int]"


class UIProperty:
    """Definição de propriedade com type safety e constraints."""

    def __init__(
        self,
        name: str,
        prop_type: UIPropertyType,
        getter: Optional[callable] = None,
        setter: Optional[callable] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.prop_type = prop_type
        self.getter = getter
        self.setter = setter
        self.constraints = constraints or {}

    def validate(self, value: Any) -> bool:
        """Valida valor contra constraints."""
        if self.prop_type == UIPropertyType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
            if "min" in self.constraints and value < self.constraints["min"]:
                return False
            if "max" in self.constraints and value > self.constraints["max"]:
                return False
            return True

        if self.prop_type == UIPropertyType.BOOL:
            return isinstance(value, bool)

        if self.prop_type == UIPropertyType.STRING:
            return isinstance(value, str)

        if self.prop_type == UIPropertyType.TUPLE_INT:
            if not isinstance(value, (tuple, list)):
                return False
            if len(value) != 3:
                return False
            return all(isinstance(x, int) for x in value)

        return True


class UIWidgetSchema:
    """Schema de propriedades para um tipo de widget."""

    def __init__(self, widget_type: str) -> None:
        self.widget_type = widget_type
        self.properties: Dict[str, UIProperty] = {}

    def add_property(self, prop: UIProperty) -> None:
        """Registra propriedade."""
        self.properties[prop.name] = prop

    def get_property(self, name: str) -> Optional[UIProperty]:
        """Retorna definição de propriedade."""
        return self.properties.get(name)

    def is_valid_property(self, name: str) -> bool:
        """Verifica se propriedade é conhecida."""
        return name in self.properties


class UIRuntimeServiceError(Exception):
    """Exceção base do UIRuntimeService."""
    pass


class UIWidgetNotFoundError(UIRuntimeServiceError):
    """Widget não encontrado."""
    pass


class UIWidgetAmbiguousError(UIRuntimeServiceError):
    """Múltiplos widgets com mesmo identificador."""
    pass


class UIPropertyTypeError(UIRuntimeServiceError):
    """Tipo de propriedade inválido."""
    pass


class UIPropertyNotFoundError(UIRuntimeServiceError):
    """Propriedade não existe neste tipo de widget."""
    pass


class UIRuntimeService:
    """
    Registro centralizado de componentes de UI em tempo de execução.

    Uso:
        ui = UIRuntimeService.instance()
        ui.register_widget(progress_component)

        value = ui.get_property("HealthBar", "value")

        ui.set_property("HealthBar", "value", 75.0)
    """

    _inst: Optional["UIRuntimeService"] = None

    def __init__(self) -> None:
        self._widgets: Dict[str, List[Any]] = {}
        self._schemas: Dict[str, UIWidgetSchema] = {}
        self._initialize_schemas()

    @classmethod
    def instance(cls) -> "UIRuntimeService":
        """Retorna instância singleton."""
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    @classmethod
    def reset(cls) -> None:
        """Limpa o singleton — útil ao trocar de cena."""
        if cls._inst is not None:
            cls._inst.clear()
        cls._inst = None

    def _initialize_schemas(self) -> None:
        """Inicializa schemas de tipos de widgets conhecidos."""
        # ProgressBarComponent
        pb_schema = UIWidgetSchema("ProgressBar")
        pb_schema.add_property(UIProperty(
            "value",
            UIPropertyType.FLOAT,
            getter=lambda w: w.value,
            setter=lambda w, v: w.set_value(v),
            constraints={"min": 0.0},
        ))
        pb_schema.add_property(UIProperty(
            "max_value",
            UIPropertyType.FLOAT,
            getter=lambda w: w.max_value,
            setter=lambda w, v: setattr(w, "max_value", v),
            constraints={"min": 0.0001},
        ))
        pb_schema.add_property(UIProperty(
            "visible",
            UIPropertyType.BOOL,
            getter=lambda w: w.visible,
            setter=lambda w, v: setattr(w, "visible", v),
        ))
        pb_schema.add_property(UIProperty(
            "x",
            UIPropertyType.FLOAT,
            getter=lambda w: w.x,
            setter=lambda w, v: setattr(w, "x", v),
        ))
        pb_schema.add_property(UIProperty(
            "y",
            UIPropertyType.FLOAT,
            getter=lambda w: w.y,
            setter=lambda w, v: setattr(w, "y", v),
        ))
        pb_schema.add_property(UIProperty(
            "width",
            UIPropertyType.FLOAT,
            getter=lambda w: w.width,
            setter=lambda w, v: setattr(w, "width", v),
        ))
        pb_schema.add_property(UIProperty(
            "height",
            UIPropertyType.FLOAT,
            getter=lambda w: w.height,
            setter=lambda w, v: setattr(w, "height", v),
        ))
        pb_schema.add_property(UIProperty(
            "fill_color",
            UIPropertyType.TUPLE_INT,
            getter=lambda w: w.fill_color,
            setter=lambda w, v: setattr(w, "fill_color", tuple(v)),
        ))
        pb_schema.add_property(UIProperty(
            "bg_color",
            UIPropertyType.TUPLE_INT,
            getter=lambda w: w.bg_color,
            setter=lambda w, v: setattr(w, "bg_color", tuple(v)),
        ))
        self._schemas["ProgressBar"] = pb_schema

        # LabelComponent
        label_schema = UIWidgetSchema("Label")
        label_schema.add_property(UIProperty(
            "text",
            UIPropertyType.STRING,
            getter=lambda w: w.text,
            setter=lambda w, v: setattr(w, "text", v),
        ))
        label_schema.add_property(UIProperty(
            "font_size",
            UIPropertyType.INT,
            getter=lambda w: w.font_size,
            setter=lambda w, v: setattr(w, "font_size", v),
        ))
        label_schema.add_property(UIProperty(
            "color",
            UIPropertyType.TUPLE_INT,
            getter=lambda w: w.color,
            setter=lambda w, v: setattr(w, "color", tuple(v)),
        ))
        self._schemas["Label"] = label_schema

    def register_widget(self, widget: Any) -> None:
        """
        Registra um componente de UI no serviço.

        Args:
            widget: RuntimeUIElement ou subclasse (ProgressBarComponent, LabelComponent, etc)

        Raises:
            UIRuntimeServiceError: Se widget_name vazio
        """
        widget_name = str(getattr(widget, "widget_name", "")).strip()
        component_type = getattr(widget, "component_type", "UIElement")

        if not widget_name:
            # Fallback: usar class name se widget_name não setado
            widget_name = widget.__class__.__name__

        if not widget_name:
            raise UIRuntimeServiceError(f"Widget sem identificador: {widget}")

        if widget_name not in self._widgets:
            self._widgets[widget_name] = []

        self._widgets[widget_name].append(widget)

    def unregister_widget(self, widget: Any) -> bool:
        """
        Remove widget do registro.

        Returns:
            True se removido, False se não encontrado
        """
        widget_name = str(getattr(widget, "widget_name", "")).strip()

        if not widget_name or widget_name not in self._widgets:
            return False

        if widget in self._widgets[widget_name]:
            self._widgets[widget_name].remove(widget)
            if not self._widgets[widget_name]:
                del self._widgets[widget_name]
            return True

        return False

    def resolve_widget(
        self,
        identifier: str,
        expected_type: Optional[str] = None,
    ) -> Any:
        """
        Resolve widget por identificador.

        Args:
            identifier: widget_name
            expected_type: Component type esperado (ex: "ProgressBar")

        Returns:
            Widget encontrado

        Raises:
            UIWidgetNotFoundError: Se não encontrado
            UIWidgetAmbiguousError: Se múltiplos encontrados
            UIPropertyTypeError: Se tipo errado
        """
        identifier = str(identifier).strip()

        if identifier not in self._widgets or not self._widgets[identifier]:
            available = self._list_available_identifiers()
            msg = f"Widget '{identifier}' não encontrado."
            if available:
                msg += f"\nDisponiveis: {available}"
            raise UIWidgetNotFoundError(msg)

        widgets = self._widgets[identifier]

        if len(widgets) > 1:
            types = [getattr(w, "component_type", "?") for w in widgets]
            raise UIWidgetAmbiguousError(
                f"Múltiplos widgets '{identifier}': {types}"
            )

        widget = widgets[0]

        if expected_type:
            widget_type = str(getattr(widget, "component_type", "UIElement"))
            if widget_type != expected_type:
                raise UIPropertyTypeError(
                    f"Widget '{identifier}' é {widget_type}, "
                    f"mas esperado {expected_type}"
                )

        return widget

    def get_property(
        self,
        identifier: str,
        property_name: str,
        expected_type: Optional[str] = None,
    ) -> Any:
        """
        Lê propriedade de widget com type safety.

        Args:
            identifier: widget_name
            property_name: Nome da propriedade
            expected_type: Component type esperado

        Returns:
            Valor da propriedade

        Raises:
            UIWidgetNotFoundError: Widget não encontrado
            UIPropertyNotFoundError: Propriedade não existe
            UIPropertyTypeError: Tipo inválido
        """
        widget = self.resolve_widget(identifier, expected_type)
        widget_type = getattr(widget, "component_type", "UIElement")

        schema = self._schemas.get(widget_type)
        if not schema:
            # Fallback: permitir getattr sem schema se type não registrado
            if hasattr(widget, property_name):
                return getattr(widget, property_name)
            raise UIPropertyNotFoundError(
                f"Propriedade '{property_name}' não existe em {widget_type}"
            )

        prop = schema.get_property(property_name)
        if not prop:
            raise UIPropertyNotFoundError(
                f"Propriedade '{property_name}' não definida para {widget_type}"
            )

        if prop.getter:
            return prop.getter(widget)
        return getattr(widget, property_name, None)

    def set_property(
        self,
        identifier: str,
        property_name: str,
        value: Any,
        expected_type: Optional[str] = None,
    ) -> None:
        """
        Escreve propriedade de widget com validação.

        Args:
            identifier: widget_name
            property_name: Nome da propriedade
            value: Novo valor
            expected_type: Component type esperado

        Raises:
            UIWidgetNotFoundError: Widget não encontrado
            UIPropertyNotFoundError: Propriedade não existe
            UIPropertyTypeError: Tipo inválido
        """
        widget = self.resolve_widget(identifier, expected_type)
        widget_type = getattr(widget, "component_type", "UIElement")

        schema = self._schemas.get(widget_type)
        if not schema:
            # Fallback: permitir setattr sem schema se type não registrado
            setattr(widget, property_name, value)
            return

        prop = schema.get_property(property_name)
        if not prop:
            raise UIPropertyNotFoundError(
                f"Propriedade '{property_name}' não definida para {widget_type}"
            )

        if not prop.validate(value):
            raise UIPropertyTypeError(
                f"Valor inválido para '{property_name}' "
                f"({prop.prop_type}): {value}"
            )

        if prop.setter:
            prop.setter(widget, value)
        else:
            setattr(widget, property_name, value)

    def exists(self, identifier: str) -> bool:
        """Verifica se widget está registrado."""
        identifier = str(identifier).strip()
        return identifier in self._widgets and bool(self._widgets[identifier])

    def get_all_widgets(self, widget_type: Optional[str] = None) -> List[Any]:
        """Retorna todos widgets, opcionalmente filtrado por tipo."""
        widgets = []
        for widget_list in self._widgets.values():
            for widget in widget_list:
                if widget_type is None:
                    widgets.append(widget)
                elif getattr(widget, "component_type", "") == widget_type:
                    widgets.append(widget)
        return widgets

    def clear(self) -> None:
        """Remove todos os widgets do registro."""
        self._widgets.clear()

    def _list_available_identifiers(self) -> str:
        """Retorna lista de identificadores disponíveis para diagnostics."""
        ids = list(self._widgets.keys())
        if len(ids) > 10:
            return ", ".join(ids[:10]) + f", ... (+{len(ids) - 10} mais)"
        return ", ".join(ids) if ids else "(nenhum)"

    def diagnostic_report(self) -> str:
        """Retorna relatório diagnostico do registro."""
        lines = ["UIRuntimeService Registry:"]
        lines.append(f"  Total widgets: {sum(len(v) for v in self._widgets.values())}")
        lines.append("")

        if not self._widgets:
            lines.append("  (vazio)")
            return "\n".join(lines)

        by_type = {}
        for widget_list in self._widgets.values():
            for widget in widget_list:
                wtype = getattr(widget, "component_type", "UIElement")
                if wtype not in by_type:
                    by_type[wtype] = []
                by_type[wtype].append(widget)

        for wtype, widgets in sorted(by_type.items()):
            lines.append(f"  {wtype}: {len(widgets)}")
            for widget in widgets:
                wname = getattr(widget, "widget_name", "?")
                lines.append(f"    - {wname}")

        return "\n".join(lines)
