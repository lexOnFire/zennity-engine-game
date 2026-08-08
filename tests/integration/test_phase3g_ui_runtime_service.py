"""
PHASE 3G: Testes de UIRuntimeService

Testa:
- Auto-registration
- Resolução determinística
- Type safety
- Detecção de duplicatas
- Property validation
- Cleanup
"""
import pytest
from engine.ui.runtime_service import (
    UIRuntimeService,
    UIWidgetNotFoundError,
    UIWidgetAmbiguousError,
    UIPropertyNotFoundError,
    UIPropertyTypeError,
)
from engine.ui.runtime_components import ProgressBarComponent, LabelComponent


class TestUIRuntimeServiceRegistration:
    """Testa registro de widgets."""

    def setup_method(self):
        UIRuntimeService.reset()
        self.ui_service = UIRuntimeService.instance()

    def test_register_progress_bar(self):
        """Registra ProgressBar com widget_name."""
        widget = ProgressBarComponent(value=75.0, max_value=100.0)
        widget.widget_name = "HealthBar"

        self.ui_service.register_widget(widget)
        assert self.ui_service.exists("HealthBar")

    def test_register_multiple_types(self):
        """Registra múltiplos tipos de widget."""
        pb = ProgressBarComponent(value=50.0)
        pb.widget_name = "Mana"

        label = LabelComponent(text="Score")
        label.widget_name = "ScoreLabel"

        self.ui_service.register_widget(pb)
        self.ui_service.register_widget(label)

        assert self.ui_service.exists("Mana")
        assert self.ui_service.exists("ScoreLabel")

    def test_unregister_widget(self):
        """Remove widget do registro."""
        widget = ProgressBarComponent(value=75.0)
        widget.widget_name = "HealthBar"

        self.ui_service.register_widget(widget)
        assert self.ui_service.exists("HealthBar")

        removed = self.ui_service.unregister_widget(widget)
        assert removed is True
        assert not self.ui_service.exists("HealthBar")

    def test_unregister_not_found(self):
        """Unregister de widget não registrado retorna False."""
        widget = ProgressBarComponent(value=75.0)
        widget.widget_name = "NotRegistered"

        removed = self.ui_service.unregister_widget(widget)
        assert removed is False

    def test_clear_all_widgets(self):
        """Limpa todos os widgets."""
        pb1 = ProgressBarComponent(value=50.0)
        pb1.widget_name = "Bar1"
        pb2 = ProgressBarComponent(value=75.0)
        pb2.widget_name = "Bar2"

        self.ui_service.register_widget(pb1)
        self.ui_service.register_widget(pb2)
        assert self.ui_service.exists("Bar1")
        assert self.ui_service.exists("Bar2")

        self.ui_service.clear()
        assert not self.ui_service.exists("Bar1")
        assert not self.ui_service.exists("Bar2")


class TestUIRuntimeServiceResolution:
    """Testa resolução de widgets."""

    def setup_method(self):
        UIRuntimeService.reset()
        self.ui_service = UIRuntimeService.instance()

    def test_resolve_widget(self):
        """Resolve widget por identificador."""
        widget = ProgressBarComponent(value=75.0, max_value=100.0)
        widget.widget_name = "HealthBar"
        self.ui_service.register_widget(widget)

        resolved = self.ui_service.resolve_widget("HealthBar")
        assert resolved is widget

    def test_resolve_not_found(self):
        """Lança UIWidgetNotFoundError se não encontrado."""
        with pytest.raises(UIWidgetNotFoundError):
            self.ui_service.resolve_widget("NonExistent")

    def test_resolve_with_expected_type(self):
        """Resolve com validação de tipo."""
        widget = ProgressBarComponent(value=75.0)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        resolved = self.ui_service.resolve_widget("Bar", expected_type="ProgressBar")
        assert resolved is widget

    def test_resolve_wrong_type(self):
        """Lança UIPropertyTypeError se tipo errado."""
        widget = LabelComponent(text="Score")
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyTypeError):
            self.ui_service.resolve_widget("Bar", expected_type="ProgressBar")

    def test_resolve_duplicate(self):
        """Lança UIWidgetAmbiguousError se múltiplos encontrados."""
        pb1 = ProgressBarComponent(value=50.0)
        pb1.widget_name = "HealthBar"
        pb2 = ProgressBarComponent(value=75.0)
        pb2.widget_name = "HealthBar"

        self.ui_service.register_widget(pb1)
        self.ui_service.register_widget(pb2)

        with pytest.raises(UIWidgetAmbiguousError):
            self.ui_service.resolve_widget("HealthBar")


