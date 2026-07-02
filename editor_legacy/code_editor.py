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
    # Clipboard Helpers
    # ------------------------------------------------------------------

    def _get_clipboard(self) -> str:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except Exception:
            return ""

    def _set_clipboard(self, text: str) -> None:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
        except Exception:
            pass

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

            # Copiar linha (Ctrl + C)
            if k == pygame.K_c and mods & pygame.KMOD_CTRL:
                self._set_clipboard(self.lines[row])
                return True

            # Recortar linha (Ctrl + X)
            if k == pygame.K_x and mods & pygame.KMOD_CTRL:
                self._set_clipboard(self.lines[row])
                if len(self.lines) > 1:
                    self.lines.pop(row)
                    self.cursor_row = min(row, len(self.lines) - 1)
                    self.cursor_col = min(col, len(self.lines[self.cursor_row]))
                else:
                    self.lines = [""]
                    self.cursor_row = 0
                    self.cursor_col = 0
                self._clamp_scroll()
                return True

            # Colar texto (Ctrl + V)
            if k == pygame.K_v and mods & pygame.KMOD_CTRL:
                clip = self._get_clipboard()
                if clip:
                    clip_lines = clip.splitlines() or [""]
                    curr_line = self.lines[row]
                    if len(clip_lines) == 1:
                        # Colar em uma única linha
                        self.lines[row] = curr_line[:col] + clip_lines[0] + curr_line[col:]
                        self.cursor_col += len(clip_lines[0])
                    else:
                        # Colar multilinha
                        first = curr_line[:col] + clip_lines[0]
                        last = clip_lines[-1] + curr_line[col:]
                        self.lines[row] = first
                        for idx, new_line in enumerate(clip_lines[1:-1]):
                            self.lines.insert(row + 1 + idx, new_line)
                        self.lines.insert(row + len(clip_lines) - 1, last)
                        self.cursor_row += len(clip_lines) - 1
                        self.cursor_col = len(clip_lines[-1])
                        self._clamp_scroll()
                return True

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
                # Achar recuo (espaços à esquerda) da linha anterior
                indent = ""
                for char in l[:col]:
                    if char == " ":
                        indent += " "
                    else:
                        break
                # Se a linha termina com ":", adicionar mais 4 espaços de indentação automática
                if col > 0 and l[:col].rstrip().endswith(":"):
                    indent += "    "
                    
                self.lines[row] = l[:col]
                self.lines.insert(row + 1, indent + l[col:])
                self.cursor_row += 1
                self.cursor_col = len(indent)
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

    def _draw_highlighted_line(self, screen: pygame.Surface, line: str, x_start: int, y: int) -> None:
        n = len(line)
        if n == 0:
            return
            
        stripped = line.strip()
        if stripped.startswith("#"):
            screen.blit(self._font.render(line, True, (110, 115, 125)), (x_start, y))
            return
            
        colors = [(240, 240, 240)] * n
        
        # 1. Identificar string literals
        in_string = False
        string_char = None
        i = 0
        while i < n:
            char = line[i]
            if char == "#" and not in_string:
                for j in range(i, n):
                    colors[j] = (110, 115, 125)
                break
            elif char in ['"', "'"] and not in_string:
                in_string = True
                string_char = char
                colors[i] = (230, 140, 80)
            elif in_string:
                colors[i] = (230, 140, 80)
                if char == string_char:
                    in_string = False
            i += 1
            
        # 2. Palavras-chave
        keywords = {
            "def", "class", "import", "from", "return", "if", "elif", "else", 
            "while", "for", "in", "and", "or", "not", "is", "pass", "try", "except", "print", "as"
        }
        engine_vars = {"self", "obj", "dt"}
        
        i = 0
        while i < n:
            if colors[i] == (240, 240, 240):
                if line[i].isalnum() or line[i] == "_":
                    start = i
                    while i < n and (line[i].isalnum() or line[i] == "_"):
                        i += 1
                    word = line[start:i]
                    if word in keywords:
                        for j in range(start, i):
                            colors[j] = (0, 200, 255)
                    elif word in engine_vars:
                        for j in range(start, i):
                            colors[j] = (120, 220, 120)
                    elif word.isdigit():
                        for j in range(start, i):
                            colors[j] = (220, 220, 100)
                    continue
            i += 1
            
        # Desenhar segmentos
        i = 0
        curr_x = x_start
        while i < n:
            color = colors[i]
            start = i
            while i < n and colors[i] == color:
                i += 1
            segment = line[start:i]
            surf = self._font.render(segment, True, color)
            screen.blit(surf, (curr_x, y))
            curr_x += self._font.size(segment)[0]

    def draw(self, screen: pygame.Surface) -> None:
        if not self.is_open:
            return
        if self._font is None:
            try:
                self._font = pygame.font.SysFont("Consolas", 15)
            except Exception:
                pass
            if self._font is None:
                try:
                    self._font = pygame.font.SysFont("Courier New", 15)
                except Exception:
                    pass
            if self._font is None:
                self._font = Assets.get_font(None, 15)

        # Overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 24, 30, 230))
        screen.blit(overlay, (0, 0))

        screen_w, screen_h = screen.get_size()
        mw, mh = 760, 520
        mx = (screen_w - mw) // 2
        my = (screen_h - mh) // 2

        modal = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(screen, (30, 34, 42), modal, border_radius=8)
        pygame.draw.rect(screen, (0, 200, 255), modal, 2, border_radius=8)

        title_bar = pygame.Rect(mx, my, mw, 35)
        pygame.draw.rect(screen, (42, 47, 57), title_bar, border_radius=8)
        pygame.draw.line(screen, (55, 60, 72), (mx, my + 35), (mx + mw, my + 35), 2)

        fname = os.path.basename(self.path or "")
        title_font = Assets.get_font(None, 18)
        screen.blit(title_font.render(f"Zennity Code Editor — {fname}", True, (0, 200, 255)), (mx + 20, my + 8))
        screen.blit(self._font.render("Ctrl+S: Salvar  |  Esc: Fechar  |  Ctrl+C/V/X: Copiar/Colar/Cortar  |  Setas: navegar", True, (150, 155, 165)), (mx + 20, my + mh - 25))

        text_bg = pygame.Rect(mx + 20, my + 50, mw - 40, mh - 90)
        pygame.draw.rect(screen, (22, 25, 30), text_bg, border_radius=4)
        pygame.draw.rect(screen, (55, 60, 72), text_bg, 1, border_radius=4)

        y_px = my + 60
        for i in range(self.scroll_y, min(len(self.lines), self.scroll_y + self.VISIBLE_LINES)):
            num_surf = self._font.render(f"{i+1:3d} |", True, (90, 95, 105))
            screen.blit(num_surf, (mx + 30, y_px))
            self._draw_highlighted_line(screen, self.lines[i], mx + 80, y_px)
            if i == self.cursor_row:
                cx = mx + 80 + self._font.size(self.lines[i][:self.cursor_col])[0]
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
