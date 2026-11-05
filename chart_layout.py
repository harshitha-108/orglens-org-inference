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
            group.append(dict(id=eid, name=p["display_name"], title=p.get("title") or "Title unavailable", x=x, y=depth*112))
            return x
        place(root, 0)
        groups.append((root, group, max(1,cursor-26), max(n["y"] for n in group)+70))
    if seen != {i for edge in edges for i in edge}:
        raise ValueError("Missing nodes in stored proposal forest")
    # Depth is local to a stored tree, not a title-derived company rank.
    groups.sort(key=lambda item: (-item[3], -len(item[1])))
    x=y=row=0
    frames=[]
    limit=max(920, max((w+36 for _,_,w,_ in groups), default=0))
    for number,(root,group,w,h) in enumerate(groups,1):
        width,height=w+36,h+62
        if x and x+width>limit:
            x=0;y+=row+24;row=0
        frames.append(dict(x=x+12,y=y+12,width=width,height=height,
                           root=root, label=f"{contacts[root]['display_name']} - {len(group)} people"))
        for n in group:
            nodes.append(n | {"x":n["x"]+x+30,"y":n["y"]+y+56,"group":number})
        x+=width+24;row=max(row,height)
    return {"nodes":nodes,"edges":edges,"groups":frames,
            "width":max((g["x"]+g["width"]+12 for g in frames),default=40),
            "height":max((g["y"]+g["height"]+12 for g in frames),default=40)}
