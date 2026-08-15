"""Direct 2-bit <-> nucleotide mapping.

    00 -> A   01 -> C   10 -> G   11 -> T

Each byte becomes exactly 4 bases, most-significant bit-pair first, e.g.
"A" (0x41 = 0b01000001) -> pairs 01,00,00,01 -> C,A,A,C -> "CAAC".

This module knows nothing about packets, compression, or text — it only
converts between raw bytes and a DNA string over {A, C, G, T}. That keeps it
reusable if a future constrained/synthesis-safe mode wants a different
bytes<->bases mapping while everything above it (packet framing, checksums)
stays the same.
"""

from __future__ import annotations

from biocrypt.codec.errors import InvalidDNAError

BASES = "ACGT"
_BASE_TO_BITS = {base: bits for bits, base in enumerate(BASES)}
_BITS_TO_BASE = BASES

BITS_PER_BASE = 2
BASES_PER_BYTE = 8 // BITS_PER_BASE  # 4


def bytes_to_dna(data: bytes) -> str:
    """Encode raw bytes as a DNA string, 4 bases per byte."""
    bases: list[str] = []
    for byte in data:
        bases.append(_BITS_TO_BASE[(byte >> 6) & 0b11])
        bases.append(_BITS_TO_BASE[(byte >> 4) & 0b11])
        bases.append(_BITS_TO_BASE[(byte >> 2) & 0b11])
        bases.append(_BITS_TO_BASE[byte & 0b11])
    return "".join(bases)


def dna_to_bytes(dna: str) -> bytes:
    """Decode a DNA string back to raw bytes.

    Raises InvalidDNAError if `dna` contains anything outside A/C/G/T
    (case-insensitive) or its length isn't a multiple of 4. Ambiguity codes
    such as 'N' are deliberately rejected here rather than silently dropped
    or guessed — only DNA this codec produced can round-trip.
    """
    dna = dna.strip().upper()
    if not dna:
        return b""

    bad = sorted(set(dna) - set(BASES))
    if bad:
        raise InvalidDNAError(
            f"DNA contains characters outside A/C/G/T: {', '.join(bad)}"
        )
    if len(dna) % BASES_PER_BYTE != 0:
        raise InvalidDNAError(
            f"DNA length ({len(dna)}) must be a multiple of {BASES_PER_BYTE} "
            "bases per byte"
        )

    out = bytearray(len(dna) // BASES_PER_BYTE)
    for i in range(0, len(dna), BASES_PER_BYTE):
        byte = 0
        for base in dna[i : i + BASES_PER_BYTE]:
            byte = (byte << 2) | _BASE_TO_BITS[base]
        out[i // BASES_PER_BYTE] = byte
    return bytes(out)


def gc_content(dna: str) -> float:
    """Percentage of bases that are G or C (a key metric for physical DNA
    stability; direct 2-bit encoding has no control over it, which is the
    documented limitation this format's `mode` field leaves room to fix)."""
    if not dna:
        return 0.0
    gc = sum(1 for base in dna if base in "GC")
    return 100.0 * gc / len(dna)


def longest_homopolymer(dna: str) -> int:
    """Length of the longest run of a single repeated base."""
    if not dna:
        return 0
    longest = current = 1
    for prev, curr in zip(dna, dna[1:]):
        current = current + 1 if curr == prev else 1
        longest = max(longest, current)
    return longest
