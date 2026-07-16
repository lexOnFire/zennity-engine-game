"""Representação didática do código equivalente a um nó visual."""
from __future__ import annotations

from typing import Any, Mapping


def _value(properties: Mapping[str, Any], name: str, default: Any) -> Any:
    return properties.get(name, default)


def node_code_preview(node: Mapping[str, Any]) -> str:
    """Gera pseudocódigo curto para caber no verso visual de um bloco."""
    node_type = str(node.get("type", ""))
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    previews = {
        "event_start": "ao_iniciar():\n    executar próximo",
        "event_update": "a_cada_frame(dt):\n    executar próximo",
        "event_timer": f"a_cada({_value(properties, 'seconds', 1.0)}s):\n    executar próximo",
        "input_axis": f"eixo = tecla({_value(properties, 'positive', 'D')})\n     - tecla({_value(properties, 'negative', 'A')})",
        "move": f"obj.x += entrada\n         * {_value(properties, 'speed', 200)} * dt",
        "move_by": f"obj.x += {_value(properties, 'x', 100)} * dt\nobj.y += {_value(properties, 'y', 0)} * dt",
        "get_position": "x = alvo.x\ny = alvo.y",
        "patrol_axis": (
            f"se pos >= {_value(properties, 'maximum', 100)}: direção = -1\n"
            f"se pos <= {_value(properties, 'minimum', -100)}: direção = 1\n"
            f"pos += direção * {_value(properties, 'speed', 100)} * dt"
        ),
        "jump": f"se no_chão:\n    pular({_value(properties, 'force', 420)})",
        "if_else": f"se {_value(properties, 'condition', True)}:\n    saída verdadeiro\nsenão: saída falso",
        "key_pressed": f"pressionou = tecla_acionada('{_value(properties, 'key', 'SPACE')}')",
        "compare_number": f"resultado = entrada {_value(properties, 'operator', '>')} {_value(properties, 'value', 0)}",
        "set_position": f"alvo.x = {_value(properties, 'x', 0)}\nalvo.y = {_value(properties, 'y', 0)}",
        "rotate": f"alvo.rotação += {_value(properties, 'degrees', 90)}",
        "set_active": f"alvo.ativo = {_value(properties, 'active', True)}",
        "destroy_object": "alvo.destruir()",
        "play_animation": f"animator.tocar('{_value(properties, 'state', 'Idle')}')",
        "play_animation_asset": f"tocar_animação(\n  '{_value(properties, 'path', 'selecione .zanim')}'\n)",
        "stop_animation": "parar_animação()",
        "play_sound": f"tocar_som(\n  '{_value(properties, 'path', 'selecione áudio')}'\n)",
        "set_sprite": f"alvo.imagem =\n  '{_value(properties, 'path', 'selecione imagem')}'",
        "set_hud": f"hud.texto = '{_value(properties, 'text', 'Texto')}'",
        "log_message": f"console('{_value(properties, 'text', 'Mensagem')}')",
        "find_tag": f"objeto = procurar_tag('{_value(properties, 'tag', 'Player')}')",
        "create_object": (
            f"novo = criar_objeto('{_value(properties, 'name', 'NovoObjeto')}',\n"
            f"  x={_value(properties, 'x', 0)}, y={_value(properties, 'y', 0)})"
        ),
        "get_variable": f"valor = ler('{_value(properties, 'name', 'value')}')",
        "set_variable": f"definir('{_value(properties, 'name', 'value')}', entrada)",
        "number_value": f"valor = {_value(properties, 'value', 0)}",
        "bool_value": f"valor = {_value(properties, 'value', True)}",
        "text_value": f"valor = '{_value(properties, 'value', 'Texto')}'",
        "add_number": "valor = a + b",
        "subtract_number": "valor = a - b",
        "multiply_number": "valor = a * b",
        "divide_number": "valor = a / b",
        "join_text": "texto = texto_a + texto_b",
        "to_text": "texto = str(valor)",
        "emit_event": f"emitir_evento('{_value(properties, 'name', 'evento')}')",
    }
    if node_type in previews:
        return previews[node_type]
    title = str(node.get("title", node_type or "bloco")).replace(" ", "_").lower()
    arguments = ", ".join(f"{key}={value!r}" for key, value in list(properties.items())[:2])
    return f"{title}({arguments})" if arguments else f"{title}()"
