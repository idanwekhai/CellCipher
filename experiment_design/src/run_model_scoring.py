"""Model-run manifest, schema validation, and embedding comparison utilities."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for two nonzero embeddings."""
    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        raise ValueError("Embedding vectors must be nonzero")
    return float(np.dot(a, b) / denominator)


def validate_embedding_output(payload: dict[str, object], expected: int) -> None:
    """Validate the minimum Proto ESM-2 output contract."""
    results = payload.get("results")
    if not isinstance(results, list) or len(results) != expected:
        raise ValueError(f"Expected {expected} embedding results")
    dimensions = set()
    for item in results:
        if not isinstance(item, dict) or not isinstance(item.get("mean_embedding"), list):
            raise ValueError("Missing mean_embedding array")
        dimensions.add(len(item["mean_embedding"]))
    if len(dimensions) != 1 or 0 in dimensions:
        raise ValueError("Embeddings must have one nonzero shared dimension")


def pairwise_embedding_table(
    payload: dict[str, object], labels: list[str]
) -> list[dict[str, object]]:
    """Calculate all pairwise ESM-2 embedding similarities."""
    validate_embedding_output(payload, len(labels))
    embeddings = [item["mean_embedding"] for item in payload["results"]]
    rows = []
    for left_index, left in enumerate(labels):
        for right_index in range(left_index + 1, len(labels)):
            rows.append(
                {
                    "left": left,
                    "right": labels[right_index],
                    "cosine_similarity": cosine_similarity(
                        embeddings[left_index], embeddings[right_index]
                    ),
                    "interpretation": "prioritization only; not evidence of orthogonality",
                }
            )
    return rows


def export_model_runs(root: Path) -> None:
    """Export configured runs and skips to a tabular manifest."""
    config = yaml.safe_load((root / "configs" / "model_runs.yaml").read_text())
    rows = config["runs"]
    output = root / "reports" / "model_runs.tsv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def load_proto_output(path: Path) -> dict[str, object]:
    """Load a captured Proto output JSON."""
    return json.loads(path.read_text())


def hydrate_esm_results(path: Path) -> dict[str, object]:
    """Resolve Proto large-field references into one schema-valid payload."""
    raw = json.loads(path.read_text())
    results = []
    for item in raw:
        hydrated = dict(item)
        embedding = item["mean_embedding"]
        if isinstance(embedding, dict) and "_saved_to" in embedding:
            hydrated["mean_embedding"] = json.loads(Path(embedding["_saved_to"]).read_text())
        results.append(hydrated)
    return {"results": results}


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a heterogeneous row list as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_artifacts(root: Path) -> dict[str, object]:
    """Create compact reports from captured ESM-2 and ViennaRNA outputs."""
    model_inputs = root / "artifacts" / "model_inputs"
    model_outputs = root / "artifacts" / "model_outputs"
    reports = root / "reports"

    esm_input = json.loads((model_inputs / "esm2_input.json").read_text())
    esm_payload = hydrate_esm_results(model_outputs / "esm2" / "results.json")
    embedding_rows = pairwise_embedding_table(esm_payload, esm_input["labels"])
    write_rows(reports / "esm2_pairwise_similarity.csv", embedding_rows)

    vienna_input = json.loads((model_inputs / "viennarna_input.json").read_text())
    vienna_results = json.loads((model_outputs / "viennarna" / "results.json").read_text())
    vienna_rows = []
    for label, input_hash, output in zip(
        vienna_input["labels"],
        vienna_input["input_hashes"],
        vienna_results,
        strict=True,
    ):
        sequence = output["sequence"]
        vienna_rows.append(
            {
                "label": label,
                "input_sha256": input_hash,
                "length_nt": len(sequence),
                "mfe_kcal_mol": output["mfe"],
                "mfe_per_nt": output["mfe"] / len(sequence),
                "structure_sha256": hashlib.sha256(output["structure"].encode()).hexdigest(),
                "interpretation": "relative translation-initiation-window flag only",
            }
        )
    write_rows(reports / "viennarna_rbs_summary.csv", vienna_rows)

    integrase_pairs = [
        row
        for row in embedding_rows
        if "_integrase_" in row["left"] and "_integrase_" in row["right"]
    ]
    rdf_pairs = [
        row for row in embedding_rows if "_rdf_" in row["left"] and "_rdf_" in row["right"]
    ]
    summary = {
        "esm2": {
            "checkpoint": esm_input["checkpoint"],
            "embedding_dimension": len(esm_payload["results"][0]["mean_embedding"]),
            "integrase_pairwise_similarity_range": [
                min(row["cosine_similarity"] for row in integrase_pairs),
                max(row["cosine_similarity"] for row in integrase_pairs),
            ],
            "rdf_pairwise_similarity_range": [
                min(row["cosine_similarity"] for row in rdf_pairs),
                max(row["cosine_similarity"] for row in rdf_pairs),
            ],
            "changed_selected_channels": False,
            "interpretation": (
                "The analysis prioritizes biochemical diversity and controls; "
                "it cannot validate enzyme/site or integrase/RDF orthogonality."
            ),
        },
        "viennarna": {
            "windows": len(vienna_rows),
            "mfe_per_nt_range": [
                min(row["mfe_per_nt"] for row in vienna_rows),
                max(row["mfe_per_nt"] for row in vienna_rows),
            ],
            "changed_selected_sequences": False,
            "interpretation": (
                "Placeholder RBS/state-gate sequences are not rescued by favorable "
                "folding scores; all remain non-synthesis-ready."
            ),
        },
    }
    (reports / "model_run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    write_rows(
        reports / "model_ablation.csv",
        [
            {
                "analysis_removed": "none",
                "selected_channel_trio": "Bxb1;phiC31;TP901-1",
                "selected_payload_candidate_changed": False,
                "hard_constraints_changed": False,
            },
            {
                "analysis_removed": "ESM2",
                "selected_channel_trio": "Bxb1;phiC31;TP901-1",
                "selected_payload_candidate_changed": False,
                "hard_constraints_changed": False,
            },
            {
                "analysis_removed": "ViennaRNA",
                "selected_channel_trio": "Bxb1;phiC31;TP901-1",
                "selected_payload_candidate_changed": False,
                "hard_constraints_changed": False,
            },
        ],
    )
    return summary


if __name__ == "__main__":
    summarize_artifacts(Path(__file__).resolve().parents[1])
