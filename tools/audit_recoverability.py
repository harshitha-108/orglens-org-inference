"""Read-only diagnostic of where frozen synthetic reporting links are lost.

This is a separate EVALUATION tool. It may read saved truth after loading
frozen predictions; it never writes to the app, inference code or runtime.
Its public output is aggregate counts only (no employee IDs or true edges).

Usage from repository root, with separately preserved private truth:
 python tools/audit_recoverability.py \
   --source-root data/<cohort>/source_inputs \
   --prediction-root reports/<cohort>/predictions \
   --truth-root data/<cohort> \
   --out reports/<new_audit>/recoverability.json

The category `parsed_compatible_pair` is a mechanical upper-bound diagnostic,
NOT a proof that a direct manager is uniquely identifiable.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

BLOCK = {
    "date_unknown", "stale", "future", "future_effective", "ended",
    "ambiguous_alias", "unverified_alias", "event_only",
    "shared_responsibility", "unspecified_subset", "negated",
}

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def usable(claim):
    return not BLOCK.intersection(claim.get("flags", []))

def compatible_pair(member, manager):
    """Approximation of the documented positive-pair eligibility checks."""
    if not usable(member) or not usable(manager):
        return False
    if member["team"] != manager["team"]:
        return False
    if member.get("scope") and manager.get("scope") and member["scope"] != manager["scope"]:
        return False
    if member["document_family_id"] == manager["document_family_id"]:
        return False
    return True

def audit_company(folder, predroot, truthroot, label):
    case = folder.name
    contacts = read(folder / "contacts.json")
    visible = {c["employee_id"] for c in contacts}
    predictions = read(predroot / case / (label + "_predictions.json"))
    claims = read(predroot / case / (label + "_claims.json"))
    truth = read(truthroot / case / "technical_audit" / "truth.json")
    if len(predictions) != len(visible) or {p["employee_id"] for p in predictions} != visible:
        raise ValueError("Incomplete or duplicate predictions in " + case)

    targets = defaultdict(set)
    for rel in truth["relationships"]:
        if rel["relation_type"] == "direct_people_management":
            targets[rel["employee_id"]].add(rel["counterpart_employee_id"])
    by_employee = defaultdict(list)
    by_manager = defaultdict(list)
    for c in claims:
        if c["kind"] == "membership" and c.get("contact_id") in visible:
            by_employee[c["contact_id"]].append(c)
        if c["kind"] == "people_accountability" and c.get("contact_id") in visible:
            by_manager[c["contact_id"]].append(c)

    counts = Counter()
    for p in predictions:
        eid = p["employee_id"]
        actual = targets[eid]
        mid = p.get("manager_id")
        known = truth["evaluation_status"].get(eid) == "complete"
        if not known:
            counts["unknown_truth"] += 1
            continue
        if not actual:
            counts["no_direct_manager_in_truth"] += 1
            counts["no_direct_manager_selected"] += mid is None
            continue
        counts["with_true_manager"] += 1
        counts["co_managed"] += len(actual) > 1
        present = actual & visible
        if not present:
            counts["true_manager_absent_from_roster"] += 1
            continue
        counts["true_manager_visible"] += 1
        if mid in actual:
            counts["correctly_selected"] += 1
        elif mid is not None:
            counts["wrongly_selected"] += 1
        else:
            counts["abstained_with_visible_manager"] += 1

        members = [c for c in by_employee[eid] if usable(c)]
        if members:
            counts["has_usable_membership"] += 1
        matching = [
            (m, a) for true_mid in present
            for m in members for a in by_manager[true_mid]
            if compatible_pair(m, a)
        ]
        if matching:
            counts["has_compatible_parsed_pair_for_true_manager"] += 1
        candidate_ids = {
            c.get("manager_id") for c in p["candidates"]
            if c.get("manager_id") is not None
        }
        if candidate_ids & present:
            counts["true_manager_in_candidate_pool"] += 1
            if mid is None:
                counts["retrieved_but_abstained"] += 1
            elif mid not in actual:
                counts["retrieved_but_selected_wrong"] += 1
        else:
            counts["true_manager_missing_from_candidate_pool"] += 1
            if not members:
                counts["missing_candidate_and_no_usable_membership"] += 1
            elif not matching:
                counts["missing_candidate_and_no_compatible_parsed_pair"] += 1
            else:
                counts["missing_candidate_despite_compatible_parsed_pair"] += 1

        if any(c.get("manager_id") not in actual for c in p["candidates"]):
            counts["had_competing_candidate"] += 1
        if any(c["kind"] == "membership" and c.get("contact_id") == eid and
               c["source_id"].startswith("provider") for c in claims):
            # Source IDs are hashed in this project; retained only as a placeholder
            # for a future explicit provenance join, not a trustworthy detector.
            counts["provider_source_id_heuristic_not_used"] += 0
    return counts

def run(source_root, prediction_root, truth_root, label):
    source = Path(source_root)
    cases = sorted(p for p in source.iterdir() if p.is_dir() and p.name.startswith("company_"))
    if not cases:
        raise ValueError("No company folders found")
    totals = Counter()
    for case in cases:
        totals.update(audit_company(case, Path(prediction_root), Path(truth_root), label))
    return {
        "label": label,
        "companies": len(cases),
        "counts": dict(sorted(totals.items())),
        "interpretation": [
            "This audit reads hidden truth only in evaluation; the predictor is not run.",
            "Candidate-pool counts are based on existing frozen predictions.",
            "Compatible parsed evidence does not prove that a direct manager is uniquely identifiable.",
            "No source-generation or predictor changes are made by this audit.",
        ],
    }

def main():
    ap = argparse.ArgumentParser()
    for arg in ("source-root", "prediction-root", "truth-root", "out"):
        ap.add_argument("--" + arg, required=True)
    ap.add_argument("--label", choices=["clean", "messy"], default="messy")
    args = ap.parse_args()
    result = run(args.source_root, args.prediction_root, args.truth_root, args.label)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
