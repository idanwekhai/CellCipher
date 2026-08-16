"""GenBank/FASTA import, CDS, feature, model-schema, and reproducibility tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from Bio import SeqIO

from build_constructs import build
from export_genbank import validate_record
from run_model_scoring import validate_embedding_output

ROOT = Path(__file__).resolve().parents[1]


def all_genbank_paths() -> list[Path]:
    """Return primary and seven state record paths."""
    return sorted((ROOT / "sequences").glob("*.gb")) + sorted((ROOT / "states").glob("*.gb"))


def test_all_records_parse_and_match_fasta() -> None:
    """Every GenBank file round-trips to an equal FASTA sequence."""
    assert len(all_genbank_paths()) == 10
    for path in all_genbank_paths():
        record = SeqIO.read(path, "genbank")
        fasta = SeqIO.read(path.with_suffix(".fasta"), "fasta")
        assert str(record.seq) == str(fasta.seq)
        assert not validate_record(record)


def test_all_feature_locations_are_current() -> None:
    """No transformed feature retains stale or out-of-range coordinates."""
    for path in all_genbank_paths():
        record = SeqIO.read(path, "genbank")
        for item in record.features:
            assert 0 <= int(item.location.start) <= int(item.location.end) <= len(record)
            assert str(item.extract(record.seq))


def test_all_cds_retranslate() -> None:
    """Every controller CDS reproduces its annotated translation."""
    for path in (ROOT / "sequences").glob("*controller.gb"):
        record = SeqIO.read(path, "genbank")
        cds_features = [item for item in record.features if item.type == "CDS"]
        assert len(cds_features) == (3 if "forward" in path.name else 6)
        for item in cds_features:
            nucleotide = item.extract(record.seq)
            try:
                observed = str(nucleotide.translate(table=11, cds=True))
            except ValueError:
                observed = str(nucleotide.translate(table=11)).rstrip("*")
            assert observed == item.qualifiers["translation"][0]


def test_model_output_schema() -> None:
    """Valid embedding outputs pass and malformed outputs fail."""
    payload = {
        "results": [
            {"mean_embedding": [1.0, 0.0], "attention_mask": [1]},
            {"mean_embedding": [0.0, 1.0], "attention_mask": [1]},
        ]
    }
    validate_embedding_output(payload, 2)
    with pytest.raises(ValueError):
        validate_embedding_output({"results": [{"attention_mask": [1]}]}, 1)


def test_deterministic_reproducibility() -> None:
    """Two complete builds produce identical selected sequence hashes."""
    first = build()["primary_records"]
    second = build()["primary_records"]
    assert first == second
    manifest = json.loads((ROOT / "artifacts" / "build_manifest.json").read_text())
    for path in (ROOT / "sequences").glob("*.gb"):
        record = SeqIO.read(path, "genbank")
        expected = hashlib.sha256(str(record.seq).encode()).hexdigest()
        assert manifest["primary_records"][path.name]["sha256"] == expected
