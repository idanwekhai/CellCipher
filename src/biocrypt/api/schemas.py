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


class EncodeResponse(BaseModel):
    dna: str
    stats: StatsModel


class DecodeRequest(BaseModel):
    dna: str = Field(..., max_length=1_000_000, description="DNA string (A/C/G/T) to decode.")


class DecodeResponse(BaseModel):
    valid: bool
    text: str | None = None
    error: str | None = None
    error_type: str | None = None
    stats: StatsModel | None = None


class ModeInfo(BaseModel):
    value: int
    name: str
    implemented: bool
    description: str


class InfoResponse(BaseModel):
    format_version: int
    magic: str
    bases_per_byte: int
    modes: list[ModeInfo]
