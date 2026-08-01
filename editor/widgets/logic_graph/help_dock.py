from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser
from PySide6.QtCore import Signal
from engine.i18n import tr
from engine.logic.graph_asset import NODE_DEFINITIONS

class LogicHelpDock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogicHelpDock")
        self.setMinimumWidth(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(tr("editor.help.search_placeholder", "Buscar nó (ex: move_towards)..."))
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter_help)
        layout.addWidget(self.search_bar)
        
        self.help_text = QTextBrowser()
        self.help_text.setOpenExternalLinks(True)
        layout.addWidget(self.help_text, 1)
        
        self._filter_help("")

    def _filter_help(self, query: str):
        query = query.lower().strip()
        html = [f"<h3>{tr('editor.help.title', 'Dicionário de Nós')}</h3>"]
        
        for node_id, definition in sorted(NODE_DEFINITIONS.items()):
            title = definition.get("title", node_id)
            desc = tr(f"graph.nodes.{node_id}.description", "Sem descrição disponível.")
            
            if query and query not in node_id.lower() and query not in title.lower() and query not in desc.lower():
                continue
                
            html.append(f"<h4>{title} <code>({node_id})</code></h4>")
            html.append(f"<p>{desc}</p>")
            
            inputs = definition.get("inputs", [])
            outputs = definition.get("outputs", [])
            if inputs or outputs:
                html.append("<ul>")
                for port, ptype in inputs:
                    html.append(f"<li><b>[In] {port}</b> <i>({ptype})</i></li>")
                for port, ptype in outputs:
                    html.append(f"<li><b>[Out] {port}</b> <i>({ptype})</i></li>")
                html.append("</ul>")
            html.append("<hr>")
            
        if len(html) == 1:
            html.append(f"<p><i>{tr('editor.help.no_results', 'Nenhum resultado encontrado.')}</i></p>")
            
        self.help_text.setHtml("".join(html))

    def show_node_help(self, node_id: str):
        self.search_bar.setText(node_id)
        self.show()
        self.raise_()
