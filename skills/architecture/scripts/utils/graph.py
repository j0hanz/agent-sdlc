from typing import Dict, List


def find_cycles(adjacency_list: Dict[str, List[str]]) -> List[List[str]]:
    """
    Find cycles in a directed graph using Tarjan's strongly connected components algorithm.
    """
    index = 0
    stack = []
    nodes = {}  # v -> {index, lowlink, onStack}
    cycles = []

    def strongconnect(v):
        nonlocal index
        nodes[v] = {"index": index, "lowlink": index, "onStack": True}
        index += 1
        stack.append(v)

        edges = adjacency_list.get(v, [])
        for w in edges:
            if w not in nodes:
                strongconnect(w)
                nodes[v]["lowlink"] = min(nodes[v]["lowlink"], nodes[w]["lowlink"])
            elif nodes[w]["onStack"]:
                nodes[v]["lowlink"] = min(nodes[v]["lowlink"], nodes[w]["index"])

        if nodes[v]["lowlink"] == nodes[v]["index"]:
            component = []
            while True:
                w = stack.pop()
                nodes[w]["onStack"] = False
                component.append(w)
                if w == v:
                    break

            if len(component) > 1:
                cycles.append(component)
            elif len(component) == 1 and component[0] in adjacency_list.get(
                component[0], []
            ):
                # Self-loop
                cycles.append(component)

    for v in adjacency_list:
        if v not in nodes:
            strongconnect(v)

    return cycles
