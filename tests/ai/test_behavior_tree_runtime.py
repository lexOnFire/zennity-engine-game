"""Testes para o novo Behavior Tree Runtime."""

import pytest
from engine.ai.behavior_tree_runtime import BehaviorTreeRuntime, BehaviorStatus


def test_sequence_all_success():
    """Sequence com todos filhos bem-sucedidos."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.sequence",
                "children": ["action1", "action2"]
            },
            "action1": {
                "type": "bt.idle",
                "duration": 0.1
            },
            "action2": {
                "type": "bt.log",
                "message": "done"
            }
        }
    }
    runtime = BehaviorTreeRuntime(tree)
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS


def test_selector_first_success():
    """Selector para no primeiro sucesso."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.selector",
                "children": ["success_node", "should_not_run"]
            },
            "success_node": {
                "type": "bt.log",
                "message": "first"
            },
            "should_not_run": {
                "type": "bt.log",
                "message": "second"
            }
        }
    }
    runtime = BehaviorTreeRuntime(tree)
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS


def test_inverter_flips_success():
    """Inverter transforma sucesso em falha."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.inverter",
                "child": "log_node"
            },
            "log_node": {
                "type": "bt.log",
                "message": "test"
            }
        }
    }
    runtime = BehaviorTreeRuntime(tree)
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.FAILURE


def test_parameter_check_equality():
    """Parameter check com ==."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.parameter_check",
                "parameter": "state",
                "operator": "==",
                "value": "ready"
            }
        }
    }
    runtime = BehaviorTreeRuntime(tree, parameters={"state": "ready"})
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS


def test_parameter_check_comparison():
    """Parameter check com >."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.parameter_check",
                "parameter": "health",
                "operator": ">",
                "value": "50"
            }
        }
    }
    runtime = BehaviorTreeRuntime(tree, parameters={"health": "75"})
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS


def test_health_check_success():
    """Health check quando saúde está OK."""
    class MockObject:
        health = 80.0

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.health_check",
                "min_health": 30.0
            }
        }
    }
    obj = MockObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS


def test_health_check_failure():
    """Health check falha quando saúde baixa."""
    class MockObject:
        health = 20.0

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.health_check",
                "min_health": 30.0
            }
        }
    }
    obj = MockObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.FAILURE


def test_repeat_counter():
    """Repeat executa N vezes."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.repeat",
                "child": "action",
                "count": 3
            },
            "action": {
                "type": "bt.log",
                "message": "repeat"
            }
        }
    }
    runtime = BehaviorTreeRuntime(tree)

    # Primeira execução
    status1 = runtime.update(dt=0.016)
    assert status1 == BehaviorStatus.RUNNING

    # Segunda execução
    status2 = runtime.update(dt=0.016)
    assert status2 == BehaviorStatus.RUNNING

    # Terceira execução
    status3 = runtime.update(dt=0.016)
    assert status3 == BehaviorStatus.SUCCESS


def test_cooldown_blocks_execution():
    """Cooldown impede execução imediata."""
    call_count = [0]

    class CustomRuntime(BehaviorTreeRuntime):
        def _tick_log(self, node_id, message, dt):
            call_count[0] += 1
            return BehaviorStatus.SUCCESS

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.cooldown",
                "child": "action",
                "seconds": 1.0
            },
            "action": {
                "type": "bt.log",
                "message": "action"
            }
        }
    }

    runtime = CustomRuntime(tree)

    # Primeira execução passa
    status1 = runtime.update(dt=0.016)
    assert status1 == BehaviorStatus.RUNNING
    assert call_count[0] == 1

    # Segunda execução bloqueada
    status2 = runtime.update(dt=0.016)
    assert status2 == BehaviorStatus.RUNNING
    assert call_count[0] == 1  # Não aumentou


