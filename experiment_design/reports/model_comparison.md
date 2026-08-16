# Model comparison and ablation

## Runs

| Analysis | Scope | Result | Decision effect |
|---|---|---|---|
| Deterministic topology | all states and orders | exact `ABC → CBA` round trip; all wrong orders classified | establishes computational topology |
| Conventional sequence analysis | three constructs plus states | GC, ORF, repeat, motif, restriction, and host exact-site reports | flags assembly and expression hazards |
| Neutral-payload Pareto search | six 96-bp payloads, multiple seeds | two non-dominated candidates | selected lower-homopolymer candidate |
| ESM-2 15B | three integrases and three RDFs | 5,120-dimensional embeddings and pairwise cosine table | no channel change |
| ViennaRNA | nine 204-nt RBS/start windows | MFE and structures at 37 °C | no sequence promotion or rejection |

## ESM-2 interpretation

The highest integrase similarity is Bxb1 versus phiC31, 0.8936. The lowest is
phiC31 versus TP901-1, 0.7581. RDF similarities are lower and broader, 0.4611
to 0.7049. The result is consistent with shared broad protein classes but does
not map attachment-site specificity or RDF switching.

The model could have changed the design only by identifying a near-redundant
pair that justified a replacement review. It did not supply enough evidence to
override direct provenance and reversal literature. The practical consequence
is experimental, include all noncognate integrase/site and integrase/RDF pairs
rather than presuming independence.

## ViennaRNA interpretation

The nine windows span -83.5 to -40.3 kcal/mol, or -0.4093 to -0.1975
kcal mol-1 nt-1 after length normalization. Forward C and reverse C integrase
windows are the least negative; reverse A integrase is the most negative.
These are relative folding flags only. The windows contain synthetic gate and
RBS placeholders, so optimization against these values would create false
precision.

## Skipped analyses

- Evo2 whole-construct scoring was skipped because genomic likelihood cannot
  resolve state-gate behavior, crosstalk, or exact recombination chemistry.
- Regulatory ML was skipped because the exact promoter/operator sequences are
  unresolved. A score for placeholders would not guide a buildable circuit.
- Structural complex prediction was skipped because interface confidence would
  not replace the required noncognate biochemical matrix, and no single
  structural answer would alter the topology.

## Ablation

Removing either ESM-2 or ViennaRNA leaves the selected channel trio, payload
candidate, and every hard constraint unchanged. This is recorded in
`model_ablation.csv`. The models add prioritization and anomaly checks, not
proof. Deterministic topology and source provenance remain the decision-bearing
analyses.
