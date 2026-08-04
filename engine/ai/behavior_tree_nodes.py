"""Nós de Behavior Tree da Zennity Engine — Sistema de Árvore de Comportamento.

Organização dos nós:
  - COMPOSITE: Selector, Sequence (controlam fluxo ramificado/sequencial)
  - DECORATOR: Repeat, Cooldown, Limiter, Inverter (modificam comportamento do filho)
  - CONDITION: TargetInRange, ParameterCheck, HealthCheck, etc (tomam decisões)
  - ACTION: Movement, Combat, Animation, etc (executam ações reais)

Uso: conecte a entrada "In" do primeiro nó. Saídas indicam o próximo passo na execução.
"""
from __future__ import annotations
from engine.core.metadata import NodeDefinition, PinDefinition, PinType


# ══════════════════════════════════════════════════════════════════════════════
# COMPOSITE NODES — Controlam o fluxo de execução
# ══════════════════════════════════════════════════════════════════════════════

class BTSequenceNode:
    """Executa os filhos EM ORDEM. Se um falhar, falha toda a sequência.

    Use para: "fazer A, depois B, depois C (tudo deve dar certo)".
    """

    __node_definition__ = NodeDefinition(
        id="bt.sequence",
        title_key="Sequência (Sequence)",
        category_key="Behavior Tree/Composite",
        description_key="Executa os filhos em ordem. Falha se qualquer filho falhar.",
        inputs=[PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC)],
        outputs=[
            PinDefinition(id="out_1", label_key="Passo 1", pin_type=PinType.EXEC),
            PinDefinition(id="out_2", label_key="Passo 2", pin_type=PinType.EXEC),
            PinDefinition(id="out_3", label_key="Passo 3", pin_type=PinType.EXEC),
        ],
        tags=["ordem", "sequência", "passos"],
    )


class BTSelectorNode:
    """Tenta os filhos na ordem até um ter SUCESSO. Falha se todos falharem.

    Use para: "tentar A, se falhar tenta B, se falhar tenta C (um deve dar certo)".
    """

    __node_definition__ = NodeDefinition(
        id="bt.selector",
        title_key="Seletor (Selector)",
        category_key="Behavior Tree/Composite",
        description_key="Tenta os filhos até um ter sucesso. Falha se todos falharem.",
        inputs=[PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC)],
        outputs=[
            PinDefinition(id="out_1", label_key="Opção 1", pin_type=PinType.EXEC),
            PinDefinition(id="out_2", label_key="Opção 2", pin_type=PinType.EXEC),
            PinDefinition(id="out_3", label_key="Opção 3", pin_type=PinType.EXEC),
        ],
        tags=["fallback", "alternativa", "escolha"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# DECORATOR NODES — Modificam como o filho é executado
# ══════════════════════════════════════════════════════════════════════════════

class BTRepeatNode:
    """Repete o filho N vezes. Use 0 para repetir infinitamente.

    Use para: patrulha, loops contínuos, ataques repetidos.
    """

    __node_definition__ = NodeDefinition(
        id="bt.repeat",
        title_key="Repetir (Repeat)",
        category_key="Behavior Tree/Decorator",
        description_key="Repete o nó filho N vezes. Use 0 para infinitamente.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="count", label_key="Vezes (0=∞)", pin_type=PinType.INT, default_value=0)
        ],
        outputs=[PinDefinition(id="child", label_key="Filho", pin_type=PinType.EXEC)],
        tags=["loop", "repetição", "patrulha"],
    )


class BTCooldownNode:
    """Aguarda tempo antes de deixar o filho executar novamente.

    Use para: limitar frequência de ataques, ações específicas do jogo.
    """

    __node_definition__ = NodeDefinition(
        id="bt.cooldown",
        title_key="Cooldown (Aguardar)",
        category_key="Behavior Tree/Decorator",
        description_key="Executa filho apenas após N segundos terem passado.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="seconds", label_key="Intervalo (s)", pin_type=PinType.FLOAT, default_value=1.0)
        ],
        outputs=[PinDefinition(id="child", label_key="Filho", pin_type=PinType.EXEC)],
        tags=["intervalo", "recarga", "ataque"],
    )


class BTLimiterNode:
    """Executa o filho no máximo N vezes e depois falha permanentemente.

    Use para: limitar tentativas, evitar loops infinitos de erro.
    """

    __node_definition__ = NodeDefinition(
        id="bt.limiter",
        title_key="Limitador (Limiter)",
        category_key="Behavior Tree/Decorator",
        description_key="Executa filho até N vezes. Depois falha sempre.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="max_count", label_key="Máx Execuções", pin_type=PinType.INT, default_value=3)
        ],
        outputs=[PinDefinition(id="child", label_key="Filho", pin_type=PinType.EXEC)],
        tags=["limite", "tentativas"],
    )


