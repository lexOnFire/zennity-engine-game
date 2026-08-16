"""Mixin de estado de execução e visualização de código para LogicNodeItem."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QBrush, QColor, QPen


class LogicNodeItemRuntimeMixin:
    """Isola estados de runtime, preview de código e estilos de borda do LogicNodeItem."""

    def toggle_code_preview(self) -> None:
        self._show_code = not self._show_code
        for port in (*self.input_ports.values(), *self.output_ports.values()):
            port.setVisible(not self._show_code and not self.collapsed)
        for label in self.port_labels:
            label.setVisible(not self._show_code and not self.collapsed)
        self.target_item.setVisible(bool(self._target_hint) and not self._show_code and not self.collapsed)
        self.code_item.setVisible(self._show_code and not self.collapsed)
        self.flip_control.setToolTip(
            "Voltar para as portas do bloco" if self._show_code else "Virar bloco e mostrar o código equivalente"
        )
        if self._show_code:
            self.refresh_text()
            self.summary_item.hide()
            self.target_item.hide()
            self.debug_item.hide()
            self.setBrush(QBrush(QColor("#111d18")))
        else:
            self.setBrush(QBrush(QColor("#151922")))
            self.set_runtime_state(*self._runtime_display)

    def set_runtime_state(
        self,
        active: bool,
        values: dict[str, Any] | None = None,
        error: str = "",
        paused: bool = False,
        data_evaluated: bool = False,
    ) -> None:
        self._runtime_display = (bool(active), values, str(error), bool(paused), bool(data_evaluated))
        if self.collapsed:
            self.summary_item.hide()
            self.target_item.hide()
            self.debug_item.hide()
            return
        if self._show_code:
            self.summary_item.hide()
            self.debug_item.hide()
            return
        visible = bool(active or error or paused or data_evaluated)
        self.summary_item.setVisible(not visible)
        self.target_item.setVisible(bool(self._target_hint) and not visible)
        self.debug_item.setVisible(visible)
        if not visible:
            self.debug_item.setPlainText("")
        else:
            if error:
                self.debug_item.setDefaultTextColor(QColor("#ff6b70"))
                self.debug_item.setPlainText("ERRO • " + error[:54])
            elif paused:
                self.debug_item.setDefaultTextColor(QColor("#e6b85c"))
                self.debug_item.setPlainText("PAUSADO ANTES DE EXECUTAR")
            elif active:
                self.debug_item.setDefaultTextColor(QColor("#7ee787"))
                pairs = list((values or {}).items())[:2]
                text = " • ".join(f"{name}={value}" for name, value in pairs) if pairs else "EXECUTANDO"
                self.debug_item.setPlainText(text)
            elif data_evaluated:
                self.debug_item.setDefaultTextColor(QColor("#00e5ff"))
                pairs = list((values or {}).items())[:2]
                text = " • ".join(f"{name}={value}" for name, value in pairs) if pairs else "DADOS AVALIADOS"
                self.debug_item.setPlainText(text)
        self._update_border_style()

    def set_breakpoint(self, enabled: bool) -> None:
        self.breakpoint_item.setVisible(bool(enabled))

    def _update_border_style(self) -> None:
        active, values, error, paused, *rest = self._runtime_display
        data_evaluated = rest[0] if rest else False
        visible = bool(active or error or paused or data_evaluated)
        if not visible:
            if self.isSelected():
                self.setPen(QPen(QColor("#7c5cff"), 2.4))
            else:
                self.setPen(QPen(QColor("#30394a"), 1.2))
        else:
            if error:
                self.setPen(QPen(QColor("#ff5d62"), 3.5 if self.isSelected() else 2.5))
            elif paused:
                self.setPen(QPen(QColor("#e6b85c"), 4.5 if self.isSelected() else 3.5))
            elif active:
                self.setPen(QPen(QColor("#7ee787"), 3.5 if self.isSelected() else 2.5))
            elif data_evaluated:
                self.setPen(QPen(QColor("#00e5ff"), 2.6 if self.isSelected() else 1.8))
