"""Editor de código interno (mini-IDE) renderizado sobre o editor 3D."""
import os
from typing import List, Optional
import pygame
from engine.assets import Assets


class CodeEditor:
    """
    Modal de edição de texto com cursor, scroll, Ctrl+S e navegação por setas.
    Abre sobre a janela do editor sem precisar de janela separada.
    """

    def __init__(self) -> None:
        self.is_open: bool = False
        self.path: Optional[str] = None
        self.lines: List[str] = [""]
        self.cursor_row: int = 0
        self.cursor_col: int = 0
        self.scroll_y: int = 0
        self.VISIBLE_LINES: int = 20
        self._font: Optional[pygame.font.Font] = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def open(self, path: str) -> None:
        self.path = path
        self.lines = [""]
        if os.path.exists(path):
            try:
                self.lines = open(path, "r", encoding="utf-8").read().splitlines() or [""]
            except Exception as e:
                print(f"[CodeEditor] Erro ao abrir '{path}': {e}")
        self.cursor_row = self.cursor_col = self.scroll_y = 0
        self.is_open = True
        pygame.key.set_repeat(300, 30)

    def close(self) -> None:
        self.is_open = False
        self.path = None
        pygame.key.set_repeat(0, 0)

    def save(self) -> None:
        if not self.path:
            return
        try:
            open(self.path, "w", encoding="utf-8").write("\n".join(self.lines))
            print(f"[CodeEditor] Salvo: {self.path}")
        except Exception as e:
            print(f"[CodeEditor] Erro ao salvar: {e}")

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa evento; retorna True se consumiu o evento."""
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            k = event.key
            mods = pygame.key.get_mods()

            if k == pygame.K_ESCAPE:
                self.close(); return True
            if k == pygame.K_s and mods & pygame.KMOD_CTRL:
                self.save(); return True

            row, col = self.cursor_row, self.cursor_col

            if k == pygame.K_UP:
                if row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = min(col, len(self.lines[self.cursor_row]))
                    self._clamp_scroll()
            elif k == pygame.K_DOWN:
                if row < len(self.lines) - 1:
                    self.cursor_row += 1
                    self.cursor_col = min(col, len(self.lines[self.cursor_row]))
                    self._clamp_scroll()
            elif k == pygame.K_LEFT:
                if col > 0:
                    self.cursor_col -= 1
                elif row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = len(self.lines[self.cursor_row])
                    self._clamp_scroll()
            elif k == pygame.K_RIGHT:
                if col < len(self.lines[row]):
                    self.cursor_col += 1
                elif row < len(self.lines) - 1:
                    self.cursor_row += 1
                    self.cursor_col = 0
                    self._clamp_scroll()
            elif k == pygame.K_BACKSPACE:
                if col > 0:
                    l = self.lines[row]
                    self.lines[row] = l[:col-1] + l[col:]
                    self.cursor_col -= 1
                elif row > 0:
                    prev = self.lines[row - 1]
                    self.cursor_col = len(prev)
                    self.lines[row - 1] = prev + self.lines[row]
                    self.lines.pop(row)
                    self.cursor_row -= 1
                    self._clamp_scroll()
            elif k == pygame.K_RETURN:
                l = self.lines[row]
                self.lines[row] = l[:col]
                self.lines.insert(row + 1, l[col:])
                self.cursor_row += 1
                self.cursor_col = 0
                self._clamp_scroll()
            elif k == pygame.K_TAB:
                l = self.lines[row]
                self.lines[row] = l[:col] + "    " + l[col:]
                self.cursor_col += 4
            else:
                if event.unicode and ord(event.unicode) >= 32:
                    l = self.lines[row]
                    self.lines[row] = l[:col] + event.unicode + l[col:]
                    self.cursor_col += 1
            return True
        return False

    # ------------------------------------------------------------------
    # Renderização
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if not self.is_open:
            return
        if self._font is None:
            self._font = Assets.get_font(None, 15)

        # Overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 24, 30, 230))
        screen.blit(overlay, (0, 0))

        modal = pygame.Rect(120, 40, 760, 520)
        pygame.draw.rect(screen, (30, 34, 42), modal, border_radius=8)
        pygame.draw.rect(screen, (0, 200, 255), modal, 2, border_radius=8)

        title_bar = pygame.Rect(120, 40, 760, 35)
        pygame.draw.rect(screen, (42, 47, 57), title_bar, border_radius=8)
        pygame.draw.line(screen, (55, 60, 72), (120, 75), (880, 75), 2)

        fname = os.path.basename(self.path or "")
        title_font = Assets.get_font(None, 18)
        screen.blit(title_font.render(f"Zennity Code Editor — {fname}", True, (0, 200, 255)), (140, 48))
        screen.blit(self._font.render("Ctrl+S: Salvar  |  Esc: Fechar  |  Setas: navegar", True, (150, 155, 165)), (140, 535))

        text_bg = pygame.Rect(140, 90, 720, 430)
        pygame.draw.rect(screen, (22, 25, 30), text_bg, border_radius=4)
        pygame.draw.rect(screen, (55, 60, 72), text_bg, 1, border_radius=4)

        y_px = 100
        for i in range(self.scroll_y, min(len(self.lines), self.scroll_y + self.VISIBLE_LINES)):
            num_surf = self._font.render(f"{i+1:3d} |", True, (90, 95, 105))
            screen.blit(num_surf, (150, y_px))
            screen.blit(self._font.render(self.lines[i], True, (240, 240, 240)), (200, y_px))
            if i == self.cursor_row:
                cx = 200 + self._font.size(self.lines[i][:self.cursor_col])[0]
                pygame.draw.line(screen, (0, 200, 255), (cx, y_px), (cx, y_px + 14), 2)
            y_px += 20

    # ------------------------------------------------------------------
    # Auxiliar
    # ------------------------------------------------------------------

    def _clamp_scroll(self) -> None:
        if self.cursor_row < self.scroll_y:
            self.scroll_y = self.cursor_row
        elif self.cursor_row >= self.scroll_y + self.VISIBLE_LINES:
            self.scroll_y = self.cursor_row - self.VISIBLE_LINES + 1
