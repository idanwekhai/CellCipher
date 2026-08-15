"""Metrics describing one encode/decode, for the API response and UI."""

from __future__ import annotations

from dataclasses import dataclass

from biocrypt.codec import nucleotide


@dataclass(frozen=True, slots=True)
class CodecStats:
    version: int
    mode: str
    byte_count: int  # length of the original UTF-8 text, in bytes
    payload_byte_count: int  # length of the (possibly compressed) payload
    packet_byte_count: int  # full packet: header + payload + crc32
    compressed: bool
    compression_ratio: float  # byte_count / payload_byte_count
    dna_length: int  # nucleotide count
    gc_content_percent: float
    longest_homopolymer: int
    bits_per_base: float  # 8 * byte_count / dna_length -- effective density
    checksum_hex: str


def compute_stats(
    *,
    version: int,
    mode_name: str,
    byte_count: int,
    payload_byte_count: int,
    packet_byte_count: int,
    compressed: bool,
    dna: str,
    checksum: int,
) -> CodecStats:
    compression_ratio = byte_count / payload_byte_count if payload_byte_count else 1.0
    bits_per_base = (8 * byte_count / len(dna)) if dna else 0.0
    return CodecStats(
        version=version,
        mode=mode_name,
        byte_count=byte_count,
        payload_byte_count=payload_byte_count,
        packet_byte_count=packet_byte_count,
        compressed=compressed,
        compression_ratio=compression_ratio,
        dna_length=len(dna),
        gc_content_percent=nucleotide.gc_content(dna),
        longest_homopolymer=nucleotide.longest_homopolymer(dna),
        bits_per_base=bits_per_base,
        checksum_hex=f"{checksum:08x}",
    )
