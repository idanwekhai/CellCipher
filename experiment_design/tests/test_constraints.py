"""Hard-constraint and deliberately invalid record tests."""

from __future__ import annotations

import csv
from pathlib import Path

from Bio import SeqIO
from fixtures.invalid_fixtures import broken_cds_record, incorrect_feature_location_record

from export_genbank import validate_record
from proto_constraints import run_all_constraints
from topology import load_pair_definitions, run_round_trip

ROOT = Path(__file__).resolve().parents[1]


def test_selected_design_has_no_hard_failures() -> None:
    """Every mandatory hard constraint passes for the selected package."""
    definitions = load_pair_definitions(ROOT / "configs" / "channels.yaml")
    states, _ = run_round_trip(definitions)
    records = {
        path.stem: SeqIO.read(path, "genbank")
        for path in list((ROOT / "sequences").glob("*.gb")) + list((ROOT / "states").glob("*.gb"))
    }
    rows = run_all_constraints(states, definitions, records)
    assert rows
    assert all(row.passed for row in rows), [row for row in rows if not row.passed]


def test_broken_cds_is_rejected() -> None:
    """Internal stops and translation mismatches fail validation."""
    errors = validate_record(broken_cds_record())
    assert any(error.startswith("CDS") for error in errors)


def test_incorrect_feature_location_is_rejected() -> None:
    """A feature beyond the record length fails validation."""
    errors = validate_record(incorrect_feature_location_record())
    assert any("exceeds record length" in error for error in errors)


def test_parts_registry_provenance_complete_or_explicit() -> None:
    """Every registry row names a source and sequence class."""
    with (ROOT / "parts_registry.tsv").open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert rows
    for row in rows:
        assert row["internal_part_id"]
        assert row["authoritative_record"]
        assert row["sequence_class"]
        assert row["confidence"]
        assert row["unresolved_concerns"]


def test_constraint_report_contains_every_mandatory_name() -> None:
    """The exported report covers the full required hard-constraint vocabulary."""
    required = {
        "topology_valid",
        "exact_round_trip",
        "required_site_integrity",
        "att_product_reconstruction_valid",
        "site_orientation_valid",
        "central_dinucleotide_valid",
        "no_unintended_active_pair",
        "wrong_order_events_classified",
        "cross_state_sequence_safety",
        "no_unintended_att_site",
        "valid_cds_translation",
        "controller_truth_table_valid",
        "genbank_annotation_integrity",
        "no_forbidden_ambiguity",
    }
    with (ROOT / "reports" / "constraint_scores.csv").open() as handle:
        observed = {row["constraint"] for row in csv.DictReader(handle)}
    assert required <= observed
