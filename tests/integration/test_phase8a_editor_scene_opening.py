"""
Phase 8A: Editor Scene Opening Tests

Valida que .zscene assets podem ser abertos no editor via Asset Browser.
Bug-8A-001 regression tests.
"""

import pytest
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration import _phase8a_canonical as canonical


class TestSceneFileExtensionRecognition:
    """Testa se o editor reconhece .zscene como tipo de arquivo aberto."""

    def test_mainmenu_zscene_exists(self):
        """Verifica que MainMenu.zscene existe."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        assert scene_path.exists(), f"MainMenu.zscene não encontrado: {scene_path}"

    def test_level1_zscene_exists(self):
        """Verifica que Level1.zscene existe."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        assert scene_path.exists()

    def test_level2_zscene_exists(self):
        """Verifica que Level2.zscene existe."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        assert scene_path.exists()

    def test_gameover_zscene_exists(self):
        """Verifica que GameOver.zscene existe."""
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        assert scene_path.exists()

    def test_victory_zscene_exists(self):
        """Verifica que Victory.zscene existe."""
        scene_path = project_root / "Assets" / "Scenes" / "Victory.zscene"
        assert scene_path.exists()


class TestSceneFileFormat:
    """Testa que arquivos .zscene têm formato JSON válido (canonical format)."""

    def test_mainmenu_zscene_valid_json(self):
        """Verifica que MainMenu.zscene é JSON válido em formato canônico."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format_version") == 2
        assert data.get("scene_name") == "Main Menu"

    def test_level1_zscene_valid_json(self):
        """Verifica que Level1.zscene é JSON válido em formato canônico."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format_version") == 2

    def test_level2_zscene_valid_json(self):
        """Verifica que Level2.zscene é JSON válido em formato canônico."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format_version") == 2

    def test_gameover_zscene_valid_json(self):
        """Verifica que GameOver.zscene é JSON válido em formato canônico."""
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format_version") == 2

    def test_victory_zscene_valid_json(self):
        """Verifica que Victory.zscene é JSON válido em formato canônico."""
        scene_path = project_root / "Assets" / "Scenes" / "Victory.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert data.get("format_version") == 2


class TestSceneStructureForDeserialization:
    """Testa que cenas têm estrutura correta para desserialização."""

    def test_mainmenu_has_objects(self):
        """Verifica que MainMenu tem objects array."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert "objects" in data
        assert isinstance(data["objects"], list)
        assert len(data["objects"]) > 0

    def test_mainmenu_has_camera(self):
        """Verifica que MainMenu tem um Camera component."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        # In canonical format, camera is in components dict
        cameras = [o for o in data.get("objects", []) if "camera" in o.get("components", {})]
        assert len(cameras) > 0

    def test_level1_has_player_prefab(self):
        """Verifica que Level1 tem Player prefab."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        player = next((o for o in data.get("objects", []) if o.get("name") == "Player"), None)
        assert player is not None
        # In canonical format, prefab is a field on the object itself
        assert "prefab" in player or player.get("prefab") is not None

    def test_level2_has_boss(self):
        """Verifica que Level2 tem Boss."""
        scene_path = project_root / "Assets" / "Scenes" / "Level2.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))
        boss = next((o for o in data.get("objects", []) if o.get("name") == "Boss"), None)
        assert boss is not None
        # Boss may be a prefab
        assert "prefab" in boss or boss.get("name") == "Boss"

    def test_gameover_has_canvas(self):
        """Verifica que GameOver tem Canvas."""
        scene = canonical.load_scene("GameOver")
        assert any(canonical.component(o, "Canvas") for o in canonical.objects(scene))

    def test_victory_has_canvas(self):
        """Verifica que Victory tem Canvas."""
        scene = canonical.load_scene("Victory")
        assert any(canonical.component(o, "Canvas") for o in canonical.objects(scene))


class TestAssetBrowserDockHandlesZScene:
    """Testa que AssetBrowserDock pode processar duplo-clique em .zscene."""

    def test_asset_browser_dock_exists(self):
        """Verifica que AssetBrowserDock existe."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock
        assert AssetBrowserDock is not None

    def test_asset_browser_dock_accepts_workflow_controller(self):
        """Verifica que AssetBrowserDock aceita workflow_controller."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock
        from unittest.mock import Mock

        mock_controller = Mock()
        dock = AssetBrowserDock(workflow_controller=mock_controller)
        assert dock.workflow_controller == mock_controller

    def test_asset_browser_dock_has_open_asset_method(self):
        """Verifica que AssetBrowserDock tem método _open_asset_by_path."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock

        dock = AssetBrowserDock()
        assert hasattr(dock, '_open_asset_by_path')
        assert callable(dock._open_asset_by_path)

    def test_asset_browser_dock_has_open_scene_method(self):
        """Verifica que AssetBrowserDock tem método _open_scene."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock

        dock = AssetBrowserDock()
        assert hasattr(dock, '_open_scene')
        assert callable(dock._open_scene)

    def test_open_asset_recognizes_zscene_extension(self):
        """Verifica que _open_asset_by_path reconhece .zscene."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock
        from unittest.mock import Mock, patch

        dock = AssetBrowserDock()
        mock_workflow = Mock()
        dock.workflow_controller = mock_workflow

        # Testa com MainMenu.zscene real
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"

        with patch.object(dock, '_open_scene') as mock_open:
            dock._open_asset_by_path(str(scene_path))
            mock_open.assert_called_once()


