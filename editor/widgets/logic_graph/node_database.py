"""Base de dados completa de nós do Logic Graph com documentação detalhada."""

NODE_DATABASE = {
    # ============ EVENTOS ============
    "on_start": {
        "title": "Ao Iniciar (On Start)",
        "category": "Eventos",
        "icon": "🎬",
        "desc": "Disparado uma única vez ao criar o objeto ou carregar a cena.",
        "detailed": "Ponto de entrada ideal para configuração inicial. Executa antes do primeiro On Tick.",
        "usage": "Inicialize variáveis, configure componentes, toque sons de entrada.",
        "example": "<b>Exemplo:</b> On Start → Set Variable (vida = 100) → Play Animation (Idle)",
        "ports": "<b>[Out] Exec</b>: Fluxo de execução.",
        "tips": "• Use para setup<br>• Executa antes de On Tick<br>• Ideal para inicialização"
    },
    "on_tick": {
        "title": "A Cada Quadro (On Tick)",
        "category": "Eventos",
        "icon": "⏱️",
        "desc": "Executado a cada frame do jogo (60 FPS).",
        "detailed": "O coração da lógica contínua. Executa repetidamente enquanto o objeto está ativo.",
        "usage": "Leia entradas, aplique movimento, atualize temporizadores, verifique colisões.",
        "example": "<b>Exemplo:</b> On Tick → Read Input → Move → Update Animation",
        "ports": "<b>[Out] Exec</b>: Fluxo contínuo.<br><b>[Out] Delta Time</b>: Tempo desde último frame.",
        "tips": "• Use delta_time para movement<br>• Não use para inicialização<br>• Ideal para loops"
    },
    "delta_time": {
        "title": "Delta Time",
        "category": "Eventos",
        "icon": "⏳",
        "desc": "Retorna o tempo em segundos desde o último frame.",
        "detailed": "Valor de ~0.016s em 60 FPS. Essencial para movimento frame-rate independente.",
        "usage": "Multiplique a velocidade por delta_time para movimento suave.",
        "example": "<b>Exemplo:</b> Delta Time × Velocidade = Distância/frame",
        "ports": "<b>[Out] Value</b>: Tempo em segundos (float).",
        "tips": "• Sempre multiplique movimento por delta_time<br>• Garante consistência<br>• Valores típicos: 0.010-0.020"
    },
    "key_pressed": {
        "title": "Tecla Pressionada (Key Pressed)",
        "category": "Entrada",
        "icon": "⌨️",
        "desc": "Detecta quando uma tecla é pressionada (bordaascendente).",
        "detailed": "Dispara uma única vez per press, não continua enquanto pressionada.",
        "usage": "Detecte ações únicas como pulos, ataques, interações.",
        "example": "<b>Exemplo:</b> Key Pressed (Space) → Jump",
        "ports": "<b>[In] Tecla</b>: Código da tecla (ex: Space, A, Enter).<br><b>[Out] Exec</b>: Executa quando pressionada.",
        "tips": "• Use para eventos únicos<br>• Para contínuo, use Key Held<br>• Suporta qualquer tecla"
    },
    "key_held": {
        "title": "Tecla Mantida (Key Held)",
        "category": "Entrada",
        "icon": "🔘",
        "desc": "Retorna true enquanto uma tecla está pressionada.",
        "detailed": "Continua retornando true enquanto mantida. Reseta ao soltar.",
        "usage": "Movimento contínuo, ações mantidas, charges.",
        "example": "<b>Exemplo:</b> Key Held (W) → Move Forward",
        "ports": "<b>[In] Tecla</b>: Código da tecla.<br><b>[Out] Value</b>: Booleano (true/false).",
        "tips": "• Use para movimento<br>• Retorna contínuo<br>• Ideal com Branch"
    },
    "input_axis": {
        "title": "Ler Entrada (Input Axis)",
        "category": "Entrada",
        "icon": "🕹️",
        "desc": "Lê direcionais WASD ou analógico (-1.0 a 1.0).",
        "detailed": "Retorna Vector2 com movimento contínuo e proporcional.",
        "usage": "Movimento básico do personagem.",
        "example": "<b>Exemplo:</b> Input Axis → Move (velocidade × input)",
        "ports": "<b>[Out] Direction</b>: Vector2 (-1 a 1).",
        "tips": "• WASD funciona automaticamente<br>• Gamepad analógico suportado<br>• Retorna -1, 0 ou 1"
    },
    "is_grounded": {
        "title": "Está no Chão? (Is Grounded)",
        "category": "Física",
        "icon": "🔽",
        "desc": "Verifica se o colisor está em contato com solo.",
        "detailed": "Essencial para mecânicas de pulo realista.",
        "usage": "Verifique antes de permitir pulo.",
        "example": "<b>Exemplo:</b> Is Grounded → Branch → (True) Jump",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[Out] Result</b>: Booleano.",
        "tips": "• Sempre verifique antes de pular<br>• Detecta plataformas<br>• Respeita colisores"
    },
    "event_collision_enter": {
        "title": "Colisão Iniciou",
        "category": "Física",
        "icon": "💥",
        "desc": "Dispara quando objeto entra em colisão com outro.",
        "detailed": "Acontece uma única vez por colisão.",
        "usage": "Detecte damage, coleta, eventos físicos.",
        "example": "<b>Exemplo:</b> Collision Enter (enemy) → Apply Damage",
        "ports": "<b>[Out] Exec</b>: Dispara na colisão.<br><b>[Out] Other</b>: Objeto colidido.",
        "tips": "• Dispara uma vez por colisão<br>• Retorna objeto colidido<br>• Use com tags"
    },
    "event_collision_exit": {
        "title": "Colisão Terminou",
        "category": "Física",
        "icon": "👋",
        "desc": "Dispara quando sai de uma colisão.",
        "detailed": "Acontece quando os colisores se separam.",
        "usage": "Detecte saída de áreas, términodenadas.",
        "example": "<b>Exemplo:</b> Collision Exit → Stop Sound",
        "ports": "<b>[Out] Exec</b>: Dispara ao sair.<br><b>[Out] Other</b>: Objeto que saiu.",
        "tips": "• Complemento de Collision Enter<br>• Útil para limpar estado<br>• Compatível com triggers"
    },

    # ============ FLUXO ============
    "if_else": {
        "title": "Ramo (If / Else)",
        "category": "Fluxo",
        "icon": "🔀",
        "desc": "Divisor condicional que redireciona execução.",
        "detailed": "Implementa if-then-else permitindo decisões no grafo.",
        "usage": "Conecte uma comparação ou booleano.",
        "example": "<b>Exemplo:</b> Input → Branch (is_grounded) → True: Jump | False: Fall",
        "ports": "<b>[In] Exec</b>: Entrada.<br><b>[In] Condition</b>: Booleano.<br><b>[Out] True/False</b>: Saídas.",
        "tips": "• Sempre conecte True E False<br>• Suporta aninhamento<br>• Mantém lógica clara"
    },
    "call_subgraph": {
        "title": "Chamar Subgrafo",
        "category": "Fluxo",
        "icon": "📦",
        "desc": "Executa outro grafo como uma função.",
        "detailed": "Reutilize lógica complexa em múltiplos objetos.",
        "usage": "Modularize comportamentos complexos.",
        "example": "<b>Exemplo:</b> Call Subgraph (ProcessDamage) → Continue",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[Out] Exec</b>: Retorna após conclusão.",
        "tips": "• Organize código complexo<br>• Reutilize em vários objetos<br>• Suporta parâmetros"
    },

    # ============ MOVIMENTO ============
    "move": {
        "title": "Mover Personagem",
        "category": "Movimento",
        "icon": "➡️",
        "desc": "Aplica movimento físico contínuo.",
        "detailed": "Integrado com sistema de física para colisão-aware.",
        "usage": "Conecte Input Axis para controlar em tempo real.",
        "example": "<b>Exemplo:</b> Input → Move (direction, 200 px/s)",
        "ports": "<b>[In] Direction</b>: Vector2.<br><b>[In] Speed</b>: Pixels/segundo.<br><b>[Out] Exec</b>: Saída.",
        "tips": "• Velocidade típica: 150-250<br>• Respeita colisores<br>• Use delta_time"
    },
    "get_position": {
        "title": "Obter Posição",
        "category": "Movimento",
        "icon": "📍",
        "desc": "Retorna posição XY atual do objeto.",
        "detailed": "Útil para cálculos de distância e lógica de posicionamento.",
        "usage": "Verifique distância, crie patrulhas, calcule direções.",
        "example": "<b>Exemplo:</b> Get Position → Calculate Distance",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[Out] X/Y</b>: Coordenadas.",
        "tips": "• Retorna posição atual<br>• Use para cálculos<br>• Compatível com comparações"
    },
    "set_position": {
        "title": "Definir Posição",
        "category": "Movimento",
        "icon": "📌",
        "desc": "Teleporta para posição exata XY.",
        "detailed": "Movimento instantâneo sem passar por pontos intermediários.",
        "usage": "Respawn, teleporte, cutscenes.",
        "example": "<b>Exemplo:</b> Player Dies → Set Position (spawn)",
        "ports": "<b>[In] X/Y</b>: Coordenadas alvo.<br><b>[Out] Exec</b>: Saída.",
        "tips": "• Instantâneo<br>• Cuidado com colisores<br>• Ideal para respawn"
    },

    # ============ ANIMAÇÃO ============
    "play_animation": {
        "title": "Reproduzir Animação",
        "category": "Animação",
        "icon": "🎥",
        "desc": "Inicia um clipe de animação no Animator.",
        "detailed": "Sincroniza visual com lógica de jogo.",
        "usage": "Alterne entre Idle, Run, Jump, Attack.",
        "example": "<b>Exemplo:</b> (Em movimento) → Play Animation (Run) : Play Animation (Idle)",
        "ports": "<b>[In] Animation</b>: Nome do clipe.<br><b>[In] Loop</b>: Repetir contínuo.",
        "tips": "• Nomes devem corresponder ao Animator<br>• Use para feedback visual<br>• Combine com transições"
    },

    # ============ LÓGICA ============
    "compare_number": {
        "title": "Comparar Números",
        "category": "Lógica",
        "icon": "🔢",
        "desc": "Compara dois números com operadores: ==, !=, >, >=, <, <=",
        "detailed": "Retorna booleano true/false.",
        "usage": "Verifique vida, pontuação, distâncias.",
        "example": "<b>Exemplo:</b> Compare (vida <= 0) → Branch → True: Game Over",
        "ports": "<b>[In] A/B</b>: Números.<br><b>[In] Operator</b>: Comparação.<br><b>[Out]</b>: Booleano.",
        "tips": "• Suporta todos operadores<br>• Use com Branch<br>• Simples e eficaz"
    },
    "compare_text": {
        "title": "Comparar Texto",
        "category": "Lógica",
        "icon": "📝",
        "desc": "Compara duas strings com ==, !=, contains.",
        "detailed": "Retorna booleano true/false.",
        "usage": "Verifique tags, nomes, estados de texto.",
        "example": "<b>Exemplo:</b> Compare (tag == 'enemy') → Take Damage",
        "ports": "<b>[In] A/B</b>: Textos.<br><b>[In] Op</b>: Operação.<br><b>[Out]</b>: Booleano.",
        "tips": "• Case-sensitive<br>• Suporte a 'contains'<br>• Use com tags"
    },
    "and": {
        "title": "E (AND)",
        "category": "Lógica",
        "icon": "🔗",
        "desc": "Retorna true se AMBAS entradas são true.",
        "detailed": "Combinação de múltiplas condições.",
        "usage": "Múltiplas condições devem ser verdadeiras.",
        "example": "<b>Exemplo:</b> (is_grounded AND key_pressed) → Jump",
        "ports": "<b>[In] A/B</b>: Booleanos.<br><b>[Out]</b>: AND resultado.",
        "tips": "• Ambas devem ser true<br>• Pode encadear<br>• Útil para validação"
    },
    "or": {
        "title": "OU (OR)",
        "category": "Lógica",
        "icon": "⚡",
        "desc": "Retorna true se qualquer entrada é true.",
        "detailed": "Alternativas de execução.",
        "usage": "Qualquer condição pode ser verdadeira.",
        "example": "<b>Exemplo:</b> (attack_pressed OR enemy_nearby) → Fight",
        "ports": "<b>[In] A/B</b>: Booleanos.<br><b>[Out]</b>: OR resultado.",
        "tips": "• Qualquer entrada pode ser true<br>• Encadeável<br>• Útil para alternativas"
    },
    "not": {
        "title": "NÃO (NOT)",
        "category": "Lógica",
        "icon": "❌",
        "desc": "Inverte booleano (true→false, false→true).",
        "detailed": "Negação lógica.",
        "usage": "Verifique condição oposta.",
        "example": "<b>Exemplo:</b> NOT (is_grounded) → Free Fall",
        "ports": "<b>[In] A</b>: Booleano.<br><b>[Out]</b>: NOT resultado.",
        "tips": "• Simples inversão<br>• Combine com outras operações<br>• Torna lógica clara"
    },

    # ============ VARIÁVEIS ============
    "get_variable": {
        "title": "Obter Variável",
        "category": "Variáveis",
        "icon": "📦",
        "desc": "Lê valor de uma variável do Blackboard.",
        "detailed": "Acessa dados salvos globalmente.",
        "usage": "Recupere vida, pontuação, estado do jogo.",
        "example": "<b>Exemplo:</b> Get Variable (player_health) → Compare",
        "ports": "<b>[Out] Value</b>: Valor da variável.",
        "tips": "• Tipo automático<br>• Globalmente acessível<br>• Use para estado persistente"
    },
    "number_value": {
        "title": "Valor Número",
        "category": "Variáveis",
        "icon": "🔢",
        "desc": "Constante numérica (inteiro ou float).",
        "detailed": "Valor fixo configurável no editor.",
        "usage": "Use valores constantes em cálculos.",
        "example": "<b>Exemplo:</b> 100 → Set Variable (max_health = 100)",
        "ports": "<b>[Out] Value</b>: Número constante.",
        "tips": "• Valor fixo<br>• Editável no painel<br>• Reutilize valores"
    },
    "bool_value": {
        "title": "Valor Booleano",
        "category": "Variáveis",
        "icon": "✓",
        "desc": "Constante booleana (true/false).",
        "detailed": "Valor fixo configurável.",
        "usage": "Use em condições, comparações.",
        "example": "<b>Exemplo:</b> True → Set Variable (is_alive = True)",
        "ports": "<b>[Out] Value</b>: Booleano constante.",
        "tips": "• True ou False<br>• Editável no painel<br>• Use em branches"
    },
    "text_value": {
        "title": "Valor Texto",
        "category": "Variáveis",
        "icon": "📝",
        "desc": "Constante de texto.",
        "detailed": "String fixa configurável.",
        "usage": "Use em comparações, logs, tags.",
        "example": "<b>Exemplo:</b> 'enemy' → Compare Text",
        "ports": "<b>[Out] Value</b>: Texto constante.",
        "tips": "• String fixa<br>• Editável no painel<br>• Use com comparações"
    },
    "self_object": {
        "title": "Este Objeto",
        "category": "Objetos",
        "icon": "🎯",
        "desc": "Retorna referência ao próprio objeto.",
        "detailed": "Útil para passar self em operações.",
        "usage": "Use como alvo para operações.",
        "example": "<b>Exemplo:</b> Self Object → Get Tag",
        "ports": "<b>[Out] Object</b>: Referência do objeto.",
        "tips": "• Sempre retorna self<br>• Use para compatibilidade<br>• Essencial em subgrafos"
    },
    "find_tag": {
        "title": "Encontrar por Tag",
        "category": "Objetos",
        "icon": "🔍",
        "desc": "Procura objeto que tem uma tag específica.",
        "detailed": "Retorna primeiro objeto encontrado com tag.",
        "usage": "Encontre 'Food', 'Player', 'Enemy'.",
        "example": "<b>Exemplo:</b> Find Tag ('Food') → Chase",
        "ports": "<b>[In] Tag</b>: Tag a procurar.<br><b>[Out] Object</b>: Objeto encontrado.",
        "tips": "• Case-insensitive<br>• Retorna um objeto<br>• Fallback para nome"
    },
    "get_tag": {
        "title": "Obter Tag",
        "category": "Objetos",
        "icon": "🏷️",
        "desc": "Lê qual é a tag de um objeto.",
        "detailed": "Retorna string com a tag.",
        "usage": "Verifique qual é a tag de algo.",
        "example": "<b>Exemplo:</b> Get Tag (objeto) → Compare Text",
        "ports": "<b>[In] Target</b>: Objeto.<br><b>[Out] Value</b>: Tag como texto.",
        "tips": "• Retorna string<br>• Use para validação<br>• Compatível com comparações"
    },
    "create_object": {
        "title": "Criar Objeto",
        "category": "Objetos",
        "icon": "✨",
        "desc": "Cria novo GameObject em tempo de execução.",
        "detailed": "Instancia objeto na cena.",
        "usage": "Gere projéteis, inimigos, efeitos.",
        "example": "<b>Exemplo:</b> Create Object (projectile) → Launch",
        "ports": "<b>[In] Object</b>: Prefab.<br><b>[In] Position</b>: XY.<br><b>[Out] Created</b>: Novo objeto.",
        "tips": "• Dinâmico<br>• Suporta posição<br>• Ideal para spawning"
    },
    "clone_object": {
        "title": "Clonar Objeto",
        "category": "Objetos",
        "icon": "📋",
        "desc": "Cria cópia de um objeto existente.",
        "detailed": "Duplica objeto mantendo propriedades.",
        "usage": "Gere cópias de objetos.",
        "example": "<b>Exemplo:</b> Clone Object → Move",
        "ports": "<b>[In] Target</b>: Objeto a clonar.<br><b>[Out] Copy</b>: Novo objeto.",
        "tips": "• Copia estado<br>• Mantém propriedades<br>• Útil para spawning"
    },
    "create_prefab": {
        "title": "Criar Prefab",
        "category": "Objetos",
        "icon": "🏗️",
        "desc": "Cria instância de um prefab.",
        "detailed": "Spawna objeto pré-configurado.",
        "usage": "Spawna inimigos, itens, efeitos.",
        "example": "<b>Exemplo:</b> Create Prefab (fireball) at position",
        "ports": "<b>[In] Prefab</b>: Asset.<br><b>[In] Position</b>: XY.<br><b>[Out] Instance</b>: Novo.",
        "tips": "• Usa prefabs salvos<br>• Rápido e eficiente<br>• Ideal para design"
    },

    # ============ MATEMÁTICA ============
    "add_number": {
        "title": "Adicionar",
        "category": "Matemática",
        "icon": "➕",
        "desc": "Soma dois números (A + B).",
        "detailed": "Operação aritmética básica.",
        "usage": "Calcule totais, danos, acumulações.",
        "example": "<b>Exemplo:</b> Health (100) + Heal (20) = 120",
        "ports": "<b>[In] A/B</b>: Números.<br><b>[Out]</b>: Resultado.",
        "tips": "• Simples e rápido<br>• Encadeável<br>• Use para cálculos"
    },
    "subtract_number": {
        "title": "Subtrair",
        "category": "Matemática",
        "icon": "➖",
        "desc": "Subtrai B de A (A - B).",
        "detailed": "Operação aritmética básica.",
        "usage": "Dano, consumo, diferenças.",
        "example": "<b>Exemplo:</b> Health (100) - Damage (10) = 90",
        "ports": "<b>[In] A/B</b>: Números.<br><b>[Out]</b>: Resultado.",
        "tips": "• A ordem importa<br>• Use para decremento<br>• Dano típico"
    },
    "multiply_number": {
        "title": "Multiplicar",
        "category": "Matemática",
        "icon": "✖️",
        "desc": "Multiplica dois números (A × B).",
        "detailed": "Operação aritmética básica.",
        "usage": "Escala, física, proporções.",
        "example": "<b>Exemplo:</b> Speed (100) × Time (0.016) = 1.6 pixels",
        "ports": "<b>[In] A/B</b>: Números.<br><b>[Out]</b>: Resultado.",
        "tips": "• Comutativo<br>• Essencial para física<br>• Use com delta_time"
    },
    "divide_number": {
        "title": "Dividir",
        "category": "Matemática",
        "icon": "➗",
        "desc": "Divide A por B (A ÷ B).",
        "detailed": "Operação aritmética básica.",
        "usage": "Média, proporções, normalização.",
        "example": "<b>Exemplo:</b> Damage (100) ÷ Armor (2) = 50",
        "ports": "<b>[In] A/B</b>: Números.<br><b>[Out]</b>: Resultado.",
        "tips": "• A ordem importa<br>• Evite divisão por zero<br>• Útil para proporções"
    },
    "absolute_number": {
        "title": "Valor Absoluto",
        "category": "Matemática",
        "icon": "📏",
        "desc": "Retorna valor positivo (|A|).",
        "detailed": "Remove sinal negativo.",
        "usage": "Distância, magnitude, velocidade.",
        "example": "<b>Exemplo:</b> Absolute (-50) = 50",
        "ports": "<b>[In] A</b>: Número.<br><b>[Out]</b>: Absoluto.",
        "tips": "• Sempre positivo<br>• Use para distância<br>• Magnitudes"
    },
    "clamp_number": {
        "title": "Limitar Número",
        "category": "Matemática",
        "icon": "📊",
        "desc": "Limita número entre mín e máx.",
        "detailed": "Garante valor dentro de intervalo.",
        "usage": "Saúde max, velocidade máxima, ranges.",
        "example": "<b>Exemplo:</b> Clamp (150 health, 0, 100) = 100",
        "ports": "<b>[In] Value</b>: Número.<br><b>[In] Min/Max</b>: Limites.<br><b>[Out]</b>: Limitado.",
        "tips": "• Essencial para validação<br>• Evita overflow<br>• Use para clamps de vida"
    },
    "random_number": {
        "title": "Número Aleatório",
        "category": "Matemática",
        "icon": "🎲",
        "desc": "Gera número aleatório entre min e máx.",
        "detailed": "Valores pseudo-aleatórios.",
        "usage": "Variação, dano crítico, spawning.",
        "example": "<b>Exemplo:</b> Random (10, 20) = 15.3",
        "ports": "<b>[In] Min/Max</b>: Intervalo.<br><b>[Out] Value</b>: Aleatório.",
        "tips": "• Útil para variação<br>• Use para unpredictability<br>• Range customizável"
    },

    # ============ TEXTO ============
    "join_text": {
        "title": "Juntar Texto",
        "category": "Texto",
        "icon": "🔤",
        "desc": "Concatena múltiplos textos.",
        "detailed": "Combine strings em uma.",
        "usage": "Criar mensagens, logs, labels.",
        "example": "<b>Exemplo:</b> Join ('Saúde: ', '100') = 'Saúde: 100'",
        "ports": "<b>[In] A/B</b>: Textos.<br><b>[Out]</b>: Concatenado.",
        "tips": "• Ordem importa<br>• Encadeável<br>• Use para UI"
    },
    "to_text": {
        "title": "Converter para Texto",
        "category": "Texto",
        "icon": "📄",
        "desc": "Converte número/booleano em texto.",
        "detailed": "Casting para string.",
        "usage": "Exiba números, converta tipos.",
        "example": "<b>Exemplo:</b> To Text (100) = '100'",
        "ports": "<b>[In] Value</b>: Qualquer tipo.<br><b>[Out]</b>: Texto.",
        "tips": "• Automático<br>• Use para display<br>• Compatível com Join"
    },

    # ============ SUBGRAFOS ============
    "subgraph_input": {
        "title": "Entrada de Subgrafo",
        "category": "Subgrafos",
        "icon": "📥",
        "desc": "Recebe parâmetro passado ao chamar subgrafo.",
        "detailed": "Interface de entrada do subgrafo.",
        "usage": "Receba valores passados.",
        "example": "<b>Exemplo:</b> Subgraph Input (target) → Use in Logic",
        "ports": "<b>[Out] Value</b>: Parâmetro recebido.",
        "tips": "• Configure no editor<br>• Type-safe<br>• Usado em Call Subgraph"
    },

    # ============ BEHAVIOR TREE (EXTRAS) ============
    "cooldown": {
        "title": "Cooldown",
        "category": "Behavior Tree",
        "icon": "⏱️",
        "desc": "Bloqueia execução por um tempo após sucesso.",
        "detailed": "Implementa tempo de espera entre execuções.",
        "usage": "Limitar frequência de ataques, habilidades, decisões.",
        "example": "<b>Exemplo:</b> Attack → Cooldown (5s) → Pode atacar novamente",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[In] Duration</b>: Tempo em segundos.<br><b>[Out] Exec</b>: Saída.",
        "tips": "• Evita spam de ações<br>• Tempo em segundos<br>• Ideal para cadência de ataque"
    },
    "inverter": {
        "title": "Inversor",
        "category": "Behavior Tree",
        "icon": "🔄",
        "desc": "Inverte resultado do filho (success→failure, failure→success).",
        "detailed": "Implementa lógica NOT para condições.",
        "usage": "Negar uma condição ou resultado.",
        "example": "<b>Exemplo:</b> NOT (is_grounded) → Free Fall",
        "ports": "<b>[In] Exec</b>: Gatilho.<br><b>[Out] Exec</b>: Resultado invertido.",
        "tips": "• Inverte apenas sucesso/falha<br>• Running continua Running<br>• Use com Sequence"
    },
    "wait": {
        "title": "Esperar (Wait)",
        "category": "Behavior Tree",
        "icon": "⏳",
        "desc": "Aguarda um tempo configurado.",
        "detailed": "Pausa a execução por duração especificada.",
        "usage": "Pausas entre ações, delays, animações.",
        "example": "<b>Exemplo:</b> Attack → Wait (0.5s) → Next Attack",
        "ports": "<b>[In] Duration</b>: Tempo em segundos.<br><b>[Out] Exec</b>: Após tempo decorrido.",
        "tips": "• Use tempo curto para responsividade<br>• Ideal entre ações<br>• Configurable"
    },
    "repeat": {
        "title": "Repetir (Repeat)",
        "category": "Behavior Tree",
        "icon": "🔁",
        "desc": "Repete o filho um número de vezes ou continuamente.",
        "detailed": "Loop controlado de execução.",
        "usage": "Rotinas, rondas, comportamentos persistentes.",
        "example": "<b>Exemplo:</b> Repeat (0 = infinito) → Patrol",
        "ports": "<b>[In] Count</b>: Número de repetições (0=infinito).<br><b>[Out] Exec</b>: Saída.",
        "tips": "• 0 = repetição infinita<br>• Compatível com Sequence<br>• Use com cuidado"
    },
    "attack": {
        "title": "Atacar (Attack)",
        "category": "Behavior Tree",
        "icon": "⚔️",
        "desc": "Aplica dano ao alvo se em alcance.",
        "detailed": "Ação de combate corpo a corpo.",
        "usage": "Inimigos, combate, dano.",
        "example": "<b>Exemplo:</b> (Em Alcance) → Attack → Cooldown",
        "ports": "<b>[In] Target</b>: Alvo.<br><b>[In] Damage</b>: Valor dano.<br><b>[Out] Exec</b>: Saída.",
        "tips": "• Use com Cooldown<br>• Combine com condições<br>• Respeita alcance"
    },
    "parameter_condition": {
        "title": "Condição de Parâmetro",
        "category": "Behavior Tree",
        "icon": "🔍",
        "desc": "Compara um parâmetro do Behavior Tree.",
        "detailed": "Comparação de variáveis de estado.",
        "usage": "Alerta, vida baixa, estados personalizados.",
        "example": "<b>Exemplo:</b> if (health <= 20) → Flee",
        "ports": "<b>[In] Parameter</b>: Nome.<br><b>[In] Value</b>: Comparar com.<br><b>[Out] Exec</b>: Saída.",
        "tips": "• Operadores: ==, !=, >, >=, <, <=<br>• Use com variáveis BT<br>• Type-safe"
    },

    # ============ EVENTO CUSTOMIZADO ============
    "event_custom": {
        "title": "Evento Customizado",
        "category": "Eventos",
        "icon": "🎯",
        "desc": "Evento disparado por script ou editor.",
        "detailed": "Ponto de entrada customizável.",
        "usage": "Gatilhos personalizados, eventos do jogo.",
        "example": "<b>Exemplo:</b> Custom Event (on_damage) → Play Animation",
        "ports": "<b>[Out] Exec</b>: Fluxo de execução.",
        "tips": "• Configurável<br>• Use para eventos<br>• Compatível com fluxo"
    },
}

# Aliases para nós com múltiplos nomes
NODE_ALIASES = {
    "read_key_axis": "input_axis",
    "read_input": "input_axis",
    "event_collision_exit": "event_collision_exit",
    "event_collision_enter": "event_collision_enter",
    "event_trigger_enter": "event_collision_enter",
    "event_trigger_exit": "event_collision_exit",
    "event_custom": "event_custom",
    "cooldown": "cooldown",
    "inverter": "inverter",
    "wait": "wait",
    "repeat": "repeat",
    "attack": "attack",
    "parameter_condition": "parameter_condition",
}
