"""
Phase 8A Step 5: Level1 Progression (Collectibles, Key, Guard, Door, Level2)

Validates:
- Coin collection and HUD updates
- Key collection and has_key flag
- Guard interaction and dialogue
- Dialogue conditional branching
- Door unlock via event
- Level exit and autosave
- Level2 loading
- Persistence across scenes
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCoinPrefab:
    """Test Coin collectible."""

    def test_coin_prefab_exists(self):
        """Verify Coin.zprfb exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Coin.zprfb"
        assert prefab_path.exists()

    def test_coin_has_trigger_collider(self):
        """Verify Coin has trigger collider."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Coin.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        collider = next((c for c in data.get("root", {}).get("components", [])
                        if c.get("type") == "BoxCollider2D"), None)
        assert collider is not None
        assert collider.get("is_trigger") is True

    def test_coin_has_collection_logic(self):
        """Verify Coin has CoinCollectionLogic."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Coin.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        graphs = data.get("root", {}).get("logic_graphs", [])
        has_collection = any(g.get("path") == "Assets/Logic/CoinCollectionLogic.zlogic"
                            for g in graphs)
        assert has_collection


class TestCoinCollectionLogic:
    """Test coin collection logic."""

    def test_logic_exists(self):
        """Verify CoinCollectionLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "CoinCollectionLogic.zlogic"
        assert logic_path.exists()

    def test_logic_has_trigger_listener(self):
        """Verify logic has trigger enter listener."""
        logic_path = project_root / "Assets" / "Logic" / "CoinCollectionLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "on_trigger_enter" in node_ids

    def test_logic_has_coins_variable_update(self):
        """Verify logic updates project coins variable."""
        logic_path = project_root / "Assets" / "Logic" / "CoinCollectionLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "get_coins" in node_ids
        assert "set_coins" in node_ids

    def test_logic_has_destroy(self):
        """Verify logic destroys coin after collection."""
        logic_path = project_root / "Assets" / "Logic" / "CoinCollectionLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "destroy_coin" in node_ids


class TestKeyPrefab:
    """Test Key collectible."""

    def test_key_prefab_exists(self):
        """Verify Key.zprfb exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Key.zprfb"
        assert prefab_path.exists()

    def test_key_has_trigger_collider(self):
        """Verify Key has trigger collider."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Key.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        collider = next((c for c in data.get("root", {}).get("components", [])
                        if c.get("type") == "BoxCollider2D"), None)
        assert collider is not None
        assert collider.get("is_trigger") is True

    def test_key_has_collection_logic(self):
        """Verify Key has KeyCollectionLogic."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Key.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        graphs = data.get("root", {}).get("logic_graphs", [])
        has_logic = any(g.get("path") == "Assets/Logic/KeyCollectionLogic.zlogic"
                       for g in graphs)
        assert has_logic


class TestKeyCollectionLogic:
    """Test key collection logic."""

    def test_logic_exists(self):
        """Verify KeyCollectionLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "KeyCollectionLogic.zlogic"
        assert logic_path.exists()

    def test_logic_sets_has_key(self):
        """Verify logic sets has_key to true."""
        logic_path = project_root / "Assets" / "Logic" / "KeyCollectionLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_has_key" in node_ids


class TestGuardPrefab:
    """Test Guard NPC."""

    def test_guard_prefab_exists(self):
        """Verify Guard.zprfb exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Guard.zprfb"
        assert prefab_path.exists()

    def test_guard_has_interaction_logic(self):
        """Verify Guard has GuardInteractionLogic."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Guard.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        graphs = data.get("root", {}).get("logic_graphs", [])
        has_logic = any(g.get("path") == "Assets/Logic/GuardInteractionLogic.zlogic"
                       for g in graphs)
        assert has_logic

    def test_guard_has_dialogue_owner_id(self):
        """Verify Guard has dialogue_owner_id variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Guard.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "dialogue_owner_id" in variables
        assert variables["dialogue_owner_id"] == "Guard"


