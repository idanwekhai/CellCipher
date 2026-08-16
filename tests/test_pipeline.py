import pytest

from biocrypt.codec import pipeline
from biocrypt.codec.errors import DecodeError, PassphraseRequiredError

TEXT = "Only someone with the passphrase should be able to read this."


def test_encode_without_passphrase_is_unscrambled():
    result = pipeline.encode(TEXT)
    assert result.scrambled is False
    assert result.nonce_hex is None
    assert pipeline.decode(result.dna).text == TEXT


def test_encode_decode_round_trip_with_passphrase():
    encoded = pipeline.encode(TEXT, passphrase="hunter2", use_nonce=True)
    assert encoded.scrambled is True
    assert encoded.nonce_hex is not None

    decoded = pipeline.decode(encoded.dna, passphrase="hunter2")
    assert decoded.scrambled is True
    assert decoded.text == TEXT


def test_decode_scrambled_dna_without_passphrase_raises():
    encoded = pipeline.encode(TEXT, passphrase="hunter2")
    with pytest.raises(PassphraseRequiredError):
        pipeline.decode(encoded.dna)


def test_decode_scrambled_dna_with_wrong_passphrase_fails_loudly():
    # A wrong passphrase yields a wrong block order, which then fails one of
    # the inner packet's own checks (magic bytes and/or CRC32) -- whichever
    # trips first depends on exactly how the blocks landed. Either way it
    # must raise, never silently return the original (or any) text.
    encoded = pipeline.encode(TEXT, passphrase="hunter2")
    with pytest.raises(DecodeError):
        pipeline.decode(encoded.dna, passphrase="wrong-passphrase")


def test_deterministic_scramble_without_nonce_is_reproducible():
    a = pipeline.encode(TEXT, passphrase="hunter2", use_nonce=False)
    b = pipeline.encode(TEXT, passphrase="hunter2", use_nonce=False)
    assert a.dna == b.dna


def test_nonce_scramble_varies_between_encodes():
    a = pipeline.encode(TEXT, passphrase="hunter2", use_nonce=True)
    b = pipeline.encode(TEXT, passphrase="hunter2", use_nonce=True)
    assert a.dna != b.dna
    assert pipeline.decode(a.dna, passphrase="hunter2").text == TEXT
    assert pipeline.decode(b.dna, passphrase="hunter2").text == TEXT
