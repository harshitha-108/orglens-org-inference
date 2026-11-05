# OrgLens

[Open the live Streamlit demo](https://orglens-demo.streamlit.app/) · [Firmable assessment brief](docs/ASSESSMENT_BRIEF.md)

OrgLens suggests direct managers from messy synthetic employee records and organisational documents. Pick a company to explore its partial reporting chart, search for an employee and inspect the cited evidence. OrgLens leaves a manager unresolved when the records are insufficient or ambiguous. Every displayed line is an unconfirmed proposal.

## Run locally

Use Python 3.13. From the repository root, create and activate a virtual environment, then install the runtime dependencies and start Streamlit.

```sh
python -m venv .venv
# Activate .venv using your platform's normal command.
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app reads the bundled [focused runtime](runtime/recovery_focused.sqlite). Dataset generation and evaluation run separately.

## Repository guide

| Path | Where to look |
|---|---|
| [`app.py`](app.py), [`adapter.py`](adapter.py), [`chart_layout.py`](chart_layout.py), [`chart_component/`](chart_component/) | Streamlit pages, read-only SQLite access, chart layout and chart interactions. |
| [`experiments/product_recovery_v1/`](experiments/product_recovery_v1/) | Dataset generation, observation and publication. The base generator is in [`foundation.py`](experiments/product_recovery_v1/foundation.py), with size, disclosure and noise settings in [`config.json`](experiments/product_recovery_v1/config.json). See the experiment guide below for the active inference path. |
| [`confidence.py`](confidence.py) | Relationship evidence ratings, calculated from cited source records. |
| [`evidence/`](evidence/), [`runtime/`](runtime/) | Frozen evaluation metrics and SQLite datasets. The [focused release manifest](evidence/focused_release.json) ties the active runtime and metrics to their SHA-256 hashes. |
| [`tests/`](tests/), [`tools/reproduce.py`](tools/reproduce.py), [`examples/`](examples/) | Regression tests, source verification, cohort plans and a source-only example with expected outputs. |
| [`docs/`](docs/), [`SOURCE_MANIFEST.json`](SOURCE_MANIFEST.json) | Assessment, methodology, limitations and hashes for the 35 source and configuration files covered by the original publication check. |

### Experiment directories

- [`product_recovery_v1/focused_improvement/`](experiments/product_recovery_v1/focused_improvement/) contains the current focused release's added source publication, claim extraction, direct-manager inference and evaluation runner.
- [`product_recovery_v1/inference/`](experiments/product_recovery_v1/inference/) contains the earlier source-only baseline, shared input contracts and evaluator. The focused runner uses that evaluator and runs the baseline arm for paired comparisons.
- [`product_recovery_v1_scale500/`](experiments/product_recovery_v1_scale500/) and [`product_recovery_v1_validation/`](experiments/product_recovery_v1_validation/) contain the earlier recovery cohort protocols, orchestration and audit code. They support historical comparisons and the portable reproduction tool.
- [`v4_m22_sources/`](experiments/v4_m22_sources/), [`v4_m24_history/`](experiments/v4_m24_history/) and [`v4_m25a/`](experiments/v4_m25a/) supply shared generator code for organisational facts, historical validation and source projection. Their versioned paths are used by imports and freeze checks.

## How it works

1. Generate teams, roles, staffing history and management duties before assigning hidden reporting lines.
2. Publish synthetic records from organisational facts, with separate randomness for contact visibility and observation noise. The focused release adds dated staff registers and distinguishes leadership-team membership from other team membership.
3. Extract team membership and people-management claims with exact text spans, dates and source families. Suggest a manager only when compatible records support the relationship. A provider listing or a senior title alone cannot establish a reporting line.
4. Freeze proposals before evaluating against hidden synthetic truth. Unknown truth is excluded from scored precision and included in coverage.

The three ratings describe evidence quality. **Corroborated** uses at least three eligible source families with no recorded candidate concern. **Supported** uses two separate eligible families with no recorded candidate concern. **Supported with caveats** has a usable pair plus a recorded concern or alternative. Unresolved employees receive no rating. These categories provide no calibrated individual probability or independent confirmation. See [the rating definitions and limitations](docs/CONFIDENCE_AND_ASSESSMENT.md).

## Current release and historical comparisons

The live app serves the **focused 500-company cohort**. Model Performance displays earlier results for comparison alongside the active release.

| Focused synthetic scale-up | Result |
|---|---:|
| Companies / visible employees | 500 / 74,501 |
| Proposed reporting lines | 16,129 |
| Scored precision | 100.00% (16,129 / 16,129 scored) |
| Employee coverage | 21.65% (16,129 / 74,501) |
| Candidate recall among employees with a visible true manager | 49.54% (33,838 / 68,302) |
| Correct two-link chains | 2,838 |
| Employees without a proposal | 58,372 |

The [focused scale-up results](evidence/focused_scale_metrics.json) and [paired 30-company validation](evidence/focused_validation_metrics.json) are distinct synthetic evaluations. The [earlier scale-up](evidence/scale_metrics.json) used a different 500-company cohort with 74,612 visible employees, 9,004 proposals and 96.00% scored precision. The [earlier validation](evidence/validation_metrics.json) and [historical methodology](docs/EVALUATION_METHODOLOGY.md) belong to that earlier workflow.

Observed synthetic precision does not establish real-world accuracy or purchasing authority. Coverage is limited by missing, stale and ambiguous evidence, and shared management can remain unresolved.

## Tests and reproduction

```sh
python -m pip install -r requirements-dev.txt
python tools/reproduce.py verify
python -m pytest tests -p no:cacheprovider -q
python tools/reproduce.py plan --cohort scale500
python tools/reproduce.py plan --cohort validation30
python tools/reproduce.py infer-example --out _reproduction/example
```

Source verification and all 12 tracked tests passed in the existing environment. The earlier cohort plans were checked, and the earlier source-only example replay matched six frozen JSON outputs without hidden truth. Use a new output folder for that replay.

The `generate`, `predict` and `evaluate` commands in [`tools/reproduce.py`](tools/reproduce.py) target the earlier cohorts. For the focused experiment, see [the focused run and score commands](docs/FOCUSED_RECOVERY.md#reproduction). Those commands were exercised in the internal workspace. Full end-to-end reproduction and SQLite reconstruction from a clean public clone remain unverified. Keep generated truth in local output directories.

[`PUBLICATION_MANIFEST.json`](PUBLICATION_MANIFEST.json) is the historical review-package snapshot. Use the focused release manifest to verify current runtime and evaluation files. The older `runtime/recovery.sqlite` remains the default for adapter calls that omit the database path, so retain it.

Codex assisted implementation, debugging, testing, packaging and documentation.
