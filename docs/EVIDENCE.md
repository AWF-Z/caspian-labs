# Evidence

This repository publishes sanitized evidence for CASP's benchmark and
historical results. The underlying artifacts and claim boundaries are described
below.

## WANDR matched 45-task result

CASP produced 45 genuine official metric-bearing receipts on the matched
45-task WANDR surface. The sealed aggregate reports:

| Measure | CASP | Published leader |
|---|---:|---:|
| Soft F1 | 0.583303 | 0.447 |
| Hard F1 | 0.492648 | 0.224 |
| Aggregate soft precision | 0.917306 | Not used in the comparison headline |
| Tasks with genuine official scores | 45 | 44 for the published leader |

The strongest published matched result was Perplexity Search as Code at xhigh.
CASP was 30.5% higher on soft F1 and 120% higher on hard F1. The latter is the
same result as 2.20 times the leader's hard F1, expressed as a relative increase
for consistency.

WANDR's soft measure captures research quality and coverage. Its hard measure
requires the complete evidence structure for a candidate to be correct. CASP's
largest advantage was therefore on complete, evidence-backed research rather
than unsupported volume.

### Published matched field

| System | Best published setting | Soft F1 | Hard F1 |
|---|---|---:|---:|
| CASP 5.0 | Caspian Labs aggregate | 0.583303 | 0.492648 |
| Perplexity Search as Code | xhigh | 0.447 | 0.224 |
| Anthropic Managed Agents | high | 0.262 | 0.099 |
| OpenAI Responses API | high | 0.153 | 0.073 |
| Exa Agent | xhigh | 0.111 | 0.036 |
| Parallel Tasks | ultra8x | 0.080 | 0.035 |
| Gemini Deep Research | max | 0.074 | 0.028 |

Comparator values are from [WANDR Table 6](https://arxiv.org/html/2608.14747v1#S5.T6).
CASP values come from the sealed official-evaluator aggregate whose public hash
is recorded in [`result.json`](../evidence/wandr-s45/result.json).

### Boundary

The claim is limited to the identical matched 45-task surface and official
evaluator. The sealed aggregate combines preserved genuine official task
receipts. It is not a full-500 leaderboard claim, a claim about every unseen
research task, or an endorsement by Perplexity, WANDR's authors, or any compared
company.

## Historical clinical opportunity result

Across five frozen opened historical clinical-development folds, the CASP
opportunity-ranking lineage placed 3,821 of 8,031 later-positive opportunities
inside the top 0.9% review slice. The matched GPT-5.6 Sol-authored historical
strategy placed 3,155.

That is 47.5781% versus 39.2853%, an 8.2929 percentage-point difference and
21.1094% relative lift. Exact deterministic replay reproduced the result.

The test used official historical AACT cutoff archives derived from public
ClinicalTrials.gov records. The five folds were opened development evidence,
not a new prospective examination. The comparison was a frozen historical
strategy authored with OpenAI's flagship GPT-5.6 Sol, not live ChatGPT or an
OpenAI-endorsed evaluation. The stricter precommitted activation gate did not
pass.

The public summary is in
[`evidence/clinical-opportunity/result.json`](../evidence/clinical-opportunity/result.json).

## What remains private

The result-bearing engine, task compilers, evaluator reconstruction, repair
logic, full receipts, candidate outputs, ranking artifacts, private labels,
datasets, and internal infrastructure are not public. Qualified diligence can
inspect additional evidence under an appropriate confidential process.