class TestUIRuntimeServiceProperties:
    """Testa acesso a propriedades."""

    def setup_method(self):
        UIRuntimeService.reset()
        self.ui_service = UIRuntimeService.instance()

    def test_get_property_value(self):
        """Lê propriedade 'value'."""
        widget = ProgressBarComponent(value=75.0, max_value=100.0)
        widget.widget_name = "HealthBar"
        self.ui_service.register_widget(widget)

        value = self.ui_service.get_property("HealthBar", "value")
        assert value == 75.0

    def test_get_property_max_value(self):
        """Lê propriedade 'max_value'."""
        widget = ProgressBarComponent(value=50.0, max_value=200.0)
        widget.widget_name = "Mana"
        self.ui_service.register_widget(widget)

        max_val = self.ui_service.get_property("Mana", "max_value")
        assert max_val == 200.0

    def test_get_property_not_found(self):
        """Lança UIPropertyNotFoundError se propriedade não existe."""
        widget = ProgressBarComponent(value=75.0)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyNotFoundError):
            self.ui_service.get_property("Bar", "nonexistent_property")

    def test_set_property_value(self):
        """Escreve propriedade 'value' com validação."""
        widget = ProgressBarComponent(value=50.0, max_value=100.0)
        widget.widget_name = "HealthBar"
        self.ui_service.register_widget(widget)

        self.ui_service.set_property("HealthBar", "value", 75.0)
        assert widget.value == 75.0

        # Verificar leitura após escrita (mesma instância)
        read_value = self.ui_service.get_property("HealthBar", "value")
        assert read_value == 75.0

    def test_set_property_clamps_value(self):
        """Clampeia valor ao máximo via set_value."""
        widget = ProgressBarComponent(value=50.0, max_value=100.0)
        widget.widget_name = "HealthBar"
        self.ui_service.register_widget(widget)

        # Tentar definir acima do máximo
        self.ui_service.set_property("HealthBar", "value", 150.0)

        # Deve ter clamped
        assert widget.value == 100.0

    def test_set_property_invalid_type(self):
        """Rejeita tipo inválido."""
        widget = ProgressBarComponent(value=50.0)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyTypeError):
            self.ui_service.set_property("Bar", "value", "not a number")

    def test_set_property_with_expected_type(self):
        """Define propriedade com validação de tipo de widget."""
        widget = ProgressBarComponent(value=50.0, max_value=100.0)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        self.ui_service.set_property("Bar", "value", 80.0, expected_type="ProgressBar")
        assert widget.value == 80.0


class TestUIRuntimeServiceValidation:
    """Testa validação de propriedades."""

    def setup_method(self):
        UIRuntimeService.reset()
        self.ui_service = UIRuntimeService.instance()

    def test_validate_positive_value(self):
        """Rejeita valor negativo para 'value'."""
        widget = ProgressBarComponent(value=50.0)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyTypeError):
            self.ui_service.set_property("Bar", "value", -10.0)

    def test_validate_max_value_positive(self):
        """Rejeita max_value zero ou negativo."""
        widget = ProgressBarComponent(value=50.0, max_value=100.0)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyTypeError):
            self.ui_service.set_property("Bar", "max_value", 0.0)

    def test_validate_bool_property(self):
        """Valida propriedade booleana."""
        widget = ProgressBarComponent(visible=True)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        self.ui_service.set_property("Bar", "visible", False)
        assert widget.visible is False

    def test_validate_bool_rejects_non_bool(self):
        """Rejeita não-booleano para propriedade bool."""
        widget = ProgressBarComponent(visible=True)
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyTypeError):
            self.ui_service.set_property("Bar", "visible", "yes")

    def test_validate_tuple_color(self):
        """Valida propriedade de cor (tuple de ints)."""
        widget = ProgressBarComponent(fill_color=(46, 204, 113))
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        self.ui_service.set_property("Bar", "fill_color", (255, 0, 0))
        assert widget.fill_color == (255, 0, 0)

    def test_validate_tuple_rejects_wrong_length(self):
        """Rejeita tuple com tamanho errado."""
        widget = ProgressBarComponent(fill_color=(46, 204, 113))
        widget.widget_name = "Bar"
        self.ui_service.register_widget(widget)

        with pytest.raises(UIPropertyTypeError):
            self.ui_service.set_property("Bar", "fill_color", (255, 0))


