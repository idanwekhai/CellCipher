"""Reproducible multi-objective search over neutral payload barcodes only."""

from __future__ import annotations

import csv
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from Bio.Seq import Seq

from validate_sequences import gc_fraction, longest_homopolymer, repeated_kmers

BASES = "ACGT"
SEEDS = (11, 23, 47)


@dataclass(frozen=True)
class Candidate:
    """One six-payload candidate and independent objective axes."""

    candidate_id: str
    seed: int
    payloads: dict[str, str]
    gc_deviation: float
    homopolymer_max: int
    repeated_12mers: int
    cross_payload_12mer_collisions: int
    reverse_complement_collisions: int


def candidate_metrics(payloads: dict[str, str], seed: int, index: int) -> Candidate:
    """Calculate independent objectives without a composite score."""
    all_sequence = "".join(payloads.values())
    kmers: dict[str, set[str]] = {}
    for name, sequence in payloads.items():
        kmers[name] = {sequence[i : i + 12] for i in range(len(sequence) - 11)}
    collisions = sum(
        len(kmers[left] & kmers[right])
        for i, left in enumerate(payloads)
        for right in list(payloads)[i + 1 :]
    )
    rc_collisions = sum(
        1
        for left in payloads.values()
        for right in payloads.values()
        if left in str(Seq(right).reverse_complement())
    )
    digest = hashlib.sha256(all_sequence.encode()).hexdigest()[:12]
    return Candidate(
        candidate_id=f"payload_{seed}_{index}_{digest}",
        seed=seed,
        payloads=payloads,
        gc_deviation=abs(gc_fraction(all_sequence) - 0.5),
        homopolymer_max=max(longest_homopolymer(sequence)[1] for sequence in payloads.values()),
        repeated_12mers=len(repeated_kmers(all_sequence, 12)),
        cross_payload_12mer_collisions=collisions,
        reverse_complement_collisions=rc_collisions,
    )


def generate_candidates(per_seed: int = 30, length: int = 96) -> list[Candidate]:
    """Generate deterministic neutral barcode candidates with multiple seeds."""
    output = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for index in range(per_seed):
            payloads = {
                name: "".join(rng.choice(BASES) for _ in range(length)) for name in "ABCDEF"
            }
            output.append(candidate_metrics(payloads, seed, index))
    return output


def dominates(left: Candidate, right: Candidate) -> bool:
    """Return whether left Pareto-dominates right."""
    left_values = (
        left.gc_deviation,
        left.homopolymer_max,
        left.repeated_12mers,
        left.cross_payload_12mer_collisions,
        left.reverse_complement_collisions,
    )
    right_values = (
        right.gc_deviation,
        right.homopolymer_max,
        right.repeated_12mers,
        right.cross_payload_12mer_collisions,
        right.reverse_complement_collisions,
    )
    return all(a <= b for a, b in zip(left_values, right_values, strict=False)) and any(
        a < b for a, b in zip(left_values, right_values, strict=False)
    )


def pareto_front(candidates: list[Candidate]) -> list[Candidate]:
    """Return the diverse nondominated candidate set."""
    return [
        candidate
        for candidate in candidates
        if not any(dominates(other, candidate) for other in candidates if other != candidate)
    ]


def selected_payloads() -> tuple[dict[str, str], list[Candidate]]:
    """Return a deterministic safety-first Pareto selection."""
    front = pareto_front(generate_candidates())
    selected = min(
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
    return selected.payloads, front


def export_pareto(path: Path, front: list[Candidate]) -> None:
    """Write the Pareto front without collapsing objectives."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidate_id",
        "seed",
        "gc_deviation",
        "homopolymer_max",
        "repeated_12mers",
        "cross_payload_12mer_collisions",
        "reverse_complement_collisions",
        "payload_hashes",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in front:
            writer.writerow(
                {
                    **{field: getattr(item, field) for field in fields[:-1]},
                    "payload_hashes": ";".join(
                        f"{name}:{hashlib.sha256(sequence.encode()).hexdigest()}"
                        for name, sequence in item.payloads.items()
                    ),
                }
            )
