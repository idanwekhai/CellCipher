"""Generate a deterministic whole-package checksum manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

INCLUDED_ROOTS = (
    "sequences",
    "states",
    "configs",
    "src",
    "tests",
    "reports",
    "artifacts",
)
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
MANIFEST_PATH = Path("artifacts/package_manifest.json")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_entries(root: Path) -> list[dict[str, object]]:
    """Enumerate stable package files and their checksums."""
    entries = []
    for directory in INCLUDED_ROOTS:
        for path in sorted((root / directory).rglob("*")):
            relative = path.relative_to(root)
            if (
                not path.is_file()
                or relative == MANIFEST_PATH
                or any(part in EXCLUDED_PARTS for part in relative.parts)
            ):
                continue
            entries.append(
                {
                    "path": relative.as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return entries


def write_package_manifest(root: Path) -> dict[str, object]:
    """Write a self-excluding manifest for all reproducibility artifacts."""
    entries = package_entries(root)
    manifest = {
        "algorithm": "sha256",
        "manifest_self_excluded": True,
        "file_count": len(entries),
        "files": entries,
    }
    output = root / MANIFEST_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    write_package_manifest(Path(__file__).resolve().parents[1])
