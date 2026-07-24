"""Operações de estado aplicáveis a canais de áudio reais ou simulados."""
from __future__ import annotations

from typing import Any, Mapping


def set_channels_paused(channels: Mapping[str, Any], paused: bool) -> None:
    method_name = "pause" if paused else "unpause"
    for channel in list(channels.values()):
        method = getattr(channel, method_name, None)
        if callable(method):
            method()

