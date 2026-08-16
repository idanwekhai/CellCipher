# Design comparison

## Architecture choice

| Architecture | Exact conservative inverse | Three addressable channels | Main rejection reason |
|---|---|---|---|
| Large serine integrase plus RDF | yes in cognate chemistry | plausible, requires matrix | selected |
| Bridge-RNA recombinase | potentially programmable | not yet a mature reversible three-channel system | insufficient direct reverse-cycle evidence |
| Tyrosine recombinases | possible with engineered sites | crosstalk and host-factor context | weaker direction-control fit |
| Natural invertases | system-specific | limited portable channel panel | poor programmability |
| CRISPR cut and repair | no exact conservative guarantee | guide-programmable | repair outcomes are not byte-exact |

The LSI/RDF design was selected because product sites encode direction and the
same physical substrate can be reversed without double-strand-break repair.
Bxb1 supplies direct mechanistic and cellular reversal precedent
[@Ghosh2003Bxb1Orientation; @Ghosh2006Bxb1RDF; @Bonnet2012Rewritable].
PhiC31 supplies a separately characterized RDF and reversal precedent
[@Khaleel2011PhiC31RDF; @Farruggio2012PhiC31Reverse]. TP901-1 supplies an
independently sourced serine-integrase channel with sequence-resolved minimal
sites and an annotated excisionase [@Breuner2001TP901; @Stoll2002TP901].

## Channel-set decision

The provisional trio is:

1. Bxb1 integrase with gp47 RDF.
2. PhiC31 integrase with gp3 RDF.
3. TP901-1 integrase with Xis.

Bxb1 is the anchor because its site identity and RDF direction control are
particularly well characterized. PhiC31 is retained for depth of evidence, but
its known integrase-only excision concern lowers confidence in long-term state
stability. TP901-1 adds phylogenetic and sequence diversity. Protein-language
model similarity did not justify replacing any channel, and cannot establish
orthogonality.

PhiBT1, SprA/SprB, and newer RDF-matched LSIs remain reserve candidates. They
were not substituted merely to increase model diversity because the present
set has stronger sequence provenance and reversal evidence. A measured full
matrix can still force replacement.

## Controller format

The exported pACYC177-derived controllers are interoperable development
artifacts, not the preferred final deployment format. A single-copy
chromosomal controller is preferred to reduce copy-number variation, basal
leakage, and burden. The message cassette itself is single-copy and
locus-independent; no landing locus or homology arms were invented.

## Collaborator sensor proposal

The conventional proposal was evaluated as IPTG/P_lac, aTc/P_LtetO-1, and
an arabinose-family third input, with rhamnose considered as an alternative.
The retained set is IPTG, aTc, and L-arabinose/P_BAD.

- IPTG/P_lac is accepted as a familiar, independently repressible input.
- aTc/P_LtetO-1 is accepted as a strong orthogonal partner, with TetR supply
  and aTc light sensitivity treated as implementation constraints.
- L-arabinose/P_BAD is accepted provisionally and assigned to the final forward
  step, where slower or heterogeneous activation is less likely to expose a
  premature downstream deletion substrate.
- L-rhamnose is not selected for the three-input baseline because adding a
  second CRP-linked sugar sensor increases global metabolic coupling and
  media-dependent behavior without adding a needed logical capability.

Marionette demonstrates that optimized small-molecule sensors can provide a
measured starting panel in *E. coli* [@Meyer2019Marionette]. It does not validate
these sensors under the burden of six recombination proteins or prove the exact
one-hot state-gate circuit. Exact promoter/operator sequences therefore remain
unresolved.

## Smallest discriminating experiment

The first experiment should not use the autonomous controllers. Use one
single-copy-equivalent register substrate and deliver one cognate protein set
at a time:

1. Verify each forward inversion and reverse inversion independently.
2. Measure the complete three-integrase by three-site matrix.
3. Measure the complete three-integrase by three-RDF reverse-direction matrix.
4. Execute externally timed `ABC`, purify or clone the State 3 product, then
   execute `CBA`.
5. Require long-read or full-amplicon sequence identity and population state
   purity, not reporter color alone.

Only after this passes should chemical sensors and sequence-level state gates be
added.
