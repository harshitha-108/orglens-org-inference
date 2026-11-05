"""Layout only: pack the stored, acyclic proposal forest, without inventing edges."""
from collections import defaultdict

def chart_payload(data):
    contacts = {p["employee_id"]: p for p in data["contacts"]}
    edges = [(r["proposed_manager_id"], r["employee_id"]) for r in data["relationships"] if r["proposed_manager_id"] is not None]
    children = defaultdict(list)
    parents = {}
    for manager, employee in edges:
        if manager not in contacts or employee not in contacts or employee in parents:
            raise ValueError("Invalid stored proposal forest")
        children[manager].append(employee)
        parents[employee] = manager
    roots = [i for i in contacts if i in children and i not in parents]
    nodes = []
    seen = set()
    groups = []
    for root in roots:
        group = []
        cursor = 0
        def place(eid, depth):
            nonlocal cursor
            if eid in seen:
                raise ValueError("Cycle in stored proposal forest")
            seen.add(eid)
            if children[eid]:
                xs = [place(child, depth + 1) for child in children[eid]]
                x = (xs[0] + xs[-1]) / 2
            else:
                x = cursor
                cursor += 206
            p = contacts[eid]
            group.append(dict(id=eid, name=p["display_name"], title=p.get("title") or "Job title not listed", x=x, y=depth*112))
            return x
        place(root, 0)
        groups.append((root, group, max(1,cursor-26), max(n["y"] for n in group)+70))
    if seen != {i for edge in edges for i in edge}:
        raise ValueError("Missing nodes in stored proposal forest")
    # Depth is local to a stored tree, not a title-derived company rank.
    groups.sort(key=lambda item: (-item[3], -len(item[1])))
    gap = 24
    frames = []
    sized_groups = [(number, root, group, w + 36, h + 62)
                    for number, (root, group, w, h) in enumerate(groups, 1)]

    def pack(limit):
        rows = []
        row, used = [], 0
        for number, root, group, width, height in sized_groups:
            if row and used + gap + width > limit:
                rows.append((used, row))
                row, used = [], 0
            x = used + gap if row else 0
            row.append((number, root, group, width, height, x))
            used = x + width
        if row:
            rows.append((used, row))
        return rows

    def fit_cost(rows):
        width = max((w for w, _ in rows), default=0)
        height = sum(max(item[4] for item in row) + gap for _, row in rows)
        return max((width + 24) / 2.35, height)

    # Try every row break width and choose the arrangement that fits the
    # wide chart canvas at the largest scale.
    widths = [item[3] + gap for item in sized_groups]
    minimum = max(widths, default=0)
    limits = {minimum}
    for start in range(len(widths)):
        width = 0
        for value in widths[start:]:
            width += value
            limits.add(max(minimum, width - gap))
    rows = min((pack(limit) for limit in sorted(limits)), key=fit_cost)

    widest = max((width for width, _ in rows), default=0)
    y = 0
    for width, row in rows:
        offset = (widest - width) / 2
        for number, root, group, w, h, x in row:
            left = x + offset
            frames.append(dict(x=left+12, y=y+12, width=w, height=h,
                               root=root, label=f"{contacts[root]['display_name']} - {len(group)} people"))
            for node in group:
                nodes.append(node | {"x":node["x"]+left+30,"y":node["y"]+y+56,"group":number})
        y += max(item[4] for item in row) + gap
    return {"nodes":nodes,"edges":edges,"groups":frames,
            "width":max((g["x"]+g["width"]+12 for g in frames),default=40),
            "height":max((g["y"]+g["height"]+12 for g in frames),default=40)}
