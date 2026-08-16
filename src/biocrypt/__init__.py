"""biocrypt: a versioned text <-> DNA (A/C/G/T) encoding/storage codec.

The base digital-mode pipeline (`biocrypt.codec.digital`) is *encoding*, not
encryption: anyone who knows the format (published in the README) can decode
DNA it produces without a secret key -- treat it like base64 or hex.

Passing a `passphrase` to `encode`/`decode` (this module's top-level API)
opts into an additional keyed block-scramble layer (`biocrypt.codec.scramble`)
that *is* a real, if simple, cipher -- see that module's docstring for its
honest limitations (it's a transposition cipher, not a substitution one).
"""

from biocrypt.codec.pipeline import DecodeResult, EncodeResult, decode, encode

__all__ = ["encode", "decode", "EncodeResult", "DecodeResult"]