class TestGuardInteractionLogic:
    """Test guard interaction logic."""

    def test_logic_exists(self):
        """Verify GuardInteractionLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "GuardInteractionLogic.zlogic"
        assert logic_path.exists()

    def test_logic_has_trigger_detection(self):
        """Verify logic detects Player in range."""
        logic_path = project_root / "Assets" / "Logic" / "GuardInteractionLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "interaction_trigger_enter" in node_ids

    def test_logic_has_dialogue_start(self):
        """Verify logic starts dialogue on E key."""
        logic_path = project_root / "Assets" / "Logic" / "GuardInteractionLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "e_key_down" in node_ids
        assert "start_dialogue" in node_ids


class TestGuardDialogue:
    """Test Guard dialogue asset."""

    def test_dialogue_exists(self):
        """Verify GuardDialogue.zdialogue exists."""
        dialogue_path = project_root / "Assets" / "Dialogues" / "GuardDialogue.zdialogue"
        assert dialogue_path.exists()

    def test_dialogue_valid_json(self):
        """Verify dialogue is valid JSON."""
        dialogue_path = project_root / "Assets" / "Dialogues" / "GuardDialogue.zdialogue"
        data = json.loads(dialogue_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.dialogue"

    def test_dialogue_has_condition(self):
        """Verify dialogue has has_key condition."""
        dialogue_path = project_root / "Assets" / "Dialogues" / "GuardDialogue.zdialogue"
        data = json.loads(dialogue_path.read_text(encoding="utf-8"))

        condition_node = next((n for n in data.get("nodes", [])
                             if n.get("type") == "condition"), None)
        assert condition_node is not None
        assert "has_key" in condition_node.get("variable", "")

    def test_dialogue_has_event(self):
        """Verify dialogue has open_gate event."""
        dialogue_path = project_root / "Assets" / "Dialogues" / "GuardDialogue.zdialogue"
        data = json.loads(dialogue_path.read_text(encoding="utf-8"))

        event_nodes = [n for n in data.get("nodes", [])
                      if n.get("type") == "event"]
        assert len(event_nodes) > 0
        assert any(e.get("event_name") == "open_gate" for e in event_nodes)


class TestDoorPrefab:
    """Test Door prefab."""

    def test_door_prefab_exists(self):
        """Verify Door.zprfb exists."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Door.zprfb"
        assert prefab_path.exists()

    def test_door_has_locked_variable(self):
        """Verify Door has locked variable."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Door.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        variables = data.get("root", {}).get("variables", {})
        assert "locked" in variables
        assert variables["locked"] is True

    def test_door_has_logic_graph(self):
        """Verify Door has DoorLogic."""
        prefab_path = project_root / "Assets" / "Prefabs" / "Door.zprfb"
        data = json.loads(prefab_path.read_text(encoding="utf-8"))

        graphs = data.get("root", {}).get("logic_graphs", [])
        has_logic = any(g.get("path") == "Assets/Logic/DoorLogic.zlogic"
                       for g in graphs)
        assert has_logic


class TestDoorLogic:
    """Test door logic."""

    def test_logic_exists(self):
        """Verify DoorLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "DoorLogic.zlogic"
        assert logic_path.exists()

    def test_logic_listens_gate_event(self):
        """Verify logic listens for gate_opened event."""
        logic_path = project_root / "Assets" / "Logic" / "DoorLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "listen_gate_opened" in node_ids

    def test_logic_unlocks_door(self):
        """Verify logic sets locked to false."""
        logic_path = project_root / "Assets" / "Logic" / "DoorLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "set_unlocked" in node_ids


class TestLevelExitLogic:
    """Test level exit and autosave logic."""

    def test_logic_exists(self):
        """Verify LevelExitLogic.zlogic exists."""
        logic_path = project_root / "Assets" / "Logic" / "LevelExitLogic.zlogic"
        assert logic_path.exists()

    def test_logic_has_trigger(self):
        """Verify logic has trigger listener."""
        logic_path = project_root / "Assets" / "Logic" / "LevelExitLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "on_trigger_enter" in node_ids

    def test_logic_autosaves(self):
        """Verify logic saves game."""
        logic_path = project_root / "Assets" / "Logic" / "LevelExitLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "autosave_game" in node_ids

    def test_logic_loads_level2(self):
        """Verify logic loads Level2 scene."""
        logic_path = project_root / "Assets" / "Logic" / "LevelExitLogic.zlogic"
        data = json.loads(logic_path.read_text(encoding="utf-8"))

        node_ids = [n.get("id") for n in data.get("nodes", [])]
        assert "load_level2" in node_ids


