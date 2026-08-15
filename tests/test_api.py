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
