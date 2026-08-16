"""HTTP endpoints. Thin: parse request, call `biocrypt.codec`, shape response.
No codec logic lives here.
"""

from __future__ import annotations

from fastapi import APIRouter

from biocrypt.codec import packet, pipeline, scramble
from biocrypt.codec.errors import DecodeError
from biocrypt.api.schemas import (
    DecodeRequest,
    DecodeResponse,
    EncodeRequest,
    EncodeResponse,
    InfoResponse,
    ModeInfo,
    ScrambleInfo,
    StatsModel,
)

router = APIRouter(prefix="/api", tags=["codec"])


@router.post("/encode", response_model=EncodeResponse)
def encode_text(request: EncodeRequest) -> EncodeResponse:
    result = pipeline.encode(request.text, passphrase=request.passphrase, use_nonce=request.use_nonce)
    return EncodeResponse(
        dna=result.dna,
        stats=StatsModel.model_validate(result.stats),
        scrambled=result.scrambled,
        nonce_hex=result.nonce_hex,
    )


@router.post("/decode", response_model=DecodeResponse)
def decode_dna(request: DecodeRequest) -> DecodeResponse:
    """Decode DNA back to text. Malformed or corrupted DNA -- including a
    missing or wrong passphrase for scrambled DNA -- is reported as
    `valid: false` with an explanatory `error`, not an HTTP error: decoding
    untrusted/damaged input is the expected use case, not an exceptional one.
    """
    try:
        result = pipeline.decode(request.dna, passphrase=request.passphrase)
    except DecodeError as exc:
        return DecodeResponse(
            valid=False,
            error=str(exc),
            error_type=type(exc).__name__,
            scrambled=scramble.is_scrambled(request.dna),
        )

    return DecodeResponse(
        valid=True,
        text=result.text,
        stats=StatsModel.model_validate(result.stats),
        scrambled=result.scrambled,
        nonce_hex=result.nonce_hex,
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
        scrambling=ScrambleInfo(
            supported=True,
            magic=scramble.MAGIC.decode("ascii"),
            block_bytes=scramble.BLOCK_BYTES,
            nonce_bytes=scramble.NONCE_BYTES,
            description=(
                "Optional keyed block-transposition layer on top of any mode's "
                "DNA output. A transposition cipher, not a substitution one -- "
                "short messages (few blocks) are brute-forceable regardless of "
                "passphrase strength."
            ),
        ),
    )
