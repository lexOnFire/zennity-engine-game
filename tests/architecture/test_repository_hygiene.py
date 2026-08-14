"""Metadata hashes stay coherent, and the working tree stays still.

PHASE 9 recovery item 16B.1. Two symptoms looked like one defect and are not:

* On a Windows clone, ~47 ``.meta`` files appeared modified after every test
  run. They are not stale in the repository. ``compute_file_hash`` is SHA-256
  over **raw bytes**, so a working tree checked out with CRLF hashes every text
  asset differently from the LF bytes recorded here, and each scan rewrites
  them. The cause is the working tree, not the metadata -- ``git add
  --renormalize .`` fixes it on that machine, and nothing in the repository
  needs to change.
* Exactly **one** hash was genuinely stale: ``Level1.zscene.meta``, recorded
  against the scene's previous content. That one made every asset scan rewrite
  the file even on Linux, which is what made item 16A's "no assets modified"
  gate fail depending on command order.

The gates below check the property rather than a list of filenames, so a hash
that goes stale in the future is caught wherever it appears.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from engine.assets.asset_metadata import compute_file_hash

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "Assets"


def _tracked_meta_files() -> list[Path]:
    # -z because asset paths contain spaces, and bytes because they also
    # contain accents. ``text=True`` decodes with the locale encoding, which on
    # Windows is cp1252: git emits UTF-8, so "Cenário" came back as "CenÃ¡rio"
    # and the file lookup failed for three PNG sidecars. The paths are fine; the
    # decoding was not. ``-c core.quotepath=off`` keeps git from escaping the
    # non-ASCII bytes before we ever see them.
    out = subprocess.run(
        ["git", "-c", "core.quotepath=off", "ls-files", "-z", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return [REPO_ROOT / line for line in out if line.endswith(".meta")]


def _asset_for(meta: Path) -> Path:
    """``Foo.zscene.meta`` describes ``Foo.zscene``."""
    return meta.with_suffix("")


#: ``.meta`` files whose asset is gone. Every one is a ``.bak`` sidecar left
#: behind when the backup it described was deleted, plus one behaviour file.
#: Named rather than pattern-skipped: a *new* orphan is a real finding, and a
#: listed one that gains its asset back must be removed from here deliberately.
KNOWN_ORPHAN_META = {
    "Assets/Behaviors/testetree.zbehavior.meta",
    "Assets/Demos/PortalStation/PortalStation.zscene.bak.meta",
    "Assets/Logic/NebulaDefense/NebulaPlayer.zlogic.bak.meta",
    "Assets/Logic/NebulaDefense/NebulaSpawner.zlogic.bak.meta",
    "Assets/Logic/NewLogic.zlogic.bak.meta",
    "Assets/Logic/PlayerLogicTEST.zlogic.bak.meta",
    "Assets/Logic/PlayerMovement_wasd.zlogic.bak.meta",
    "Assets/Logic/Showcase_Player.zlogic.bak.meta",
    "Assets/Logic/plano_movi.zlogic.bak.meta",
    "Assets/Logic/teste.zlogic.bak.meta",
    "Assets/Scenes/BehaviorControllerDemo.zscene.bak.meta",
    "Assets/Scenes/JogoBase2D.zscene.bak.meta",
    "Assets/Scenes/NebulaDefense.zscene.bak.meta",
    "Assets/Scenes/RPG_Showcase.zscene.bak.meta",
    "Assets/Scenes/TestGame_Showcase.zscene.bak.meta",
}


def test_the_sweep_is_not_vacuous():
    assert len(_tracked_meta_files()) > 300


def test_every_meta_hash_matches_its_asset():
    """The defect this item closed, checked as a property.

    A mismatch means the next asset scan rewrites the file, which is how a
    single stale hash turned into an intermittent failure of unrelated gates.
    """
    stale = []
    for meta in _tracked_meta_files():
        asset = _asset_for(meta)
        if not asset.exists():
            continue
        try:
            recorded = json.loads(meta.read_text(encoding="utf-8")).get("hash", "")
        except (OSError, ValueError):
            stale.append((str(meta.relative_to(REPO_ROOT)), "unreadable", ""))
            continue
        actual = compute_file_hash(asset)
        if recorded != actual:
            stale.append((str(meta.relative_to(REPO_ROOT)).replace("\\", "/"),
                          recorded[:12], actual[:12]))
    assert stale == [], (
        "stale metadata hashes -- every asset scan will rewrite these:\n"
        + "\n".join(f"  {m}: recorded {r}… actual {a}…" for m, r, a in stale)
    )


def test_orphan_meta_files_are_the_known_ones():
    """Debt with names. A new orphan fails; a resolved one must be removed."""
    orphans = {
        str(meta.relative_to(REPO_ROOT)).replace("\\", "/")
        for meta in _tracked_meta_files()
        if not _asset_for(meta).exists()
    }
    assert orphans == KNOWN_ORPHAN_META


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_the_hash_is_deterministic():
    asset = ASSETS / "Prefabs" / "Boss.zprfb"
    assert compute_file_hash(asset) == compute_file_hash(asset)


def test_line_endings_change_the_hash(tmp_path):
    """Why a CRLF working tree makes every ``.meta`` look stale.

    ``compute_file_hash`` digests raw bytes, so this is expected behaviour, not
    a bug -- but it is the entire mechanism behind the Windows churn, and
    recording it here keeps the next person from chasing the metadata instead
    of the checkout.
    """
    source = (ASSETS / "Prefabs" / "Boss.zprfb").read_bytes()
    assert b"\r\n" not in source, "the repository copy must be LF"

    lf, crlf = tmp_path / "lf", tmp_path / "crlf"
    lf.write_bytes(source)
    crlf.write_bytes(source.replace(b"\n", b"\r\n"))
    assert compute_file_hash(lf) != compute_file_hash(crlf)


def test_only_one_hash_implementation_exists():
    """Two would mean 'stale' depends on who asked."""
    from engine.assets import asset_database, asset_importer, asset_metadata

    assert asset_importer.compute_file_hash is asset_metadata.compute_file_hash
    assert "hashlib" not in asset_database.__dict__


# ---------------------------------------------------------------------------
# Line-ending policy
# ---------------------------------------------------------------------------


def test_the_line_ending_policy_covers_the_asset_formats():
    text = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in text
    for extension in (".meta", ".zlogic", ".zscene", ".zprefab"):
        assert f"*{extension} text eol=lf" in text, extension


def test_the_policy_file_has_no_byte_order_mark():
    """A BOM ahead of the first rule is silently swallowed by older gits.

    This one tolerates it, so the rule was applying -- but the global
    ``* text=auto eol=lf`` line is exactly the rule that covers ``.py``, and
    losing it silently is how a repository ends up with mixed endings again.
    """
    assert not (REPO_ROOT / ".gitattributes").read_bytes().startswith(b"\xef\xbb\xbf")


def test_no_tracked_text_file_carries_crlf_in_the_repository():
    attrs = subprocess.run(
        ["git", "ls-files", "--eol"], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    offenders = [
        line.split("\t")[-1]
        for line in attrs
        if line.startswith("i/crlf") or line.startswith("i/mixed")
    ]
    assert offenders == [], f"tracked files stored with CRLF: {offenders[:10]}"


# ---------------------------------------------------------------------------
# Idempotency: the point of the whole item
# ---------------------------------------------------------------------------


def _dirty_paths() -> list[str]:
    return [
        line for line in subprocess.run(
            ["git", "status", "--porcelain", "--", "Assets", "engine"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.splitlines() if line.strip()
    ]


def test_scanning_the_assets_twice_writes_nothing(tmp_path):
    """Running the metadata check must not itself modify the repository.

    Deliberately measured on a *copy*: a test that scans the real tree to prove
    scanning is safe would be the very thing it is checking for.
    """
    import shutil

    from engine.assets.asset_database import AssetDatabase

    project = tmp_path / "proj"
    (project / "Assets").mkdir(parents=True)
    for name in ("Prefabs/Boss.zprfb", "Prefabs/Boss.zprfb.meta"):
        destination = project / "Assets" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ASSETS / name, destination)

    database = AssetDatabase(project)
    database.scan()
    first = (project / "Assets" / "Prefabs" / "Boss.zprfb.meta").read_bytes()
    database.scan()
    second = (project / "Assets" / "Prefabs" / "Boss.zprfb.meta").read_bytes()

    assert first == second, "a second scan rewrote metadata; the hash is not stable"


def test_non_ascii_asset_paths_are_decoded_correctly():
    """The bug this file shipped with, kept from coming back.

    Three PNG sidecars under ``Assets/Scenes`` have accented names. Reading
    ``git ls-files`` with the locale encoding turned "Cenário" into "CenÃ¡rio"
    on Windows, so their assets appeared to be missing and they were reported as
    orphans. Linux never showed it, which is exactly why it needs a test rather
    than a memory.
    """
    accented = [p for p in _tracked_meta_files() if "\u00e1" in p.name or "\u00e3" in p.name]
    assert accented, "no accented asset path found; this check would be vacuous"
    for meta in accented:
        assert "Ã" not in meta.name, f"mojibake: {meta.name}"
        assert _asset_for(meta).exists(), f"{meta.name} does not resolve to its asset"


# ---------------------------------------------------------------------------
# Case collisions
# ---------------------------------------------------------------------------


def _tracked_paths() -> list[str]:
    out = subprocess.run(
        ["git", "-c", "core.quotepath=off", "ls-files", "-z"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout
    return [p for p in out.decode("utf-8", errors="surrogateescape").split("\0") if p]


def _case_collisions(paths) -> dict[str, list[str]]:
    """Paths that a case-insensitive filesystem cannot tell apart."""
    groups: dict[str, list[str]] = {}
    for path in paths:
        groups.setdefault(path.casefold(), []).append(path)
    return {key: sorted(v) for key, v in groups.items() if len(v) > 1}


def test_no_two_tracked_paths_collide_when_casefolded():
    """Windows and macOS cannot check out both, so only one ever lands.

    Item 16D removed the ``assets/scripts`` tree, which duplicated all ten files
    of ``Assets/Scripts`` byte for byte. Cloning on Windows printed a collision
    warning and silently dropped one side, which is why the ``Assets/Scripts``
    metadata hashes looked stale there: the file on disk was the other copy.

    Checked over the whole repository rather than that one directory -- the
    defect is a property of the path set, not of a folder.
    """
    collisions = _case_collisions(_tracked_paths())
    assert collisions == {}, (
        "paths differing only by case cannot both exist on Windows/macOS:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(collisions.items()))
    )


def test_the_collision_check_is_not_vacuous():
    """The detector must actually detect; proven on a synthetic pair."""
    assert _case_collisions(["Assets/Scripts/a.py", "assets/scripts/a.py"])
    assert _case_collisions(["A/B.PY", "a/b.py"])
    assert _case_collisions(["x.py", "y.py"]) == {}
    assert len(_tracked_paths()) > 1000, "the real sweep would be vacuous"


def test_the_lowercase_assets_root_is_gone():
    """The canonical root is ``Assets/``, decided before this item.

    ``docs/architecture/ASSETS_CASING_MIGRATION.md`` recorded the choice and
    said the lowercase tree had been removed. It had not: all ten files were
    still tracked, and ``test_canonical_assets_root`` had been failing ever
    since. Item 16D finished the migration the document described.
    """
    assert not any(p.startswith("assets/") for p in _tracked_paths())
