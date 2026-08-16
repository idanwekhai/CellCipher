"""Keyed block-transposition layer.

Reorders a DNA string in fixed-size blocks (4 bytes = 16 bases each, per
BLOCK_BYTES) using a permutation derived from a passphrase and, optionally,
a per-message nonce. The result is unreadable without the passphrase.

Be honest about what this is: a *transposition cipher*, not encryption in
the strong sense. It preserves the exact multiset of block contents (only
their order changes), and for short messages the number of possible
orderings (N!) can be small enough to brute-force outright regardless of
passphrase strength -- e.g. a message that splits into only 5 blocks has
just 120 possible arrangements. Real confidentiality would additionally
need a substitution step (e.g. XOR against a keystream) before this; that's
a natural Phase 2, not implemented here.

This module is orthogonal to `digital.py` -- it operates on any already-
valid DNA string (any mode) and doesn't know or care what's inside it. That
inner content's own checks (packet.py's magic bytes and CRC32) are what end
up detecting a wrong passphrase: unscrambling with the wrong key silently
produces the wrong block order, and the resulting garbage fails one of
those checks downstream -- usually the magic bytes, since reordering
displaces the header too. This module itself raises only for a
structurally malformed preamble, never for "wrong passphrase" (it has no
way to tell).

Preamble layout (always unscrambled, prepended in front of the shuffled
body so a decoder can read it before it has any passphrase):

    magic(2) | version(1) | flags(1) | pad_len(1) [ | nonce(8) ]

- magic: b"SC" -- distinguishes scrambled output from plain digital-mode
  DNA (which starts with packet.MAGIC == b"BC"), so callers can tell the
  two apart by peeking, with no passphrase needed.
- flags: bit0 = HAS_NONCE.
- pad_len: 0-3 -- zero bytes appended before splitting into 4-byte blocks,
  stripped back off after unscrambling.
- nonce: 8 random bytes, present only if HAS_NONCE. Not secret -- like an
  IV, its only job is to make the same passphrase shuffle differently on
  every message, so a key reused across many messages doesn't leak the
  permutation pattern.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct
from dataclasses import dataclass

from biocrypt.codec import nucleotide
from biocrypt.codec.errors import (
    InvalidDNAError,
    InvalidScramblePreambleError,
    UnsupportedScrambleVersionError,
)

MAGIC = b"SC"
VERSION = 1

FLAG_NONE = 0
FLAG_HAS_NONCE = 0b0000_0001

BLOCK_BYTES = 4  # a "block" = 4 sub-sequences; 1 sub-sequence = 1 byte = 4 bases
NONCE_BYTES = 8

_PREAMBLE_FORMAT = ">2sBBB"  # magic, version, flags, pad_len
_PREAMBLE_SIZE = struct.calcsize(_PREAMBLE_FORMAT)  # 5


def _derive_key(passphrase: str) -> bytes:
    # MVP simplification: a single SHA-256 of the passphrase. A hardened
    # version should run this through a slow KDF (PBKDF2/scrypt) with a
    # stored salt to resist offline brute-forcing of the passphrase itself
    # -- orthogonal to the permutation mechanism below, tracked as a
    # follow-up rather than blocking it.
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def _keyed_permutation(key: bytes, n: int, nonce: bytes) -> list[int]:
    """Deterministic Fisher-Yates shuffle of range(n), driven by an
    HMAC-SHA256 counter-mode stream keyed on `key` (+ `nonce`). Encode and
    decode each call this independently and always get the same order back
    -- nothing about the permutation itself needs to travel with the DNA."""
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        digest = hmac.new(key, nonce + i.to_bytes(4, "big"), hashlib.sha256).digest()
        j = int.from_bytes(digest, "big") % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def _read_preamble(dna: str) -> tuple[bool, bytes, int, int]:
    """Parse the unscrambled preamble. Returns (has_nonce, nonce, pad_len,
    body_start_base_index). Raises InvalidScramblePreambleError /
    UnsupportedScrambleVersionError on anything malformed."""
    header_bases = _PREAMBLE_SIZE * nucleotide.BASES_PER_BYTE
    if len(dna) < header_bases:
        raise InvalidScramblePreambleError("DNA is too short to contain a scramble preamble")

    header_bytes = nucleotide.dna_to_bytes(dna[:header_bases])
    magic, version, flags, pad_len = struct.unpack(_PREAMBLE_FORMAT, header_bytes)
    if magic != MAGIC:
        raise InvalidScramblePreambleError(f"bad scramble magic {magic!r}")
    if version != VERSION:
        raise UnsupportedScrambleVersionError(f"unsupported scramble preamble version {version}")

    has_nonce = bool(flags & FLAG_HAS_NONCE)
    cursor = header_bases
    nonce = b""
    if has_nonce:
        nonce_bases = NONCE_BYTES * nucleotide.BASES_PER_BYTE
        if len(dna) < cursor + nonce_bases:
            raise InvalidScramblePreambleError("DNA is too short to contain its declared nonce")
        nonce = nucleotide.dna_to_bytes(dna[cursor : cursor + nonce_bases])
        cursor += nonce_bases

    return has_nonce, nonce, pad_len, cursor


def is_scrambled(dna: str) -> bool:
    """Whether `dna` has the scramble preamble -- decodable with no
    passphrase, since the preamble is unscrambled by design."""
    try:
        _read_preamble(dna)
    except (InvalidDNAError, InvalidScramblePreambleError, UnsupportedScrambleVersionError):
        return False
    return True


@dataclass(frozen=True, slots=True)
class PreambleInfo:
    has_nonce: bool
    nonce_hex: str
    pad_len: int
    block_count: int


def preamble_info(dna: str) -> PreambleInfo:
    """Read the scramble preamble's metadata for display purposes (e.g. API
    stats) -- no passphrase required, since none of this is secret."""
    has_nonce, nonce, pad_len, cursor = _read_preamble(dna)
    body_bytes = (len(dna) - cursor) // nucleotide.BASES_PER_BYTE
    return PreambleInfo(
        has_nonce=has_nonce,
        nonce_hex=nonce.hex(),
        pad_len=pad_len,
        block_count=body_bytes // BLOCK_BYTES,
    )


def scramble(dna: str, passphrase: str, *, use_nonce: bool = True) -> str:
    """Shuffle `dna` (any valid A/C/G/T string) into 4-byte blocks ordered
    by a permutation derived from `passphrase`. Returns a new DNA string:
    an unscrambled preamble followed by the shuffled body."""
    key = _derive_key(passphrase)
    nonce = os.urandom(NONCE_BYTES) if use_nonce else b""

    data = bytearray(nucleotide.dna_to_bytes(dna))
    pad_len = (-len(data)) % BLOCK_BYTES
    data.extend(b"\x00" * pad_len)

    blocks = [bytes(data[i : i + BLOCK_BYTES]) for i in range(0, len(data), BLOCK_BYTES)]
    order = _keyed_permutation(key, len(blocks), nonce)
    shuffled = b"".join(blocks[i] for i in order)

    flags = FLAG_HAS_NONCE if use_nonce else FLAG_NONE
    preamble = struct.pack(_PREAMBLE_FORMAT, MAGIC, VERSION, flags, pad_len) + nonce
    return nucleotide.bytes_to_dna(preamble) + nucleotide.bytes_to_dna(shuffled)


def unscramble(dna: str, passphrase: str) -> str:
    """Reverse `scramble()`. Raises InvalidScramblePreambleError /
    UnsupportedScrambleVersionError on a malformed preamble. Does *not*
    raise on a wrong passphrase -- see the module docstring."""
    has_nonce, nonce, pad_len, cursor = _read_preamble(dna)

    body = nucleotide.dna_to_bytes(dna[cursor:])
    if len(body) % BLOCK_BYTES != 0:
        raise InvalidScramblePreambleError("scrambled body length is not a multiple of the block size")

    key = _derive_key(passphrase)
    blocks = [body[i : i + BLOCK_BYTES] for i in range(0, len(body), BLOCK_BYTES)]
    order = _keyed_permutation(key, len(blocks), nonce)

    original = [b""] * len(blocks)
    for position, source in enumerate(order):
        original[source] = blocks[position]

    data = b"".join(original)
    if pad_len:
        data = data[:-pad_len]
    return nucleotide.bytes_to_dna(data)
