"""Build all primary, state, candidate, provenance, and topology artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import yaml
from Bio import SeqIO
from Bio.Data.CodonTable import TranslationError
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, SeqFeature
from Bio.SeqRecord import SeqRecord

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from controller_logic import export_truth_table  # noqa: E402
from export_genbank import prepare_record, sequence_sha256, write_record  # noqa: E402
from optimize_sequences import (  # noqa: E402
    export_pareto,
    generate_candidates,
    selected_payloads,
)
from proto_constraints import export_constraint_scores, run_all_constraints  # noqa: E402
from run_model_scoring import export_model_runs  # noqa: E402
from topology import (  # noqa: E402
    Chemistry,
    Molecule,
    SiteClass,
    build_initial_register,
    enumerate_cognate_pairs,
    enumerate_orders,
    load_pair_definitions,
    run_round_trip,
    state_summary,
)
from validate_sequences import analyze_record, scan_host_exact, write_analysis  # noqa: E402

RETRIEVED = ROOT / "artifacts" / "retrieved_parts"
SEQUENCES = ROOT / "sequences"
STATES = ROOT / "states"
REPORTS = ROOT / "reports"
TOPOLOGY_OUTPUTS = ROOT / "artifacts" / "topology_outputs"
CANDIDATES = ROOT / "candidates"
MODEL_INPUTS = ROOT / "artifacts" / "model_inputs"


def deterministic_dna(label: str, length: int) -> str:
    """Return deterministic synthetic placeholder DNA."""
    output: list[str] = []
    bases = "ACGT"
    counter = 0
    while len(output) < length:
        digest = hashlib.sha256(f"{label}:{counter}".encode()).digest()
        output.extend(bases[byte & 0b11] for byte in digest)
        counter += 1
    return "".join(output[:length])


def feature(
    start: int,
    end: int,
    feature_type: str,
    label: str,
    strand: int = 1,
    **qualifiers: str,
) -> SeqFeature:
    """Create one consistently annotated feature."""
    data = {"label": [label], **{key: [value] for key, value in qualifiers.items()}}
    return SeqFeature(
        FeatureLocation(start, end, strand=strand),
        type=feature_type,
        qualifiers=data,
    )


def source_feature(length: int, topology: str, status: str) -> SeqFeature:
    """Create a full-record source annotation."""
    return feature(
        0,
        length,
        "source",
        "complete_construct",
        organism="synthetic DNA construct",
        host="Escherichia coli K-12",
        topology=topology,
        design_status=status,
    )


def molecule_to_record(molecule: Molecule) -> SeqRecord:
    """Convert a transformed message molecule into a coordinate-correct record."""
    record = SeqRecord(
        Seq(molecule.sequence),
        id=f"SRV1_{molecule.name}",
        name=molecule.name[:16],
        description=f"Sequential rearrangement message register {molecule.name}",
    )
    record.annotations["topology"] = molecule.molecule_type.value
    record.annotations["organism"] = "Escherichia coli K-12 candidate chromosomal cassette"
    record.features.append(
        source_feature(
            len(record),
            molecule.molecule_type.value,
            "candidate; topology-valid; not synthesis-ready",
        )
    )
    offsets = molecule.element_offsets()
    for element in molecule.elements:
        start, end = offsets[element.identity]
        qualifiers = {
            "orientation_state": "+" if element.orientation == 1 else "-",
            "canonical_identity": element.identity,
            "design_status": "candidate",
            "note": element.note or "typed topology element",
        }
        if element.kind == "attachment_site":
            qualifiers.update(
                {
                    "channel": element.channel or "",
                    "site_class": element.site_class.value if element.site_class else "",
                    "site_origin": element.site_origin or "",
                    "accessibility": str(element.accessible).lower(),
                }
            )
            record.features.append(
                feature(
                    start,
                    end,
                    "protein_bind",
                    element.identity,
                    strand=element.orientation,
                    bound_moiety=f"LSI channel {element.channel}",
                    **qualifiers,
                )
            )
        elif element.kind == "payload":
            record.features.append(
                feature(
                    start,
                    end,
                    "misc_feature",
                    f"payload_{element.identity}",
                    strand=element.orientation,
                    function="neutral sequencing barcode; no biological function",
                    **qualifiers,
                )
            )
        elif element.kind == "inert_boundary":
            record.features.append(
                feature(
                    start,
                    end,
                    "misc_feature",
                    "S4_inert_boundary",
                    strand=element.orientation,
                    function="logical boundary only",
                    **qualifiers,
                )
            )
        else:
            record.features.append(
                feature(
                    start,
                    end,
                    "misc_feature",
                    element.identity,
                    strand=element.orientation,
                    **qualifiers,
                )
            )
    record.features.append(
        feature(
            0,
            min(48, len(record)),
            "misc_feature",
            "unresolved_chromosomal_integration_interface",
            design_status="unresolved",
            note="No landing locus or homology arms were invented.",
        )
    )
    return prepare_record(record, "candidate; not synthesis-ready")


def extract_native_cds(accession: str, protein_id: str) -> tuple[str, str, dict[str, object]]:
    """Extract one authoritative CDS and translation by protein accession."""
    path = RETRIEVED / f"{accession}.gb"
    record = SeqIO.read(path, "genbank")
    matches = [
        item
        for item in record.features
        if item.type == "CDS" and protein_id in item.qualifiers.get("protein_id", [])
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {protein_id} feature in {accession}, found {len(matches)}")
    item = matches[0]
    nucleotide = str(item.extract(record.seq)).upper()
    translation = item.qualifiers["translation"][0]
    try:
        translated = str(Seq(nucleotide).translate(table=11, cds=True))
    except (ValueError, TranslationError):
        translated = str(Seq(nucleotide).translate(table=11, to_stop=False)).rstrip("*")
    if translated != translation.rstrip("*"):
        raise ValueError(f"Source CDS translation mismatch for {protein_id}")
    provenance = {
        "accession": accession,
        "protein_id": protein_id,
        "coordinates_0_based": [int(item.location.start), int(item.location.end)],
        "strand": item.location.strand,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    return nucleotide, translation, provenance


def expression_cassette(
    channel: str,
    mode: str,
    integrase: tuple[str, str],
    rdf: tuple[str, str] | None,
) -> tuple[str, list[dict[str, object]]]:
    """Construct one annotated prototypical state-and-drug expression cassette."""
    sensor_names = {"A": "P_lac/IPTG", "B": "P_LtetO-1/aTc", "C": "P_BAD/L-arabinose"}
    parts: list[tuple[str, str, str, dict[str, str]]] = [
        (
            "insulator",
            deterministic_dna(f"{mode}:{channel}:insulator", 48),
            "misc_feature",
            {"design_status": "synthetic placeholder"},
        ),
        (
            "drug_sensor_promoter",
            deterministic_dna(f"{mode}:{channel}:sensor", 80),
            "regulatory",
            {
                "regulatory_class": "promoter",
                "sensor": sensor_names[channel],
                "design_status": "synthetic placeholder; logic only",
            },
        ),
        (
            "state_gate",
            deterministic_dna(f"{mode}:{channel}:state-gate", 64),
            "regulatory",
            {
                "regulatory_class": "operator",
                "required_state": (
                    {"A": "0", "B": "1", "C": "2"}[channel]
                    if mode == "forward"
                    else {"C": "3", "B": "2", "A": "1"}[channel]
                ),
                "design_status": "unresolved synthetic placeholder",
            },
        ),
        (
            "rbs_integrase",
            deterministic_dna(f"{mode}:{channel}:rbs-int", 24),
            "regulatory",
            {"regulatory_class": "ribosome_binding_site", "design_status": "synthetic placeholder"},
        ),
        (
            "integrase",
            integrase[0],
            "CDS",
            {
                "translation": integrase[1],
                "channel": channel,
                "expression_status": "native phage CDS; not codon-adapted",
            },
        ),
    ]
    if rdf is not None:
        parts.extend(
            [
                (
                    "rbs_rdf",
                    deterministic_dna(f"{mode}:{channel}:rbs-rdf", 24),
                    "regulatory",
                    {
                        "regulatory_class": "ribosome_binding_site",
                        "design_status": "synthetic placeholder",
                    },
                ),
                (
                    "rdf",
                    rdf[0],
                    "CDS",
                    {
                        "translation": rdf[1],
                        "channel": channel,
                        "expression_status": "native phage CDS; not codon-adapted",
                    },
                ),
            ]
        )
    parts.append(
        (
            "terminator",
            deterministic_dna(f"{mode}:{channel}:terminator", 72),
            "regulatory",
            {"regulatory_class": "terminator", "design_status": "synthetic placeholder"},
        )
    )
    sequence = ""
    annotations: list[dict[str, object]] = []
    for name, part_sequence, part_type, qualifiers in parts:
        start = len(sequence)
        sequence += part_sequence
        annotations.append(
            {
                "start": start,
                "end": len(sequence),
                "type": part_type,
                "label": f"{mode}_{channel}_{name}",
                "qualifiers": qualifiers,
            }
        )
    return sequence, annotations


def build_controller(
    mode: str,
    channels_config: dict[str, object],
) -> tuple[SeqRecord, list[dict[str, object]]]:
    """Build one circular pACYC177-derived development controller."""
    backbone = SeqIO.read(RETRIEVED / "X06402.1.gb", "genbank")
    sequence = str(backbone.seq).upper()
    annotations: list[dict[str, object]] = []
    provenance: list[dict[str, object]] = []
    for channel, item in channels_config["channels"].items():
        int_cfg = item["integrase"]
        int_nt, int_aa, int_provenance = extract_native_cds(
            int_cfg["accession"], int_cfg["protein_id"]
        )
        rdf_data = None
        rdf_cfg = item["rdf"]
        rdf_nt, rdf_aa, rdf_provenance = extract_native_cds(
            rdf_cfg["accession"], rdf_cfg["protein_id"]
        )
        if mode == "reverse":
            rdf_data = (rdf_nt, rdf_aa)
        cassette, cassette_features = expression_cassette(channel, mode, (int_nt, int_aa), rdf_data)
        offset = len(sequence)
        sequence += cassette
        for item_feature in cassette_features:
            shifted = deepcopy(item_feature)
            shifted["start"] += offset
            shifted["end"] += offset
            annotations.append(shifted)
        provenance.extend([int_provenance, rdf_provenance])
    record = SeqRecord(
        Seq(sequence),
        id=f"SRV1_{mode}_controller",
        name=f"{mode}_controller"[:16],
        description=f"Sequential rearrangement {mode} development controller",
    )
    record.annotations["topology"] = "circular"
    record.annotations["organism"] = "synthetic construct for Escherichia coli K-12"
    record.features.append(
        source_feature(
            len(record),
            "circular",
            "development prototype; state-gate sequences unresolved",
        )
    )
    for old_feature in backbone.features:
        if old_feature.type == "source":
            continue
        copied = deepcopy(old_feature)
        copied.qualifiers.setdefault("provenance", ["X06402.1 pACYC177"])
        record.features.append(copied)
    for item in annotations:
        qualifiers = item["qualifiers"]
        record.features.append(
            feature(
                item["start"],
                item["end"],
                item["type"],
                item["label"],
                **qualifiers,
            )
        )
    record.annotations["comment"] = (
        f"pACYC177 source sequence X06402.1 plus three {mode} cassettes. "
        f"Source proteins: {json.dumps(provenance, sort_keys=True)}"
    )
    return prepare_record(record, "controller prototype; not synthesis-ready"), provenance


def export_model_inputs(
    channels_config: dict[str, object],
    forward: SeqRecord,
    reverse: SeqRecord,
) -> None:
    """Export hashed, decision-scoped ESM-2 and ViennaRNA input manifests."""
    MODEL_INPUTS.mkdir(parents=True, exist_ok=True)
    protein_labels: list[str] = []
    proteins: list[str] = []
    for channel, item in channels_config["channels"].items():
        for role in ("integrase", "rdf"):
            cfg = item[role]
            _, amino_acid, _ = extract_native_cds(cfg["accession"], cfg["protein_id"])
            protein_labels.append(f"{channel}_{role}_{cfg['protein_id']}")
            proteins.append(amino_acid)
    esm_payload = {
        "decision": "prioritize biochemical diversity and informative crosstalk controls",
        "change_threshold": "review any near-redundant channel; never infer orthogonality",
        "tool": "esm2-embedding",
        "checkpoint": "esm2_t48_15B_UR50D",
        "seed": 0,
        "labels": protein_labels,
        "sequences": proteins,
        "input_hashes": [hashlib.sha256(sequence.encode()).hexdigest() for sequence in proteins],
    }
    (MODEL_INPUTS / "esm2_input.json").write_text(
        json.dumps(esm_payload, indent=2, sort_keys=True) + "\n"
    )

    rbs_labels: list[str] = []
    rbs_windows: list[str] = []
    for record in (forward, reverse):
        for item in record.features:
            label = item.qualifiers.get("label", [""])[0]
            if "_rbs_" not in label:
                continue
            start = int(item.location.start)
            end = min(len(record), int(item.location.end) + 180)
            rbs_labels.append(label)
            rbs_windows.append(str(record.seq[start:end]))
    vienna_payload = {
        "decision": "flag unusually stable structures around translation-initiation regions",
        "change_threshold": "extreme MFE outliers trigger RBS/spacer redesign, not efficacy claims",
        "tool": "viennarna-prediction",
        "version": "workspace deployment",
        "temperature_c": 37,
        "seed": 0,
        "labels": rbs_labels,
        "sequences": rbs_windows,
        "input_hashes": [hashlib.sha256(sequence.encode()).hexdigest() for sequence in rbs_windows],
    }
    (MODEL_INPUTS / "viennarna_input.json").write_text(
        json.dumps(vienna_payload, indent=2, sort_keys=True) + "\n"
    )


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a homogeneous row set as TSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True)
                    if isinstance(value, dict | list | tuple)
                    else value
                    for key, value in row.items()
                }
            )


def build_parts_registry(
    definitions: dict[str, object],
    channels_config: dict[str, object],
    states: list[Molecule],
) -> None:
    """Write exact provenance for biological and synthetic parts."""
    rows: list[dict[str, object]] = []
    for channel, definition in definitions.items():
        item = channels_config["channels"][channel]
        for role in ("integrase", "rdf"):
            cfg = item[role]
            nucleotide, amino_acid, provenance = extract_native_cds(
                cfg["accession"], cfg["protein_id"]
            )
            rows.append(
                {
                    "internal_part_id": f"{channel}_{role}",
                    "construct_role": role,
                    "feature_role": f"Channel {channel} {role}",
                    "organism_of_origin": item["system"],
                    "authoritative_record": str(RETRIEVED / f"{cfg['accession']}.gb"),
                    "accession_version": cfg["accession"],
                    "coordinates_0_based": provenance["coordinates_0_based"],
                    "strand": provenance["strand"],
                    "nucleotide_sequence": nucleotide,
                    "amino_acid_sequence": amino_acid,
                    "literature_citation": item["evidence"],
                    "sequence_class": "native",
                    "modifications": "none",
                    "confidence": "high sequence provenance",
                    "unresolved_concerns": "E. coli expression and cross-channel activity untested",
                }
            )
        for site_class, site_sequence in (
            ("attB", definition.att_b),
            ("attP", definition.att_p),
            ("attL", definition.sequence_for(SiteClass.L)),
            ("attR", definition.sequence_for(SiteClass.R)),
        ):
            rows.append(
                {
                    "internal_part_id": f"{channel}_{site_class}",
                    "construct_role": "message_register",
                    "feature_role": f"Channel {channel} {site_class}",
                    "organism_of_origin": item["system"],
                    "authoritative_record": item["sites"]["source"],
                    "accession_version": "FlyBase stable tool ID",
                    "coordinates_0_based": "not applicable",
                    "strand": "design-dependent",
                    "nucleotide_sequence": site_sequence,
                    "amino_acid_sequence": "",
                    "literature_citation": item["sites"]["source"],
                    "sequence_class": "curated native-derived attachment site",
                    "modifications": "none",
                    "confidence": "high sequence identity; context portability untested",
                    "unresolved_concerns": "orthogonality and exact activity require measurement",
                }
            )
    initial = states[0]
    for element in initial.elements:
        if element.kind == "payload":
            rows.append(
                {
                    "internal_part_id": f"payload_{element.identity}",
                    "construct_role": "message_register",
                    "feature_role": "neutral barcode",
                    "organism_of_origin": "synthetic",
                    "authoritative_record": "generated by deterministic SHA-256 fixture algorithm",
                    "accession_version": "design_v1",
                    "coordinates_0_based": initial.element_offsets()[element.identity],
                    "strand": element.orientation,
                    "nucleotide_sequence": element.canonical_sequence,
                    "amino_acid_sequence": "",
                    "literature_citation": "",
                    "sequence_class": "synthetic",
                    "modifications": "none",
                    "confidence": "computational sequence identity only",
                    "unresolved_concerns": "not experimentally tested",
                }
            )
    write_tsv(ROOT / "parts_registry.tsv", rows)


def build() -> dict[str, object]:
    """Run the complete deterministic build."""
    for path in (SEQUENCES, STATES, REPORTS, TOPOLOGY_OUTPUTS, CANDIDATES):
        path.mkdir(parents=True, exist_ok=True)
    definitions = load_pair_definitions(ROOT / "configs" / "channels.yaml")
    channels_config = yaml.safe_load((ROOT / "configs" / "channels.yaml").read_text())
    payloads, front = selected_payloads()
    states, events = run_round_trip(definitions, payloads)
    export_pareto(REPORTS / "candidate_pareto_front.csv", front)
    all_candidates = generate_candidates()
    rejected = [candidate for candidate in all_candidates if candidate not in front]
    write_tsv(
        CANDIDATES / "rejected_candidate_metadata.tsv",
        [
            {
                "candidate_id": item.candidate_id,
                "seed": item.seed,
                "gc_deviation": item.gc_deviation,
                "homopolymer_max": item.homopolymer_max,
                "repeated_12mers": item.repeated_12mers,
                "cross_payload_12mer_collisions": item.cross_payload_12mer_collisions,
                "reverse_complement_collisions": item.reverse_complement_collisions,
                "rejection_reason": "Pareto-dominated; no hard-constraint failure implied",
            }
            for item in rejected
        ],
    )
    front_sorted = sorted(
        front,
        key=lambda item: (
            item.reverse_complement_collisions,
            item.cross_payload_12mer_collisions,
            item.homopolymer_max,
            item.repeated_12mers,
            item.gc_deviation,
            item.candidate_id,
        ),
    )
    for index, candidate in enumerate(front_sorted[:3], start=1):
        candidate_molecule = build_initial_register(definitions, candidate.payloads)
        candidate_record = molecule_to_record(candidate_molecule)
        candidate_record.id = f"SRV1_candidate_{index}"
        candidate_record.description = (
            f"Pareto payload candidate {candidate.candidate_id}; same frozen topology"
        )
        write_record(
            candidate_record,
            CANDIDATES / f"pareto_{index}_{candidate.candidate_id}.gb",
            CANDIDATES / f"pareto_{index}_{candidate.candidate_id}.fasta",
        )

    state_paths = []
    for state in states:
        record = molecule_to_record(state)
        gb = STATES / f"{state.name}.gb"
        fasta = STATES / f"{state.name}.fasta"
        write_record(record, gb, fasta)
        state_paths.extend([str(gb.relative_to(ROOT)), str(fasta.relative_to(ROOT))])
    message_record = molecule_to_record(states[0])
    write_record(
        message_record,
        SEQUENCES / "01_message_register.gb",
        SEQUENCES / "01_message_register.fasta",
    )
    forward, forward_provenance = build_controller("forward", channels_config)
    reverse, reverse_provenance = build_controller("reverse", channels_config)
    write_record(
        forward,
        SEQUENCES / "02_forward_controller.gb",
        SEQUENCES / "02_forward_controller.fasta",
    )
    write_record(
        reverse,
        SEQUENCES / "03_reverse_controller.gb",
        SEQUENCES / "03_reverse_controller.fasta",
    )
    export_model_inputs(channels_config, forward, reverse)
    build_parts_registry(definitions, channels_config, states)
    export_truth_table(REPORTS / "controller_truth_table.tsv")

    forward_orders = enumerate_orders(definitions, states[0], Chemistry.INTEGRASE)
    reverse_orders = enumerate_orders(definitions, states[3], Chemistry.INTEGRASE_RDF)
    all_pairs = [row for state in states for row in enumerate_cognate_pairs(state, definitions)]
    write_tsv(REPORTS / "unintended_pair_matrix.tsv", all_pairs)
    transition_rows = []
    for index, state in enumerate(states):
        transition_rows.append(
            {
                **state_summary(state),
                "incoming_event": asdict(events[index - 1]) if index else None,
                "exactly_restored": index == len(states) - 1
                and state.sequence == states[0].sequence,
            }
        )
    write_tsv(REPORTS / "state_transition_table.tsv", transition_rows)
    topology_results = {
        "states": [state_summary(state) for state in states],
        "events": [asdict(event) for event in events],
        "forward_orders": forward_orders,
        "reverse_orders": reverse_orders,
        "exact_round_trip": states[-1].sequence == states[0].sequence,
        "legacy_fixture": {
            "path": "../simulation_results.json",
            "role": "regression oracle only",
        },
    }
    (TOPOLOGY_OUTPUTS / "topology_results.json").write_text(
        json.dumps(topology_results, indent=2, default=str) + "\n"
    )
    selected_records = {
        "01_message_register": message_record,
        "02_forward_controller": forward,
        "03_reverse_controller": reverse,
        **{state.name: molecule_to_record(state) for state in states},
    }
    constraint_rows = run_all_constraints(states, definitions, selected_records)
    export_constraint_scores(REPORTS / "constraint_scores.csv", constraint_rows)
    hard_failures = [asdict(row) for row in constraint_rows if not row.passed]
    if hard_failures:
        (REPORTS / "hard_constraint_failures.json").write_text(
            json.dumps(hard_failures, indent=2) + "\n"
        )
        raise ValueError(f"{len(hard_failures)} hard-constraint checks failed")
    analyses = [analyze_record(record) for record in selected_records.values()]
    write_analysis(REPORTS / "conventional_sequence_analysis.json", analyses)
    host_sequence = (RETRIEVED / "NC_000913.3.fasta").read_text()
    host_queries = {
        f"{channel}_{site_class.value}": definition.sequence_for(site_class)
        for channel, definition in definitions.items()
        for site_class in (SiteClass.B, SiteClass.P, SiteClass.L, SiteClass.R)
    }
    host_scan = scan_host_exact(host_sequence, host_queries)
    (REPORTS / "host_exact_site_scan.json").write_text(
        json.dumps(host_scan, indent=2, sort_keys=True) + "\n"
    )
    export_model_runs(ROOT)
    manifest = {
        "primary_records": {
            path.name: {
                "length_bp": len(SeqIO.read(path, "genbank")),
                "sha256": sequence_sha256(SeqIO.read(path, "genbank")),
                "topology": SeqIO.read(path, "genbank").annotations["topology"],
                "features": len(SeqIO.read(path, "genbank").features),
            }
            for path in sorted(SEQUENCES.glob("*.gb"))
        },
        "state_records": state_paths,
        "exact_round_trip": topology_results["exact_round_trip"],
        "hard_constraints_passed": not hard_failures,
        "hard_constraint_checks": len(constraint_rows),
        "forward_provenance": forward_provenance,
        "reverse_provenance": reverse_provenance,
    }
    (ROOT / "artifacts" / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
