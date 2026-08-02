from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser, QLabel, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from engine.localization import tr

NODE_HELP_DATABASE: dict[str, dict[str, str]] = {
    "jump": {
        "title": "Pular (Jump)",
        "category": "Movimento",
        "desc": "Aplica um impulso vertical instantâneo para fazer o personagem saltar.",
        "usage": "Combine com a verificação <code>Está no Chão?</code> para evitar pulos no ar. Você pode ajustar a força do pulo no painel de propriedades.",
        "ports": "<b>[In] Exec</b>: Gatilho do pulo.<br><b>[In] Força</b>: Impulso vertical (ex.: 12.0 N).<br><b>[Out] Exec</b>: Saída de execução."
    },
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
    "get_continuous_motion": {
        "title": "Obter Movimento Contínuo (Get Continuous Motion)",
        "category": "Movimento",
        "desc": "Consulta o vetor de velocidade e direção do movimento contínuo ativo no objeto.",
        "usage": "Utilize para verificar se o objeto está se movendo e qual a sua velocidade atual em cada eixo.",
        "ports": "<b>[In] Exec</b>: Consulta.<br><b>[Out] Velocidade X</b>: Velocidade horizontal.<br><b>[Out] Velocidade Y</b>: Velocidade vertical."
    },
    "motion_state_query": {
        "title": "Consulta de Estado de Movimento (Motion State Query)",
        "category": "Movimento",
        "desc": "Verifica o estado físico atual do personagem (se está parado, correndo, pulando ou caindo).",
        "usage": "Ideal para acionar transições de animação no Animator com base no estado físico real.",
        "ports": "<b>[In] Exec</b>: Consulta.<br><b>[Out] Em Movimento</b>: Booleano.<br><b>[Out] No Ar</b>: Booleano."
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
    "set_position": {
        "title": "Definir Posição (Set Position)",
        "category": "Transform",
        "desc": "Teleporta ou define a posição exata (X, Y) do objeto na cena.",
        "usage": "Utilize para respawnar o personagem ou mover objetos instantaneamente.",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] X</b>: Posição X.<br><b>[In] Y</b>: Posição Y."
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
        query_clean = query.lower().strip().replace(" ", "_")
        raw_query = query.lower().strip()
        
        # Match inteligente no dicionário pré-cadastrado
        matched_keys = []
        for k, data in NODE_HELP_DATABASE.items():
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

        # Fallback genérico quando o nó pesquisado não está no dicionário estático
        pretty_title = query.strip().capitalize()
        self.help_text.setHtml(
            f"<h3 style='color:#38bdf8; margin: 4px 0;'>{pretty_title}</h3>"
            f"<p style='color:#94a3b8; font-size:10px; margin: 2px 0;'><b>Categoria:</b> Grafo / Lógica Visual</p>"
            f"<p style='margin: 4px 0;'>Nó executor/avaliador do Visual Scripting. Processa a lógica do grafo quando acionado no fluxo.</p>"
            f"<div style='background:#181c28; padding:6px; border-radius:4px; margin:4px 0;'><b>Como Usar:</b><br>Conecte os pinos de entrada e saída no fluxo de execução do seu grafo de personagem ou objeto.</div>"
        )

    def show_node_help(self, node_id_or_name: str):
        if not node_id_or_name:
            return
        self.search_bar.setText(node_id_or_name)
        self._filter_help(node_id_or_name)
        self.show()
        self.raise_()
