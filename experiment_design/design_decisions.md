# Design decisions

## Architecture

The primary design uses three large serine integrase (LSI) channels on one
linear, single-copy chromosomal cassette. Forward controllers provide
integrase alone. Reverse controllers provide the same integrase plus its
cognate directionality factor. Exchanging the forward and reverse development
controllers is the explicit global direction mode.

This was selected over bridge-RNA, tyrosine-recombinase, natural-invertase, and
CRISPR double-strand-break architectures because only the LSI/RDF architecture
combines conservative strand exchange, distinct product sites, an explicit
inverse chemistry, multiple addressable channels, and mature evidence.

## Channel set

The provisional set is Bxb1/gp47, phiC31/gp3, and TP901-1/Xis. Bxb1 is the
anchor. PhiC31 provides unusually deep reversal evidence but has a documented
integrase-only excision concern. TP901-1 supplies independently sourced
minimal sites and experimentally annotated integrase/excisionase genes.

The set is not claimed orthogonal. Sequence divergence and protein embeddings
only prioritize experiments. A complete integrase/site/RDF matrix remains a
release-blocking experimental dependency.

## State gating

Wrong-order topology can delete sequence, so one-hot drug selection and exact
state matching are hard Boolean requirements. The exported controllers contain
annotated state-gate interfaces, but their promoter/operator sequences are
synthetic placeholders. Boolean logic is validated; in-cell regulatory
performance is unresolved. A chemistry-only, externally verified sequential
fallback is therefore the first recommended experiment.

## Chemical sensors

The leading set is IPTG/P_lac, aTc/P_LtetO-1, and L-arabinose/P_BAD. This
preserves the collaborator's strongest conventional choices while avoiding a
second CRP-dependent rhamnose sensor. P_BAD is assigned to the final forward
step, where slower and heterogeneous activation is less likely to expose a
premature downstream channel. Exact promoters and strain modifications remain
to be selected from measured Marionette-compatible implementations.

## Sequence status

Integrases, RDFs, sites, and pACYC177 backbone sequence have stable provenance.
Payload barcodes, state gates, insulators, RBSs, and terminators are synthetic
computational placeholders. Consequently, these records are candidate
artifacts, not synthesis-ready constructs.
