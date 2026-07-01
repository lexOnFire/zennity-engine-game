from __future__ import annotations
"""
editor/launcher.py
──────────────────
Cena do Launcher inicial que permite escolher entre o Editor 2D e o Editor 3D.
"""

import sys
import pygame
from engine.core import Scene
import editor.theme as T
from editor.scene import EditorScene
from editor.editor_2d import Editor2DScene


class LauncherScene(Scene):
    def start(self) -> None:
        self.font_title = pygame.font.SysFont("monospace", 46, bold=True)
        self.font_subtitle = pygame.font.SysFont("monospace", 16)
        self.font_header = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_desc = pygame.font.SysFont("monospace", 13)

        # Definição dos dois Cards grandes
        # Posicionados simetricamente
        self.card_2d = pygame.Rect(320, 260, 320, 340)
        self.card_3d = pygame.Rect(760, 260, 320, 340)

        self.hover_2d = False
        self.hover_3d = False

    def update(self, dt: float) -> None:
        mx, my = pygame.mouse.get_pos()
        self.hover_2d = self.card_2d.collidepoint(mx, my)
        self.hover_3d = self.card_3d.collidepoint(mx, my)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Botão esquerdo
                if self.hover_2d:
                    # Abre o Editor 2D dedicado
                    if self.engine:
                        self.engine.change_scene(Editor2DScene())
                elif self.hover_3d:
                    # Abre o Editor 3D clássico
                    if self.engine:
                        self.engine.change_scene(EditorScene())

    def draw(self, screen: pygame.Surface) -> None:
        # Fundo geral escuro com gradiente sutil
        screen.fill(T.BG)
        
        # Desenha algumas linhas de fundo futuristas
        for i in range(0, 1400, 80):
            pygame.draw.line(screen, T.alpha_blend(T.BORDER, 0.15), (i, 0), (i, 800), 1)
        for i in range(0, 800, 80):
            pygame.draw.line(screen, T.alpha_blend(T.BORDER, 0.15), (0, i), (1400, i), 1)

        # Título
        title_surf = self.font_title.render("ZENNITY ENGINE", True, T.ACCENT)
        title_rect = title_surf.get_rect(center=(1400 // 2, 100))
        # Sombra do título
        title_shadow = self.font_title.render("ZENNITY ENGINE", True, T.BG)
        screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title_surf, title_rect)

        # Subtítulo
        sub_surf = self.font_subtitle.render("Escolha o modelo do projeto para iniciar", True, T.TEXT_MUTED)
        sub_rect = sub_surf.get_rect(center=(1400 // 2, 160))
        screen.blit(sub_surf, sub_rect)

        # Linha divisória sob o título
        pygame.draw.line(screen, T.BORDER, (1400 // 2 - 200, 190), (1400 // 2 + 200, 190), 1)

        # ── CARD 2D ──────────────────────────────────────────────────────────
        c2d_bg = T.alpha_blend(T.SURFACE_2, 0.75) if self.hover_2d else T.PANEL
        c2d_border = T.ACCENT if self.hover_2d else T.BORDER
        
        pygame.draw.rect(screen, c2d_bg, self.card_2d, border_radius=16)
        pygame.draw.rect(screen, c2d_border, self.card_2d, 2, border_radius=16)

        # Ícone visual simples de Grid 2D dentro do Card
        icon_2d_rect = pygame.Rect(self.card_2d.x + 80, self.card_2d.y + 30, 160, 100)
        pygame.draw.rect(screen, T.SURFACE, icon_2d_rect, border_radius=8)
        # Grade 2D no ícone
        for gx in range(icon_2d_rect.x + 20, icon_2d_rect.right, 20):
            pygame.draw.line(screen, T.BORDER_SOFT, (gx, icon_2d_rect.y), (gx, icon_2d_rect.bottom), 1)
        for gy in range(icon_2d_rect.y + 20, icon_2d_rect.bottom, 20):
            pygame.draw.line(screen, T.BORDER_SOFT, (icon_2d_rect.x, gy), (icon_2d_rect.right, gy), 1)
        # Quadrado verde (jogador/bloco)
        pygame.draw.rect(screen, (50, 200, 100), (icon_2d_rect.x + 60, icon_2d_rect.y + 40, 40, 40), border_radius=4)

        # Textos do Card 2D
        h2d_surf = self.font_header.render("Projeto 2D", True, T.TEXT_PRIMARY)
        screen.blit(h2d_surf, (self.card_2d.x + 20, self.card_2d.y + 160))

        desc_2d_lines = [
            "• Edição focada em planos X e Y",
            "• Suporte nativo a Tilemaps 2D",
            "• Física 2D e colisores AABB",
            "• Sistema de partículas plano",
            "• Customização e scripts leves",
        ]
        for idx, line in enumerate(desc_2d_lines):
            surf = self.font_desc.render(line, True, T.TEXT_MUTED)
            screen.blit(surf, (self.card_2d.x + 25, self.card_2d.y + 205 + idx * 24))

        # ── CARD 3D ──────────────────────────────────────────────────────────
        c3d_bg = T.alpha_blend(T.SURFACE_2, 0.75) if self.hover_3d else T.PANEL
        c3d_border = T.ACCENT if self.hover_3d else T.BORDER
        
        pygame.draw.rect(screen, c3d_bg, self.card_3d, border_radius=16)
        pygame.draw.rect(screen, c3d_border, self.card_3d, 2, border_radius=16)

        # Ícone visual simples de cubo 3D/geometria dentro do Card
        icon_3d_rect = pygame.Rect(self.card_3d.x + 80, self.card_3d.y + 30, 160, 100)
        pygame.draw.rect(screen, T.SURFACE, icon_3d_rect, border_radius=8)
        # Cubo desenhado em linhas (vetorial simples)
        cx, cy, cs = icon_3d_rect.centerx, icon_3d_rect.centery, 30
        pts_front = [
            (cx - cs, cy - cs), (cx + cs, cy - cs),
            (cx + cs, cy + cs), (cx - cs, cy + cs)
        ]
        pts_back = [
            (cx - cs + 15, cy - cs - 15), (cx + cs + 15, cy - cs - 15),
            (cx + cs + 15, cy + cs - 15), (cx - cs + 15, cy + cs - 15)
        ]
        # Conexões
        pygame.draw.polygon(screen, T.alpha_blend(T.BORDER, 0.3), pts_back, 0)
        pygame.draw.polygon(screen, T.alpha_blend(T.ACCENT, 0.4), pts_front, 0)
        pygame.draw.polygon(screen, T.ACCENT, pts_front, 2)
        for i in range(4):
            pygame.draw.line(screen, T.ACCENT, pts_front[i], pts_back[i], 2)

        # Textos do Card 3D
        h3d_surf = self.font_header.render("Projeto 3D", True, T.TEXT_PRIMARY)
        screen.blit(h3d_surf, (self.card_3d.x + 20, self.card_3d.y + 160))

        desc_3d_lines = [
            "• Espaço tridimensional (XYZ)",
            "• Malhas geométricas e OBJ",
            "• Iluminação direcional/ponto",
            "• Rotação por quaterniões/euler",
            "• Câmera orbital e projeção",
        ]
        for idx, line in enumerate(desc_3d_lines):
            surf = self.font_desc.render(line, True, T.TEXT_MUTED)
            screen.blit(surf, (self.card_3d.x + 25, self.card_3d.y + 205 + idx * 24))
