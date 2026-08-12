"""Duplicate definitions must be detected on the real catalogue path.

PHASE 9 recovery item 4.1.

Recovery item 1 gave the registry duplicate detection and proved it with direct
unit calls. Those calls passed, and the guard was still not protecting anything:
``_harvest_declarative`` collected owners into a plain dict, so when two modules
declared the same id the first claim was overwritten *before the registry ever
saw it*. ``duplicate_definition_conflicts()`` returned ``[]`` while
``play_animation`` and ``stop_animation`` were each declared twice, in
``actions_nodes`` and ``animation_nodes``, with different pins and two different
executors.

That is the shape of the bug this whole phase keeps finding: the check exists,
the check is correct, and nothing feeds it the real data. So the test that
matters here does not call the registry directly. It puts a genuine second
declaration on disk, builds the catalogue the way the engine builds it, and
requires the build to fail.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from engine.logic.node_definitions import (
    KNOWN_DUPLICATE_DEFINITIONS,
    NODE_DEFINITIONS,
    DuplicateNodeDefinitionError,
    definition_owner,
    duplicate_definition_conflicts,
    unexpected_definition_conflicts,
)
from engine.logic.node_definitions.catalogue import (
    ensure_catalogue_loaded,
    reset_catalogue_for_tests,
    reset_discovery_cache_for_tests,
)

PACKAGE_DIR = Path(__file__).resolve().parents[2] / "engine" / "logic" / "node_definitions"
PROBE_MODULE = PACKAGE_DIR / "zz_duplicate_probe_nodes.py"

PROBE_SOURCE = textwrap.dedent(
    '''
    """Temporary probe module written by a test. Never committed."""
    from engine.core.metadata import NodeDefinition, PinDefinition, PinType


    class DuplicateProbeNode(NodeDefinition):
        __node_definition__ = NodeDefinition(
            id="{node_id}",
            title_key="Duplicate Probe",
            category_key="Flow",
            inputs=[PinDefinition(id="exec", label_key="Exec", pin_type=PinType.EXEC)],
            outputs=[PinDefinition(id="next", label_key="Next", pin_type=PinType.EXEC)],
        )
    '''
)


PROBE_IMPORT_NAME = "engine.logic.node_definitions.zz_duplicate_probe_nodes"


def _forget_probe() -> None:
    """Drop the probe from disk AND from sys.modules.

    Deleting the file is not enough: import_module hands back the cached module
    object, so the probe's declaration would survive into the next test and make
    the results depend on order -- the exact defect item 9B spent a whole item
    removing from this suite.
    """
    import sys

    if PROBE_MODULE.exists():
        PROBE_MODULE.unlink()
    sys.modules.pop(PROBE_IMPORT_NAME, None)


@pytest.fixture
def rebuilt_catalogue():
    """Rebuild the catalogue from disk, and put it back afterwards."""
    _forget_probe()
    yield
    _forget_probe()
    reset_discovery_cache_for_tests()
    reset_catalogue_for_tests()
    ensure_catalogue_loaded()


def _write_probe(node_id: str) -> None:
    _forget_probe()
    PROBE_MODULE.write_text(PROBE_SOURCE.format(node_id=node_id), encoding="utf-8")
    reset_discovery_cache_for_tests()
    reset_catalogue_for_tests()


def test_a_second_declaration_on_disk_fails_the_real_build(rebuilt_catalogue):
    """The test that item 1 was missing.

    A module is added to the package declaring an id that already exists, and
    the catalogue is built exactly as the engine builds it. Before this fix the
    build succeeded and the duplicate was invisible.
    """
    _write_probe("if_else")
    with pytest.raises(DuplicateNodeDefinitionError) as excinfo:
        ensure_catalogue_loaded()

    message = str(excinfo.value)
    assert "if_else" in message
    assert "flow_nodes" in message, message
    assert "zz_duplicate_probe_nodes" in message, message


def test_the_error_names_both_claimants(rebuilt_catalogue):
    _write_probe("add_number")
    with pytest.raises(DuplicateNodeDefinitionError) as excinfo:
        ensure_catalogue_loaded()
    message = str(excinfo.value)
    assert "math_nodes" in message and "zz_duplicate_probe_nodes" in message


def test_a_probe_with_a_fresh_id_builds_cleanly(rebuilt_catalogue):
    """The guard must fire on duplication, not on any new module."""
    _write_probe("zz_probe_unique_node")
    ensure_catalogue_loaded()  # must not raise
    assert "zz_probe_unique_node" in NODE_DEFINITIONS
    assert definition_owner("zz_probe_unique_node") == "zz_duplicate_probe_nodes"


def test_discovery_picks_the_probe_up_at_all(rebuilt_catalogue):
    """Guards the two tests above against passing for the wrong reason."""
    from engine.logic.node_definitions.catalogue import _discover_declarative_modules

    _write_probe("zz_probe_unique_node")
    assert "zz_duplicate_probe_nodes" in _discover_declarative_modules()
    ensure_catalogue_loaded()


# ---------------------------------------------------------------------------
# The duplicates that exist right now
# ---------------------------------------------------------------------------

def test_the_real_catalogue_reports_its_actual_duplicates():
    """Recorded truthfully rather than collapsed away."""
    ensure_catalogue_loaded()
    conflicts = {node_id for node_id, _first, _second in duplicate_definition_conflicts()}
    assert conflicts == set(KNOWN_DUPLICATE_DEFINITIONS), (
        f"recorded {sorted(conflicts)}, scheduled {sorted(KNOWN_DUPLICATE_DEFINITIONS)}"
    )


def test_every_recorded_duplicate_names_two_different_modules():
    ensure_catalogue_loaded()
    for node_id, first, second in duplicate_definition_conflicts():
        assert first != second, node_id
        assert first and second


def test_nothing_unexpected_is_duplicated():
    ensure_catalogue_loaded()
    assert unexpected_definition_conflicts() == []


def test_the_first_claimant_keeps_ownership():
    """Last-write-wins is the bug; the earlier module must remain the owner."""
    ensure_catalogue_loaded()
    for node_id, first, _second in duplicate_definition_conflicts():
        assert definition_owner(node_id) == first, (
            f"{node_id} is owned by {definition_owner(node_id)}, not by its first "
            f"claimant {first}; a later module overwrote the claim"
        )


def test_the_known_set_is_a_debt_not_an_exemption():
    """Every listed id must actually be duplicated, or the entry is stale."""
    ensure_catalogue_loaded()
    recorded = {node_id for node_id, _f, _s in duplicate_definition_conflicts()}
    stale = sorted(set(KNOWN_DUPLICATE_DEFINITIONS) - recorded)
    assert not stale, (
        f"{stale} are listed as known duplicates but are not duplicated any more; "
        "remove them from KNOWN_DUPLICATE_DEFINITIONS"
    )


def test_the_harvest_does_not_collapse_claims_before_publishing():
    """Pins the mechanism, not just the symptom."""
    import inspect

    from engine.logic.node_definitions import catalogue

    import ast
    import textwrap

    source = textwrap.dedent(inspect.getsource(catalogue._harvest_declarative))
    # The docstring describes the old code on purpose, so only the executable
    # statements are compared -- an earlier draft of this assertion matched its
    # own prose, and inspect.getdoc() returns a cleaned string that no longer
    # matches the raw source, so removing it by substring did nothing.
    function = ast.parse(source).body[0]
    statements = function.body
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        statements = statements[1:]
    body = "\n".join(ast.get_source_segment(source, node) or "" for node in statements)
    assert body.strip(), "the function body could not be extracted; check is vacuous"
    assert "owners[node_id]" not in body, (
        "the harvest assigns into a dict keyed by node id; a second claim "
        "overwrites the first before the registry can record the conflict"
    )
    assert "claims.append" in body
