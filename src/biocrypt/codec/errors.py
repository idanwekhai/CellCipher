"""Exceptions raised by the codec.

All decode-path errors derive from DecodeError so API layers can catch one
type and turn it into a `{"valid": false, "error": ...}` response instead of
a 500. Encode-path input errors derive from EncodeError.
"""

from __future__ import annotations


class CodecError(Exception):
    """Base class for every error this package raises."""


class EncodeError(CodecError):
    """Raised when input to the encoder can't be turned into DNA."""


class DecodeError(CodecError):
    """Base class for every reason a DNA string failed to decode to text."""


class InvalidDNAError(DecodeError):
    """The input string contains characters outside the supported alphabet,
    or its length isn't a multiple of the base-pair-per-byte ratio."""


class InvalidPacketError(DecodeError):
    """The decoded bytes don't parse as a valid biocrypt packet (bad magic,
    packet too short, etc.)."""


class UnsupportedVersionError(DecodeError):
    """The packet declares a format version this build doesn't understand."""


class UnsupportedModeError(DecodeError):
    """The packet declares an encoding mode this build doesn't implement yet
    (e.g. a future synthesis-safe mode)."""


class ChecksumMismatchError(DecodeError):
    """The CRC32 stored in the packet doesn't match the recomputed CRC32 —
    the DNA was corrupted or truncated after encoding."""


class PayloadLengthMismatchError(DecodeError):
    """After decompression the payload length disagrees with the length
    recorded in the packet header — silent corruption that CRC32 alone
    would not always catch after decompression."""


class TextDecodeError(DecodeError):
    """The recovered payload bytes are not valid UTF-8."""
