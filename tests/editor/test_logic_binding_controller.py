from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from editor.controllers.logic_binding_controller import LogicBindingController
from engine.logic.graph_asset import save_logic_graph


class _AssetBrowser:
    def __init__(self) -> None:
        self.refresh_count = 0

    def refresh(self) -> None:
        self.refresh_count += 1


class _Repository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.saved: list[tuple[Path, dict]] = []
        self._assets: list[tuple[Path, dict]] = []

    def assets(self):
        return list(self._assets)

    def for_object(self, name, obj):
        path = self.root / "Assets" / "Logic" / "player.zlogic"
        return [(path, {"target": {"value": name}})] if obj else []

    def save(self, path: Path, graph: dict) -> None:
        save_logic_graph(path, graph)
        self.saved.append((Path(path), dict(graph)))


def _host(tmp_path: Path):
    asset_browser = _AssetBrowser()
    refreshed: list[str] = []
    return SimpleNamespace(
        _selected_name="Player",
        _objects_by_name={"Player": {"name": "Player"}},
        _logic_assets_repository=_Repository(tmp_path),
        _asset_browser=asset_browser,
        _update_inspector=lambda name: refreshed.append(name),
        refreshed=refreshed,
    )


def test_logic_binding_controller_creates_graph_for_object(tmp_path: Path) -> None:
    host = _host(tmp_path)
    controller = LogicBindingController(host, tmp_path)

    path = controller.create_for_object("Player")

    assert path == tmp_path / "Assets" / "Logic" / "PlayerLogic.zlogic"
    assert path.is_file()
    assert host._logic_assets_repository.saved[-1][1]["target"] == {"type": "name", "value": "Player"}
    assert host._asset_browser.refresh_count == 1
    assert host.refreshed == ["Player"]


def test_logic_binding_controller_creates_blank_graph_for_object(tmp_path: Path) -> None:
    host = _host(tmp_path)
    controller = LogicBindingController(host, tmp_path)

    path = controller.create_blank_for_object("Player")
    graph = host._logic_assets_repository.saved[-1][1]

    assert path.is_file()
    assert graph["target"] == {"type": "name", "value": "Player"}
    assert graph["nodes"] == []


def test_logic_binding_controller_detaches_all_object_graphs(tmp_path: Path) -> None:
    """Desvincular limpa o objeto e nao reescreve o grafo compartilhado.

    A assercao anterior exigia que o detach salvasse o .zlogic com
    enabled: False. b1a62a78 removeu exatamente essa escrita -- o mesmo grafo
    pode estar vinculado a varios objetos, e desabilita-lo no asset derrubava
    todos eles, alem de produzir o card em branco e o reanexo automatico que
    aquele commit corrigiu.
    """
    host = _host(tmp_path)
    obj = host._objects_by_name["Player"]
    obj["logic_assets"] = ["Assets/Logic/player.zlogic"]
    obj["components"] = {"items": [{"type": "LogicGraph", "graph_path": "Assets/Logic/player.zlogic"}]}
    obj["editor_data"] = {"logic_graphs": [{"path": "Assets/Logic/player.zlogic"}]}
    controller = LogicBindingController(host, tmp_path)

    count = controller.detach_all_for_object("Player")

    assert count == 1
    assert obj["logic_assets"] == []
    assert obj["components"]["items"] == []
    assert "logic_graphs" not in obj["editor_data"]
    assert not host._logic_assets_repository.saved, (
        "detach reescreveu o grafo compartilhado em disco"
    )
    assert host._asset_browser.refresh_count == 1
