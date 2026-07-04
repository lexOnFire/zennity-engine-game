"""
editor/viewport/selection_outline.py
─────────────────────────────────────────────────────────────────────────────
Desenho da borda de seleção (selection outline) rotacionada para o objeto selecionado,
suportando formas retangulares e circulares.
"""
from __future__ import annotations

from typing import Any, Callable
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen


class SelectionOutlineRenderer:
    """Renderiza a borda de destaque do objeto selecionado.

    Desenhado em Qt (QPainter) com suporte a rotação e espessura customizável.
    """

    def __init__(
        self,
        color: QColor = QColor(80, 160, 255),  # Azul clássico
        thickness: int = 2,
    ) -> None:
        self.color: QColor = color
        self.thickness: int = thickness

    def draw(
        self,
        painter: QPainter,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> None:
        """Desenha a borda de seleção ao redor do objeto (retângulo ou círculo).

        Mapeia a largura e altura mundial para a tela e aplica transformações locais
        no painter para desenhar alinhado à rotação real (rz) do objeto.
        """
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        scale = getattr(selected.transform, "scale", None)
        if pos is None or scale is None:
            return

        cx, cy = world_to_viewport(pos)

        # Determina largura e altura na tela projetando os cantos do objeto
        p0 = world_to_viewport((pos[0] - scale[0] / 2.0, pos[1] - scale[1] / 2.0, pos[2]))
        p1 = world_to_viewport((pos[0] + scale[0] / 2.0, pos[1] + scale[1] / 2.0, pos[2]))
        sw = abs(p1[0] - p0[0])
        sh = abs(p1[1] - p0[1])

        # Cria o retângulo com folga de 3 pixels
        rect = QRectF(-sw / 2.0 - 3.0, -sh / 2.0 - 3.0, sw + 6.0, sh + 6.0)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        pen = QPen(self.color, self.thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Translada o centro de coordenadas para o centro do objeto e rotaciona
        painter.translate(cx, cy)
        rz = float(getattr(selected.transform, "rz", 0.0))
        painter.rotate(rz)

        # Detecta se é círculo via mesh_type ou CircleCollider
        is_circle = False
        if getattr(selected, "mesh_type", "") == "Círculo":
            is_circle = True
        elif hasattr(selected, "get_component"):
            # Importação tardia para evitar dependências circulares
            from engine.physics.collider import CircleCollider
            if selected.get_component(CircleCollider) is not None:
                is_circle = True

        # Desenha conforme a forma geométrica
        if is_circle:
            painter.drawEllipse(rect)
        else:
            painter.drawRect(rect)
        
        painter.restore()
