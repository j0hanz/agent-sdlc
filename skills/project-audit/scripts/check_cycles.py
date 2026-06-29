"""Joins lanes' free-text import claims into an inter-lane graph and finds cycles.

This is the one deterministic step in project-audit's "ask, don't compute"
pipeline: free-text import answers from parallel lane agents need a reliable
join, which judgment alone can't guarantee (see design brief Risks section).
Intra-lane edges are dropped on purpose -- a cycle within one directory isn't
the "circular dependency between modules" finding this audit cares about.

Does NOT attempt full alias/re-export resolution -- normalization only
strips superficial formatting (quotes, semicolons, a leading "./"). An import
expressed in a form normalization can't reconcile with the target lane's
directory prefix will simply not resolve to an edge; this is an accepted,
disclosed limitation, not a bug.
"""

from __future__ import annotations


def normalize_import(raw: str) -> str:
    s = raw.strip()
    s = s.rstrip(";")
    s = s.strip().strip("'\"")
    if s.startswith("./"):
        s = s[2:]
    return s.strip()


def resolve_lane(import_path: str, lane_dirs: dict[str, str]) -> str | None:
    for lane, prefix in lane_dirs.items():
        prefix = prefix.strip("/")
        if import_path == prefix or import_path.startswith(prefix + "/"):
            return lane
    return None


def build_lane_graph(
    lane_imports: dict[str, list[str]], lane_dirs: dict[str, str]
) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {lane: set() for lane in lane_imports}
    for lane, raw_imports in lane_imports.items():
        for raw in raw_imports:
            target_lane = resolve_lane(normalize_import(raw), lane_dirs)
            if target_lane and target_lane != lane:
                graph[lane].add(target_lane)
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's strongly-connected-components, iterative (no recursion limit).

    Returns each SCC of size > 1 as a cycle, plus any single-node self-loop.
    """
    index_counter = [0]
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    result: list[list[str]] = []

    for start in graph:
        if start in index:
            continue
        work_stack = [(start, iter(graph.get(start, ())))]
        index[start] = index_counter[0]
        lowlink[start] = index_counter[0]
        index_counter[0] += 1
        stack.append(start)
        on_stack[start] = True

        while work_stack:
            node, neighbors = work_stack[-1]
            advanced = False
            for neighbor in neighbors:
                if neighbor not in index:
                    index[neighbor] = index_counter[0]
                    lowlink[neighbor] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(neighbor)
                    on_stack[neighbor] = True
                    work_stack.append((neighbor, iter(graph.get(neighbor, ()))))
                    advanced = True
                    break
                elif on_stack.get(neighbor):
                    lowlink[node] = min(lowlink[node], index[neighbor])
            if advanced:
                continue

            work_stack.pop()
            if work_stack:
                parent = work_stack[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

            if lowlink[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack[member] = False
                    component.append(member)
                    if member == node:
                        break
                is_self_loop = len(component) == 1 and component[0] in graph.get(
                    component[0], ()
                )
                if len(component) > 1 or is_self_loop:
                    result.append(component)

    return result