class TestUIRuntimeServiceLabelProperties:
    """Testa propriedades de LabelComponent."""

    def setup_method(self):
        UIRuntimeService.reset()
        self.ui_service = UIRuntimeService.instance()

    def test_label_get_text(self):
        """Lê propriedade 'text' de Label."""
        label = LabelComponent(text="Hello World")
        label.widget_name = "Title"
        self.ui_service.register_widget(label)

        text = self.ui_service.get_property("Title", "text")
        assert text == "Hello World"

    def test_label_set_text(self):
        """Escreve propriedade 'text' de Label."""
        label = LabelComponent(text="Initial")
        label.widget_name = "Title"
        self.ui_service.register_widget(label)

        self.ui_service.set_property("Title", "text", "Updated")
        assert label.text == "Updated"

    def test_label_get_font_size(self):
        """Lê propriedade 'font_size'."""
        label = LabelComponent(text="Score", font_size=32)
        label.widget_name = "ScoreLabel"
        self.ui_service.register_widget(label)

        size = self.ui_service.get_property("ScoreLabel", "font_size")
        assert size == 32


class TestUIRuntimeServiceDiagnostics:
    """Testa relatórios diagnosticos."""

    def setup_method(self):
        UIRuntimeService.reset()
        self.ui_service = UIRuntimeService.instance()

    def test_diagnostic_empty(self):
        """Diagnostic report para registry vazio."""
        report = self.ui_service.diagnostic_report()
        assert "UIRuntimeService Registry:" in report
        assert "(vazio)" in report

    def test_diagnostic_with_widgets(self):
        """Diagnostic report com widgets registrados."""
        pb = ProgressBarComponent(value=50.0)
        pb.widget_name = "HealthBar"
        label = LabelComponent(text="Score")
        label.widget_name = "ScoreLabel"

        self.ui_service.register_widget(pb)
        self.ui_service.register_widget(label)

        report = self.ui_service.diagnostic_report()
        assert "ProgressBar: 1" in report
        assert "Label: 1" in report
        assert "HealthBar" in report
        assert "ScoreLabel" in report

    def test_diagnostic_with_duplicates(self):
        """Diagnostic report com widgets duplicados."""
        pb1 = ProgressBarComponent(value=50.0)
        pb1.widget_name = "Bar"
        pb2 = ProgressBarComponent(value=75.0)
        pb2.widget_name = "Bar"

        self.ui_service.register_widget(pb1)
        self.ui_service.register_widget(pb2)

        report = self.ui_service.diagnostic_report()
        assert "ProgressBar: 2" in report


class TestUIRuntimeServiceSingleton:
    """Testa padrão singleton."""

    def test_singleton_instance(self):
        """Retorna mesma instância."""
        UIRuntimeService.reset()

        service1 = UIRuntimeService.instance()
        service2 = UIRuntimeService.instance()

        assert service1 is service2

    def test_reset_clears_singleton(self):
        """Reset limpa e recria singleton."""
        service1 = UIRuntimeService.instance()
        pb = ProgressBarComponent(value=50.0)
        pb.widget_name = "Bar"
        service1.register_widget(pb)
        assert service1.exists("Bar")

        UIRuntimeService.reset()
        service2 = UIRuntimeService.instance()

        assert service2 is not service1
        assert not service2.exists("Bar")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
