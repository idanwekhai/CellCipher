import pytest

from biocrypt.codec import digital, scramble
from biocrypt.codec.errors import InvalidScramblePreambleError

TEXT = "The scramble layer reorders 4-byte blocks using a keyed permutation."


def _encode_dna(text: str = TEXT) -> str:
    return digital.encode(text).dna


# --- round trips -------------------------------------------------------------


@pytest.mark.parametrize("use_nonce", [True, False])
def test_scramble_round_trips(use_nonce):
    dna = _encode_dna()
    scrambled = scramble.scramble(dna, "correct horse battery staple", use_nonce=use_nonce)
    assert scramble.is_scrambled(scrambled)
    recovered = scramble.unscramble(scrambled, "correct horse battery staple")
    assert recovered == dna
    assert digital.decode(recovered).text == TEXT


def test_scrambled_dna_is_reordered_not_identical():
    dna = _encode_dna()
    scrambled = scramble.scramble(dna, "a passphrase")
    assert scrambled != dna
    # still valid DNA alphabet
    assert set(scrambled) <= set("ACGT")


def test_plain_digital_dna_is_not_reported_as_scrambled():
    dna = _encode_dna()
    assert scramble.is_scrambled(dna) is False


# --- nonce behavior ------------------------------------------------------------


def test_nonce_makes_repeated_scrambles_differ():
    dna = _encode_dna()
    a = scramble.scramble(dna, "same passphrase", use_nonce=True)
    b = scramble.scramble(dna, "same passphrase", use_nonce=True)
    assert a != b  # different random nonce -> different shuffle
    assert scramble.unscramble(a, "same passphrase") == dna
    assert scramble.unscramble(b, "same passphrase") == dna


def test_no_nonce_is_fully_deterministic():
    dna = _encode_dna()
    a = scramble.scramble(dna, "same passphrase", use_nonce=False)
    b = scramble.scramble(dna, "same passphrase", use_nonce=False)
    assert a == b  # no randomness involved -> identical every time


# --- wrong / missing key behavior ----------------------------------------------


def test_wrong_passphrase_produces_garbage_not_original_text():
    dna = _encode_dna()
    scrambled = scramble.scramble(dna, "right passphrase", use_nonce=False)
    wrongly_unscrambled = scramble.unscramble(scrambled, "wrong passphrase")
    # unscramble() itself can't detect a wrong key -- it just yields a
    # different (wrong) block order. The inner packet's own checksum is
    # what actually catches this, one layer up.
    assert wrongly_unscrambled != dna


def test_preamble_info_readable_without_passphrase():
    dna = _encode_dna()
    scrambled = scramble.scramble(dna, "a passphrase", use_nonce=True)
    info = scramble.preamble_info(scrambled)
    assert info.has_nonce is True
    assert len(info.nonce_hex) == scramble.NONCE_BYTES * 2
    assert info.block_count > 0


def test_unscramble_rejects_malformed_preamble():
    with pytest.raises(InvalidScramblePreambleError):
        scramble.unscramble("ACGT" * 10, "any passphrase")
