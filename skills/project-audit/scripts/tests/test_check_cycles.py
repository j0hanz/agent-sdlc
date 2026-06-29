from check_cycles import normalize_import, resolve_lane, build_lane_graph, find_cycles


def test_normalize_import_strips_quotes_and_semicolon():
    assert normalize_import("'./billing/invoice';") == "billing/invoice"
    assert normalize_import('"billing/invoice"') == "billing/invoice"


def test_normalize_import_strips_leading_dot_slash():
    assert normalize_import("./orders/order") == "orders/order"


def test_resolve_lane_matches_prefix():
    lane_dirs = {"billing": "billing", "orders": "orders"}
    assert resolve_lane("billing/invoice", lane_dirs) == "billing"
    assert resolve_lane("orders/order", lane_dirs) == "orders"


def test_resolve_lane_no_match_returns_none():
    lane_dirs = {"billing": "billing"}
    assert resolve_lane("shared/utils", lane_dirs) is None


def test_resolve_lane_does_not_match_partial_directory_name():
    # "billingx" should not match the "billing" prefix
    lane_dirs = {"billing": "billing"}
    assert resolve_lane("billingx/thing", lane_dirs) is None


def test_build_lane_graph_drops_intra_lane_edges():
    lane_dirs = {"billing": "billing"}
    lane_imports = {"billing": ["'./billing/helpers'"]}
    graph = build_lane_graph(lane_imports, lane_dirs)
    assert graph["billing"] == set()


def test_build_lane_graph_builds_inter_lane_edge():
    lane_dirs = {"billing": "billing", "orders": "orders"}
    lane_imports = {
        "billing": ["'./orders/order'"],
        "orders": [],
    }
    graph = build_lane_graph(lane_imports, lane_dirs)
    assert graph["billing"] == {"orders"}
    assert graph["orders"] == set()


def test_build_lane_graph_ignores_unresolved_imports():
    lane_dirs = {"billing": "billing"}
    lane_imports = {"billing": ["express"]}
    graph = build_lane_graph(lane_imports, lane_dirs)
    assert graph["billing"] == set()


def test_find_cycles_detects_two_lane_cycle():
    graph = {"billing": {"orders"}, "orders": {"billing"}}
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"billing", "orders"}


def test_find_cycles_detects_transitive_three_lane_cycle():
    graph = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"a", "b", "c"}


def test_find_cycles_returns_empty_for_acyclic_graph():
    graph = {"a": {"b"}, "b": {"c"}, "c": set()}
    assert find_cycles(graph) == []


def test_find_cycles_detects_self_loop():
    graph = {"a": {"a"}}
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0] == ["a"]
