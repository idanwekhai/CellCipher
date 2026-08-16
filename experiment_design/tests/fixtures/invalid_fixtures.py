"""Deliberately invalid designs used to verify rejection paths."""

from __future__ import annotations

from copy import deepcopy

from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, SeqFeature
from Bio.SeqRecord import SeqRecord

from topology import Molecule, PairDefinition, build_initial_register


def wrong_site_orientation(
    definitions: dict[str, PairDefinition],
) -> Molecule:
    """Return State 0 with Channel A converted to a deletion substrate."""
    molecule = build_initial_register(definitions)
    for element in molecule.elements:
        if element.identity == "S5":
            element.orientation = 1
    return molecule


def corrupted_att_core(
    definitions: dict[str, PairDefinition],
) -> Molecule:
    """Return a register with one changed crossover base."""
    molecule = build_initial_register(definitions)
    site = next(element for element in molecule.elements if element.identity == "S1")
    site.canonical_sequence = (
        site.canonical_sequence[: definitions["A"].b_core_index]
        + "A"
        + site.canonical_sequence[definitions["A"].b_core_index + 1 :]
    )
    return molecule


def duplicated_cognate_site(
    definitions: dict[str, PairDefinition],
) -> Molecule:
    """Return a register containing a third Channel B site."""
    molecule = build_initial_register(definitions)
    duplicate = deepcopy(next(item for item in molecule.elements if item.identity == "S2"))
    duplicate.identity = "S2_duplicate"
    molecule.elements.insert(4, duplicate)
    return molecule


def broken_cds_record() -> SeqRecord:
    """Return a record with an internal stop in the annotated CDS."""
    record = SeqRecord(Seq("ATGAAATAATTTTAA"), id="broken_cds")
    record.annotations.update(
        {"molecule_type": "DNA", "topology": "linear", "organism": "synthetic construct"}
    )
    record.features.append(
        SeqFeature(
            FeatureLocation(0, 15, strand=1),
            type="CDS",
            qualifiers={"label": ["broken"], "translation": ["MKF"]},
        )
    )
    return record


def incorrect_feature_location_record() -> SeqRecord:
    """Return a record with a feature extending beyond the molecule."""
    record = SeqRecord(Seq("ACGT"), id="bad_location")
    record.annotations.update(
        {"molecule_type": "DNA", "topology": "linear", "organism": "synthetic construct"}
    )
    record.features.append(SeqFeature(FeatureLocation(0, 8), type="misc_feature"))
    return record
