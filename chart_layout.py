"""Layout only: pack the stored, acyclic proposal forest, without inventing edges."""
from collections import defaultdict
import re

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
            group.append(dict(id=eid, name=p["display_name"], title=p.get("title") or "Title unavailable", x=x, y=depth*112))
            return x
        place(root, 0)
        groups.append((group, max(1,cursor-26), max(n["y"] for n in group)+70))
    if seen != {i for edge in edges for i in edge}:
        raise ValueError("Missing nodes in stored proposal forest")
    # Depth is local to a stored tree, not a title-derived company rank.
    groups.sort(key=lambda item: (-item[2], -len(item[0])))
    x=y=row=0
    frames=[]
    limit=max(920, max((w+36 for _,w,_ in groups), default=0))
    for number,(group,w,h) in enumerate(groups,1):
        width,height=w+36,h+62
        if x and x+width>limit:
            x=0;y+=row+24;row=0
        frames.append(dict(x=x+12,y=y+12,width=width,height=height,
                           label=f"Group {number:02} · {len(group)} people"))
        for n in group:
            nodes.append(n | {"x":n["x"]+x+30,"y":n["y"]+y+56,"group":number})
        x+=width+24;row=max(row,height)
    return {"nodes":nodes,"edges":edges,"groups":frames,
            "width":max((g["x"]+g["width"]+12 for g in frames),default=40),
            "height":max((g["y"]+g["height"]+12 for g in frames),default=40)}


def role_payload(contacts):
    """Title bands are a display heuristic. This function has no edge input."""
    bands = [
        ("Executive title cues", r"\b(?:chief|ceo|cfo|coo|cto|cio|president)\b"),
        ("Head / director title cues", r"\b(?:head|director|vp|vice president)\b"),
        ("Manager / supervisor title cues", r"\b(?:manager|mgr|supervisor)\b"),
        ("Other or unclear titles", None),
    ]
    rows = [[] for _ in bands]
    for person in contacts:
        title = person.get("title") or "Title unavailable"
        index = next(i for i, (_, pattern) in enumerate(bands)
                     if pattern is None or re.search(pattern, title, re.I))
        rows[index].append((person, title))
    y = 12
    nodes, groups = [], []
    columns = 6
    width = 30 + columns * 206
    for (label, _), people in zip(bands, rows):
        if not people:
            continue
        height = 54 + ((len(people) + columns - 1) // columns) * 92
        groups.append(dict(x=12, y=y, width=width-24, height=height,
                           label=f"{label} · {len(people)}", hypothetical=True))
        for i, (person, title) in enumerate(people):
            nodes.append(dict(id=person["employee_id"], name=person["display_name"],
                              title=title, x=30+(i % columns)*206,
                              y=y+42+(i // columns)*92))
        y += height+18
    return dict(nodes=nodes, edges=[], groups=groups, width=width, height=y,
                hypothetical=True)
