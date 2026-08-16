"""Custom hard constraints for the sequential rearrangement design."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from Bio.SeqRecord import SeqRecord

from controller_logic import ControllerInput, DNAState, Mode, evaluate_controller
from export_genbank import validate_record
from topology import (
    Chemistry,
    Molecule,
    PairDefinition,
    SiteClass,
    channel_sites,
    enumerate_orders,
    reverse_complement,
)
from validate_sequences import circular_count


@dataclass(frozen=True)
class ConstraintResult:
    """Structured hard-constraint diagnostic."""

    constraint: str
    passed: bool
    construct: str
    state: str
    coordinates: str
    channel: str
    feature_identity: str
    diagnostic: str
    suggested_correction_class: str


def result(
    constraint: str,
    passed: bool,
    construct: str,
    diagnostic: str,
    *,
    state: str = "",
    coordinates: str = "",
    channel: str = "",
    feature_identity: str = "",
    correction: str = "",
) -> ConstraintResult:
    """Create one compact diagnostic."""
    return ConstraintResult(
        constraint,
        passed,
        construct,
        state,
        coordinates,
        channel,
        feature_identity,
        diagnostic,
        correction,
    )


def topology_constraints(
    states: list[Molecule],
    definitions: dict[str, PairDefinition],
) -> list[ConstraintResult]:
    """Validate topology, sites, reconstruction, and order classifications."""
    rows: list[ConstraintResult] = []
    expected_names = (
        "state_0",
        "state_1",
        "state_2",
        "state_3",
        "reverse_state_2",
        "reverse_state_1",
        "restored_state_0",
    )
    rows.append(
        result(
            "topology_valid",
            tuple(state.name for state in states) == expected_names,
            "message_register",
            "Seven expected physical states are present in order.",
            correction="rebuild state graph",
        )
    )
    rows.append(
        result(
            "exact_round_trip",
            states[0].sequence == states[-1].sequence,
            "message_register",
            "Restored sequence is byte-for-byte equal to State 0.",
            state="restored_state_0",
            correction="inspect inverse site chemistry and transformed interval",
        )
    )
    rows.append(
        result(
            "att_product_reconstruction_valid",
            states[0].physical_labels() == states[-1].physical_labels(),
            "message_register",
            "Feature identity, order, orientation, and site state are restored.",
            state="restored_state_0",
            correction="restore exact B/P half-site products",
        )
    )
    for state in states:
        offsets = state.element_offsets()
        for channel, definition in definitions.items():
            sites = channel_sites(state, channel)
            valid_count = len(sites) == 2
            rows.append(
                result(
                    "no_unintended_active_pair",
                    valid_count,
                    "message_register",
                    f"Observed {len(sites)} cognate sites; exactly two are required.",
                    state=state.name,
                    channel=channel,
                    coordinates=str([offsets.get(site.identity) for site in sites]),
                    feature_identity=",".join(site.identity for site in sites),
                    correction="remove duplicated or missing cognate site",
                )
            )
            for site in sites:
                expected = definition.sequence_for(site.site_class)
                intact = site.canonical_sequence == expected
                rows.append(
                    result(
                        "required_site_integrity",
                        intact,
                        "message_register",
                        f"{site.identity} exact {site.site_class.value} sequence check.",
                        state=state.name,
                        channel=channel,
                        coordinates=str(offsets[site.identity]),
                        feature_identity=site.identity,
                        correction="restore authoritative site arms and core",
                    )
                )
                rows.append(
                    result(
                        "central_dinucleotide_valid",
                        (
                            definition.core
                            in (
                                site.canonical_sequence[
                                    definition.b_core_index : definition.b_core_index
                                    + len(definition.core)
                                ],
                                site.canonical_sequence[
                                    definition.p_core_index : definition.p_core_index
                                    + len(definition.core)
                                ],
                            )
                        ),
                        "message_register",
                        f"Core {definition.core} is retained at a valid channel crossover.",
                        state=state.name,
                        channel=channel,
                        coordinates=str(offsets[site.identity]),
                        feature_identity=site.identity,
                        correction="restore the channel crossover core",
                    )
                )
                rows.append(
                    result(
                        "site_orientation_valid",
                        site.orientation in (-1, 1),
                        "message_register",
                        f"Typed orientation is {site.orientation}.",
                        state=state.name,
                        channel=channel,
                        coordinates=str(offsets[site.identity]),
                        feature_identity=site.identity,
                        correction="set an explicit physical strand",
                    )
                )
            sequence = state.sequence
            circular = state.molecule_type.value == "circular"
            expected_classes = {site.site_class for site in sites}
            for site_class in (SiteClass.B, SiteClass.P, SiteClass.L, SiteClass.R):
                query = definition.sequence_for(site_class)
                observed = circular_count(sequence, query, circular) + circular_count(
                    sequence,
                    reverse_complement(query),
                    circular,
                )
                expected_count = 1 if site_class in expected_classes else 0
                rows.append(
                    result(
                        "no_unintended_att_site",
                        observed == expected_count,
                        "message_register",
                        (
                            f"Exact {channel}-{site_class.value} count is {observed}; "
                            f"expected {expected_count}."
                        ),
                        state=state.name,
                        channel=channel,
                        feature_identity=site_class.value,
                        correction="redesign neutral sequence or remove duplicate site",
                    )
                )
        rows.append(
            result(
                "no_forbidden_ambiguity",
                not (set(state.sequence) - set("ACGT")),
                "message_register",
                "Only unambiguous A/C/G/T symbols are present.",
                state=state.name,
                correction="resolve every ambiguous nucleotide",
            )
        )
        rows.append(
            result(
                "cross_state_sequence_safety",
                all(len(channel_sites(state, channel)) == 2 for channel in definitions),
                "message_register",
                "Every channel remains uniquely represented in this state.",
                state=state.name,
                correction="remove duplicated exact attachment sites",
            )
        )

    if len(states) >= 4:
        forward = enumerate_orders(definitions, states[0], Chemistry.INTEGRASE)
        reverse = enumerate_orders(definitions, states[3], Chemistry.INTEGRASE_RDF)
        forward_ok = next(row for row in forward if row["order"] == "ABC")["completed"]
        reverse_ok = next(row for row in reverse if row["order"] == "CBA")["completed"]
        classified = len(forward) == 6 and len(reverse) == 6 and forward_ok and reverse_ok
    else:
        classified = False
    rows.append(
        result(
            "wrong_order_events_classified",
            bool(classified),
            "message_register",
            "All six forward and reverse orders are enumerated; only ABC and CBA complete.",
            correction="classify every permutation to a physical outcome",
        )
    )
    return rows


def controller_constraints() -> list[ConstraintResult]:
    """Validate required intended and blocked Boolean cases."""
    rows: list[ConstraintResult] = []
    expected = (
        (Mode.FORWARD, DNAState.STATE_0, "A"),
        (Mode.FORWARD, DNAState.STATE_1, "B"),
        (Mode.FORWARD, DNAState.STATE_2, "C"),
        (Mode.REVERSE, DNAState.STATE_3, "C"),
        (Mode.REVERSE, DNAState.STATE_2, "B"),
        (Mode.REVERSE, DNAState.STATE_1, "A"),
    )
    intended_pass = True
    for mode, state, channel in expected:
        drugs = {name: name == channel for name in "ABC"}
        output = evaluate_controller(
            ControllerInput(
                mode,
                state,
                drugs["A"],
                drugs["B"],
                drugs["C"],
            )
        )
        intended_pass &= output.integrases == (channel,) and (
            output.rdfs == ((channel,) if mode == Mode.REVERSE else ())
        )
    blocked_pass = True
    for mode in Mode:
        for state in DNAState:
            for drugs in ((False, False, False), (True, True, False), (True, True, True)):
                blocked_pass &= evaluate_controller(ControllerInput(mode, state, *drugs)).blocked
    rows.append(
        result(
            "controller_truth_table_valid",
            bool(intended_pass and blocked_pass),
            "controllers",
            "Six intended commands pass; no-input and simultaneous-input cases fail closed.",
            correction="repair state AND one-hot drug logic",
        )
    )
    return rows


def record_constraints(records: dict[str, SeqRecord]) -> list[ConstraintResult]:
    """Validate all selected sequence records and CDSs."""
    rows = []
    for name, record in records.items():
        errors = validate_record(record)
        rows.append(
            result(
                "genbank_annotation_integrity",
                not errors,
                name,
                "Record and all feature coordinates validate." if not errors else "; ".join(errors),
                correction="repair record annotations and feature locations",
            )
        )
        cds_errors = [error for error in errors if error.startswith("CDS")]
        rows.append(
            result(
                "valid_cds_translation",
                not cds_errors,
                name,
                "All CDS translations exactly match annotated amino-acid sequences.",
                correction="restore source CDS frame and translation",
            )
        )
        rows.append(
            result(
                "no_forbidden_ambiguity",
                not (set(str(record.seq).upper()) - set("ACGT")),
                name,
                "Only unambiguous A/C/G/T symbols are present.",
                correction="resolve every ambiguous nucleotide",
            )
        )
    return rows


def run_all_constraints(
    states: list[Molecule],
    definitions: dict[str, PairDefinition],
    records: dict[str, SeqRecord],
) -> list[ConstraintResult]:
    """Run every mandatory hard constraint."""
    return (
        topology_constraints(states, definitions)
        + controller_constraints()
        + record_constraints(records)
    )


def export_constraint_scores(path: Path, rows: list[ConstraintResult]) -> None:
    """Write every hard diagnostic to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
