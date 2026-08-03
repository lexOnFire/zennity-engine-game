"""
editor/inspector/component_preset_manager.py
─────────────────────────────────────────────────────────────────────────────
Gerenciamento de Presets de Componentes (Salvar/Carregar configurações do Inspector).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


class ComponentPresetManager:
    """Salva e carrega configurações de componentes em arquivos .zpreset."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd())
        self.presets_dir = self.project_root / "Assets" / "Presets"
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def save_preset(self, component_name: str, preset_title: str, properties: Dict[str, Any]) -> Path:
        filename = f"{component_name}_{preset_title.replace(' ', '_')}.zpreset"
        file_path = self.presets_dir / filename
        data = {
            "format": "zennity.component_preset",
            "component": component_name,
            "title": preset_title,
            "properties": properties,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path

    def load_preset(self, file_path: Path) -> Dict[str, Any] | None:
        if not file_path.is_file():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("properties")
        except Exception:
            return None

    def list_presets_for_component(self, component_name: str) -> list[Path]:
        if not self.presets_dir.is_dir():
            return []
        prefix = f"{component_name}_".lower()
        return [
            p for p in self.presets_dir.glob("*.zpreset")
            if p.name.lower().startswith(prefix)
        ]
