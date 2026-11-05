"""Describe the support for a frozen proposal using cited observable records only."""


def evidence_strength(prediction, citations):
    """Return an ordinal evidence description, never a correctness probability."""
    manager = prediction["manager_id"]
    if not manager:
        return None

    families = {"membership": set(), "people_accountability": set()}
    expected = {"membership": prediction["employee_id"], "people_accountability": manager}
    for claim, document in citations:
        kind = claim["kind"]
        if (
            kind in families
            and claim.get("contact_id") == expected[kind]
            and claim.get("published_at")
            and not claim.get("flags")
            and document.get("source_type") != "synthetic_contact_provider"
            and document.get("provenance_status") != "uncorroborated_provider"
            and claim.get("document_family_id")
        ):
            families[kind].add(claim["document_family_id"])

    membership, duty = families.values()
    alternatives = prediction.get("candidates", [])
    cautions = any(c.get("reasons") or c.get("manager_id") != manager for c in alternatives)
    if not any(a != b for a in membership for b in duty):
        return ("Limited", "The cited records do not show a usable team and management pair from separate document families.")
    if cautions:
        return ("Supported with caveats", "A dated pair supports the suggestion, but the records also contain alternatives or weaker evidence.")
    if len(membership | duty) >= 3:
        return ("Corroborated", "Three or more document families support the employee's team and the proposed manager's duties.")
    return ("Supported", "Separate dated records link the employee to a team and describe the proposed manager's duties.")
