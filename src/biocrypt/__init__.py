"""biocrypt: a versioned text <-> DNA (A/C/G/T) encoding/storage codec.

This is an *encoding* system, not an encryption system. Anyone who knows the
format (published below) can decode the DNA back to text without a secret
key. Treat DNA produced here the way you'd treat base64 or hex: reversible,
inspectable, not confidential.
"""

from biocrypt.codec.digital import DecodeResult, EncodeResult, decode, encode

__all__ = ["encode", "decode", "EncodeResult", "DecodeResult"]
