"""Topology, chemistry, order, and exact restoration tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from fixtures.invalid_fixtures import (
    corrupted_att_core,
    duplicated_cognate_site,
    wrong_site_orientation,
)

from proto_constraints import topology_constraints
from topology import (
    Chemistry,
    Outcome,
    PairDefinition,
    SiteClass,
    apply_recombination,
    build_initial_register,
    channel_sites,
    classify_event,
    enumerate_orders,
    load_pair_definitions,
    run_round_trip,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def definitions() -> dict[str, PairDefinition]:
    """Load authoritative site definitions."""
    return load_pair_definitions(ROOT / "configs" / "channels.yaml")


def test_three_forward_and_reverse_transitions(
    definitions: dict[str, PairDefinition],
) -> None:
    """All six intended transitions are antiparallel inversions."""
    states, events = run_round_trip(definitions)
    assert len(events) == 6
    assert all(event.outcome == Outcome.INVERSION for event in events)
    assert [state.name for state in states] == [
        "state_0",
        "state_1",
        "state_2",
        "state_3",
        "reverse_state_2",
        "reverse_state_1",
        "restored_state_0",
    ]


def test_exact_sequence_and_feature_restoration(
    definitions: dict[str, PairDefinition],
) -> None:
    """The final state restores bytes, order, orientation, sites, and coordinates."""
    states, _ = run_round_trip(definitions)
    assert states[-1].sequence == states[0].sequence
    assert states[-1].sha256 == states[0].sha256
    assert states[-1].physical_labels() == states[0].physical_labels()
    assert states[-1].element_offsets() == states[0].element_offsets()


def test_expected_payload_order(definitions: dict[str, PairDefinition]) -> None:
    """Forward states reproduce the user-specified payload oracle."""
    states, _ = run_round_trip(definitions)
    assert states[1].payload_order() == ["-D", "-C", "-B", "-A", "+E", "+F"]
    assert states[2].payload_order() == ["-D", "-C", "-B", "-F", "-E", "+A"]
    assert states[3].payload_order() == ["-D", "-C", "+F", "+B", "-E", "+A"]


def test_site_product_conversion_and_reconstruction(
    definitions: dict[str, PairDefinition],
) -> None:
    """B/P becomes exact R/L hybrids and reverse chemistry reconstructs B/P."""
    molecule = build_initial_register(definitions)
    before = {site.identity: site.canonical_sequence for site in channel_sites(molecule, "A")}
    apply_recombination(molecule, "A", Chemistry.INTEGRASE, definitions)
    products = {site.site_class: site.canonical_sequence for site in channel_sites(molecule, "A")}
    assert products[SiteClass.L] == definitions["A"].sequence_for(SiteClass.L)
    assert products[SiteClass.R] == definitions["A"].sequence_for(SiteClass.R)
    apply_recombination(molecule, "A", Chemistry.INTEGRASE_RDF, definitions)
    after = {site.identity: site.canonical_sequence for site in channel_sites(molecule, "A")}
    assert after == before


def test_all_forward_permutations(definitions: dict[str, PairDefinition]) -> None:
    """Only ABC completes; wrong orders reach the expected deletion channel."""
    rows = {
        row["order"]: row
        for row in enumerate_orders(
            definitions, build_initial_register(definitions), Chemistry.INTEGRASE
        )
    }
    assert rows["ABC"]["completed"]
    assert not any(rows[order]["completed"] for order in rows if order != "ABC")
    assert [event["outcome"] for event in rows["ACB"]["events"]] == [
        Outcome.INVERSION,
        Outcome.DELETION,
    ]
    assert rows["BAC"]["events"][0]["outcome"] == Outcome.DELETION
    assert rows["BCA"]["events"][0]["outcome"] == Outcome.DELETION
    assert [event["outcome"] for event in rows["CAB"]["events"]] == [
        Outcome.INVERSION,
        Outcome.DELETION,
    ]
    assert [event["outcome"] for event in rows["CBA"]["events"]] == [
        Outcome.INVERSION,
        Outcome.DELETION,
    ]


def test_all_reverse_permutations(definitions: dict[str, PairDefinition]) -> None:
    """Only CBA restores from encrypted State 3."""
    states, _ = run_round_trip(definitions)
    rows = {
        row["order"]: row
        for row in enumerate_orders(definitions, states[3], Chemistry.INTEGRASE_RDF)
    }
    assert rows["CBA"]["completed"]
    assert not any(rows[order]["completed"] for order in rows if order != "CBA")


def test_wrong_orientation_is_deletion(definitions: dict[str, PairDefinition]) -> None:
    """A parallel cognate pair is classified as deletion/excision."""
    molecule = wrong_site_orientation(definitions)
    assert (
        classify_event(molecule, "A", Chemistry.INTEGRASE, definitions).outcome == Outcome.DELETION
    )


def test_corrupt_core_is_rejected(definitions: dict[str, PairDefinition]) -> None:
    """A changed attachment core fails site-integrity constraints."""
    molecule = corrupted_att_core(definitions)
    rows = topology_constraints([molecule], definitions)
    assert any(row.constraint == "required_site_integrity" and not row.passed for row in rows)


def test_incompatible_core_definition_is_rejected() -> None:
    """Pair definitions reject a declared crossover at the wrong offset."""
    with pytest.raises(ValueError):
        PairDefinition("X", "bad", "AACCGG", "TTCCGG", "CC", 0, 2, "invalid")


def test_duplicate_site_is_ambiguous(definitions: dict[str, PairDefinition]) -> None:
    """A third cognate site fails unique-pairing and classifies as ambiguous."""
    molecule = duplicated_cognate_site(definitions)
    assert (
        classify_event(molecule, "B", Chemistry.INTEGRASE, definitions).outcome
        == Outcome.AMBIGUOUS_SUBSTRATE
    )


def test_mutation_breaks_exact_restoration(definitions: dict[str, PairDefinition]) -> None:
    """The exact equality oracle detects post-cycle mutation."""
    states, _ = run_round_trip(definitions)
    altered = deepcopy(states[-1])
    first = altered.elements[2].canonical_sequence[0]
    altered.elements[2].canonical_sequence = ("C" if first == "A" else "A") + altered.elements[
        2
    ].canonical_sequence[1:]
    assert altered.sequence != states[0].sequence
