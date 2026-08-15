"""Versioned binary packet format.

    magic(2) | version(1) | mode(1) | flags(1) | original_length(4)  -- header, 9 bytes
    payload(N)                                                        -- compressed or raw UTF-8
    crc32(4)                                                          -- over header + payload

The whole packet (header + payload + crc32) is what gets mapped to DNA by
`nucleotide.bytes_to_dna`. Keeping `version` and `mode` as separate one-byte
fields (rather than packing everything into one flags byte) is what lets this
format grow without breaking old decoders:

- `version` bumps only if the *header layout itself* changes.
- `mode` selects the encoding scheme applied to the payload before it became
  bytes -- today only MODE_DIGITAL_2BIT exists. A future constraint-aware
  scheme (homopolymer/GC-safe rotating code, chunked oligos with sequence
  numbers, Reed-Solomon, ...) is a new mode value with its own codec module;
  `decode()` can dispatch on it without touching this framing.
- `flags` is a bitfield for orthogonal per-payload choices, currently just
  "was this payload Brotli-compressed".
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

from biocrypt.codec.errors import (
    ChecksumMismatchError,
    InvalidPacketError,
    UnsupportedVersionError,
)

MAGIC = b"BC"
CURRENT_VERSION = 1
SUPPORTED_VERSIONS = {1}

# --- modes: what scheme encoded the payload ---------------------------------
MODE_DIGITAL_2BIT = 1
# MODE_SYNTHESIS_SAFE = 2  # reserved for a future homopolymer/GC-constrained codec

MODE_NAMES = {
    MODE_DIGITAL_2BIT: "digital-2bit",
}

# --- flags: orthogonal per-payload bits --------------------------------------
FLAG_NONE = 0
FLAG_COMPRESSED = 0b0000_0001

_HEADER_FORMAT = ">2sBBBI"  # magic, version, mode, flags, original_length
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)  # 9
_CRC_FORMAT = ">I"
_CRC_SIZE = struct.calcsize(_CRC_FORMAT)  # 4


@dataclass(frozen=True, slots=True)
class Packet:
    version: int
    mode: int
    flags: int
    original_length: int
    payload: bytes
    checksum: int  # CRC32 as stored/verified

    @property
    def compressed(self) -> bool:
        return bool(self.flags & FLAG_COMPRESSED)

    @property
    def mode_name(self) -> str:
        return MODE_NAMES.get(self.mode, f"unknown(0x{self.mode:02x})")


def pack(*, mode: int, flags: int, original_length: int, payload: bytes) -> bytes:
    """Build the full packet (header + payload + crc32) as raw bytes."""
    header = struct.pack(_HEADER_FORMAT, MAGIC, CURRENT_VERSION, mode, flags, original_length)
    body = header + payload
    checksum = zlib.crc32(body) & 0xFFFFFFFF
    return body + struct.pack(_CRC_FORMAT, checksum)


def unpack(data: bytes) -> Packet:
    """Parse and validate raw packet bytes. Raises InvalidPacketError,
    UnsupportedVersionError, or ChecksumMismatchError."""
    if len(data) < _HEADER_SIZE + _CRC_SIZE:
        raise InvalidPacketError(
            f"packet too short: got {len(data)} bytes, need at least "
            f"{_HEADER_SIZE + _CRC_SIZE}"
        )

    header = data[:_HEADER_SIZE]
    body, (stored_crc,) = data[:-_CRC_SIZE], struct.unpack(_CRC_FORMAT, data[-_CRC_SIZE:])
    payload = data[_HEADER_SIZE:-_CRC_SIZE]

    magic, version, mode, flags, original_length = struct.unpack(_HEADER_FORMAT, header)
    if magic != MAGIC:
        raise InvalidPacketError(
            f"bad magic bytes {magic!r} -- this DNA wasn't produced by biocrypt "
            "(or the header is corrupted)"
        )
    if version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(
            f"packet format version {version} is not supported by this build "
            f"(supported: {sorted(SUPPORTED_VERSIONS)})"
        )

    computed_crc = zlib.crc32(body) & 0xFFFFFFFF
    if computed_crc != stored_crc:
        raise ChecksumMismatchError(
            f"checksum mismatch: expected 0x{stored_crc:08x}, computed "
            f"0x{computed_crc:08x} -- the DNA was corrupted or truncated"
        )

    return Packet(
        version=version,
        mode=mode,
        flags=flags,
        original_length=original_length,
        payload=payload,
        checksum=stored_crc,
    )
