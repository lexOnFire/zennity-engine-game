"""Receitas didáticas e reutilizáveis para o editor de Lógica Visual."""
from __future__ import annotations

import unicodedata
import uuid
from copy import deepcopy
from typing import Any, Mapping

from .graph_asset import create_logic_node


LOGIC_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "move_x_every_frame",
        "topics": ("Movimento", "Posição"),
        "title": "Mover sozinho no eixo X",
        "category": "Posição e movimento",
        "summary": "Move o objeto continuamente para a direita, sem precisar apertar teclas.",
        "keywords": "mover andar sozinho automático x direita cada frame velocidade",
        "steps": (
            "A cada frame inicia o fluxo continuamente.",
            "Mover continuamente acrescenta 120 unidades por segundo no eixo X.",
            "Use um valor negativo em X para mover para a esquerda.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "move", "type": "move_by", "position": (270.0, 0.0), "properties": {"x": 120.0, "y": 0.0}},
        ),
        "edges": (("update", "next", "move", "in", "flow"),),
    },
    {
        "id": "move_y_every_frame",
        "topics": ("Movimento", "Posição"),
        "title": "Mover sozinho no eixo Y",
        "category": "Posição e movimento",
        "summary": "Move o objeto continuamente para baixo sem usar o teclado.",
        "keywords": "mover andar sozinho automático y baixo cima cada frame velocidade",
        "steps": (
            "A cada frame executa o movimento.",
            "Mover continuamente acrescenta 120 unidades por segundo no eixo Y.",
            "Use um valor negativo em Y para mover para cima.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "move", "type": "move_by", "position": (270.0, 0.0), "properties": {"x": 0.0, "y": 120.0}},
        ),
        "edges": (("update", "next", "move", "in", "flow"),),
    },
    {
        "id": "set_initial_position",
        "topics": ("Posição",),
        "title": "Definir posição ao iniciar",
        "category": "Posição e movimento",
        "summary": "Coloca o objeto em uma coordenada específica quando o Play começa.",
        "keywords": "posição inicial começar spawn teleporte x y ao iniciar",
        "steps": (
            "Ao iniciar executa somente uma vez.",
            "Definir posição troca imediatamente as coordenadas X e Y.",
            "Edite X e Y nas propriedades do bloco.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "position", "type": "set_position", "position": (270.0, 0.0), "properties": {"x": 100.0, "y": 100.0}},
        ),
        "edges": (("start", "next", "position", "in", "flow"),),
    },
    {
        "id": "create_object_on_start",
        "topics": ("Objetos", "Criação"),
        "title": "Criar um objeto ao iniciar",
        "category": "Objetos e cena",
        "summary": "Cria um novo objeto quando o Play começa e permite reutilizá-lo em outros blocos.",
        "keywords": "criar objeto spawn instanciar novo imagem posição tamanho cor",
        "steps": (
            "Ao iniciar executa apenas uma vez.",
            "Criar objeto define nome, posição, tamanho, cor, imagem e tag.",
            "A saída Objeto pode ser ligada a Mover, Girar, Trocar imagem ou Destruir.",
            "Marque Posição relativa para usar X e Y como deslocamento do objeto atual.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "create", "type": "create_object", "position": (270.0, 0.0)},
        ),
        "edges": (("start", "next", "create", "in", "flow"),),
    },
    {
        "id": "patrol_y_between_limits",
        "topics": ("Movimento", "Posição"),
        "title": "Patrulhar no Y entre -100 e 100",
        "category": "Posição e movimento",
        "summary": "Move continuamente no eixo Y e inverte o sentido ao alcançar 100 ou -100.",
        "keywords": "patrulha ping pong inverter direção limite y menos 100 mais 100 automático",
        "steps": (
            "A cada frame executa a patrulha.",
            "O objeto começa subindo no eixo Y até o limite máximo 100.",
            "Ao chegar em 100 inverte; em -100 volta a inverter.",
            "Velocidade controla quantas unidades são percorridas por segundo.",
            "A patrulha no Y assume o controle do eixo e não é desviada pela gravidade.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "patrol", "type": "patrol_axis", "position": (270.0, 0.0), "properties": {"axis": "Y", "minimum": -100.0, "maximum": 100.0, "speed": 100.0}},
        ),
        "edges": (("update", "next", "patrol", "in", "flow"),),
    },
    {
        "id": "patrol_x_between_limits",
        "topics": ("Movimento", "Posição"),
        "title": "Patrulhar no X entre dois pontos",
        "category": "Posição e movimento",
        "summary": "Cria uma plataforma ou inimigo que percorre o eixo X em ida e volta.",
        "keywords": "patrulha plataforma inimigo ping pong inverter direção limite x",
        "steps": (
            "A cada frame executa a patrulha.",
            "O eixo X é limitado entre -200 e 200.",
            "Edite mínimo, máximo e velocidade no bloco.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "patrol", "type": "patrol_axis", "position": (270.0, 0.0), "properties": {"axis": "X", "minimum": -200.0, "maximum": 200.0, "speed": 120.0}},
        ),
        "edges": (("update", "next", "patrol", "in", "flow"),),
    },
    {
        "id": "show_x_on_hud",
        "topics": ("Posição", "Texto"),
        "title": "Mostrar posição X no HUD",
        "category": "Posição e movimento",
        "summary": "Lê a posição atual do objeto e mostra o valor X na interface durante o Play.",
        "keywords": "ler posição coordenada x hud texto debug mostrar",
        "steps": (
            "A cada frame atualiza o texto.",
            "Ler posição fornece as coordenadas atuais do objeto.",
            "Converter para texto transforma X em texto e Atualizar HUD o exibe.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "position", "type": "get_position", "position": (0.0, 180.0)},
            {"key": "text", "type": "to_text", "position": (270.0, 180.0)},
            {"key": "hud", "type": "set_hud", "position": (540.0, 0.0)},
        ),
        "edges": (
            ("update", "next", "hud", "in", "flow"),
            ("position", "x", "text", "value", "number"),
            ("text", "value", "hud", "text", "text"),
        ),
    },
    {
        "id": "sprite_on_start",
        "topics": ("Ação", "Objetos"),
        "title": "Trocar imagem ao iniciar",
        "category": "Imagem e sprite",
        "summary": "Vincula uma imagem de Assets e a aplica ao objeto quando o Play começa.",
        "keywords": "imagem sprite textura png jpg trocar vincular ao iniciar",
        "steps": (
            "Ao iniciar executa uma vez.",
            "Selecione Trocar imagem do objeto e use Selecionar asset do projeto.",
            "Escolha um PNG, JPG, BMP ou WEBP da pasta Assets.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "sprite", "type": "set_sprite", "position": (270.0, 0.0)},
        ),
        "edges": (("start", "next", "sprite", "in", "flow"),),
    },
    {
        "id": "animation_asset_on_start",
        "topics": ("Ação",),
        "title": "Tocar animação ao iniciar",
        "category": "Animação",
        "summary": "Vincula e toca diretamente um arquivo .zanim quando o Play começa.",
        "keywords": "animação animar zanim frames sprite sheet iniciar vincular",
        "steps": (
            "Ao iniciar dispara uma vez.",
            "Selecione Tocar arquivo de animação e vincule um .zanim de Assets.",
            "A engine carrega o clip no objeto automaticamente durante o Play.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "animation", "type": "play_animation_asset", "position": (270.0, 0.0)},
        ),
        "edges": (("start", "next", "animation", "in", "flow"),),
    },
    {
        "id": "sound_on_start",
        "topics": ("Ação",),
        "title": "Tocar som ao iniciar",
        "category": "Áudio",
        "summary": "Vincula um som de Assets e o reproduz uma vez quando o Play começa.",
        "keywords": "som áudio musica efeito wav ogg mp3 iniciar vincular",
        "steps": (
            "Ao iniciar dispara uma vez.",
            "Selecione Tocar som e use Selecionar asset do projeto.",
            "Escolha WAV, OGG, MP3 ou FLAC dentro de Assets.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "sound", "type": "play_sound", "position": (270.0, 0.0)},
        ),
        "edges": (("start", "next", "sound", "in", "flow"),),
    },
    {
        "id": "sound_on_collision",
        "topics": ("Eventos", "Ação"),
        "title": "Tocar som ao colidir",
        "category": "Colisão e áudio",
        "summary": "Reproduz um efeito sonoro sempre que o objeto começa uma colisão.",
        "keywords": "colisão bater impacto som efeito evento collider",
        "steps": (
            "Ao colidir é chamado pelo sistema de física.",
            "Tocar som reproduz o asset escolhido.",
            "O objeto precisa possuir um Collider configurado.",
        ),
        "nodes": (
            {"key": "collision", "type": "event_collision_enter", "position": (0.0, 0.0)},
            {"key": "sound", "type": "play_sound", "position": (270.0, 0.0)},
        ),
        "edges": (("collision", "next", "sound", "in", "flow"),),
    },
    {
        "id": "jump_with_space",
        "topics": ("Movimento", "Condição"),
        "title": "Pular com Espaço",
        "category": "Entrada e movimento",
        "summary": "Verifica a tecla Espaço a cada frame e pula somente quando ela é pressionada.",
        "keywords": "pular espaço space tecla condição input movimento",
        "steps": (
            "A cada frame verifica a entrada.",
            "Tecla pressionada libera o fluxo Verdadeiro somente no clique.",
            "Pular aplica a força configurada se o objeto estiver no chão.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "key", "type": "key_pressed", "position": (270.0, 0.0), "properties": {"key": "SPACE"}},
            {"key": "jump", "type": "jump", "position": (540.0, 0.0), "properties": {"force": 420.0}},
        ),
        "edges": (
            ("update", "next", "key", "in", "flow"),
            ("key", "true", "jump", "in", "flow"),
        ),
    },
    {
        "id": "timer_console_message",
        "topics": ("Eventos",),
        "title": "Executar ação a cada segundo",
        "category": "Tempo e eventos",
        "summary": "Usa um temporizador repetido para escrever uma mensagem no Console.",
        "keywords": "timer tempo segundo repetir evento console mensagem",
        "steps": (
            "Após um tempo conta um segundo e repete.",
            "Mostrar no Console confirma cada disparo.",
            "Troque o bloco final por qualquer ação desejada.",
        ),
        "nodes": (
            {"key": "timer", "type": "event_timer", "position": (0.0, 0.0), "properties": {"seconds": 1.0, "repeat": True}},
            {"key": "log", "type": "log_message", "position": (270.0, 0.0), "properties": {"text": "Um segundo passou"}},
        ),
        "edges": (("timer", "next", "log", "in", "flow"),),
    },
    {
        "id": "if_else_example",
        "topics": ("Lógica", "Condição"),
        "title": "Escolher entre duas ações",
        "category": "Lógica e condição",
        "summary": "Mostra como executar caminhos diferentes para Verdadeiro e Falso.",
        "keywords": "if else se senão verdadeiro falso decisão condição lógica",
        "steps": (
            "Ao iniciar entra no bloco If / Else.",
            "Verdadeiro e Falso possuem saídas independentes.",
            "Edite Condição nas propriedades para testar os dois caminhos.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "branch", "type": "if_else", "position": (270.0, 0.0), "properties": {"condition": True}},
            {"key": "yes", "type": "log_message", "position": (540.0, -80.0), "properties": {"text": "Condição verdadeira"}},
            {"key": "no", "type": "log_message", "position": (540.0, 100.0), "properties": {"text": "Condição falsa"}},
        ),
        "edges": (
            ("start", "next", "branch", "in", "flow"),
            ("branch", "true", "yes", "in", "flow"),
            ("branch", "false", "no", "in", "flow"),
        ),
    },
    {
        "id": "find_and_hide_tag",
        "topics": ("Objetos",),
        "title": "Encontrar objeto por Tag e ocultar",
        "category": "Objetos e cena",
        "summary": "Procura outro objeto pela Tag e o desativa durante o Play.",
        "keywords": "objeto procurar encontrar tag ocultar desativar cena",
        "steps": (
            "Procurar por Tag localiza o primeiro objeto compatível.",
            "A porta object envia a referência para Ativar / Desativar.",
            "Edite a Tag e o valor Ativo nas propriedades.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "find", "type": "find_tag", "position": (270.0, 0.0), "properties": {"tag": "Enemy"}},
            {"key": "active", "type": "set_active", "position": (540.0, 0.0), "properties": {"active": False}},
        ),
        "edges": (
            ("start", "next", "find", "in", "flow"),
            ("find", "next", "active", "in", "flow"),
            ("find", "object", "active", "target", "object"),
        ),
    },
    {
        "id": "store_starting_health",
        "topics": ("Variáveis",),
        "title": "Criar variável de vida",
        "category": "Variáveis",
        "summary": "Define a variável Vida do objeto com valor inicial 100.",
        "keywords": "variável vida health pontos valor guardar definir",
        "steps": (
            "Ao iniciar executa uma vez.",
            "Número fornece o valor 100.",
            "Definir variável guarda Vida no escopo deste objeto.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "number", "type": "number_value", "position": (0.0, 180.0), "properties": {"value": 100.0}},
            {"key": "set", "type": "set_variable", "position": (270.0, 0.0), "properties": {"scope": "object", "name": "Vida", "value": 100.0}},
        ),
        "edges": (
            ("start", "next", "set", "in", "flow"),
            ("number", "value", "set", "value", "number"),
        ),
    },
    {
        "id": "math_to_hud",
        "topics": ("Matemática",),
        "title": "Somar números e mostrar no HUD",
        "category": "Matemática e HUD",
        "summary": "Soma dois números, converte o resultado em texto e exibe na tela.",
        "keywords": "somar matemática números resultado converter hud",
        "steps": (
            "Somar recebe A e B nas propriedades ou por conexões.",
            "Converter para texto adapta o número para o HUD.",
            "Atualizar HUD mostra o resultado durante o Play.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "add", "type": "add_number", "position": (0.0, 180.0), "properties": {"a": 10.0, "b": 5.0}},
            {"key": "text", "type": "to_text", "position": (270.0, 180.0)},
            {"key": "hud", "type": "set_hud", "position": (540.0, 0.0)},
        ),
        "edges": (
            ("start", "next", "hud", "in", "flow"),
            ("add", "value", "text", "value", "number"),
            ("text", "value", "hud", "text", "text"),
        ),
    },
    {
        "id": "join_text_to_hud",
        "topics": ("Texto",),
        "title": "Juntar textos e mostrar no HUD",
        "category": "Texto e HUD",
        "summary": "Combina duas partes de texto e mostra a frase resultante na tela.",
        "keywords": "texto juntar frase nome hud interface",
        "steps": (
            "Juntar textos combina A e B.",
            "A saída value entra na propriedade text do HUD.",
            "Edite as duas partes para criar sua própria mensagem.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "join", "type": "join_text", "position": (0.0, 180.0), "properties": {"a": "Olá, ", "b": "jogador!"}},
            {"key": "hud", "type": "set_hud", "position": (320.0, 0.0)},
        ),
        "edges": (
            ("start", "next", "hud", "in", "flow"),
            ("join", "value", "hud", "text", "text"),
        ),
    },
)


