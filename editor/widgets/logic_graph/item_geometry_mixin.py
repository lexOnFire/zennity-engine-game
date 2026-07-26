"""Mixin de geometria e layout para LogicNodeItem."""

from __future__ import annotations

class LogicNodeItemGeometryMixin:
    """Isola cálculos de geometria e posicionamento de portas do LogicNodeItem."""

    def toggle_collapsed(self) -> None:
        self.collapsed = not self.collapsed
        self.node.setdefault("editor", {}).update({
            "collapsed": self.collapsed,
            "width": round(self.width, 2),
            "height": round(self.expanded_height, 2),
        })
        self._apply_geometry()
        self.editor.mark_dirty()

    def _apply_geometry(self, notify: bool = True) -> None:
        self.height = self.COLLAPSED_HEIGHT if self.collapsed else self.expanded_height
        self.setRect(0.0, 0.0, self.width, self.height)
        self.header.setRect(0.0, 0.0, self.width, self.HEADER_HEIGHT)
        self.accent.setRect(0.0, 0.0, 4.0, self.height)
        self.breakpoint_item.setRect(self.width - 20.0, 8.0, 10.0, 10.0)
        self.flip_control.setPos(self.width - 52.0, 2.0)
        self.collapse_control.refresh()
        self.summary_item.setTextWidth(self.width - 22.0)
        self.summary_item.setPos(10.0, self.expanded_height - 25.0)
        self.target_item.setTextWidth(self.width - 22.0)
        self.target_item.setPos(10.0, self.expanded_height - 45.0)
        self.debug_item.setTextWidth(self.width - 22.0)
        self.debug_item.setPos(10.0, self.expanded_height - 25.0)
        self.code_item.setTextWidth(self.width - 18.0)
        self.resize_handle.setPos(
            self.width - self.resize_handle.SIZE - 3.0,
            self.expanded_height - self.resize_handle.SIZE - 3.0,
        )
        for index, (name, _data_type) in enumerate(self.input_definitions):
            y = self.PORT_START_Y + index * self.PORT_SPACING
            port = self.input_ports[name]
            port.setRect(-port.SIZE / 2, y - port.SIZE / 2, port.SIZE, port.SIZE)
            port.setTransformOriginPoint(port.boundingRect().center())
            self.port_labels[index].setPos(13.0, y - 12.0)
        output_label_offset = len(self.input_definitions)
        for index, (name, _data_type) in enumerate(self.output_definitions):
            y = self.PORT_START_Y + index * self.PORT_SPACING
            port = self.output_ports[name]
            port.setRect(self.width - port.SIZE / 2, y - port.SIZE / 2, port.SIZE, port.SIZE)
            port.setTransformOriginPoint(port.boundingRect().center())
            label = self.port_labels[output_label_offset + index]
            label.setTextWidth(min(110.0, self.width * 0.45))
            label.setPos(self.width - min(118.0, self.width * 0.48), y - 12.0)
        body_visible = not self.collapsed
        self.flip_control.setVisible(body_visible)
        self.resize_handle.setVisible(body_visible)
        for port in (*self.input_ports.values(), *self.output_ports.values()):
            port.setVisible(body_visible and not self._show_code)
        for label in self.port_labels:
            label.setVisible(body_visible and not self._show_code)
        self.code_item.setVisible(body_visible and self._show_code)
        if self.collapsed:
            self.summary_item.hide()
            self.target_item.hide()
            self.debug_item.hide()
        else:
            self.set_runtime_state(*self._runtime_display)
        if notify:
            self.editor.refresh_connections()
            self.update()
