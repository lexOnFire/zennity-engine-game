"""Provedor de Preview desacoplado para a Plataforma de Animação."""
from pathlib import Path
from typing import Any
from engine.animation.clip_asset import load_animation_asset
from engine.animation.controller_asset import load_animator_controller


class AnimationPreviewProvider:
    """Gera dados de visualização e previews para assets de animação (.zanim e .zanimator)."""

    @classmethod
    def generate_preview_data(cls, path: Path) -> dict[str, Any]:
        path = Path(path)
        if not path.exists():
            return {"label": "Animation Resource", "details": f"Arquivo não encontrado: {path.name}"}

        ext = path.suffix.lower()
        if ext == ".zanim":
            try:
                asset = load_animation_asset(path)
                return {
                    "label": "🎞 Animation",
                    "details": f"Clip: <b>{asset.get('name', 'Clip')}</b><br>Frames: {len(asset.get('frames', []))}<br>FPS: {asset.get('fps', 10.0):g}<br>Loop: {'Sim' if asset.get('loop') else 'Não'}",
                }
            except Exception as exc:
                return {"label": "🎞 Animation", "details": f"Erro ao ler clipe: {exc}"}

        if ext == ".zanimator":
            try:
                asset = load_animator_controller(path)
                return {
                    "label": "◉ Animator Controller",
                    "details": f"Controller: <b>{asset.get('name', 'Controller')}</b><br>Estado Inicial: {asset.get('initial_state')}<br>Estados: {len(asset.get('states', {}))}<br>Transições: {len(asset.get('transitions', []))}",
                }
            except Exception as exc:
                return {"label": "◉ Animator Controller", "details": f"Erro ao ler controlador: {exc}"}

        return {"label": "Animation Resource", "details": str(path.name)}
