# Unresolved risks and release blockers

| Priority | Risk | Why computation cannot close it | Required evidence |
|---|---|---|---|
| Blocker | integrase/site crosstalk | exact sequence difference and embeddings do not measure recombination | complete 3 × 3 integrase/site matrix in the intended host context |
| Blocker | integrase/RDF crosstalk | noncognate RDF interactions are documented | complete forward and reverse integrase/RDF/site matrix |
| Blocker | state-gate implementation | exported gate sequences are placeholders | measured exact-state AND one-hot-input circuits for all six commands |
| Blocker | wrong-order deletion | topology predicts irreversible excision | wrong-state substrate assays and fail-closed leakage limits |
| Blocker | final genomic locus | no locus or homology arms were selected | locus choice, off-target review, and integration/QC plan |
| High | phiC31 integrase-only excision | threatens stored-state stability | long no-input dwell and pulse-tail measurements |
| High | population heterogeneity | bulk averages can hide mixed states | single-cell or clone-resolved DNA state purity |
| High | controller copy-number burden | pACYC177-derived records are development artifacts | single-copy controller implementation and burden assay |
| High | host pseudo-sites | exact full-site search misses partial or degenerate sites | unbiased junction mapping and strain-specific genome verification |
| High | native CDS expression | no codon or expression optimization was validated | per-protein expression and activity titration |
| Medium | sensor coupling | sugar sensors depend on host physiology and media | three-input crosstalk, dose-response, and pulse-clearance matrix |
| Medium | mutation over cycles | sites, gates, and repeats may evolve under selection | multi-cycle long-read sequencing and stability limit |
| Medium | assembly constraints | message record contains two BsaI sites | choose a compatible assembly route or redesign without changing topology |
| Medium | incidental expression | ORF and promoter proxies are only sequence flags | strand-specific RNA and toxicity measurements |

## Explicitly unavailable inputs

The collaborator's original message file and image were not present at the
recorded paths. Payloads are therefore neutral deterministic barcodes with no
claimed biological meaning.

## Release rule

Do not label any construct synthesis-ready until all blocker rows are closed.
The current files are reproducible candidate records for computational review
and staged experimental planning only.