def test_limiter_stops_after_max():
    """Limiter falha após N execuções."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.limiter",
                "child": "action",
                "max_count": 2
            },
            "action": {
                "type": "bt.log",
                "message": "limited"
            }
        }
    }

    runtime = BehaviorTreeRuntime(tree)

    # Primeira (OK)
    status1 = runtime.update(dt=0.016)
    assert status1 == BehaviorStatus.SUCCESS

    # Segunda (OK)
    status2 = runtime.update(dt=0.016)
    assert status2 == BehaviorStatus.SUCCESS

    # Terceira (Falha - passou limite)
    status3 = runtime.update(dt=0.016)
    assert status3 == BehaviorStatus.FAILURE


def test_random_chance():
    """Random chance tem chance certa."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.random_chance",
                "chance": 100.0
            }
        }
    }

    runtime = BehaviorTreeRuntime(tree)
    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS


def test_events_emitted():
    """Eventos são emitidos corretamente."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.log",
                "message": "test"
            }
        }
    }

    runtime = BehaviorTreeRuntime(tree)
    status = runtime.update(dt=0.016)

    assert len(runtime.events) > 0
    assert any(e["type"] == "action_done" for e in runtime.events)


def test_set_parameter_action():
    """Set Parameter modifica parâmetros."""
    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.set_parameter",
                "parameter": "alert",
                "value": "true"
            }
        }
    }

    runtime = BehaviorTreeRuntime(tree)
    assert runtime.get_parameter("alert") != "true"

    status = runtime.update(dt=0.016)
    assert status == BehaviorStatus.SUCCESS
    assert runtime.get_parameter("alert") == "true"


def test_set_ui_text_action():
    """Set UI Text atualiza texto de widget."""
    class MockUIWidget:
        def __init__(self):
            self.text = "original"
            self.widget_name = "label"

    class MockGameObject:
        def __init__(self):
            self.children = [MockUIWidget()]

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.set_ui_text",
                "widget": "label",
                "text": "updated"
            }
        }
    }

    obj = MockGameObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)

    assert status == BehaviorStatus.SUCCESS
    assert obj.children[0].text == "updated"
    assert any(e["type"] == "ui_action_done" for e in runtime.events)


def test_set_ui_progress_action():
    """Set UI Progress atualiza valor de barra."""
    class MockProgressBar:
        def __init__(self):
            self.value = 50.0
            self.widget_name = "hp_bar"

    class MockGameObject:
        def __init__(self):
            self.children = [MockProgressBar()]

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.set_ui_progress",
                "widget": "hp_bar",
                "value": 75.0
            }
        }
    }

    obj = MockGameObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)

    assert status == BehaviorStatus.SUCCESS
    assert obj.children[0].value == 75.0


def test_increment_ui_value():
    """Increment UI Value soma ao valor numérico."""
    class MockUILabel:
        def __init__(self):
            self.text = "10"
            self.widget_name = "coins"

    class MockGameObject:
        def __init__(self):
            self.children = [MockUILabel()]

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.increment_ui_value",
                "widget": "coins",
                "amount": 5.0
            }
        }
    }

    obj = MockGameObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)

    assert status == BehaviorStatus.SUCCESS
    assert obj.children[0].text == "15"


def test_decrement_ui_value():
    """Decrement UI Value subtrai do valor numérico."""
    class MockUILabel:
        def __init__(self):
            self.text = "100"
            self.widget_name = "stamina"

    class MockGameObject:
        def __init__(self):
            self.children = [MockUILabel()]

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.decrement_ui_value",
                "widget": "stamina",
                "amount": 25.0
            }
        }
    }

    obj = MockGameObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)

    assert status == BehaviorStatus.SUCCESS
    assert obj.children[0].text == "75"


def test_set_ui_visible():
    """Set UI Visible controla visibilidade."""
    class MockUIWidget:
        def __init__(self):
            self.visible = True
            self.widget_name = "menu"

    class MockGameObject:
        def __init__(self):
            self.children = [MockUIWidget()]

    tree = {
        "format": "zennity.behavior_tree",
        "version": 1,
        "start_node": "root",
        "nodes": {
            "root": {
                "type": "bt.set_ui_visible",
                "widget": "menu",
                "visible": False
            }
        }
    }

    obj = MockGameObject()
    runtime = BehaviorTreeRuntime(tree, game_object=obj)
    status = runtime.update(dt=0.016)

    assert status == BehaviorStatus.SUCCESS
    assert obj.children[0].visible is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
