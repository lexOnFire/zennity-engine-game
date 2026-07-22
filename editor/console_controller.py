"""Bounded console model and rendering for the isolated editor."""
from __future__ import annotations

from typing import Any


class ConsoleController:
    def __init__(self, host: Any, *, maximum_records: int = 2000) -> None:
        if maximum_records < 1:
            raise ValueError("maximum_records must be positive")
        self.host = host
        self.maximum_records = int(maximum_records)
        self.records: list[tuple[str, str]] = []
        self._connected = False

    def connect(self) -> bool:
        if self._connected:
            return False
        for check in self.host.console_level_checks.values():
            check.toggled.connect(self.refresh)
        self.host.console_clear_button.clicked.connect(self.clear)
        self._connected = True
        return True

    def disconnect(self) -> bool:
        if not self._connected:
            return False
        for check in self.host.console_level_checks.values():
            check.toggled.disconnect(self.refresh)
        self.host.console_clear_button.clicked.disconnect(self.clear)
        self._connected = False
        return True

    def log(self, level: str, message: str) -> None:
        normalized = str(level).upper()
        text = str(message)
        self.records.append((normalized, text))
        overflow = len(self.records) - self.maximum_records
        if overflow > 0:
            del self.records[:overflow]
        check = self.host.console_level_checks.get(normalized)
        if check is None or check.isChecked():
            self.host.console_output.appendPlainText(f"[{normalized}] {text}")

    def refresh(self) -> None:
        visible = {
            level for level, check in self.host.console_level_checks.items()
            if check.isChecked()
        }
        self.host.console_output.setPlainText("\n".join(
            f"[{level}] {message}"
            for level, message in self.records
            if level in visible
        ))

    def clear(self) -> None:
        self.records.clear()
        self.host.console_output.clear()
