"""Top-level orchestration: composes the digital-mode pipeline with the
optional keyed scramble layer. This is the entry point the API (and any
other embedding code) should call -- `digital.py` and `scramble.py` stay
pure, independent, and independently testable; this module just wires them
together, in order:

    text -> digital.encode -> dna -> [scramble.scramble if passphrase] -> dna

Decoding runs the same composition in reverse, detecting whether scrambling
was applied by peeking at the (always-unscrambled) preamble -- no
passphrase is needed just to tell the two cases apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from biocrypt.codec import digital, scramble, stats
from biocrypt.codec.errors import PassphraseRequiredError


@dataclass(frozen=True, slots=True)
class EncodeResult:
    dna: str
    stats: stats.CodecStats
    scrambled: bool
    nonce_hex: str | None = None


@dataclass(frozen=True, slots=True)
class DecodeResult:
    text: str
    stats: stats.CodecStats
    scrambled: bool
    nonce_hex: str | None = None


def encode(text: str, *, passphrase: str | None = None, use_nonce: bool = True) -> EncodeResult:
    """Encode `text` to DNA, then apply the keyed scramble layer if
    `passphrase` is non-empty. Scrambling reorders whatever DNA
    `digital.encode` produced without needing to know what's inside it."""
    inner = digital.encode(text)
    if not passphrase:
        return EncodeResult(dna=inner.dna, stats=inner.stats, scrambled=False)

    scrambled_dna = scramble.scramble(inner.dna, passphrase, use_nonce=use_nonce)
    info = scramble.preamble_info(scrambled_dna)
    final_stats = stats.recompute_dna_fields(inner.stats, scrambled_dna)
    return EncodeResult(
        dna=scrambled_dna,
        stats=final_stats,
        scrambled=True,
        nonce_hex=info.nonce_hex if info.has_nonce else None,
    )


def decode(dna: str, *, passphrase: str | None = None) -> DecodeResult:
    """Decode DNA that may or may not have the scramble layer applied. A
    wrong (as opposed to missing) passphrase isn't caught here -- it
    silently unscrambles to the wrong block order, which then fails one of
    the inner packet's own checks inside `digital.decode` (bad magic bytes
    and/or a CRC32 mismatch), surfacing as a DecodeError like any other
    corruption."""
    if not scramble.is_scrambled(dna):
        result = digital.decode(dna)
        return DecodeResult(text=result.text, stats=result.stats, scrambled=False)

    if not passphrase:
        raise PassphraseRequiredError("this DNA is scrambled; a passphrase is required to decode it")

    info = scramble.preamble_info(dna)
    inner_dna = scramble.unscramble(dna, passphrase)
    result = digital.decode(inner_dna)
    final_stats = stats.recompute_dna_fields(result.stats, dna)
    return DecodeResult(
        text=result.text,
        stats=final_stats,
        scrambled=True,
        nonce_hex=info.nonce_hex if info.has_nonce else None,
    )
