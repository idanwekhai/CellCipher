"""HTTP endpoints. Thin: parse request, call `biocrypt.codec`, shape response.
No codec logic lives here.
"""

from __future__ import annotations

from fastapi import APIRouter

from biocrypt.codec import digital, packet
from biocrypt.codec.errors import DecodeError
from biocrypt.api.schemas import (
    DecodeRequest,
    DecodeResponse,
    EncodeRequest,
    EncodeResponse,
    InfoResponse,
    ModeInfo,
    StatsModel,
)

router = APIRouter(prefix="/api", tags=["codec"])


@router.post("/encode", response_model=EncodeResponse)
def encode_text(request: EncodeRequest) -> EncodeResponse:
    result = digital.encode(request.text)
    return EncodeResponse(
        dna=result.dna,
        stats=StatsModel.model_validate(result.stats),
    )


@router.post("/decode", response_model=DecodeResponse)
def decode_dna(request: DecodeRequest) -> DecodeResponse:
    """Decode DNA back to text. Malformed or corrupted DNA is reported as
    `valid: false` with an explanatory `error`, not an HTTP error -- decoding
    untrusted/damaged input is the expected use case, not an exceptional one.
    """
    try:
        result = digital.decode(request.dna)
    except DecodeError as exc:
        return DecodeResponse(valid=False, error=str(exc), error_type=type(exc).__name__)

    return DecodeResponse(
        valid=True,
        text=result.text,
        stats=StatsModel.model_validate(result.stats),
    )


@router.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    """Describes the current packet format so clients (and future codec
    versions) can introspect it instead of hardcoding assumptions."""
    modes = [
        ModeInfo(
            value=packet.MODE_DIGITAL_2BIT,
            name=packet.MODE_NAMES[packet.MODE_DIGITAL_2BIT],
            implemented=True,
            description="UTF-8, optional Brotli compression, direct 2-bit/base mapping.",
        ),
        ModeInfo(
            value=2,
            name="synthesis-safe",
            implemented=False,
            description=(
                "Planned: homopolymer/GC-constrained encoding, chunked oligos "
                "with sequence numbers, Reed-Solomon error correction."
            ),
        ),
    ]
    return InfoResponse(
        format_version=packet.CURRENT_VERSION,
        magic=packet.MAGIC.decode("ascii"),
        bases_per_byte=4,
        modes=modes,
    )
