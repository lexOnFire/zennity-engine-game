"""Sistema de HUD simplificado para Zennity Engine.

Torna fácil criar, mostrar e gerenciar HUDs em jogos.
Abstrai UIManager, UICanvas, e positioning para um API simples.

Uso básico:
    hud = HUDSystem()

    # Adicionar HP bar
    hud.add_health_bar(x=10, y=10, width=200, max_health=100)

    # Adicionar score
    hud.add_score_display(x=-10, y=10, anchor=Anchor.TOP_RIGHT)

    # Mostrar na tela
    hud.show()

    # Atualizar durante o jogo
    hud.set_health(50)
    hud.add_score(10)
"""

from __future__ import annotations

from typing import Callable, Optional, Any
from enum import Enum

from engine.ui import (
    UIManager, UICanvas, Panel, Label, Button, ProgressBar,
    Anchor, Pivot, UIElement
)


class HAlignmentUI(Enum):
    """Alinhamento horizontal simples."""
    LEFT = Anchor.TOP_LEFT
    CENTER = Anchor.TOP_CENTER
    RIGHT = Anchor.TOP_RIGHT


class VAlignmentUI(Enum):
    """Alinhamento vertical simples."""
    TOP = Anchor.TOP_LEFT
    MIDDLE = Anchor.MIDDLE_LEFT
    BOTTOM = Anchor.BOTTOM_LEFT


