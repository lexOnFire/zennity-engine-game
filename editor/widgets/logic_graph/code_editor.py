"""Highlighter de sintaxe Python e widget de edição de código com números de linha."""
from __future__ import annotations

import re
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Highlight de sintaxe Python seguro e leve para Custom Scripts."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._highlighting_rules: list[tuple[re.Pattern, QTextCharFormat]] = []

        # Formatos
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c678dd"))
        keyword_format.setFontWeight(QFont.Bold)

        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#61afef"))

        ctx_format = QTextCharFormat()
        ctx_format.setForeground(QColor("#e5c07b"))
        ctx_format.setFontWeight(QFont.Bold)

        disallowed_format = QTextCharFormat()
        disallowed_format.setForeground(QColor("#e06c75"))
        disallowed_format.setFontUnderline(True)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98c379"))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#d19a66"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5c6370"))
        comment_format.setFontItalic(True)

        # Regras de Keywords permitidas
        keywords = [
            r"\bif\b", r"\belse\b", r"\belif\b", r"\bfor\b", r"\bin\b",
            r"\bTrue\b", r"\bFalse\b", r"\bNone\b", r"\band\b", r"\bor\b",
            r"\bnot\b", r"\bis\b", r"\bpass\b", r"\breturn\b",
        ]
        for pattern in keywords:
            self._highlighting_rules.append((re.compile(pattern), keyword_format))

        # Safe Builtins
        builtins = [
            r"\babs\b", r"\bmin\b", r"\bmax\b", r"\bround\b", r"\blen\b",
            r"\bbool\b", r"\bfloat\b", r"\bint\b", r"\bstr\b",
        ]
        for pattern in builtins:
            self._highlighting_rules.append((re.compile(pattern), builtin_format))

        # Context API
        ctx_patterns = [
            r"\bctx\b", r"\bget_input\b", r"\bset_output\b", r"\bemit\b",
        ]
        for pattern in ctx_patterns:
            self._highlighting_rules.append((re.compile(pattern), ctx_format))

        # Disallowed keywords warning
        disallowed = [
            r"\bimport\b", r"\bfrom\b", r"\bclass\b", r"\bdef\b", r"\blambda\b",
            r"\bwhile\b", r"\btry\b", r"\bexcept\b", r"\bfinally\b", r"\braise\b",
            r"\bwith\b", r"\bglobal\b", r"\bnonlocal\b", r"\byield\b",
            r"\beval\b", r"\bexec\b", r"\bcompile\b", r"\bopen\b",
        ]
        for pattern in disallowed:
            self._highlighting_rules.append((re.compile(pattern), disallowed_format))

        # Numbers
        self._highlighting_rules.append((re.compile(r"\b[0-9]+(\.[0-9]+)?\b"), number_format))

        # Strings (simples e duplas)
        self._highlighting_rules.append((re.compile(r"\"[^\"]*\""), string_format))
        self._highlighting_rules.append((re.compile(r"'[^']*'"), string_format))

        # Comments
        self._highlighting_rules.append((re.compile(r"#[^\n]*"), comment_format))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


class LineNumberArea(QWidget):
    """Área lateral para renderização dos números de linha."""

    def __init__(self, editor: CodeEditorWidget) -> None:
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.code_editor.line_number_area_paint_event(event)


class CodeEditorWidget(QPlainTextEdit):
    """Editor de código com números de linha, highlight e suporte a identação."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PythonSyntaxHighlighter(self.document())

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Configurações visuais
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setStyleSheet(
            "QPlainTextEdit { background-color: #0b0d14; color: #f8fafc; font-family: Consolas, 'Courier New', monospace; "
            "font-size: 13px; line-height: 1.4; border: 1px solid #1e2430; border-radius: 4px; padding: 2px; selection-background-color: #1e3a8a; }"
        )

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        space = 14 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#141824")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#0f121a"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setPen(QColor("#4b5563"))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, top, self.line_number_area.width() - 6, self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, event) -> None:
        # Tab -> 4 espaços
        if event.key() == Qt.Key_Tab and not (event.modifiers() & Qt.ShiftModifier):
            self.insertPlainText("    ")
            event.accept()
            return
        super().keyPressEvent(event)
