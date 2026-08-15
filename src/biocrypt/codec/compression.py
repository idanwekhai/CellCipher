"""Thin wrapper around Brotli so the rest of the codec doesn't import a
third-party library directly. Swappable for zstd later without touching
callers.
"""

from __future__ import annotations

import brotli

# Text-tuned quality; MODE_TEXT gives Brotli's context modeling for natural
# language, which is what this codec exists to compress.
_QUALITY = 11


def compress(data: bytes) -> bytes:
    return brotli.compress(data, mode=brotli.MODE_TEXT, quality=_QUALITY)


def decompress(data: bytes) -> bytes:
    return brotli.decompress(data)
