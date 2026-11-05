# Firmable requirements and relationship evidence

| Original requirement or supporting check | Status |
|---|---|
| At least 500 synthetic companies | Met. The focused runtime has 500. |
| At least 100 employees per company | Met. Visible company rosters range from 100 to 199 and total 74,501. |
| Varied industries, company sizes, functions and seniority | Met in the synthetic design. Five archetypes span clinical, regulated, product, regional services and multi-site structures. Real-world representativeness remains unverified. |
| Inconsistent titles, abbreviations and missing fields | Met. The frozen messy observation pipeline produces these variations. |
| Infer reporting lines from observable employee information | Met. The focused runtime contains 16,129 unverified proposals. |
| Confidence on each inferred line | Implemented as an ordinal evidence rating. A calibrated probability remains unavailable. |
| Leave managers unresolved when evidence is insufficient | Met. The frozen focused cohort has 58,372 employees without a proposal. |
| Design the data so inference can be checked | Met. Hidden synthetic truth is scored separately from source-only inference. |
| Hosted company selection and inferred org charts | Met in the existing public recovery app. It also supports employee exploration and citations. |
| Git repository with source, generator and a short write-up | Met by the existing recovery repository and README. The public package has tested source-only example replay. Full end-to-end replay from a public-only clone remains unverified. |
| Submit within five days of receipt | Pending user submission. The assessment brief states five days and the user supplied November 5, 2026. |

## Evidence rating

The frozen proposal stays intact. The local profile rates its cited observable records by checking dated, unflagged employee membership and manager duty claims for the named contacts, excluding uncorroborated provider records and counting document families rather than copies. Separate families are required for a usable pair. A recorded alternative or weaker candidate evidence takes precedence over extra corroboration. A third family distinguishes corroborated from supported evidence. Missing support yields limited evidence. Unresolved employees receive no rating. Distinct document families do not prove independent reporting in the real world.

### Reporting-line confidence (evidence-based)

- **Corroborated.** Dated, usable team and manager-duty records come from at least three source families, with no recorded candidate concerns.
- **Supported.** Two separate source families provide dated, usable team and manager-duty records, with no recorded candidate concerns.
- **Supported with caveats.** A usable pair from separate source families supports the suggestion, but the saved candidate records include a reason flag or another possible manager. This label takes precedence over additional corroboration.

These ratings describe the strength of the available evidence. They are not calibrated probabilities or independently confirmed reporting relationships.

The fixed evidence-rating code had SHA-256 892e4eeabdb6d73bb214d6c7914feefc22ebcdd2a7250eaa980a2555352eb0c8 before the retrospective audit. Ratings were computed before the separate evaluation step opened the saved synthetic truth.

| Evidence rating | Focused runtime proposals | Coverage of 74,501 | Existing 30-company focused validation correct / wrong | Same companies, older baseline correct / wrong |
|---|---:|---:|---:|---:|
| Corroborated | 7,474 | 10.03% | 429 / 0 | 0 / 0 |
| Supported | 7,057 | 9.47% | 447 / 0 | 507 / 0 |
| Supported with caveats | 1,598 | 2.14% | 98 / 0 | 0 / 0 |
| Limited | 0 | 0.00% | 0 / 0 | 1 / 20 |

Each populated focused validation band had 100% observed precision. The same validation companies have already been used to evaluate inference. This is a retrospective diagnostic, and the older baseline's errors reflect a different evidence and proposal policy. Neither result independently validates the ordering or supports numerical calibration. No fresh cohort was generated, no probability was fitted, and Brier score and calibration error are inapplicable.

## AI use

The brief states, “Firmable is fully **AI-native**. AI is the workflow, not a tool bolted on.” It does not impose an AI restriction or an explicit disclosure format. Codex assisted implementation, testing and documentation. The existing AI usage history remains available.
