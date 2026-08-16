"""Standards-compliant GenBank and FASTA export with round-trip validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from Bio import SeqIO
from Bio.Data.CodonTable import TranslationError
from Bio.SeqFeature import CompoundLocation, SeqFeature
from Bio.SeqRecord import SeqRecord


class GenBankValidationError(ValueError):
    """Raised when a generated sequence record fails round-trip validation."""


def sequence_sha256(record: SeqRecord) -> str:
    """Return the SHA-256 of a record sequence."""
    return hashlib.sha256(str(record.seq).upper().encode()).hexdigest()


def prepare_record(record: SeqRecord, design_status: str) -> SeqRecord:
    """Add required record-level metadata before export."""
    record.annotations["molecule_type"] = "DNA"
    record.annotations.setdefault("topology", "linear")
    record.annotations.setdefault("organism", "Escherichia coli K-12 candidate construct")
    record.annotations["structured_comment"] = {
        "Design-Data": {
            "Project-Version": "1.0.0-candidate",
            "Design-Status": design_status,
            "Sequence-SHA256": sequence_sha256(record),
            "Host-Context": "non-pathogenic Escherichia coli K-12",
            "Provenance": "see parts_registry.tsv and retrieval_manifest.json",
        }
    }
    standard_comment = (
        "Computational proof-of-concept only. Regulatory placeholders are not "
        "synthesis-ready and no in-cell performance is claimed."
    )
    existing = record.annotations.get("comment", "")
    record.annotations["comment"] = (
        f"{existing}\n{standard_comment}" if existing else standard_comment
    )
    return record


def _location_parts(feature: SeqFeature) -> list[object]:
    if isinstance(feature.location, CompoundLocation):
        return list(feature.location.parts)
    return [feature.location]


def validate_record(record: SeqRecord) -> list[str]:
    """Validate coordinates, CDS translations, and required annotations."""
    errors: list[str] = []
    length = len(record)
    for key in ("molecule_type", "topology", "organism"):
        if key not in record.annotations:
            errors.append(f"missing record annotation: {key}")
    if set(str(record.seq).upper()) - set("ACGT"):
        errors.append("record contains ambiguous or non-DNA symbols")
    for feature in record.features:
        if feature.location is None:
            errors.append(f"{feature.type} has no location")
            continue
        for part in _location_parts(feature):
            start, end = int(part.start), int(part.end)
            if not (0 <= start <= end <= length):
                errors.append(
                    f"{feature.type} location {start}:{end} exceeds record length {length}"
                )
        if feature.type == "CDS":
            nucleotide = feature.extract(record.seq)
            if len(nucleotide) % 3:
                errors.append(f"CDS {feature.qualifiers.get('label')} is out of frame")
                continue
            try:
                translation = str(nucleotide.translate(table=11, cds=True))
            except (ValueError, TranslationError):
                translation = str(nucleotide.translate(table=11, to_stop=False)).rstrip("*")
            if "*" in translation:
                errors.append(f"CDS {feature.qualifiers.get('label')} has an internal stop")
            expected = feature.qualifiers.get("translation", [translation])[0].rstrip("*")
            if translation != expected:
                errors.append(f"CDS {feature.qualifiers.get('label')} translation mismatch")
    return errors


def write_record(record: SeqRecord, genbank_path: Path, fasta_path: Path) -> None:
    """Write, parse back, and verify one GenBank/FASTA record."""
    genbank_path.parent.mkdir(parents=True, exist_ok=True)
    fasta_path.parent.mkdir(parents=True, exist_ok=True)
    errors = validate_record(record)
    if errors:
        raise GenBankValidationError("; ".join(errors))
    SeqIO.write(record, genbank_path, "genbank")
    SeqIO.write(record, fasta_path, "fasta")
    parsed = SeqIO.read(genbank_path, "genbank")
    parsed_fasta = SeqIO.read(fasta_path, "fasta")
    if str(parsed.seq) != str(record.seq) or str(parsed_fasta.seq) != str(record.seq):
        raise GenBankValidationError(f"Sequence changed during export: {record.id}")
    if len(parsed.features) != len(record.features):
        raise GenBankValidationError(f"Feature count changed during export: {record.id}")
    errors = validate_record(parsed)
    if errors:
        raise GenBankValidationError("; ".join(errors))
