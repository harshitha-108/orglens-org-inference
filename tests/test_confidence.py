from confidence import evidence_strength


def test_document_families_missing_and_caveats():
    pred = {"employee_id": "employee", "manager_id": "manager"}
    doc = {"source_type": "synthetic_company_website"}
    def citation(kind, subject, family, **extra):
        return ({"kind": kind, "contact_id": subject, "document_family_id": family,
                 "published_at": "2026-01-01", **extra}, doc)

    member = citation("membership", "employee", "one")
    copied = citation("people_accountability", "manager", "one")
    duty = citation("people_accountability", "manager", "two")
    extra = citation("people_accountability", "manager", "three")
    assert evidence_strength(pred, [member, copied])[0] == "Limited"
    assert evidence_strength(pred, [member, duty, duty])[0] == "Supported"
    assert evidence_strength(pred, [member, duty, extra])[0] == "Corroborated"
    assert evidence_strength(pred, [member, citation("people_accountability", "manager", "two", flags=["stale"])])[0] == "Limited"
    assert evidence_strength(pred | {"candidates": [{"manager_id": "manager", "reasons": ["scope_disagreement"]}]}, [member, duty])[0] == "Supported with caveats"
    assert evidence_strength(pred | {"manager_id": None}, []) is None
    assert evidence_strength(pred | {"true_manager_id": "wrong", "is_correct": False}, [member, duty]) == evidence_strength(pred, [member, duty])
