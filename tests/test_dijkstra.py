"""Tests for the dependency-free Dijkstra implementation."""

import pytest

from redundant_topology.dijkstra import dijkstra, shortest_path

# A->B 1, B->C 2, A->C 4. Cheapest A->C is A-B-C (cost 3), not the direct edge.
TRIANGLE = {
    "A": {"B": 1.0, "C": 4.0},
    "B": {"A": 1.0, "C": 2.0},
    "C": {"A": 4.0, "B": 2.0},
}


def test_shortest_path_prefers_cheaper_route():
    assert shortest_path(TRIANGLE, "A", "C") == ["A", "B", "C"]


def test_distances_are_correct():
    distances, _ = dijkstra(TRIANGLE, "A")
    assert distances == {"A": 0.0, "B": 1.0, "C": 3.0}


def test_path_to_self_is_singleton():
    assert shortest_path(TRIANGLE, "A", "A") == ["A"]


def test_unreachable_node_returns_none():
    graph = {
        "A": {"B": 1.0},
        "B": {"A": 1.0},
        "X": {"Y": 1.0},
        "Y": {"X": 1.0},
    }
    assert shortest_path(graph, "A", "X") is None


def test_missing_start_raises_keyerror():
    with pytest.raises(KeyError):
        dijkstra(TRIANGLE, "Z")


def test_negative_weight_raises_valueerror():
    graph = {"A": {"B": -1.0}, "B": {"A": -1.0}}
    with pytest.raises(ValueError):
        dijkstra(graph, "A")


def test_ties_do_not_compare_incomparable_nodes():
    # Equal-distance frontier with non-orderable node labels must not raise.
    graph = {
        0: {"a": 1.0, "b": 1.0},
        "a": {0: 1.0},
        "b": {0: 1.0},
    }
    distances, _ = dijkstra(graph, 0)
    assert distances == {0: 0.0, "a": 1.0, "b": 1.0}
