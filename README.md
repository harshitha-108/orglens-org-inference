# OrgLens · focused recovery candidate

The focused recovery build in this checkout uses the existing evidence-based workflow and a fresh, fixed 500-company synthetic cohort. The app keeps the earlier frozen baseline selectable; both cohorts use their own matching runtime and metrics. The previously published deployment is unchanged until approval.

Focused scale-up: **74,501 visible employees**, **16,129 proposals**, **100.00% scored precision**, **21.65% coverage**, **49.54% visible-manager candidate recall**. These results are synthetic. There are no calibrated individual probabilities or confirmed reporting lines.

See [Focused recovery: evaluation and reproduction](docs/FOCUSED_RECOVERY.md). The original baseline documentation below is retained for reference.

# OrgLens · evidence-based experimental recovery

OrgLens turns flat, messy employee records and synthetic organisational documents into a **partial graph of possible direct managers**. Every proposal is unverified and has source-linked evidence. Where evidence is insufficient, the system abstains. The app does not establish real reporting relationships or purchasing authority.

Existing experimental app: https://orglens-recovery-experimental-bvn4yjeusj4tg67e6zekyv.streamlit.app/ . This publication package is a **reviewed local candidate** and includes an approved-for-review UI polish that is not yet deployed. Original v1 remains a separate historical system at https://github.com/harshitha-108/orglens . It cannot reproduce these recovery results.

## Measured results

| Frozen messy-source scale-up | Result |
|---|---:|
| Synthetic companies / visible employees |500 /74,612|
| Experimental proposals |9,004|
| Correct / wrong / unscorable |8,641 /360 /3|
| Precision on9,001 scored proposals |96.00%|
| All-visible employee coverage |12.07%|
| Candidate recall, a true manager visible |31.92%|
| Companies with proposals |466|
| Structural violations |0|
| Published / externally confirmed relationships |0 /0|

The separate prior30-company, company-disjoint synthetic validation had4,483visible employees,517correct/23wrong proposals,95.74%precision and12.05%coverage. The500-company run is scale-up under a frozen synthetic distribution, **not another independent holdout**. Neither proves real-world accuracy. Individual confidence probabilities are unavailable; pooled precision must not be assigned to an employee.

## How it works and key decisions

1. Establish teams, roles, staffing, histories and people-management responsibility before selecting direct-reporting truth.
2. Project committed facts to public publication facts. Publish imperfect biographies, directories, responsibility pages and historical announcements without reading selected reporting edges. Visibility and observation noise have separate random streams.
3. Extract observable claims with exact source spans, dates and copy-family provenance. The conservative M2.5C source-only baseline combines team membership and named people-accountability, or abstains. Its candidate sets are unranked and scores remain null.
4. Freeze predictions before a separate evaluator opens synthetic truth. Unknown truth is not silently scored negative. All employees and wrong/unscorable proposals remain in the runtime.

The recovery improvement is associated with richer synthetic evidence/distribution, not a demonstrated new inference algorithm. The unchanged M2.5B reference produced the same development outcomes. Do not claim that ranking or production calibration was improved.

## Source map

- `experiments/product_recovery_v1/{foundation,publication}.py`: authoritative recovery generation/publication; `config.json` is the frozen noise/disclosure/size configuration.
- `experiments/product_recovery_v1/inference/`: exact frozen extractor, predictor, source-input contracts, isolated prediction runner and evaluator, copied unchanged from recovery's M2.5C baseline.
- `experiments/v4_m25a/`, `v4_m24_history/`, `v4_m22_sources/`: **active transitive dependencies** of recovery facts/temporal validation/public projection/RNGs. Only required modules/configs are included; these are not the historical v1 engine or unrelated experiment outputs.
- `experiments/product_recovery_v1_scale500/` and `product_recovery_v1_validation/`: original orchestration/audit source and exact predeclared seed protocols. Their historical `main()` paths require unpublished prior freeze assets; they are provided for traceability, not represented as standalone turnkey commands.
- `tools/reproduce.py`: new portable orchestration, importing frozen functions unchanged. See the tested/not-tested distinction below.
- `SOURCE_MANIFEST.json`: relative-path sizes and SHA256 hashes of35 authoritative source/config/contract files, checked against available scientific freezes.
- `evidence/`: byte-identical frozen aggregate scale-up and validation metrics. `examples/`: one fixed observable-only company and its six frozen scientific prediction outputs. No per-employee correctness labels, private facts or saved true edges are distributed.
- `app.py`, `adapter.py`, `runtime/`: Streamlit presentation and the exact source-only frozen SQLite. The app does not import the generator/evaluator or regenerate data.
- `docs/EVALUATION_METHODOLOGY.md`: denominators, versioning, limitations and audit caveats. `docs/ASSESSMENT_BRIEF.md` is the original task.

