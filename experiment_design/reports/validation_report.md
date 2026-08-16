# Validation report

## Verdict

The package passes its computational contract. It does not establish an
experimentally functional or synthesis-ready device.

Evidence labels used here are **[D]** direct published or source-record
evidence, **[C]** deterministic computation, **[M]** model output, **[I]**
inference, and **[U]** unresolved.

## Primary records

| Record | Topology | Length | Status |
|---|---|---:|---|
| `01_message_register.gb` | linear | 966 bp | exact seven-state topology validated **[C]** |
| `02_forward_controller.gb` | circular | 9,584 bp | parseable development-controller candidate **[C/U]** |
| `03_reverse_controller.gb` | circular | 10,727 bp | parseable development-controller candidate **[C/U]** |

Every GenBank record has a matching FASTA record. Parse-back checks require
sequence equality, valid coordinates, declared topology, and CDS translations
under bacterial genetic code 11. Protein CDSs and attachment sites are traced
to the records listed in `artifacts/retrieved_parts/retrieval_manifest.json`.

## Exact topology result

The typed simulator applies channel-specific `attB × attP → attL + attR`
half-site exchange for integrase and the exact inverse for integrase plus
cognate RDF. Site identity, state, strand, crossover index, physical element
order, orientation, and coordinates are explicit.

Forward `ABC` gives State 3, and reverse `CBA` restores State 0 byte for byte:

- State 0 SHA-256:
  `41d201bb92dabcae863aa73f976cebc5242dcce37013c3a82827d8d9ebf64583`
- State 3 SHA-256:
  `b60293c357c39fe4272839b24cfbf8640d2e343110610cc574af583bc1ca5e97`
- Restored State 0 SHA-256 equals the original State 0 hash. **[C]**

The simulator exports all seven physical records and their full feature
coordinates in `states/` and `reports/state_transition_table.tsv`.

## Order discrimination

All six forward and all six reverse permutations were enumerated. Only forward
`ABC` and reverse `CBA` complete. Every other order reaches a physically
classified parallel cognate-site deletion/excision substrate before completion.
This is a falsifying result, not a benign software rejection. A leaky or
mistimed downstream enzyme could permanently delete sequence. **[C]**

The required safeguard is therefore an AND of exact DNA state, one-hot chemical
input, and direction mode. The Boolean controller passes all six intended
commands and fails closed for no-input and simultaneous-input cases. The
sequence-level state gates are placeholders, so that safety property has not
been implemented biologically. **[C/U]**

## Constraint and sequence checks

- 280 of 280 hard checks pass. **[C]**
- Exact full-length searches found no cognate `attB`, `attP`, `attL`, or `attR`
  occurrence on either strand of the MG1655 reference. This is only a lower
  bound on pseudo-site risk. **[C/U]**
- No ambiguous bases occur in exported constructs. **[C]**
- The message register has global GC 50.93%, a longest homopolymer of 5 nt,
  and no repeated 16-mers. **[C]**
- Two BsaI sites remain in the message record. This is not a topology failure,
  but it constrains assembly-method choice. **[C]**
- Incidental ORFs and promoter-like motif proxies are reported, not treated as
  proof of expression. **[C/U]**

Hard validity is never merged into the payload optimization score. The selected
neutral payload candidate is one of a two-member Pareto front. The alternate
trades perfect aggregate GC balance for a 7-nt homopolymer and is not preferred.

## Model checks

ESM-2 15B generated 5,120-dimensional embeddings for all three integrases and
three RDFs. Integrase pairwise cosine similarities span 0.7581 to 0.8936; RDF
similarities span 0.4611 to 0.7049. These results support prioritizing a broad
crosstalk matrix but do not measure enzyme/site or enzyme/RDF compatibility.
They did not change the selected channel trio. **[M/U]**

ViennaRNA folded nine 204-nt translation-initiation windows at 37 °C. Normalized
MFE spans -0.4093 to -0.1975 kcal mol-1 nt-1. Because the regulatory sequences
are placeholders and MFE is not an expression model, no sequence was promoted
to synthesis-ready status and no design decision changed. **[M/U]**

## Test boundaries

The automated suite covers exact round trip, intermediate payload order,
forward and reverse permutations, deletion geometry, invalid crossover indices,
wrong RDF assignment, controller perturbations, GenBank/FASTA round trip, CDS
translation, provenance, model-output schema, and deterministic regeneration.
Deliberately invalid fixtures must be rejected with diagnostics.

No wet-lab efficiency, state purity, leakage, burden, mutation rate, crosstalk,
cycle life, or off-target junction frequency is inferred.
