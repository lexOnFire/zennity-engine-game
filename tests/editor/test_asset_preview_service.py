from pathlib import Path

from editor.asset_preview_service import AssetPreviewService


def test_asset_preview_cache_reuses_unchanged_file_and_invalidates_revision(tmp_path: Path) -> None:
    path = tmp_path / "material.txt"
    path.write_text("first", encoding="utf-8")
    service = AssetPreviewService("#ff0000", maximum_entries=2)

    first = service.preview(path)
    second = service.preview(path)
    path.write_text("second revision", encoding="utf-8")
    third = service.preview(path)

    assert first is second
    assert third is not second
    assert service.cache_hits == 1
    assert service.cache_misses == 2
    assert service.cached_entries == 1


def test_asset_preview_cache_has_a_strict_memory_bound(tmp_path: Path) -> None:
    service = AssetPreviewService("#ff0000", maximum_entries=2)
    for index in range(5):
        path = tmp_path / f"asset-{index}.txt"
        path.write_text(str(index), encoding="utf-8")
        service.preview(path)

    assert service.cached_entries == 2


def test_editor_delegates_asset_preview_generation() -> None:
    source = Path("editor/asset_browser_controller.py").read_text(encoding="utf-8")

    assert "AssetPreviewService(DEFAULT_TOKENS.danger)" in source
    assert "preview = self.preview_service.preview(Path(path_value))" in source
    assert "os.path.getsize(path)" not in source