class BTInverterNode:
    """Inverte o resultado: sucesso vira falha, falha vira sucesso.

    Use para: "fazer algo ENQUANTO não tiver sucesso".
    """

    __node_definition__ = NodeDefinition(
        id="bt.inverter",
        title_key="Inversor (Inverter)",
        category_key="Behavior Tree/Decorator",
        description_key="Inverte resultado: sucesso→falha, falha→sucesso.",
        inputs=[PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC)],
        outputs=[PinDefinition(id="child", label_key="Filho", pin_type=PinType.EXEC)],
        tags=["não", "inverter"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# CONDITION NODES — Verificam condições e decidem se continua
# ══════════════════════════════════════════════════════════════════════════════

class BTTargetInRangeNode:
    """Checa se um alvo (por tag) está dentro de uma distância.

    Sucesso: alvo encontrado e dentro do alcance.
    Falha: alvo não encontrado ou fora do alcance.
    """

    __node_definition__ = NodeDefinition(
        id="bt.target_in_range",
        title_key="Alvo no Alcance?",
        category_key="Behavior Tree/Condition",
        description_key="Sucesso se alvo existe e está dentro da distância.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Tag do Alvo", pin_type=PinType.STRING, default_value="Player"),
            PinDefinition(id="distance", label_key="Alcance", pin_type=PinType.FLOAT, default_value=200.0)
        ],
        outputs=[PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC)],
        tags=["distância", "visão", "detecção"],
    )


class BTHealthCheckNode:
    """Checa a saúde (health) do próprio objeto.

    Sucesso: health > valor.
    Falha: health ≤ valor.
    """

    __node_definition__ = NodeDefinition(
        id="bt.health_check",
        title_key="Saúde Acima de?",
        category_key="Behavior Tree/Condition",
        description_key="Sucesso se health do objeto > valor.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="min_health", label_key="Valor Mínimo", pin_type=PinType.FLOAT, default_value=30.0)
        ],
        outputs=[PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC)],
        tags=["saúde", "vida", "status"],
    )


class BTParameterCheckNode:
    """Compara um parâmetro com um valor usando operadores.

    Operadores: ==, !=, <, ≤, >, ≥
    """

    __node_definition__ = NodeDefinition(
        id="bt.parameter_check",
        title_key="Parâmetro == Valor?",
        category_key="Behavior Tree/Condition",
        description_key="Sucesso se parâmetro operador valor.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parameter", label_key="Parâmetro", pin_type=PinType.STRING, default_value="alert"),
            PinDefinition(id="operator", label_key="Operador", pin_type=PinType.STRING, default_value="=="),
            PinDefinition(id="value", label_key="Valor", pin_type=PinType.STRING, default_value="true")
        ],
        outputs=[PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC)],
        tags=["variável", "condição", "comparação"],
    )


class BTRandomChanceNode:
    """Sucesso aleatório com probabilidade X%.

    Use para: comportamento imprevisível, decisões com chance.
    """

    __node_definition__ = NodeDefinition(
        id="bt.random_chance",
        title_key="Chance Aleatória?",
        category_key="Behavior Tree/Condition",
        description_key="Sucesso com probabilidade X% (0-100).",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="chance", label_key="Chance (%)", pin_type=PinType.FLOAT, default_value=50.0)
        ],
        outputs=[PinDefinition(id="success", label_key="Sucesso", pin_type=PinType.EXEC)],
        tags=["aleatório", "sorte", "probabilidade"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# ACTION NODES — Fazem coisas reais no jogo
# ══════════════════════════════════════════════════════════════════════════════

class BTIdleNode:
    """Fica parado por N segundos. Útil para pausas naturais.

    Use para: transições suaves, esperar antes da próxima ação.
    """

    __node_definition__ = NodeDefinition(
        id="bt.idle",
        title_key="Esperar/Descansar",
        category_key="Behavior Tree/Action",
        description_key="Fica parado e espera N segundos.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="duration", label_key="Duração (s)", pin_type=PinType.FLOAT, default_value=1.0)
        ],
        outputs=[PinDefinition(id="out", label_key="Pronto", pin_type=PinType.EXEC)],
        tags=["pausa", "espera", "repouso"],
    )


