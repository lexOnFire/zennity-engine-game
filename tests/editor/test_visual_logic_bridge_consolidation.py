from editor.runtime.visual_scripting_bridge import VisualLogicBridge, VisualScriptingBridge


class _Context:
    selection = None


def test_visual_logic_bridge_is_the_single_owner_of_mode_bridges():
    bridge = VisualLogicBridge(_Context())
    behavior = bridge.mode_bridge("behavior_tree")
    assert behavior is bridge.mode_bridge("behavior_tree")
    assert bridge.mode_bridge("dialogue") is not behavior
    assert VisualScriptingBridge is VisualLogicBridge
