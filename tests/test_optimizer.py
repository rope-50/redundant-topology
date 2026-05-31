"""Tests for the redundant-topology link-minimization heuristic."""

import copy

import pytest

from redundant_topology import RedundantTopologyOptimizer, count_links
from redundant_topology.dijkstra import dijkstra


def make_ring():
    """A 4-node ring: 1-2-3-4-1, all edges weight 1.0."""
    return {
        "1": {"2": 1.0, "4": 1.0},
        "2": {"1": 1.0, "3": 1.0},
        "3": {"2": 1.0, "4": 1.0},
        "4": {"3": 1.0, "1": 1.0},
    }


@pytest.fixture
def optimizer():
    return RedundantTopologyOptimizer()


def test_input_graph_is_not_mutated(optimizer):
    graph = make_ring()
    snapshot = copy.deepcopy(graph)
    optimizer.optimize(graph)
    assert graph == snapshot


def test_result_is_symmetric(optimizer):
    result = optimizer.optimize(make_ring())
    for u, neighbors in result.items():
        for v, weight in neighbors.items():
            assert result[v][u] == weight


def test_result_uses_only_original_edges_and_weights(optimizer):
    graph = make_ring()
    result = optimizer.optimize(graph)
    for u, neighbors in result.items():
        for v, weight in neighbors.items():
            assert v in graph[u]          # never invents a link
            assert weight == graph[u][v]  # keeps the original weight


def test_result_keeps_every_node_reachable(optimizer):
    graph = make_ring()
    result = optimizer.optimize(graph)
    distances, _ = dijkstra(result, next(iter(graph)))
    assert set(distances) == set(graph)   # still connected


def test_result_never_increases_link_count(optimizer):
    graph = make_ring()
    result = optimizer.optimize(graph)
    assert count_links(result) <= count_links(graph)


def test_validation_rejects_negative_weight(optimizer):
    with pytest.raises(ValueError):
        optimizer.optimize({"A": {"B": -1.0}, "B": {"A": -1.0}})


def test_validation_rejects_asymmetric_weights(optimizer):
    with pytest.raises(ValueError):
        optimizer.optimize({"A": {"B": 1.0}, "B": {"A": 2.0}})


def test_validation_rejects_dangling_node(optimizer):
    # C is referenced but never defined as a node.
    with pytest.raises(ValueError):
        optimizer.optimize({"A": {"B": 1.0}, "B": {"A": 1.0, "C": 1.0}})


def test_validation_rejects_self_loop(optimizer):
    with pytest.raises(ValueError):
        optimizer.optimize({"A": {"A": 1.0}})


def test_count_links_counts_undirected_edges():
    assert count_links(make_ring()) == 4