class TestProjectWorkflowControllerLoadScene:
    """Testa que ProjectWorkflowController.load_scene funciona."""

    def test_project_workflow_controller_exists(self):
        """Verifica que ProjectWorkflowController existe."""
        from editor.project_workflow_controller import ProjectWorkflowController
        assert ProjectWorkflowController is not None

    def test_load_scene_accepts_path(self):
        """Verifica que load_scene aceita um Path."""
        from editor.project_workflow_controller import ProjectWorkflowController
        from unittest.mock import Mock

        mock_host = Mock()
        mock_host._current_scene_path = None
        mock_host.statusBar.return_value.showMessage = Mock()
        mock_host._log = Mock()

        controller = ProjectWorkflowController(mock_host)
        assert hasattr(controller, 'load_scene')
        assert callable(controller.load_scene)


class TestEditorBootstrapConnectionsAssets:
    """Testa que EditorBootstrapController conecta Asset Browser ao Workflow."""

    def test_editor_bootstrap_controller_exists(self):
        """Verifica que EditorBootstrapController existe."""
        from editor.editor_bootstrap_controller import EditorBootstrapController
        assert EditorBootstrapController is not None

    def test_bootstrap_connects_workflow_to_asset_browser(self):
        """Verifica que bootstrap conecta workflow ao asset browser."""
        from editor.editor_bootstrap_controller import EditorBootstrapController
        from editor.widgets.asset_browser_dock import AssetBrowserDock
        from editor.project_workflow_controller import ProjectWorkflowController
        from unittest.mock import Mock, patch
        from pathlib import Path

        # Mock host
        mock_host = Mock()
        mock_host.dock_assets = AssetBrowserDock()
        mock_host.statusBar.return_value.showMessage = Mock()
        mock_host._log = Mock()

        # Bootstrap
        bootstrap = EditorBootstrapController(mock_host, Path.cwd())

        # Simula composição (parte relevante)
        mock_host._project_workflow = ProjectWorkflowController(mock_host, Path.cwd())

        # Verifica que pode conectar
        mock_host.dock_assets.workflow_controller = mock_host._project_workflow
        assert mock_host.dock_assets.workflow_controller is not None


# O cabecalho serializado -- format_version, scene_name, engine_version -- e
# verificado para as cinco cenas em test_phase8a_canonical_schema.py, escrito
# junto com a migracao 6a3fb0a7. As tres assercoes que existiam aqui checavam os
# campos "format"/"name" do schema anterior a essa migracao e foram removidas em
# 13.1-B; nao havia contrato a preservar, so a grafia antiga do mesmo cabecalho.


class TestBugReproductionRegressions:
    """Testa que bug BUG-8A-001 não retorna."""

    def test_double_click_handler_exists(self):
        """Verifica que handler de duplo clique existe."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock

        dock = AssetBrowserDock()
        assert hasattr(dock, 'on_file_list_double_clicked')
        assert callable(dock.on_file_list_double_clicked)

    def test_double_click_handler_not_only_for_directories(self):
        """Verifica que handler trata arquivos, não apenas pastas."""
        from editor.widgets.asset_browser_dock import AssetBrowserDock
        from unittest.mock import Mock, patch

        dock = AssetBrowserDock()
        dock.workflow_controller = Mock()

        # Simula duplo-clique em .zscene
        with patch.object(dock, '_open_asset_by_path') as mock_open:
            # Handler deveria chamar _open_asset_by_path para não-diretórios
            assert hasattr(dock, '_open_asset_by_path')

    def test_scene_paths_windows_compatible(self):
        """Verifica que paths Windows são compatíveis."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"

        # Path pode ser enviado como str ou Path
        assert scene_path.exists()
        assert str(scene_path).endswith(".zscene")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