def _search_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def find_logic_recipes(query: str = "", topic: str = "") -> list[dict[str, Any]]:
    """Pesquisa receitas por linguagem simples, título, categoria e passos."""
    wanted = _search_key(query).strip()
    result: list[dict[str, Any]] = []
    for recipe in LOGIC_RECIPES:
        if topic and topic not in recipe.get("topics", ()):
            continue
        searchable = _search_key(" ".join((
            str(recipe.get("title", "")), str(recipe.get("category", "")),
            str(recipe.get("summary", "")), str(recipe.get("keywords", "")),
            " ".join(str(step) for step in recipe.get("steps", ())),
        )))
        if not wanted or all(term in searchable for term in wanted.split()):
            result.append(deepcopy(recipe))
    return result


def build_logic_recipe(recipe_id: str, origin: tuple[float, float] = (0.0, 0.0)) -> dict[str, list[dict[str, Any]]]:
    """Materializa uma receita como fragmento independente de nós e conexões."""
    recipe = next((entry for entry in LOGIC_RECIPES if entry["id"] == recipe_id), None)
    if recipe is None:
        raise KeyError(f"Receita de Logic Graph desconhecida: {recipe_id}")
    nodes: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for specification in recipe["nodes"]:
        position = specification.get("position", (0.0, 0.0))
        node = create_logic_node(
            str(specification["type"]),
            (float(origin[0]) + float(position[0]), float(origin[1]) + float(position[1])),
        )
        node["properties"].update(deepcopy(specification.get("properties", {})))
        nodes.append(node)
        by_key[str(specification["key"])] = node
    edges = [{
        "id": uuid.uuid4().hex,
        "from_node": by_key[source]["id"], "from_port": from_port,
        "to_node": by_key[target]["id"], "to_port": to_port,
        "kind": kind,
    } for source, from_port, target, to_port, kind in recipe["edges"]]
    return {"nodes": nodes, "edges": edges}


def logic_recipe(recipe_id: str) -> Mapping[str, Any]:
    """Retorna os metadados de uma receita sem permitir mutação global."""
    recipe = next((entry for entry in LOGIC_RECIPES if entry["id"] == recipe_id), None)
    if recipe is None:
        raise KeyError(f"Receita de Logic Graph desconhecida: {recipe_id}")
    return deepcopy(recipe)