## Setup and tested commands

Use Python3.13. From this package root:

```sh
python -m venv .venv
# Activate .venv using your platform's normal command.
python -m pip install -r requirements-dev.txt
python tools/reproduce.py verify
python tools/reproduce.py plan --cohort scale500
python tools/reproduce.py plan --cohort validation30
python tools/reproduce.py infer-example --out _reproduction/example
python -m pytest tests/test_publication_package.py -p no:cacheprovider -q
python -m streamlit run app.py
```

Actually tested in this preparation task: source verification, both fixed cohort plans, the existing-company source-only replay and the three package tests. The replay produced six scientific JSON outputs equal to the frozen example, with an enforced truth-read boundary; path-bearing access logs are not distributed. The eight existing exhaustive application/data/citation tests also passed in the UI staging workspace. The app uses existing dependency pins; an entirely fresh dependency installation was not repeated here. Package-local import/startup smoke checks are recorded in the review report. The runtime/metric hashes remain unchanged.

The example replay is a regression check, not a new performance experiment. Output folders must not already exist. No dataset was regenerated in this preparation task.

### Full fixed-cohort workflow — provided, NOT executed in this exported package

```sh
python tools/reproduce.py generate --cohort scale500 --out _reproduction/scale500
python tools/reproduce.py predict --run _reproduction/scale500
python tools/reproduce.py evaluate --run _reproduction/scale500
```

For the fixed30-company cohort, substitute `validation30` and a fresh `_reproduction/validation30` folder.500seeds are4090400–4090899;30validation seeds4080400–4080429. These are reproductions of consumed cohorts, never fresh validation. No seed replacement/resampling/tuning is allowed. The wrapper writes newly generated truth only below ignored `_reproduction/`, runs the predictor as a separate source-only process, then invokes the frozen evaluator separately.

**Do not claim that this portable full workflow, cloud regeneration or byte-identical SQLite reconstruction has been tested.** The original full runs were completed in the protected research workspace; the new exported orchestration has only import/plan/example verification here. Full outputs may differ in formatting across platforms; example scientific comparison uses parsed JSON. The historical runtime builder is supplied unchanged but its research paths are not a portable app-regeneration command. The app intentionally serves the supplied immutable runtime.

## Limitations and publication safety

Missing evidence leaves65,608employees without a proposal. Low-disclosure precision is88.31%. All360scored errors cite misleading provider affiliations.30co-management cases have wrong proposals and co-manager recovery is not solved. Source independence, disclosure rates and realism are modelling assumptions. Internal retrieval95%, coverage15%, calibration and targeted manager-removal requirements remain unmet. A structurally valid graph can still be wrong.

No existing evaluation truth, personal correctness verdicts, credentials, environment files, test XML, caches or review archives belong in publication. Do not upload `_reproduction/`; `.gitignore` adds defensive exclusions. `.gitattributes` preserves exact source bytes for freeze verification. Inspect the explicit publication manifest before committing. Review reports, dependency audit folders and historical corpora remain outside this package.

## AI-assisted development

Codex assisted implementation, debugging, tests, packaging and documentation. Frozen hashes, source-only boundaries, exact citations and company-disjoint evaluation support engineering review; AI assistance and engineering tests are not independent domain or real-world validation. Negative historical findings and current error patterns are acknowledged rather than replaced with favourable results.
