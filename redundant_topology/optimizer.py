"""Heuristic designer for minimal, redundant network topologies.

Given a weighted, undirected graph that models every *possible* link between
nodes, the heuristic selects a smaller set of links such that every pair of
nodes is still connected by **two** independent routes (so the network survives
a single link failure). It is domain-agnostic: the nodes and weights can model
fiber/optical links, roads, power lines, pipelines, logistics routes, or any
other weighted network. See the README for the rationale and the step-by-step
description of the heuristic.
"""

from __future__ import annotations

from typing import Dict, Hashable, List, Mapping, Tuple

from .dijkstra import Graph, Number, shortest_path

Edge = Tuple[Hashable, Hashable, Number]


def count_links(graph: Graph) -> int:
    """Return the number of undirected links (edges) in a symmetric graph."""
    return sum(len(neighbors) for neighbors in graph.values()) // 2


def _natural_key(node: Hashable):
    """Order numeric-looking labels numerically, the rest lexicographically.

    This keeps node ``"2"`` before ``"10"`` instead of the lexicographic order
    ``"10"`` < ``"2"``, which makes the output deterministic and intuitive.
    """
    text = str(node)
    return (0, int(text)) if text.isdigit() else (1, text)


class RedundantTopologyOptimizer:
    """Select a minimal, redundant set of links for a network topology."""

    def optimize(self, graph: Graph) -> Dict[Hashable, Dict[Hashable, Number]]:
        """Return an optimized, weighted topology ``{node: {neighbor: weight}}``.

        The input ``graph`` is never modified. For every ordered pair of
        distinct nodes the heuristic keeps the shortest path and a link-disjoint
        alternative, then biases later iterations toward reusing links already
        selected (their *working* weight is set to zero so they look "free").
        The weights in the returned graph are the original link weights.

        Args:
            graph: Weighted, non-negative, symmetric adjacency mapping.

        Returns:
            The optimized topology, also a symmetric weighted adjacency mapping.

        Raises:
            ValueError: if ``graph`` is not a valid non-negative, symmetric,
                weighted adjacency mapping (see :meth:`_validate`).
        """
        self._validate(graph)

        # Independent working copy: a dict-of-dicts of immutable numbers, so a
        # one-level copy of each adjacency dict is enough to avoid mutating the
        # caller's graph (this is the bug the original `copy.copy` had).
        working: Dict[Hashable, Dict[Hashable, Number]] = {
            node: dict(neighbors) for node, neighbors in graph.items()
        }
        final: Dict[Hashable, Dict[Hashable, Number]] = {}

        # Visit every ordered pair of nodes. Because each pair makes its chosen
        # links "free" for later pairs (step 3), the outcome is order-dependent;
        # sorting the nodes keeps the result deterministic.
        nodes: List[Hashable] = sorted(working, key=_natural_key)
        for source in nodes:
            for target in nodes:
                if source == target:
                    continue

                # Step 1 -- keep the cheapest route between this pair.
                primary = shortest_path(working, source, target)
                if primary is None:
                    continue  # disconnected pair: nothing to route

                self._add_path(final, primary, graph)

                # Step 2 -- keep a link-disjoint backup route. Hide the primary
                # path's edges, re-run Dijkstra, then restore them so that only
                # step 3 below actually mutates the working graph.
                removed = self._remove_edges(working, primary)
                alternative = shortest_path(working, source, target)
                self._restore_edges(working, removed)

                if alternative is not None:
                    self._add_path(final, alternative, graph)

                # Step 3 -- zero the working weight of the chosen links so later
                # pairs prefer to route over them instead of adding new links.
                self._zero_edges(working, primary)
                if alternative is not None:
                    self._zero_edges(working, alternative)

        return final

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _add_path(
        final: Dict[Hashable, Dict[Hashable, Number]],
        path: List[Hashable],
        weight_source: Graph,
    ) -> None:
        """Add every edge of ``path`` to ``final`` using original weights."""
        # zip(path, path[1:]) walks each consecutive (node, next) edge of the
        # path. Weights are read from `weight_source` (the original graph), not
        # the working graph, whose weights may have been zeroed by the bias step.
        for u, v in zip(path, path[1:]):
            weight = weight_source[u][v]
            # Undirected graph: store the link in both directions.
            final.setdefault(u, {})[v] = weight
            final.setdefault(v, {})[u] = weight

    @staticmethod
    def _remove_edges(
        graph: Dict[Hashable, Dict[Hashable, Number]], path: List[Hashable]
    ) -> List[Edge]:
        """Remove ``path``'s edges from ``graph``; return them for restoration."""
        removed: List[Edge] = []
        for u, v in zip(path, path[1:]):
            weight = graph[u][v]
            del graph[u][v]
            del graph[v][u]
            removed.append((u, v, weight))
        return removed

    @staticmethod
    def _restore_edges(
        graph: Dict[Hashable, Dict[Hashable, Number]], removed: List[Edge]
    ) -> None:
        """Re-insert edges previously taken out by :meth:`_remove_edges`."""
        for u, v, weight in removed:
            graph[u][v] = weight
            graph[v][u] = weight

    @staticmethod
    def _zero_edges(
        graph: Dict[Hashable, Dict[Hashable, Number]], path: List[Hashable]
    ) -> None:
        """Set the working weight of ``path``'s edges to zero ("free to reuse")."""
        for u, v in zip(path, path[1:]):
            graph[u][v] = 0.0
            graph[v][u] = 0.0

    @staticmethod
    def _validate(graph: Graph) -> None:
        """Validate the graph is a non-negative, symmetric weighted mapping.

        Raises:
            ValueError: describing the first problem found.
        """
        if not isinstance(graph, Mapping):
            raise ValueError("graph must be a mapping of node -> {neighbor: weight}")

        for u, neighbors in graph.items():
            if not isinstance(neighbors, Mapping):
                raise ValueError(f"adjacency for node {u!r} must be a mapping")
            for v, weight in neighbors.items():
                if u == v:
                    raise ValueError(f"self-loop on node {u!r} is not allowed")
                if v not in graph:
                    raise ValueError(
                        f"edge {u!r}->{v!r} references undefined node {v!r}"
                    )
                # bool is a subclass of int; reject it explicitly.
                if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                    raise ValueError(
                        f"weight of edge {u!r}->{v!r} must be a number, got {weight!r}"
                    )
                if weight < 0:
                    raise ValueError(
                        f"negative weight {weight!r} on edge {u!r}->{v!r}"
                    )
                if u not in graph[v]:
                    raise ValueError(
                        f"graph is not symmetric: reverse edge {v!r}->{u!r} is missing"
                    )
                if graph[v][u] != weight:
                    raise ValueError(
                        f"asymmetric weight between {u!r} and {v!r}: "
                        f"{weight!r} vs {graph[v][u]!r}"
                    )
