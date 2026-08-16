# Sequential rearrangement design v1

Computational proof-of-concept for a three-channel, exactly reversible DNA
message register in non-pathogenic *Escherichia coli* K-12.

## Status

- Deterministic topology and exact sequence round trip: validated.
- Biological channel selection: provisional.
- Controller Boolean logic: validated.
- Sequence-level state gates: annotated synthetic placeholders.
- ESM-2 15B and ViennaRNA comparative checks: completed.
- Experimental validation: not performed.
- Synthesis readiness: **no**.

## Build

```bash
cd /Users/advikanand/crispr-forge/research/sequential_rearrangement/design_v1
/Users/advikanand/crispr-forge/.venv/bin/python src/build_constructs.py
/Users/advikanand/crispr-forge/.venv/bin/python src/run_model_scoring.py
/Users/advikanand/crispr-forge/.venv/bin/python src/finalize_package.py
/Users/advikanand/crispr-forge/.venv/bin/pytest -q
```

The build writes the three primary GenBank/FASTA records, seven message-state
records, topology tables, constraint reports, provenance manifests, and
reproducibility hashes.

`reports/validation_report.md` is the concise evidence-boundary report.
`artifacts/package_manifest.json` hashes the scripts, configs, tests, records,
retrieved inputs, model inputs and outputs, and generated reports. The manifest
excludes itself by definition.

## Primary records

- `sequences/01_message_register.gb`
- `sequences/02_forward_controller.gb`
- `sequences/03_reverse_controller.gb`

The message record is a locus-independent linear cassette. No homology arms or
chromosomal landing locus are invented. The controller records are
pACYC177-derived circular development plasmids, not the recommended final
single-copy controller implementation.

## Legacy fixture

`../simulate.py` and `../simulation_results.json` remain a separate 766-bp
symbolic regression oracle. New biological records are not required to match
legacy hashes.
