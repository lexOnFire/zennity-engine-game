from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser, QLabel, QHBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from engine.localization import tr

NODE_HELP_DATABASE: dict[str, dict[str, str]] = {
    "jump": {
        "title": "Pular (Jump)",
        "category": "Movimento",
        "icon": "🦘",
        "desc": "Aplica um impulso vertical instantâneo para fazer o personagem saltar.",
        "detailed": "Adiciona força vertical ao objeto, causando uma animação de salto. Ideal para plataformers e jogos de ação.",
        "usage": "Combine com a verificação <code>Está no Chão?</code> para evitar pulos no ar. Você pode ajustar a força do pulo no painel de propriedades.",
        "example": "<b>Exemplo:</b> On Tick → Ler Entrada → Branch (está no chão?) → Jump → Play Animation (Jump)",
        "ports": "<b>[In] Exec</b>: Gatilho do pulo.<br><b>[In] Força</b>: Impulso vertical (ex.: 12.0 N).<br><b>[Out] Exec</b>: Saída de execução.",
        "tips": "• Ajuste a força entre 8-15 para pulos naturais<br>• Combine com is_grounded para evitar pulos duplos<br>• Use cooldown para limitar frequência de pulos"
    },
    "on_start": {
        "title": "Ao Iniciar (On Start)",
        "category": "Eventos",
        "icon": "🎬",
        "desc": "Nó de evento inicializador disparado <b>uma única vez</b> ao criar o objeto ou carregar a cena.",
        "detailed": "Este é o ponto de entrada ideal para configuração inicial. É executado antes do primeiro On Tick.",
        "usage": "Utilize para definir valores iniciais de variáveis (vida, pontuação), tocar sons de entrada ou configurar o estado inicial.",
        "example": "<b>Exemplo:</b> On Start → Set Variable (vida = 100) → Play Animation (Idle)",
        "ports": "<b>[Out] Exec</b>: Fluxo de execução de saída.",
        "tips": "• Sempre use para inicializar estado<br>• Executa antes de On Tick no primeiro frame<br>• Ideal para setup de componentes"
    },
    "on_tick": {
        "title": "A Cada Quadro (On Tick / Update)",
        "category": "Eventos",
        "icon": "⏱️",
        "desc": "Nó de evento de atualização contínua executado a <b>cada frame do jogo</b> (60 FPS / delta_time).",
        "detailed": "O coração da lógica contínua. Executa repetidamente enquanto o objeto está ativo na cena.",
        "usage": "Essencial para ler entradas do teclado/gamepad, aplicar movimento contínuo, atualizar temporizadores e checar colisões.",
        "example": "<b>Exemplo:</b> On Tick → Read Input → Move Character → Update Animation State",
        "ports": "<b>[Out] Exec</b>: Fluxo contínuo.<br><b>[Out] Delta Time</b>: Tempo em segundos desde o último frame (ex.: 0.016s).",
        "tips": "• Use delta_time para movement frame-rate independent<br>• Não use para inicialização (use On Start)<br>• Ideal para loops e verificações contínuas"
    },
    "input_axis": {
        "title": "Ler Entrada (Input Axis)",
        "category": "Entrada",
        "icon": "⌨️",
        "desc": "Lê o estado atual dos controles do jogador (direcionais, WASD ou analógico).",
        "detailed": "Retorna valores de -1.0 a 1.0 para cada eixo, permitindo movimento suave e proporcional.",
        "usage": "Fornece um vetor <code>Vector2</code> (X, Y) do direcional para movimentar personagens horizontalmente e verticalmente.",
        "example": "<b>Exemplo:</b> On Tick → Input Axis → Move (velocidade * input) → Play Animation",
        "ports": "<b>[Out] Direção</b>: Vetor (X, Y) do direcional.<br><b>[Out] Pular</b>: Booleano.",
        "tips": "• Retorna -1 a 1 (não 0 ou 1)<br>• WASD funciona automaticamente<br>• Suporta gamepad analógico"
    },
    "move": {
        "title": "Mover Personagem (Move)",
        "category": "Movimento",
        "icon": "➡️",
        "desc": "Aplica deslocamento físico contínuo ao personagem na direção e velocidade especificadas.",
        "detailed": "Integra com o sistema de física do jogo para movimento suave e colisão-aware.",
        "usage": "Conecte a saída de <code>Ler Entrada</code> na entrada de Direção para controlar em tempo real.",
        "example": "<b>Exemplo:</b> On Tick → Input Axis → Move (direction, 200 pixels/s)",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] Direção</b>: Vetor2 normalizando (-1 to 1).<br><b>[In] Velocidade</b>: Pixels/segundo (ex.: 220.0).<br><b>[Out] Exec</b>: Saída.",
        "tips": "• Velocidade típica: 150-250 pixels/s<br>• Normalize a entrada antes de usar<br>• Respeita colisores e obstáculos"
    },
    "is_grounded": {
        "title": "Está no Chão? (Is Grounded)",
        "category": "Física",
        "icon": "🔽",
        "desc": "Verifica se o colisor está em contato direto com uma superfície de chão.",
        "detailed": "Essencial para implementar mecânicas de pulo e movimentação vertical realista.",
        "usage": "Conecte na entrada de uma condição <code>Ramo</code> antes de permitir pulos para evitar pulos infinitos no ar.",
        "example": "<b>Exemplo:</b> On Tick → Is Grounded → Branch → (True) Jump",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[Out] Result</b>: <code>true</code> se no chão, <code>false</code> se no ar.",
        "tips": "• Sempre verifique antes de permitir pulo<br>• Use com Branch para lógica condicional<br>• Detecta plataformas e terreno"
    },
    "branch": {
        "title": "Ramo (If / Else)",
        "category": "Fluxo",
        "icon": "🔀",
        "desc": "Divisor de fluxo condicional que redireciona execução baseado em condição booleana.",
        "detailed": "Implementa lógica if-then-else permitindo decisões no grafo.",
        "usage": "Conecte uma comparação ou estado booleano (ex.: <code>Está no Chão?</code> ou <code>vida <= 0</code>).",
        "example": "<b>Exemplo:</b> Input → Branch (is_grounded) → True: Jump | False: Fall",
        "ports": "<b>[In] Exec</b>: Fluxo entrada.<br><b>[In] Condição</b>: Booleano.<br><b>[Out] True</b>: Se verdadeiro.<br><b>[Out] False</b>: Se falso.",
        "tips": "• Sempre conecte True e False<br>• Suporta aninhamento<br>• Mantém lógica clara e legível"
    },
    "play_animation": {
        "title": "Reproduzir Animação (Play Animation)",
        "category": "Animação",
        "icon": "🎥",
        "desc": "Solicita ao componente Animator para reproduzir uma animação específica.",
        "detailed": "Sincroniza o visual com a lógica de jogo alterando estado do animator.",
        "usage": "Alterne entre clipes como <code>Idle</code>, <code>Run</code>, <code>Jump</code> baseado na velocidade.",
        "example": "<b>Exemplo:</b> Motion Query → (Em movimento?) → Play Animation (Run) : Play Animation (Idle)",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] Animação</b>: Nome do clipe (ex.: Run).<br><b>[In] Loop</b>: Repetir contínuo.",
        "tips": "• Nomes devem corresponder aos clipes do Animator<br>• Use para feedback visual<br>• Combine com transições suaves"
    },
    "set_position": {
        "title": "Definir Posição (Set Position)",
        "category": "Transform",
        "icon": "📍",
        "desc": "Teleporta ou define a posição exata (X, Y) do objeto na cena.",
        "detailed": "Movimento instantâneo sem passar pelos pontos intermediários.",
        "usage": "Utilize para respawnar personagem, teleporte ou cutscenes.",
        "example": "<b>Exemplo:</b> Player Dies → Set Position (spawn_point) → Play Animation (Respawn)",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] X</b>: Posição X.<br><b>[In] Y</b>: Posição Y.",
        "tips": "• Use com cuidado em áreas com colisores<br>• Ideal para respawn e checkpoints<br>• Instantâneo (sem interpolação)"
    },
    "compare": {
        "title": "Comparar (Compare)",
        "category": "Lógica",
        "icon": "🔗",
        "desc": "Compara dois valores numéricos e retorna booleano (verdadeiro/falso).",
        "detailed": "Suporta operadores: ==, !=, >, >=, <, <=",
        "usage": "Use em ramos condicionais para verificar estado (vida <= 0, score >= 100).",
        "example": "<b>Exemplo:</b> Compare (vida <= 0) → Branch → True: Game Over",
        "ports": "<b>[In] A</b>: Primeiro valor.<br><b>[In] B</b>: Segundo valor.<br>[In] Operador: ==, !=, >, >=, <, <=<br><b>[Out]</b>: Resultado booleano.",
        "tips": "• Tipos devem ser compatíveis<br>• Use com Branch para lógica<br>• Aceita números e variáveis"
    },
    "compare_text": {
        "title": "Comparar Texto (Compare Text)",
        "category": "Lógica",
        "icon": "📝",
        "desc": "Compara dois textos e retorna booleano (verdadeiro/falso).",
        "detailed": "Compara strings de forma exata. Suporta operadores: ==, !=, contains (contém).",
        "usage": "Use para verificar nomes, tags de texto, diálogos ou identificadores de string.",
        "example": "<b>Exemplo:</b> Get Tag → Compare Text (== 'enemy') → Branch → True: Attack",
        "ports": "<b>[In] A</b>: Primeiro texto.<br><b>[In] B</b>: Segundo texto.<br>[In] Operador: ==, !=, contains<br><b>[Out]</b>: Resultado booleano.",
        "tips": "• Comparação é case-sensitive<br>• Use 'contains' para busca parcial<br>• Ideal com Get Tag ou variáveis de texto"
    },
    "compare_text_ignore_case": {
        "title": "Comparar Texto (Sem Maiúsculas) (Compare Text Ignore Case)",
        "category": "Lógica",
        "icon": "📝",
        "desc": "Compara dois textos ignorando maiúsculas/minúsculas (case-insensitive).",
        "detailed": "Mesma funcionalidade do Compare Text, mas ignora diferenças de capitalização.",
        "usage": "Use quando a diferença entre maiúsculas não importa (ex: 'PLAYER', 'player', 'Player' são iguais).",
        "example": "<b>Exemplo:</b> Player Name → Compare Text Ignore Case (== 'hero') → Branch",
        "ports": "<b>[In] A</b>: Primeiro texto.<br><b>[In] B</b>: Segundo texto.<br>[In] Operador: ==, !=, contains<br><b>[Out]</b>: Resultado booleano.",
        "tips": "• Ignora diferença entre maiúsculas/minúsculas<br>• Melhor para nomes de jogadores<br>• Mais flexível que Compare Text"
    },
}

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

    def _filter_help(self, query: str):
        query_clean = query.lower().strip().replace(" ", "_")
        raw_query = query.lower().strip()

        # Match inteligente no dicionário
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

        if not matched_keys:
            self._show_fallback(query)
            return

        html = []
        for k in matched_keys[:5]:
            data = NODE_HELP_DATABASE[k]
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
            # Nó não encontrado
            pretty_title = query.strip()
            self.help_text.setHtml(f"""
            <div style='padding: 10px;'>
                <div style='background:#141824; border-left: 4px solid #f87171; padding: 12px; margin: 8px 0; border-radius: 4px;'>
                    <h3 style='color:#f87171; margin: 0 0 6px 0; font-size: 12px;'>❓ "{pretty_title}"</h3>
                    <p style='color:#cbd5e1; font-size: 10px; margin: 6px 0; line-height: 1.5;'>
                        Este nó não está documentado na base de dados ainda.
                    </p>
                    <p style='color:#cbd5e1; font-size: 10px; margin: 6px 0; line-height: 1.5;'>
                        <b>Informações disponíveis:</b><br>
                        • Tipo: Nó do Logic Graph<br>
                        • Categoria: Visual Scripting<br>
                        • Processa a lógica quando acionado no fluxo
                    </p>
                </div>

                <div style='background:#141824; border-left: 4px solid #fbbf24; padding: 12px; margin: 12px 0; border-radius: 4px;'>
                    <p style='color:#fbbf24; font-size: 10px; font-weight: bold; margin: 0 0 6px 0;'>💡 Dicas:</p>
                    <ul style='color:#cbd5e1; font-size: 10px; margin: 0; padding-left: 20px;'>
                        <li>Procure documentação do nó no editor</li>
                        <li>Verifique os pinos de entrada e saída</li>
                        <li>Teste conectando em um ramo simples</li>
                        <li>Consulte exemplos no projeto</li>
                    </ul>
                </div>

                <p style='color:#64748b; font-size: 9px; margin-top: 14px; text-align: center;'>
                    🔍 Tente buscar outros nós documentados na paleta
                </p>
            </div>
            """)

    def show_node_help(self, node_id_or_name: str):
        """Mostra ajuda para um nó específico."""
        if not node_id_or_name:
            return
        self.search_bar.blockSignals(True)
        self.search_bar.setText(node_id_or_name)
        self.search_bar.blockSignals(False)
        self._filter_help(node_id_or_name)
