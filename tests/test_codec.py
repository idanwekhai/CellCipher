import pytest

from biocrypt.codec import digital, nucleotide, packet
from biocrypt.codec.errors import (
    ChecksumMismatchError,
    InvalidDNAError,
    InvalidPacketError,
    UnsupportedVersionError,
)


# --- nucleotide: raw bytes <-> DNA -------------------------------------------


def test_bytes_to_dna_matches_spec_example():
    # "A" = 0x41 = 0b01000001 -> pairs 01,00,00,01 -> C,A,A,C
    assert nucleotide.bytes_to_dna(b"A") == "CAAC"


def test_dna_to_bytes_round_trips_all_byte_values():
    data = bytes(range(256))
    assert nucleotide.dna_to_bytes(nucleotide.bytes_to_dna(data)) == data


def test_dna_to_bytes_is_case_insensitive_and_strips_whitespace():
    assert nucleotide.dna_to_bytes(" caac \n") == b"A"


def test_dna_to_bytes_rejects_bad_alphabet():
    with pytest.raises(InvalidDNAError):
        nucleotide.dna_to_bytes("CAAN")


def test_dna_to_bytes_rejects_bad_length():
    with pytest.raises(InvalidDNAError):
        nucleotide.dna_to_bytes("CAA")  # not a multiple of 4


def test_gc_content():
    assert nucleotide.gc_content("GGCC") == 100.0
    assert nucleotide.gc_content("AATT") == 0.0
    assert nucleotide.gc_content("") == 0.0


def test_longest_homopolymer():
    assert nucleotide.longest_homopolymer("ACGTAAAAGT") == 4
    assert nucleotide.longest_homopolymer("ACGT") == 1
    assert nucleotide.longest_homopolymer("") == 0


# --- packet: framing, checksum, versioning -----------------------------------


def test_packet_round_trip():
    raw = packet.pack(mode=packet.MODE_DIGITAL_2BIT, flags=packet.FLAG_NONE, original_length=5, payload=b"hello")
    pkt = packet.unpack(raw)
    assert pkt.payload == b"hello"
    assert pkt.original_length == 5
    assert pkt.mode == packet.MODE_DIGITAL_2BIT
    assert pkt.compressed is False


def test_packet_rejects_bad_magic():
    with pytest.raises(InvalidPacketError):
        packet.unpack(b"\x00\x00" + b"\x01\x01\x00" + (0).to_bytes(4, "big") + b"hi" + b"\x00\x00\x00\x00")


def test_packet_rejects_truncated_data():
    with pytest.raises(InvalidPacketError):
        packet.unpack(b"BC\x01")


def test_packet_rejects_unsupported_version():
    good = packet.pack(mode=packet.MODE_DIGITAL_2BIT, flags=0, original_length=0, payload=b"")
    tampered = bytearray(good)
    tampered[2] = 99  # version byte
    with pytest.raises(UnsupportedVersionError):
        packet.unpack(bytes(tampered))


def test_packet_detects_corruption_via_checksum():
    good = packet.pack(mode=packet.MODE_DIGITAL_2BIT, flags=0, original_length=5, payload=b"hello")
    tampered = bytearray(good)
    tampered[-5] ^= 0xFF  # flip a bit in the payload, leave the crc alone
    with pytest.raises(ChecksumMismatchError):
        packet.unpack(bytes(tampered))


# --- digital pipeline: end-to-end --------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "",
        "A",
        "Hello, DNA!",
        "The quick brown fox jumps over the lazy dog. " * 20,  # compresses well
        "🧬 unicode: café, naïve, 你好",
    ],
)
def test_encode_decode_round_trip(text):
    encoded = digital.encode(text)
    assert set(encoded.dna) <= set("ACGT")
    decoded = digital.decode(encoded.dna)
    assert decoded.text == text


def test_compression_is_chosen_when_it_shrinks_output():
    repetitive = "biocrypt " * 200
    encoded = digital.encode(repetitive)
    assert encoded.stats.compressed is True
    assert encoded.stats.payload_byte_count < encoded.stats.byte_count


def test_compression_is_skipped_for_short_text():
    encoded = digital.encode("hi")
    assert encoded.stats.compressed is False


def test_corrupted_dna_reports_checksum_mismatch_not_a_crash():
    encoded = digital.encode("round trip me")
    bases = list(encoded.dna)
    # Flip a base in the middle to corrupt the payload without changing length.
    mid = len(bases) // 2
    bases[mid] = "A" if bases[mid] != "A" else "C"
    corrupted = "".join(bases)

    with pytest.raises(ChecksumMismatchError):
        digital.decode(corrupted)


def test_decode_rejects_foreign_dna():
    with pytest.raises(InvalidPacketError):
        digital.decode("ACGT" * 10)  # valid alphabet, but not a biocrypt packet
