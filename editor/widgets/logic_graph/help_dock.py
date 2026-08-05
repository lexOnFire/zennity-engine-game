from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser, QLabel, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from engine.localization import tr
from editor.widgets.logic_graph.node_database import NODE_DATABASE, NODE_ALIASES


class LogicHelpDock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogicHelpDock")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Título
        title = QLabel("📖 AJUDA & DOCUMENTAÇÃO DO NÓ")
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #38bdf8; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Barra de pesquisa
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Buscar nó... (ex: Mover, Pular, Ramo)")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setStyleSheet(
            "QLineEdit { background: #0f1419; border: 1px solid #38bdf8; border-radius: 6px; padding: 6px 10px; "
            "color: #f8fafc; font-size: 11px; selection-background-color: #38bdf8; }"
            "QLineEdit:focus { border: 2px solid #60a5fa; }"
        )
        self.search_bar.textChanged.connect(self._filter_help)
        layout.addWidget(self.search_bar)

        # Área de help com scroll
        self.help_text = QTextBrowser()
        self.help_text.setOpenExternalLinks(True)
        self.help_text.setStyleSheet(
            "QTextBrowser { background: #0f1419; border: 1px solid #1e2430; border-radius: 6px; "
            "color: #cbd5e1; font-size: 10px; padding: 8px; font-family: 'Segoe UI', sans-serif; }"
            "QScrollBar:vertical { background: #141720; border: none; width: 8px; }"
            "QScrollBar::handle:vertical { background: #38bdf8; border-radius: 4px; }"
            "QScrollBar::handle:vertical:hover { background: #60a5fa; }"
        )
        layout.addWidget(self.help_text, 1)

        self._filter_help("")

    def _resolve_node_id(self, query: str) -> str:
        """Resolve node ID usando aliases e normalizando."""
        query_clean = query.lower().strip().replace(" ", "_")

        # Tenta match direto
        if query_clean in NODE_DATABASE:
            return query_clean

        # Tenta alias
        if query_clean in NODE_ALIASES:
            return NODE_ALIASES[query_clean]

        # Tenta partial match no banco
        for key in NODE_DATABASE.keys():
            if query_clean in key or key in query_clean:
                return key

        return None

    def _filter_help(self, query: str):
        query_clean = query.lower().strip().replace(" ", "_")
        raw_query = query.lower().strip()

        # Match inteligente no dicionário
        matched_keys = []
        for k, data in NODE_DATABASE.items():
            if not raw_query:
                matched_keys.append(k)
            elif (
                raw_query in k
                or query_clean in k
                or raw_query in data["title"].lower()
                or raw_query in data["category"].lower()
                or raw_query in data["desc"].lower()
            ):
                matched_keys.append(k)

        if not matched_keys:
            self._show_fallback(query)
            return

        html = []
        for k in matched_keys[:5]:
            data = NODE_DATABASE[k]
            icon = data.get("icon", "🔹")
            category = data.get("category", "Genérico")
            detailed = data.get("detailed", "")
            example = data.get("example", "")
            tips = data.get("tips", "")

            html.append(f"""
            <div style='background:#141824; border-left: 4px solid #38bdf8; padding: 12px; margin: 10px 0; border-radius: 6px;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                    <h3 style='color:#38bdf8; margin: 0; font-size: 13px; font-weight: bold;'>{icon} {data['title']}</h3>
                    <span style='background:#38bdf8; color:#0f1419; padding: 3px 8px; border-radius: 12px; font-size: 9px; font-weight: bold;'>{category}</span>
                </div>
                <p style='margin: 8px 0; font-size: 10px; line-height: 1.6; color:#cbd5e1;'>{data['desc']}</p>
            """)

            if detailed:
                html.append(f"<p style='margin: 8px 0; font-size: 10px; color:#a3e635; font-style: italic;'>ℹ️ {detailed}</p>")

            html.append(f"<div style='background:#0f1419; padding: 8px; border-radius: 4px; margin: 8px 0;'>"
                       f"<p style='margin: 0 0 6px 0; font-size: 10px; color:#38bdf8; font-weight: bold;'>💡 Como Usar:</p>"
                       f"<p style='margin: 0; font-size: 10px; color:#cbd5e1; line-height: 1.5;'>{data['usage']}</p>"
                       f"</div>")

            if example:
                html.append(f"<div style='background:#181c28; padding: 8px; border-left: 2px solid #60a5fa; border-radius: 4px; margin: 8px 0;'>"
                           f"<p style='margin: 0; font-size: 9px; color:#60a5fa; font-weight: bold;'>{example}</p>"
                           f"</div>")

            html.append(f"<div style='background:#0f1419; padding: 8px; border-radius: 4px; margin: 8px 0;'>"
                       f"<p style='margin: 0 0 6px 0; font-size: 10px; color:#38bdf8; font-weight: bold;'>🔌 Portas (Pinos):</p>"
                       f"<p style='margin: 0; font-size: 10px; color:#cbd5e1; line-height: 1.5;'>{data['ports']}</p>"
                       f"</div>")

            if tips:
                html.append(f"<div style='background:#1a2428; padding: 8px; border-left: 2px solid #a3e635; border-radius: 4px; margin: 8px 0;'>"
                           f"<p style='margin: 0 0 6px 0; font-size: 10px; color:#a3e635; font-weight: bold;'>⚡ Dicas Úteis:</p>"
                           f"<p style='margin: 0; font-size: 10px; color:#cbd5e1; line-height: 1.5;'>{tips}</p>"
                           f"</div>")

            html.append("</div>")

        self.help_text.setHtml("".join(html))

    def _show_fallback(self, query: str):
        """Mostra mensagem quando nó não está na base de dados."""
        if not query or query.strip() == "":
            # Tela inicial vazia
            self.help_text.setHtml(f"""
            <div style='padding: 20px; text-align: center;'>
                <p style='color:#94a3b8; font-size: 12px; font-weight: bold;'>📚 Bem-vindo à Ajuda do Logic Graph</p>
                <p style='color:#64748b; font-size: 10px; margin-top: 10px;'>
                    Selecione um nó na <b>paleta</b> ou clique em um nó no <b>editor</b><br>
                    para ver documentação detalhada e exemplos práticos.
                </p>
                <div style='background:#141824; border-left: 3px solid #38bdf8; padding: 12px; margin-top: 16px; border-radius: 4px; text-align: left;'>
                    <p style='color:#38bdf8; font-size: 10px; font-weight: bold; margin: 0 0 8px 0;'>⚡ Comece aqui:</p>
                    <ul style='color:#cbd5e1; font-size: 10px; margin: 0; padding-left: 20px;'>
                        <li>Use <b>On Tick</b> para lógica contínua</li>
                        <li>Use <b>On Start</b> para inicialização</li>
                        <li>Use <b>Branch</b> para decisões</li>
                        <li>Use <b>Move</b> para movimento</li>
                    </ul>
                </div>
            </div>
            """)
        else:
            # Nó não encontrado - mostra com informação útil
            pretty_title = query.strip()
            self.help_text.setHtml(f"""
            <div style='padding: 10px;'>
                <div style='background:#141824; border-left: 4px solid #f87171; padding: 12px; margin: 8px 0; border-radius: 4px;'>
                    <h3 style='color:#f87171; margin: 0 0 6px 0; font-size: 12px;'>❓ "{pretty_title}"</h3>
                    <p style='color:#cbd5e1; font-size: 10px; margin: 6px 0; line-height: 1.5;'>
                        <b>✓ Este nó EXISTE no Logic Graph!</b>
                    </p>
                    <p style='color:#cbd5e1; font-size: 10px; margin: 6px 0; line-height: 1.5;'>
                        Documentação ainda não disponível. Para mais informações:
                    </p>
                    <p style='color:#cbd5e1; font-size: 10px; margin: 6px 0; line-height: 1.5;'>
                        <b>Tipo:</b> Nó do Logic Graph<br>
                        <b>Categoria:</b> Visual Scripting<br>
                        <b>Propósito:</b> Processa lógica quando acionado no fluxo
                    </p>
                </div>

                <div style='background:#141824; border-left: 4px solid #fbbf24; padding: 12px; margin: 12px 0; border-radius: 4px;'>
                    <p style='color:#fbbf24; font-size: 10px; font-weight: bold; margin: 0 0 6px 0;'>💡 Próximos Passos:</p>
                    <ul style='color:#cbd5e1; font-size: 10px; margin: 0; padding-left: 20px;'>
                        <li>Verifique os pinos de entrada/saída no editor</li>
                        <li>Procure exemplos de uso em outros grafos</li>
                        <li>Consulte tutoriais do Logic Graph</li>
                        <li>Experimente conectar em um ramo simples</li>
                    </ul>
                </div>

                <p style='color:#64748b; font-size: 9px; margin-top: 14px; text-align: center;'>
                    🔍 Tente buscar outros nós documentados na paleta
                </p>
            </div>
            """)

    def show_node_help(self, node_id_or_name: str):
        """Mostra ajuda para um nó específico. Recebe ID ou nome do nó."""
        if not node_id_or_name:
            return

        # Resolve node ID
        resolved_id = self._resolve_node_id(node_id_or_name)

        # Se não resolver, tenta o termo original
        if not resolved_id:
            search_term = node_id_or_name
        else:
            # Se resolver, usa o título do nó para melhor UX
            search_term = NODE_DATABASE[resolved_id].get("title", node_id_or_name)

        self.search_bar.blockSignals(True)
        self.search_bar.setText(search_term)
        self.search_bar.blockSignals(False)
        self._filter_help(search_term)
