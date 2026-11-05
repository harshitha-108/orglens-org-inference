# Focused recovery: evidence and evaluation

The original recovery cohort remains selectable. Focused recovery uses a fresh synthetic cohort and adds independently sampled staff-register and line-management statements derived from organisational facts established before selecting parents. Substantive and leadership-team membership are matched separately. A provider listing alone cannot support a proposal. Competing, incomplete and stale evidence can still cause abstention.

A proposal is not a published or independently confirmed reporting line. Individual correctness probabilities are unavailable. Precision counts correct proposals among scorable proposals; coverage counts proposals across all visible employees. Candidate recall measures retrieval where a true manager is visible. A correct two-edge chain requires both consecutive proposals to match scorable synthetic truth.

The paired development and independent synthetic validation cohorts contained 15 and 30 companies respectively. Fixed seeds start at 4100400 and 4110400; the unpaired 500-company scale-up starts at 4120400. Code and settings were frozen before scoring. The older scale-up is a different cohort. Perfect observed precision on a cohort with no wrong predictions is not a reliability guarantee; a bootstrap cannot estimate errors it never observed. Synthetic disclosure, wording and reporting structures do not establish real-world accuracy. M0 production calibration and publication requirements remain unmet.

## Reproduction

From the assessment root, use Python with the repository development requirements installed. The following entry points were run on the internal assessment workspace. Do not overwrite an existing frozen run. The staged publication candidate contains the focused code and safe aggregates, not the private generated evaluation artifacts. Complete end-to-end replay from a public-only clone has not been tested.

```text
python -B -m experiments.product_recovery_v1.focused_improvement.experiment run development
python -B -m experiments.product_recovery_v1.focused_improvement.experiment score development
python -B -m experiments.product_recovery_v1.focused_improvement.experiment run validation
python -B -m experiments.product_recovery_v1.focused_improvement.experiment score validation
python -B -m experiments.product_recovery_v1.focused_improvement.experiment run scale
python -B -m experiments.product_recovery_v1.focused_improvement.experiment score scale
```

Each run freezes source-only predictions before the separate scorer opens hidden labels. The runtime is built from visible contacts, source documents, claims and predictions only. Its release manifest binds the database and aggregate metrics to their hashes. Never publish generated private truth, individual evaluation labels, or prediction access logs.
