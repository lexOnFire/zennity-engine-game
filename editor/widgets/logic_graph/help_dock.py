from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser, QLabel, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from engine.localization import tr

NODE_HELP_DATABASE: dict[str, dict[str, str]] = {
    "on_start": {
        "title": "Ao Iniciar (On Start)",
        "category": "Eventos",
        "desc": "Nó de evento inicializador. É disparado automaticamente <b>uma única vez</b> no instante em que o objeto é criado ou a cena é carregada.",
        "usage": "Utilize para definir valores iniciais de variáveis (vida, pontuação), tocar sons de entrada ou configurar o estado inicial do personagem.",
        "ports": "<b>[Out] Exec</b>: Fluxo de execução de saída."
    },
    "on_tick": {
        "title": "A Cada Quadro (On Tick / Update)",
        "category": "Eventos",
        "desc": "Nó de evento de atualização contínua. É executado a <b>cada frame do jogo</b> (60 FPS / delta_time).",
        "usage": "Essencial para ler entradas do teclado/gamepad, aplicar movimento contínuo, atualizar temporizadores e checar condições de colisão.",
        "ports": "<b>[Out] Exec</b>: Fluxo contínuo.<br><b>[Out] Delta Time</b>: Tempo em segundos desde o último frame (ex.: 0.016s)."
    },
    "input_axis": {
        "title": "Ler Entrada (Input Axis)",
        "category": "Entrada",
        "desc": "Lê o estado atual dos controles do jogador (direcionais, WASD ou analógico do controle).",
        "usage": "Fornece um vetor <code>Vector2</code> com valores de -1.0 a 1.0 para movimentar o personagem horizontal e verticalmente.",
        "ports": "<b>[Out] Direção</b>: Vetor (X, Y) do direcional.<br><b>[Out] Pular</b>: Booleano (true se a tecla Pular estiver pressionada)."
    },
    "read_input": {
        "title": "Ler Entrada (Input Axis)",
        "category": "Entrada",
        "desc": "Lê o estado atual dos controles do jogador (direcionais, WASD ou analógico do controle).",
        "usage": "Fornece um vetor <code>Vector2</code> com valores de -1.0 a 1.0 para movimentar o personagem horizontal e verticalmente.",
        "ports": "<b>[Out] Direção</b>: Vetor (X, Y) do direcional.<br><b>[Out] Pular</b>: Booleano (true se a tecla Pular estiver pressionada)."
    },
    "move": {
        "title": "Mover Personagem (Move)",
        "category": "Movimento",
        "desc": "Aplica deslocamento físico ao personagem na direção e velocidade especificadas.",
        "usage": "Conecte a saída de <code>Ler Entrada</code> na entrada de Direção deste nó para controlar o personagem em tempo real.",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] Direção</b>: Vetor2.<br><b>[In] Velocidade</b>: Velocidade em pixels/segundo (ex.: 220.0).<br><b>[Out] Exec</b>: Saída do fluxo."
    },
    "move_towards": {
        "title": "Mover Personagem (Move)",
        "category": "Movimento",
        "desc": "Aplica deslocamento físico ao personagem na direção e velocidade especificadas.",
        "usage": "Conecte a saída de <code>Ler Entrada</code> na entrada de Direção deste nó para controlar o personagem em tempo real.",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] Direção</b>: Vetor2.<br><b>[In] Velocidade</b>: Velocidade em pixels/segundo (ex.: 220.0).<br><b>[Out] Exec</b>: Saída do fluxo."
    },
    "is_grounded": {
        "title": "Está no Chão? (Is Grounded)",
        "category": "Física",
        "desc": "Verifica se o colisor do personagem está em contato direto com uma superfície de chão.",
        "usage": "Conecte na entrada de uma condição <code>Ramo</code> antes de permitir o pulo para evitar pulos infinitos no ar.",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[Out] Result</b>: Booleano <code>true</code> se estiver no chão, <code>false</code> se estiver no ar."
    },
    "branch": {
        "title": "Ramo (If / Else)",
        "category": "Fluxo",
        "desc": "Divisor de fluxo condicional. Redireciona a execução dependendo se uma condição é verdadeira ou falsa.",
        "usage": "Conecte uma comparação ou estado booleano (ex.: <code>Está no Chão?</code> ou <code>vida <= 0</code>).",
        "ports": "<b>[In] Exec</b>: Entrada.<br><b>[In] Condição</b>: Booleano.<br><b>[Out] True</b>: Executado se verdadeiro.<br><b>[Out] False</b>: Executado se falso."
    },
    "if_else": {
        "title": "Ramo (If / Else)",
        "category": "Fluxo",
        "desc": "Divisor de fluxo condicional. Redireciona a execução dependendo se uma condição é verdadeira ou falsa.",
        "usage": "Conecte uma comparação ou estado booleano (ex.: <code>Está no Chão?</code> ou <code>vida <= 0</code>).",
        "ports": "<b>[In] Exec</b>: Entrada.<br><b>[In] Condição</b>: Booleano.<br><b>[Out] True</b>: Executado se verdadeiro.<br><b>[Out] False</b>: Executado se falso."
    },
    "play_animation": {
        "title": "Reproduzir Animação (Play Animation)",
        "category": "Animação",
        "desc": "Solicita ao componente Animator para iniciar a reprodução de uma animação específica.",
        "usage": "Alterne entre os clipes de animação como <code>Idle</code>, <code>Run</code>, <code>Jump</code> com base na velocidade do personagem.",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] Animação</b>: Nome do clipe (ex.: Run).<br><b>[In] Loop</b>: Recomenda repetição contínua."
    },
}

