# Structural hypotheses

No structure prediction is presented as validation. The following are
experiment-generating hypotheses derived from known LSI/RDF direction control
and the computed topology.

## H1: RDF specificity is a protein-interface property

Cognate RDFs are expected to stabilize a reverse-competent integrase
conformation on `attL/attR`, while noncognate RDFs may bind weakly, inhibit, or
partially redirect another integrase. The broad ESM-2 similarity range does not
resolve this interface. Test every integrase with every RDF on cognate and
noncognate product sites. Variable noncognate interactions are already a
documented concern [@MacDonald2024Orthogonality].

## H2: central crossover identity is necessary but not sufficient

The exact crossover indices and half-site products are represented in the
simulator. Matching central dinucleotides alone should not be treated as enough
for productive noncognate recombination because arm contacts and synaptic
geometry also contribute. Test central-site variants and full noncognate sites
separately [@Ghosh2003Bxb1Orientation].

## H3: topology converts timing errors into deletion substrates

In the wrong DNA state, the same cognate pair can become parallel. The
simulator predicts deletion/excision rather than inversion. This is a physical
geometry hypothesis that should be checked with purified wrong-state substrates
before autonomous control is attempted.

## H4: fusion and degradation tags can perturb reversal

Any fluorescent fusion, solubility tag, or rapid degradation tag may alter
integrase oligomerization or RDF binding. Untagged proteins should establish
the baseline. Tagged versions require direct forward and reverse kinetic
comparison, not only endpoint reporter activity.

## H5: native-expression imbalance will dominate controller behavior

The retained phage CDSs differ strongly in size and context. Translation-window
folding values also vary, but the annotated RBSs are placeholders. Expression
stoichiometry, proteolysis, and post-pulse persistence are expected to dominate
over small MFE differences. Measure protein time courses and tune each channel
independently before combining them.