class BTPatrolNode:
    """Alterna continuamente entre dois pontos.

    Use para: patrulhagem, rota simples.
    """

    __node_definition__ = NodeDefinition(
        id="bt.patrol",
        title_key="Patrulhar (A→B→A)",
        category_key="Behavior Tree/Action",
        description_key="Move continuamente entre os pontos A e B.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="point_a", label_key="Ponto A", pin_type=PinType.VECTOR2, default_value="0,0"),
            PinDefinition(id="point_b", label_key="Ponto B", pin_type=PinType.VECTOR2, default_value="200,0"),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=80.0)
        ],
        outputs=[PinDefinition(id="out", label_key="Em Patrulha", pin_type=PinType.EXEC)],
        tags=["patrulha", "movimento", "rota"],
    )


class BTChaseNode:
    """Persegue um alvo até ele sair do alcance.

    Use para: inimigo seguindo o jogador.
    """

    __node_definition__ = NodeDefinition(
        id="bt.chase",
        title_key="Perseguir Alvo",
        category_key="Behavior Tree/Action",
        description_key="Move em direção ao alvo até distância de parada.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Tag do Alvo", pin_type=PinType.STRING, default_value="Player"),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=120.0),
            PinDefinition(id="stop_distance", label_key="Distância de Parada", pin_type=PinType.FLOAT, default_value=48.0)
        ],
        outputs=[PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC)],
        tags=["perseguição", "movimento", "combate"],
    )


class BTMoveToNode:
    """Move para uma posição específica.

    Use para: mover a um ponto fixo ou recalculado.
    """

    __node_definition__ = NodeDefinition(
        id="bt.move_to",
        title_key="Mover Para Posição",
        category_key="Behavior Tree/Action",
        description_key="Move para uma posição específica.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target_pos", label_key="Posição Alvo", pin_type=PinType.VECTOR2, default_value="0,0"),
            PinDefinition(id="speed", label_key="Velocidade", pin_type=PinType.FLOAT, default_value=100.0)
        ],
        outputs=[PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC)],
        tags=["movimento", "posição", "caminho"],
    )


class BTAttackNode:
    """Ataca um alvo dentro do alcance.

    Use para: combate corpo-a-corpo ou à distância.
    """

    __node_definition__ = NodeDefinition(
        id="bt.attack",
        title_key="Atacar Alvo",
        category_key="Behavior Tree/Action",
        description_key="Aplica dano ao alvo se estiver no alcance.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="target", label_key="Tag do Alvo", pin_type=PinType.STRING, default_value="Player"),
            PinDefinition(id="damage", label_key="Dano", pin_type=PinType.FLOAT, default_value=10.0),
            PinDefinition(id="range", label_key="Alcance", pin_type=PinType.FLOAT, default_value=64.0)
        ],
        outputs=[PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC)],
        tags=["ataque", "combate", "dano"],
    )


class BTPlayAnimationNode:
    """Toca uma animação.

    Use para: atacar, pular, emotes.
    """

    __node_definition__ = NodeDefinition(
        id="bt.play_animation",
        title_key="Tocar Animação",
        category_key="Behavior Tree/Action",
        description_key="Ativa um estado de animação.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="animation", label_key="Nome da Animação", pin_type=PinType.STRING, default_value="Idle")
        ],
        outputs=[PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC)],
        tags=["animação", "movimento", "visual"],
    )


class BTSetParameterNode:
    """Define um parâmetro para um valor.

    Use para: comunicar com a lógica do jogo, mudar estado.
    """

    __node_definition__ = NodeDefinition(
        id="bt.set_parameter",
        title_key="Definir Parâmetro",
        category_key="Behavior Tree/Action",
        description_key="Define um parâmetro para um novo valor.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="parameter", label_key="Parâmetro", pin_type=PinType.STRING, default_value="alert"),
            PinDefinition(id="value", label_key="Novo Valor", pin_type=PinType.STRING, default_value="true")
        ],
        outputs=[PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC)],
        tags=["parâmetro", "estado", "comunicação"],
    )


class BTLogNode:
    """Imprime mensagem no console (para debug).

    Use para: debug durante desenvolvimento.
    """

    __node_definition__ = NodeDefinition(
        id="bt.log",
        title_key="Log (Debug)",
        category_key="Behavior Tree/Action",
        description_key="Imprime mensagem no console.",
        inputs=[
            PinDefinition(id="in", label_key="In", pin_type=PinType.EXEC),
            PinDefinition(id="message", label_key="Mensagem", pin_type=PinType.STRING, default_value="Debug")
        ],
        outputs=[PinDefinition(id="out", label_key="Próximo", pin_type=PinType.EXEC)],
        tags=["debug", "log", "teste"],
    )