class TestLevel2Scene:
    """Test Level2 placeholder."""

    def test_level2_exists(self):
        """Verify Level2.zscene exists."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        assert scene_path.exists()

    def test_level2_valid_json(self):
        """Verify Level2 is valid JSON."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format") == "zennity.scene"

    def test_level2_has_player(self):
        """Verify Level2 has Player."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        player = next((o for o in data.get("objects", [])
                      if o.get("name") == "Player"), None)
        assert player is not None

    def test_level2_has_camera(self):
        """Verify Level2 has Camera."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        camera = next((o for o in data.get("objects", [])
                      if o.get("name") == "Camera"), None)
        assert camera is not None

    def test_level2_has_hud(self):
        """Verify Level2 has HUD."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        hud = next((o for o in data.get("objects", [])
                   if o.get("name") == "HUD"), None)
        assert hud is not None


class TestLevel1Collectibles:
    """Test Level1 has collectibles."""

    def test_level1_has_coins(self):
        """Verify Level1 has 5 coins."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        coins = [o for o in data.get("objects", [])
                if o.get("name") == "Coin"]
        assert len(coins) == 5

    def test_level1_has_key(self):
        """Verify Level1 has 1 key."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        keys = [o for o in data.get("objects", [])
               if o.get("name") == "Key"]
        assert len(keys) == 1

    def test_level1_has_guard(self):
        """Verify Level1 has Guard."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        guard = next((o for o in data.get("objects", [])
                     if o.get("name") == "Guard"), None)
        assert guard is not None

    def test_level1_has_door(self):
        """Verify Level1 has Door."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        door = next((o for o in data.get("objects", [])
                    if o.get("name") == "Door"), None)
        assert door is not None

    def test_level1_has_exit(self):
        """Verify Level1 has LevelExit."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        exit = next((o for o in data.get("objects", [])
                    if o.get("name") == "LevelExit"), None)
        assert exit is not None

    def test_level1_has_project_variables(self):
        """Verify Level1 has coins and has_key project variables."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        variables = data.get("variables", {})
        assert "coins" in variables
        assert "has_key" in variables
        assert variables["coins"] == 0
        assert variables["has_key"] is False


class TestHUDCollectibles:
    """Test HUD displays collectible counts."""

    def test_hud_has_coins_label(self):
        """Verify HUD has CoinsLabel."""
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "CoinsLabel" in widgets

    def test_hud_has_key_label(self):
        """Verify HUD has KeyLabel."""
        ui_path = project_root / "Assets" / "UI" / "HUD.zui"
        data = json.loads(ui_path.read_text(encoding="utf-8"))

        widgets = [w.get("name") for w in data.get("widgets", [])]
        assert "KeyLabel" in widgets


class TestZeroPythonStep5:
    """Verify Step 5 uses ONLY visual systems."""

    def test_no_python_in_collectibles(self):
        """Verify no Python in collectibles."""
        coin_path = project_root / "Assets" / "Prefabs" / "Coin.zprfb"
        content = coin_path.read_text(encoding="utf-8")
        assert ".py" not in content.lower()

    def test_no_python_in_guard(self):
        """Verify no Python in Guard."""
        guard_path = project_root / "Assets" / "Prefabs" / "Guard.zprfb"
        content = guard_path.read_text(encoding="utf-8")
        assert ".py" not in content.lower()

    def test_no_python_in_door(self):
        """Verify no Python in Door."""
        door_path = project_root / "Assets" / "Prefabs" / "Door.zprfb"
        content = door_path.read_text(encoding="utf-8")
        assert ".py" not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
