from engine.localization.manager import LocalizationManager, tr


def test_translate_uses_positional_fallback_for_unknown_key() -> None:
    manager = LocalizationManager()

    assert manager.translate("missing.key", "Texto padrão") == "Texto padrão"
    assert tr("missing.key", "Texto padrão") == "Texto padrão"


def test_translate_prefers_registered_translation_over_fallback() -> None:
    manager = LocalizationManager()
    manager._caches["en-US"] = {"known.key": "Translated"}

    assert manager.translate("known.key", "Fallback") == "Translated"
