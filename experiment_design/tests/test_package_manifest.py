"""Whole-package reproducibility manifest tests."""

from __future__ import annotations

from pathlib import Path

from finalize_package import MANIFEST_PATH, package_entries

ROOT = Path(__file__).resolve().parents[1]


def test_package_manifest_scope_and_hashes() -> None:
    """The manifest input set is stable, unique, and excludes its own output."""
    entries = package_entries(ROOT)
    paths = [entry["path"] for entry in entries]
    assert len(paths) == len(set(paths))
    assert MANIFEST_PATH.as_posix() not in paths
    assert "src/topology.py" in paths
    assert "sequences/01_message_register.gb" in paths
    assert "artifacts/model_outputs/esm2/results.json" in paths
    assert all(len(entry["sha256"]) == 64 for entry in entries)
