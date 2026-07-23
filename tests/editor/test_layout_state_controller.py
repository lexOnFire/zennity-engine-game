from editor.layout_state_controller import LayoutStateController


class _Settings:
    def __init__(self, values=None) -> None:
        self.values = dict(values or {})

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value) -> None:
        self.values[key] = value

    def remove(self, key) -> None:
        self.values.pop(key, None)

    def sync(self) -> None:
        self.values["synced"] = True


class _Host:
    def __init__(self) -> None:
        self.geometry = b"default-geometry"
        self.state = b"default-state"
        self.accept_restore = True

    def saveGeometry(self):
        return self.geometry

    def saveState(self, version):
        assert version == LayoutStateController.SCHEMA_VERSION
        return self.state

    def restoreGeometry(self, value):
        self.geometry = value
        return self.accept_restore

    def restoreState(self, value, version):
        assert version == LayoutStateController.SCHEMA_VERSION
        self.state = value
        return self.accept_restore


def test_layout_round_trip_uses_versioned_state() -> None:
    host = _Host()
    settings = _Settings()
    controller = LayoutStateController(host, settings)
    host.geometry = b"custom-geometry"
    host.state = b"custom-state"

    controller.save()
    host.geometry = b"other"
    host.state = b"other"

    assert controller.restore() is True
    assert host.geometry == b"custom-geometry"
    assert host.state == b"custom-state"
    assert settings.values["synced"] is True


def test_corrupt_layout_is_removed_and_defaults_are_restored() -> None:
    host = _Host()
    settings = _Settings({
        "schemaVersion": LayoutStateController.SCHEMA_VERSION,
        "geometry": b"broken-geometry",
        "windowState": b"broken-state",
    })
    controller = LayoutStateController(host, settings)
    host.accept_restore = False

    assert controller.restore() is False
    assert "geometry" not in settings.values
    assert "windowState" not in settings.values
    assert "schemaVersion" not in settings.values


def test_unknown_layout_version_is_ignored() -> None:
    host = _Host()
    settings = _Settings({
        "schemaVersion": 999,
        "geometry": b"future",
        "windowState": b"future",
    })

    assert LayoutStateController(host, settings).restore() is False
    assert host.geometry == b"default-geometry"