class LogicHelpDock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogicHelpDock")
        self.setMinimumWidth(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("AJUDA & GUIA DO NÓ")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #94a3b8; letter-spacing: 0.5px;")
        layout.addWidget(title)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar nó (ex: Mover, Ramo, Teclado)...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setStyleSheet(
            "QLineEdit { background: #141720; border: 1px solid #1e2430; border-radius: 4px; padding: 4px 8px; color: #f8fafc; font-size: 11px; }"
        )
        self.search_bar.textChanged.connect(self._filter_help)
        layout.addWidget(self.search_bar)
        
        self.help_text = QTextBrowser()
        self.help_text.setOpenExternalLinks(True)
        self.help_text.setStyleSheet(
            "QTextBrowser { background: #141720; border: 1px solid #1e2430; border-radius: 6px; color: #cbd5e1; font-size: 11px; padding: 6px; }"
        )
        layout.addWidget(self.help_text, 1)
        
        self._filter_help("")

    def _filter_help(self, query: str):
        query_clean = query.lower().strip()
        
        # 1. Checa no banco interno pré-cadastrado
        matched_keys = [k for k in NODE_HELP_DATABASE if not query_clean or query_clean in k or query_clean in NODE_HELP_DATABASE[k]["title"].lower()]
        
        html = []
        if matched_keys:
            for k in matched_keys[:4]:
                data = NODE_HELP_DATABASE[k]
                html.append(f"<h3 style='color:#38bdf8; margin: 4px 0;'>{data['title']}</h3>")
                html.append(f"<p style='color:#94a3b8; font-size:10px; margin: 2px 0;'><b>Categoria:</b> {data['category']}</p>")
                html.append(f"<p style='margin: 4px 0;'>{data['desc']}</p>")
                html.append(f"<div style='background:#181c28; padding:6px; border-radius:4px; margin:4px 0;'><b>Como Usar:</b><br>{data['usage']}</div>")
                html.append(f"<p style='margin: 4px 0;'><b>Portas:</b><br>{data['ports']}</p>")
                html.append("<hr style='border:1px solid #1e2430;'>")
            self.help_text.setHtml("".join(html))
            return

        # 2. Tenta buscar na Metadata da Engine como fallback
        try:
            from engine.core.context import EngineContext
            from engine.metadata.manager import MetadataManager
            from engine.core.metadata.node import NodeDefinition
            context = EngineContext.current()
            if context:
                manager = context.services.get_optional(MetadataManager)
                if manager:
                    nodes = manager.get_all(NodeDefinition)
                    for definition in nodes:
                        if query_clean in definition.id.lower() or query_clean in definition.title_key.lower():
                            title = tr(definition.title_key, fallback=definition.title_key)
                            desc = tr(definition.description_key, fallback=definition.description_key)
                            html.append(f"<h3 style='color:#38bdf8;'>{title} ({definition.id})</h3>")
                            html.append(f"<p>{desc}</p>")
                            self.help_text.setHtml("".join(html))
                            return
        except Exception:
            pass

        self.help_text.setHtml(
            f"<h3 style='color:#38bdf8;'>Dicionário de Nós</h3>"
            f"<p>Selecione um nó no canvas ou biblioteca para visualizar sua documentação detalhada, utilidade e mapa de portas.</p>"
        )

    def show_node_help(self, node_id_or_name: str):
        if not node_id_or_name:
            return
        node_key = str(node_id_or_name).lower().strip().replace(" ", "_")
        self.search_bar.setText(node_id_or_name)
        self._filter_help(node_key)
        self.show()
        self.raise_()
