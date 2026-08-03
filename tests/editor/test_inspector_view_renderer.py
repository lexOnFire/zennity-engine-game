from types import SimpleNamespace

from editor.inspector_view_renderer import InspectorViewRenderer


class Field:
    def __init__(self) -> None:
        self.value = None
        self.enabled = True

    def setValue(self, value) -> None:
        self.value = value

    def setChecked(self, value) -> None:
        self.value = value

    def setEnabled(self, value) -> None:
        self.enabled = value

    def setText(self, value) -> None:
        self.value = value

    def setStyleSheet(self, value) -> None:
        self.style = value


def test_physics_renderer_projects_box_and_rigidbody_without_mutating_model() -> None:
    cards = []
    obj = {
        "w": 40.0, "h": 20.0,
        "rigidbody": {"use_gravity": True, "is_kinematic": False},
        "collider": {"type": "box", "width": 38.0, "height": 18.0},
    }
    before = {key: value.copy() if isinstance(value, dict) else value for key, value in obj.items()}
    host = SimpleNamespace(
        _set_inspector_card_present=lambda key, present: cards.append((key, present)),
        show_rigidbody_chk=Field(),
        physics_fields={"use_gravity": Field(), "is_kinematic": Field()},
        show_collider_chk=Field(),
        collider_fields={key: Field() for key in ("width", "height", "radius", "offset_x", "offset_y")},
        collider_trigger_field=Field(),
    )

    InspectorViewRenderer(host).render_physics(obj)

    assert obj == before
    assert ("rigidbody", True) in cards
    assert ("collider", True) in cards
    assert host.collider_fields["width"].value == 38.0
    assert host.collider_fields["radius"].enabled is False


def test_renderer_card_is_hidden_for_camera_objects() -> None:
    cards = []
    field = Field()
    host = SimpleNamespace(
        _set_inspector_card_present=lambda key, present: cards.append((key, present)),
        show_renderer_chk=field,
        sprite_renderer_body=field,
        sprite_texture_field=SimpleNamespace(setText=lambda _value: None),
        sprite_color_button=SimpleNamespace(setStyleSheet=lambda _value: None),
        sprite_layer_combo=SimpleNamespace(
            findText=lambda _value: 0, addItem=lambda _value: None, setCurrentText=lambda _value: None,
        ),
        sprite_order_field=field,
    )

    InspectorViewRenderer(host).render_renderer({"camera": {}, "renderer_enabled": True})

    assert ("sprite", False) in cards


def test_ui_renderer_accepts_native_progress_bar() -> None:
    cards = []
    host = SimpleNamespace(
        _set_inspector_card_present=lambda key, present: cards.append((key, present)),
        show_ui_chk=Field(),
        ui_type_field=Field(),
        ui_text_field=Field(),
        ui_position_fields={key: Field() for key in ("x", "y", "width", "height", "font_size", "alpha")},
        ui_color_button=Field(),
        ui_image_path_field=Field(),
        ui_image_button=Field(),
        ui_interactable_field=Field(),
        ui_event_field=Field(),
        ui_target_combo=SimpleNamespace(
            clear=lambda: None, addItem=lambda _value: None, addItems=lambda _values: None,
            setCurrentText=lambda _value: None, setEnabled=lambda _value: None,
        ),
        _objects_by_name={"HealthBar": {}},
    )

    InspectorViewRenderer(host).render_ui(
        "HealthBar",
        {"ui": {"type": "progress_bar", "value": 75.0, "max_value": 100.0}},
    )

    assert ("ui", True) in cards
    assert host.show_ui_chk.value is True
    assert host.ui_type_field.value == "Barra de progresso"
