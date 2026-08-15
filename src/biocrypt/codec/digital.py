"""Digital mode: the MVP pipeline.

    text -> UTF-8 -> (optionally Brotli-compress) -> versioned packet -> DNA

Whichever of {raw, compressed} payload is smaller is kept, and a flag bit
records which one it was so decode() doesn't need to guess. This is
"approach 1 + approach 2" from the design doc, unified behind one mode byte
(MODE_DIGITAL_2BIT) since compression is just a payload transform, not a
different bytes<->DNA mapping.

Nothing here is aware of biological synthesis constraints (homopolymers, GC
content, chunking). That's intentional: a future MODE_SYNTHESIS_SAFE gets its
own module and its own branch in decode()'s mode dispatch, without changing
this one or the packet format.
"""

from __future__ import annotations

from dataclasses import dataclass

from biocrypt.codec import compression, nucleotide, packet, stats
from biocrypt.codec.errors import (
    PayloadLengthMismatchError,
    TextDecodeError,
    UnsupportedModeError,
)


@dataclass(frozen=True, slots=True)
class EncodeResult:
    dna: str
    stats: stats.CodecStats


@dataclass(frozen=True, slots=True)
class DecodeResult:
    text: str
    stats: stats.CodecStats


def encode(text: str) -> EncodeResult:
    """Encode `text` to a DNA string using digital mode.

    Tries both the raw and Brotli-compressed payload and keeps whichever
    produces the shorter DNA sequence -- for short strings, compression
    overhead usually loses to raw.
    """
    raw = text.encode("utf-8")
    compressed_payload = compression.compress(raw) if raw else b""

    use_compression = bool(raw) and len(compressed_payload) < len(raw)
    payload = compressed_payload if use_compression else raw
    flags = packet.FLAG_COMPRESSED if use_compression else packet.FLAG_NONE

    packet_bytes = packet.pack(
        mode=packet.MODE_DIGITAL_2BIT,
        flags=flags,
        original_length=len(raw),
        payload=payload,
    )
    dna = nucleotide.bytes_to_dna(packet_bytes)
    checksum = int.from_bytes(packet_bytes[-4:], "big")

    result_stats = stats.compute_stats(
        version=packet.CURRENT_VERSION,
        mode_name=packet.MODE_NAMES[packet.MODE_DIGITAL_2BIT],
        byte_count=len(raw),
        payload_byte_count=len(payload),
        packet_byte_count=len(packet_bytes),
        compressed=use_compression,
        dna=dna,
        checksum=checksum,
    )
    return EncodeResult(dna=dna, stats=result_stats)


def decode(dna: str) -> DecodeResult:
    """Decode a DNA string produced by `encode()` back to text.

    Raises (see codec.errors): InvalidDNAError for a bad alphabet/length,
    InvalidPacketError/UnsupportedVersionError/ChecksumMismatchError from
    packet parsing, UnsupportedModeError if the packet uses a mode this
    build doesn't implement, PayloadLengthMismatchError or TextDecodeError
    if the recovered bytes aren't the text they claim to be.
    """
    packet_bytes = nucleotide.dna_to_bytes(dna)
    pkt = packet.unpack(packet_bytes)

    if pkt.mode != packet.MODE_DIGITAL_2BIT:
        raise UnsupportedModeError(
            f"packet uses mode '{pkt.mode_name}', which this build cannot decode "
            "(only digital-2bit is implemented)"
        )

    payload = compression.decompress(pkt.payload) if pkt.compressed else pkt.payload
    if len(payload) != pkt.original_length:
        raise PayloadLengthMismatchError(
            f"expected {pkt.original_length} bytes of decoded payload, got {len(payload)}"
        )

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TextDecodeError(f"payload is not valid UTF-8: {exc}") from exc

    result_stats = stats.compute_stats(
        version=pkt.version,
        mode_name=pkt.mode_name,
        byte_count=pkt.original_length,
        payload_byte_count=len(pkt.payload),
        packet_byte_count=len(packet_bytes),
        compressed=pkt.compressed,
        dna=dna.strip().upper(),
        checksum=pkt.checksum,
    )
    return DecodeResult(text=text, stats=result_stats)
