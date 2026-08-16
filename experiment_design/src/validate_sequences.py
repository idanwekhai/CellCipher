"""Deterministic sequence-hazard and provenance analyses."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

STOP_CODONS = {"TAA", "TAG", "TGA"}
RESTRICTION_SITES = {
    "EcoRI": "GAATTC",
    "BamHI": "GGATCC",
    "HindIII": "AAGCTT",
    "BsaI": "GGTCTC",
    "BsmBI": "CGTCTC",
}


@dataclass(frozen=True)
class ORF:
    """One predicted ORF on either DNA strand."""

    strand: int
    frame: int
    start: int
    end: int
    amino_acids: int


def gc_fraction(sequence: str) -> float:
    """Return GC fraction for a DNA sequence."""
    return (sequence.count("G") + sequence.count("C")) / len(sequence) if sequence else 0.0


def longest_homopolymer(sequence: str) -> tuple[str, int]:
    """Return the base and length of the longest homopolymer."""
    matches = re.findall(r"(A+|C+|G+|T+)", sequence)
    longest = max(matches, key=len, default="")
    return (longest[:1], len(longest))


def repeated_kmers(sequence: str, k: int = 16) -> dict[str, int]:
    """Return repeated exact k-mers, excluding reverse-complement deduplication."""
    counts = Counter(sequence[index : index + k] for index in range(len(sequence) - k + 1))
    return {kmer: count for kmer, count in counts.items() if count > 1}


def local_gc_extrema(sequence: str, window: int = 50) -> tuple[float, float]:
    """Return minimum and maximum sliding-window GC fractions."""
    if len(sequence) <= window:
        value = gc_fraction(sequence)
        return value, value
    values = [
        gc_fraction(sequence[index : index + window]) for index in range(len(sequence) - window + 1)
    ]
    return min(values), max(values)


def find_orfs(sequence: str, minimum_amino_acids: int = 30) -> list[ORF]:
    """Find simple ATG-to-stop ORFs on both strands."""
    output: list[ORF] = []
    for strand, strand_sequence in (
        (1, sequence),
        (-1, str(Seq(sequence).reverse_complement())),
    ):
        for frame in range(3):
            start: int | None = None
            for position in range(frame, len(strand_sequence) - 2, 3):
                codon = strand_sequence[position : position + 3]
                if start is None and codon == "ATG":
                    start = position
                elif start is not None and codon in STOP_CODONS:
                    length = (position + 3 - start) // 3 - 1
                    if length >= minimum_amino_acids:
                        output.append(ORF(strand, frame, start, position + 3, length))
                    start = None
    return output


def circular_count(sequence: str, query: str, circular: bool) -> int:
    """Count exact query starts on one strand."""
    if not query or len(query) > len(sequence):
        return 0
    search = sequence + sequence[: len(query) - 1] if circular else sequence
    limit = len(sequence) if circular else len(sequence) - len(query) + 1
    return sum(search.startswith(query, index) for index in range(limit))


def analyze_record(record: SeqRecord) -> dict[str, object]:
    """Analyze GC, repeats, motifs, both-strand ORFs, and composition."""
    sequence = str(record.seq).upper()
    circular = record.annotations.get("topology") == "circular"
    minimum_gc, maximum_gc = local_gc_extrema(sequence)
    base, run = longest_homopolymer(sequence)
    coding_bp = sum(
        int(item.location.end) - int(item.location.start)
        for item in record.features
        if item.type == "CDS"
    )
    repeats = repeated_kmers(sequence)
    reverse_sequence = str(Seq(sequence).reverse_complement())
    promoter_proxy = sum(
        sequence.count(motif) + reverse_sequence.count(motif) for motif in ("TTGACA", "TATAAT")
    )
    poly_t = sum(1 for motif in re.findall(r"T{6,}", sequence) + re.findall(r"A{6,}", sequence))
    return {
        "record_id": record.id,
        "length_bp": len(sequence),
        "topology": record.annotations.get("topology"),
        "feature_count": len(record.features),
        "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        "gc_fraction": gc_fraction(sequence),
        "local_gc_min_50bp": minimum_gc,
        "local_gc_max_50bp": maximum_gc,
        "coding_bp": coding_bp,
        "noncoding_bp": len(sequence) - coding_bp,
        "longest_homopolymer_base": base,
        "longest_homopolymer_length": run,
        "repeated_16mers": len(repeats),
        "max_16mer_count": max(repeats.values(), default=1),
        "restriction_site_counts": {
            name: circular_count(sequence, motif, circular)
            + circular_count(sequence, str(Seq(motif).reverse_complement()), circular)
            for name, motif in RESTRICTION_SITES.items()
        },
        "both_strand_orfs_30aa": [asdict(orf) for orf in find_orfs(sequence)],
        "sigma70_proxy_motif_count_both_strands": promoter_proxy,
        "poly_t_or_poly_a_terminator_proxy_count": poly_t,
        "ambiguity_symbols": sorted(set(sequence) - set("ACGT")),
    }


def scan_host_exact(host_sequence: str, queries: dict[str, str]) -> dict[str, dict[str, int]]:
    """Count exact site matches on both host-genome strands."""
    host = "".join(host_sequence.split()).upper()
    return {
        name: {
            "forward": host.count(query),
            "reverse_complement": host.count(str(Seq(query).reverse_complement())),
        }
        for name, query in queries.items()
    }


def write_analysis(path: Path, analyses: list[dict[str, object]]) -> None:
    """Write deterministic conventional analysis output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(analyses, indent=2, sort_keys=True) + "\n")
