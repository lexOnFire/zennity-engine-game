from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser
from PySide6.QtCore import Signal
from engine.localization import tr

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
        
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.node import NodeDefinition
        
        context = EngineContext.current()
        if not context:
            self.help_text.setHtml("".join(html) + f"<p><i>{tr('editor.help.no_context', 'Motor não iniciado.')}</i></p>")
            return
            
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            self.help_text.setHtml("".join(html) + f"<p><i>{tr('editor.help.no_metadata', 'Metadados não disponíveis.')}</i></p>")
            return
            
        nodes = manager.get_all(NodeDefinition)
        nodes.sort(key=lambda d: d.id)
        
        count = 0
        for definition in nodes:
            node_id = definition.id
            title = tr(definition.title_key, fallback=definition.title_key)
            desc = tr(definition.description_key, fallback=definition.description_key)
            
            if query and query not in node_id.lower() and query not in title.lower() and query not in desc.lower():
                continue
                
            count += 1
            html.append(f"<h4>{title} <code>({node_id})</code></h4>")
            html.append(f"<p>{desc}</p>")
            
            inputs = getattr(definition, "inputs", [])
            outputs = getattr(definition, "outputs", [])
            if inputs or outputs:
                html.append("<ul>")
                for pin in inputs:
                    pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=getattr(pin, "title_key", pin.id))
                    html.append(f"<li><b>[In] {pin_label}</b> <i>({pin.pin_type})</i></li>")
                for pin in outputs:
                    pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=getattr(pin, "title_key", pin.id))
                    html.append(f"<li><b>[Out] {pin_label}</b> <i>({pin.pin_type})</i></li>")
                html.append("</ul>")
            html.append("<hr>")
            
        if count == 0:
            html.append(f"<p><i>{tr('editor.help.no_results', 'Nenhum resultado encontrado.')}</i></p>")
            
        self.help_text.setHtml("".join(html))

    def show_node_help(self, node_id: str):
        self.search_bar.setText(node_id)
        self.show()
        self.raise_()
