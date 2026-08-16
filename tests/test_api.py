import pytest
from fastapi.testclient import TestClient

from biocrypt.api.app import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info():
    response = client.get("/api/info")
    assert response.status_code == 200
    body = response.json()
    assert body["magic"] == "BC"
    assert any(m["name"] == "digital-2bit" and m["implemented"] for m in body["modes"])


def test_encode_returns_dna_and_stats():
    response = client.post("/api/encode", json={"text": "Hello, DNA!"})
    assert response.status_code == 200
    body = response.json()
    assert set(body["dna"]) <= set("ACGT")
    assert body["stats"]["byte_count"] == len(b"Hello, DNA!")
    assert body["stats"]["dna_length"] == len(body["dna"])


def test_encode_then_decode_round_trips():
    text = "The biocrypt MVP: text as DNA, and back again."
    encoded = client.post("/api/encode", json={"text": text}).json()

    decoded = client.post("/api/decode", json={"dna": encoded["dna"]}).json()
    assert decoded["valid"] is True
    assert decoded["text"] == text
    assert decoded["stats"]["checksum_hex"] == encoded["stats"]["checksum_hex"]


def test_decode_reports_invalid_alphabet_without_500():
    response = client.post("/api/decode", json={"dna": "ACGTXYZ"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["error_type"] == "InvalidDNAError"


def test_decode_reports_checksum_mismatch():
    encoded = client.post("/api/encode", json={"text": "tamper with me"}).json()
    dna = list(encoded["dna"])
    mid = len(dna) // 2
    dna[mid] = "A" if dna[mid] != "A" else "C"

    response = client.post("/api/decode", json={"dna": "".join(dna)})
    body = response.json()
    assert body["valid"] is False
    assert body["error_type"] == "ChecksumMismatchError"


def test_decode_rejects_arbitrary_dna_gracefully():
    response = client.post("/api/decode", json={"dna": "ACGT" * 50})
    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_info_advertises_scrambling():
    body = client.get("/api/info").json()
    assert body["scrambling"]["supported"] is True
    assert body["scrambling"]["magic"] == "SC"


def test_encode_with_passphrase_is_scrambled_and_round_trips():
    text = "secret message for the scramble layer"
    encoded = client.post("/api/encode", json={"text": text, "passphrase": "hunter2"}).json()
    assert encoded["scrambled"] is True
    assert encoded["nonce_hex"] is not None

    decoded = client.post("/api/decode", json={"dna": encoded["dna"], "passphrase": "hunter2"}).json()
    assert decoded["valid"] is True
    assert decoded["text"] == text
    assert decoded["scrambled"] is True


def test_decode_scrambled_dna_without_passphrase_reports_clear_error():
    encoded = client.post("/api/encode", json={"text": "shh", "passphrase": "hunter2"}).json()
    response = client.post("/api/decode", json={"dna": encoded["dna"]})
    body = response.json()
    assert body["valid"] is False
    assert body["error_type"] == "PassphraseRequiredError"
    assert body["scrambled"] is True  # hinted even though decode failed


def test_decode_scrambled_dna_with_wrong_passphrase_fails_not_silently():
    encoded = client.post("/api/encode", json={"text": "shh", "passphrase": "hunter2"}).json()
    response = client.post("/api/decode", json={"dna": encoded["dna"], "passphrase": "not-it"})
    body = response.json()
    assert body["valid"] is False
    assert body["text"] is None


def test_no_nonce_scramble_is_reproducible_via_api():
    payload = {"text": "deterministic please", "passphrase": "hunter2", "use_nonce": False}
    first = client.post("/api/encode", json=payload).json()
    second = client.post("/api/encode", json=payload).json()
    assert first["dna"] == second["dna"]
    assert first["nonce_hex"] is None
