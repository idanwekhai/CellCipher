"""Request/response models. This is the only layer that knows about
pydantic/FastAPI -- everything it describes maps onto `biocrypt.codec`
dataclasses, it doesn't add new logic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StatsModel(BaseModel):
    model_config = {"from_attributes": True}

    version: int
    mode: str
    byte_count: int
    payload_byte_count: int
    packet_byte_count: int
    compressed: bool
    compression_ratio: float
    dna_length: int
    gc_content_percent: float
    longest_homopolymer: int
    bits_per_base: float
    checksum_hex: str


class EncodeRequest(BaseModel):
    text: str = Field(..., max_length=200_000, description="Text to encode as DNA.")
    passphrase: str | None = Field(
        default=None,
        max_length=1024,
        description=(
            "Optional. If set, the encoded DNA is additionally scrambled "
            "(a keyed block-transposition layer) so it can't be decoded "
            "without this same passphrase."
        ),
    )
    use_nonce: bool = Field(
        default=True,
        description=(
            "Only relevant with `passphrase`. If true (recommended), a random "
            "per-message nonce is embedded so the same passphrase produces a "
            "different scramble every time. If false, scrambling is fully "
            "deterministic from the passphrase alone."
        ),
    )


class EncodeResponse(BaseModel):
    dna: str
    stats: StatsModel
    scrambled: bool
    nonce_hex: str | None = None


class DecodeRequest(BaseModel):
    dna: str = Field(..., max_length=1_000_000, description="DNA string (A/C/G/T) to decode.")
    passphrase: str | None = Field(
        default=None, max_length=1024, description="Required if the DNA was encoded with a passphrase."
    )


class DecodeResponse(BaseModel):
    valid: bool
    text: str | None = None
    error: str | None = None
    error_type: str | None = None
    stats: StatsModel | None = None
    scrambled: bool | None = None
    nonce_hex: str | None = None


class ModeInfo(BaseModel):
    value: int
    name: str
    implemented: bool
    description: str


class ScrambleInfo(BaseModel):
    supported: bool
    magic: str
    block_bytes: int
    nonce_bytes: int
    description: str


class InfoResponse(BaseModel):
    format_version: int
    magic: str
    bases_per_byte: int
    modes: list[ModeInfo]
    scrambling: ScrambleInfo
