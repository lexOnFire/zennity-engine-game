"""Preview Provider da Plataforma de UI para renderização reativa no editor."""
from __future__ import annotations
from typing import Any
class UIPreviewProvider:
    """Provedor oficial de preview para layouts e componentes de UI."""

    def can_preview(self, asset: Any) -> bool:
        return hasattr(asset, "root_widgets") or getattr(asset, "asset_type", "") in ("ui_layout", "ui_prefab")

    def generate_preview(self, asset: Any) -> dict:
        widgets_data = getattr(asset, "root_widgets", [])
        return {
            "type": "ui_preview",
            "widgets_count": len(widgets_data),
            "rendered": True,
        }