class HUDSystem:
    """Sistema simplificado para criar e gerenciar HUDs.

    Torna fácil adicionar elementos comuns (HP bar, score, etc)
    sem se preocupar com UICanvas, Anchor, Pivot, etc.
    """

    def __init__(self, canvas_name: str = "HUD", z_order: int = 0):
        self.ui_manager = UIManager.instance()
        self.canvas_name = canvas_name
        self.z_order = z_order
        self.canvas: Optional[UICanvas] = None
        self._widgets: dict[str, UIElement] = {}
        self._is_visible = False

    # ─────────────────────────────────────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────────────────────────────────────

    def create(self) -> HUDSystem:
        """Cria o canvas interno. CHAMAR ISTO PRIMEIRO."""
        self.canvas = UICanvas(name=self.canvas_name, z_order=self.z_order)
        return self

    def show(self) -> None:
        """Mostra o HUD na tela (adiciona ao UIManager)."""
        if self.canvas is None:
            self.create()
        self.ui_manager.add_canvas(self.canvas)
        self.canvas.visible = True
        self._is_visible = True

    def hide(self) -> None:
        """Esconde o HUD."""
        if self.canvas:
            self.canvas.visible = False
            self._is_visible = False

    def toggle(self) -> None:
        """Mostra/esconde o HUD."""
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def clear(self) -> None:
        """Remove todos os widgets do HUD."""
        if self.canvas:
            self.canvas.children.clear()
        self._widgets.clear()

    def remove(self) -> None:
        """Remove o HUD completamente (do UIManager)."""
        if self.canvas:
            self.ui_manager.remove_canvas(self.canvas)
        self.clear()
        self.canvas = None

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS — Converte Anchor/Pivot simples para posicionamento
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_anchor(
        self, h_align: str | Anchor, v_align: str | Anchor | None
    ) -> Anchor:
        """Resolve alinhamento simples para Anchor."""
        if isinstance(h_align, Anchor):
            return h_align

        # Map string simples para Anchor
        if h_align == "left":
            anchor = Anchor.TOP_LEFT
        elif h_align == "center":
            anchor = Anchor.TOP_CENTER
        elif h_align == "right":
            anchor = Anchor.TOP_RIGHT
        else:
            anchor = Anchor.TOP_LEFT

        if v_align:
            if v_align == "top":
                if h_align == "left":
                    anchor = Anchor.TOP_LEFT
                elif h_align == "center":
                    anchor = Anchor.TOP_CENTER
                else:
                    anchor = Anchor.TOP_RIGHT
            elif v_align == "middle":
                if h_align == "left":
                    anchor = Anchor.MIDDLE_LEFT
                elif h_align == "center":
                    anchor = Anchor.MIDDLE_CENTER
                else:
                    anchor = Anchor.MIDDLE_RIGHT
            elif v_align == "bottom":
                if h_align == "left":
                    anchor = Anchor.BOTTOM_LEFT
                elif h_align == "center":
                    anchor = Anchor.BOTTOM_CENTER
                else:
                    anchor = Anchor.BOTTOM_RIGHT

        return anchor

    # ─────────────────────────────────────────────────────────────────────────
    # WIDGETS COMUNS — Health Bar, Score, etc
    # ─────────────────────────────────────────────────────────────────────────

    def add_health_bar(
        self,
        widget_id: str = "health_bar",
        x: float = 10,
        y: float = 10,
        width: float = 200,
        height: float = 30,
        max_health: float = 100.0,
        current_health: float | None = None,
        anchor: Anchor = Anchor.TOP_LEFT,
        label: str = "HP",
        label_color: tuple = (240, 80, 80),
        bar_color: tuple = (200, 60, 60),
        bg_color: tuple = (50, 20, 20),
        show_text: bool = True,
        **kwargs
    ) -> ProgressBar:
        """Adiciona uma barra de saúde ao HUD.

        Args:
            widget_id: ID único para referência
            x, y: Posição
            width, height: Tamanho
            max_health: Valor máximo
            current_health: Valor atual (padrão: max_health)
            anchor: Posição na tela
            label: Texto do rótulo (ex: "HP")
            show_text: Mostrar números na barra
        """
        if self.canvas is None:
            self.create()

        if current_health is None:
            current_health = max_health

        # Painel container
        panel = Panel(
            x=x, y=y,
            width=width,
            height=height + 25,  # espaço para rótulo
            color=(10, 10, 25, 150),
            border_color=(60, 80, 140, 200),
            border_radius=8,
            anchor=anchor,
            name=f"{widget_id}_panel"
        )
        self.canvas.add_child(panel)

        # Rótulo
        if label:
            label_widget = Label(
                label, x=8, y=6,
                font_size=12,
                color=label_color,
                bold=True,
            )
            panel.add_child(label_widget)

        # Barra
        bar = ProgressBar(
            x=8, y=22,
            width=width - 16,
            height=height - 22,
            value=current_health,
            max_value=max_health,
            color_fill=bar_color,
            color_bg=bg_color,
            show_text=show_text,
            font_size=10,
            smooth=True,
            smooth_speed=100.0,
        )
        panel.add_child(bar)

        self._widgets[widget_id] = bar
        return bar

    def add_score_display(
        self,
        widget_id: str = "score",
        x: float = -10,
        y: float = 10,
        initial_score: int = 0,
        anchor: Anchor = Anchor.TOP_RIGHT,
        color: tuple = (255, 220, 60),
        font_size: int = 24,
        bold: bool = True,
        **kwargs
    ) -> Label:
        """Adiciona um display de score.

        Args:
            widget_id: ID único
            x, y: Posição
            initial_score: Valor inicial
            anchor: Posição na tela
            color: Cor do texto
            font_size: Tamanho da fonte
        """
        if self.canvas is None:
            self.create()

        label = Label(
            f"Score: {initial_score}",
            x=x, y=y,
            font_size=font_size,
            color=color,
            bold=bold,
            shadow=True,
            anchor=anchor,
            pivot=Pivot.TOP_RIGHT if anchor == Anchor.TOP_RIGHT else Pivot.TOP_LEFT,
            name=widget_id
        )
        self.canvas.add_child(label)
        self._widgets[widget_id] = label

        # Store score internally
        if not hasattr(self, "_scores"):
            self._scores = {}
        self._scores[widget_id] = initial_score

        return label

    def add_text_label(
        self,
        widget_id: str,
        text: str = "",
        x: float = 10,
        y: float = 10,
        font_size: int = 16,
        color: tuple = (255, 255, 255),
        anchor: Anchor = Anchor.TOP_LEFT,
        bold: bool = False,
        shadow: bool = False,
        **kwargs
    ) -> Label:
        """Adiciona um rótulo de texto simples.

        Args:
            widget_id: ID único
            text: Texto inicial
            x, y: Posição
            font_size: Tamanho da fonte
            color: Cor (RGB ou RGBA)
            anchor: Posição na tela
        """
        if self.canvas is None:
            self.create()

        label = Label(
            text,
            x=x, y=y,
            font_size=font_size,
            color=color,
            bold=bold,
            shadow=shadow,
            anchor=anchor,
            name=widget_id
        )
        self.canvas.add_child(label)
        self._widgets[widget_id] = label
        return label

    def add_panel(
        self,
        widget_id: str,
        x: float = 10,
        y: float = 10,
        width: float = 200,
        height: float = 100,
        color: tuple = (10, 10, 25, 180),
        border_color: tuple | None = (60, 80, 140, 220),
        border_radius: int = 10,
        anchor: Anchor = Anchor.TOP_LEFT,
        **kwargs
    ) -> Panel:
        """Adiciona um painel (container).

        Args:
            widget_id: ID único
            x, y: Posição
            width, height: Tamanho
            color: Cor de fundo (RGBA)
            border_color: Cor da borda
            border_radius: Raio das bordas arredondadas
            anchor: Posição na tela
        """
        if self.canvas is None:
            self.create()

        panel = Panel(
            x=x, y=y,
            width=width,
            height=height,
            color=color,
            border_color=border_color,
            border_radius=border_radius,
            anchor=anchor,
            name=widget_id
        )
        self.canvas.add_child(panel)
        self._widgets[widget_id] = panel
        return panel

    def add_button(
        self,
        widget_id: str,
        text: str = "Click",
        on_click: Callable[[], None] | None = None,
        x: float = 10,
        y: float = 10,
        width: float = 150,
        height: float = 40,
        anchor: Anchor = Anchor.TOP_LEFT,
        color_normal: tuple = (50, 80, 160),
        color_hover: tuple = (70, 110, 210),
        font_size: int = 16,
        **kwargs
    ) -> Button:
        """Adiciona um botão.

        Args:
            widget_id: ID único
            text: Texto do botão
            on_click: Callback ao clicar
            x, y: Posição
            width, height: Tamanho
            anchor: Posição na tela
            color_normal, color_hover: Cores
            font_size: Tamanho da fonte
        """
        if self.canvas is None:
            self.create()

        button = Button(
            text,
            x=x, y=y,
            width=width,
            height=height,
            on_click=on_click or (lambda: None),
            color_normal=color_normal,
            color_hover=color_hover,
            anchor=anchor,
            font_size=font_size,
            name=widget_id
        )
        self.canvas.add_child(button)
        self._widgets[widget_id] = button
        return button

    # ─────────────────────────────────────────────────────────────────────────
    # UPDATE METHODS — Atualizar valores em tempo real
    # ─────────────────────────────────────────────────────────────────────────

    def set_health(self, widget_id: str = "health_bar", value: float = 0.0) -> None:
        """Atualiza valor da barra de saúde."""
        widget = self._widgets.get(widget_id)
        if isinstance(widget, ProgressBar):
            widget.value = value

    def set_max_health(self, widget_id: str = "health_bar", value: float = 100.0) -> None:
        """Atualiza valor máximo da barra de saúde."""
        widget = self._widgets.get(widget_id)
        if isinstance(widget, ProgressBar):
            widget.max_value = value

    def set_score(self, widget_id: str = "score", value: int = 0) -> None:
        """Define o score."""
        if not hasattr(self, "_scores"):
            self._scores = {}

        self._scores[widget_id] = value
        widget = self._widgets.get(widget_id)
        if isinstance(widget, Label):
            widget.text = f"Score: {value}"

    def add_score(self, widget_id: str = "score", value: int = 1) -> None:
        """Adiciona ao score."""
        if not hasattr(self, "_scores"):
            self._scores = {}

        self._scores[widget_id] = self._scores.get(widget_id, 0) + value
        widget = self._widgets.get(widget_id)
        if isinstance(widget, Label):
            widget.text = f"Score: {self._scores[widget_id]}"

    def set_text(self, widget_id: str, text: str) -> None:
        """Atualiza texto de um label."""
        widget = self._widgets.get(widget_id)
        if isinstance(widget, Label):
            widget.text = text

    def get_text(self, widget_id: str) -> str:
        """Pega texto de um label."""
        widget = self._widgets.get(widget_id)
        if isinstance(widget, Label):
            return widget.text
        return ""

    def get_widget(self, widget_id: str) -> UIElement | None:
        """Acessa um widget diretamente pelo ID."""
        return self._widgets.get(widget_id)

    def update(self, dt: float) -> None:
        """Atualiza o HUD (chamado pelo UIManager automaticamente)."""
        if self.canvas:
            self.canvas.update(dt)

    def draw(self, screen) -> None:
        """Desenha o HUD (chamado pelo UIManager automaticamente)."""
        if self.canvas:
            self.canvas.draw(screen)
