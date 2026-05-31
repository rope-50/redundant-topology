"""Dijkstra's shortest-path algorithm over a weighted, undirected graph.

A graph is a mapping of ``node -> {neighbor: weight}``, for example::

    {"A": {"B": 1.5, "C": 4.0},
     "B": {"A": 1.5, "C": 2.0},
     "C": {"A": 4.0, "B": 2.0}}

This implementation uses a binary heap (:mod:`heapq`) from the standard
library, so it has no third-party dependencies. The original project depended
on an external ``priodict`` module that was never committed to the repository,
which made the code impossible to run.
"""

from __future__ import annotations

import heapq
import itertools
from typing import Dict, Hashable, List, Mapping, Optional, Tuple

Number = float
Graph = Mapping[Hashable, Mapping[Hashable, Number]]


def dijkstra(
    graph: Graph,
    start: Hashable,
    end: Optional[Hashable] = None,
) -> Tuple[Dict[Hashable, Number], Dict[Hashable, Hashable]]:
    """Compute shortest distances from ``start`` using Dijkstra's algorithm.

    Args:
        graph: Weighted adjacency mapping ``node -> {neighbor: weight}``.
        start: Source node.
        end: Optional target. When given, the search stops as soon as ``end``
            is finalized, which is cheaper than exploring the whole graph.

    Returns:
        A pair ``(distances, predecessors)`` where ``distances[v]`` is the cost
        of the cheapest path from ``start`` to ``v`` and ``predecessors[v]`` is
        the node preceding ``v`` on that path. Only reachable nodes appear.

    Raises:
        KeyError: if ``start`` is not a node in ``graph``.
        ValueError: if a negative edge weight is encountered. Dijkstra's
            algorithm is only correct for non-negative weights.
    """
    if start not in graph:
        raise KeyError(f"start node {start!r} is not in the graph")

    distances: Dict[Hashable, Number] = {start: 0.0}
    predecessors: Dict[Hashable, Hashable] = {}
    finalized: set = set()

    # A monotonically increasing counter breaks ties on equal distances so the
    # heap never has to compare the node objects themselves (which may not be
    # orderable, e.g. mixed types).
    counter = itertools.count()
    heap: List[Tuple[Number, int, Hashable]] = [(0.0, next(counter), start)]

    while heap:
        # Pop the nearest node not yet finalized; Dijkstra guarantees its
        # tentative distance is now its definitive shortest distance.
        dist_u, _, u = heapq.heappop(heap)
        if u in finalized:
            continue  # stale entry left behind by lazy deletion
        finalized.add(u)
        if u == end:
            break  # early exit: only the distance to `end` was requested

        # Relax every edge out of u: if reaching v through u is cheaper than any
        # route found so far, record the improvement and (re)queue v.
        for v, weight in graph[u].items():
            if weight < 0:
                raise ValueError(
                    f"negative edge weight {weight!r} on {u!r}->{v!r}; "
                    "Dijkstra requires non-negative weights"
                )
            if v in finalized:
                continue
            new_dist = dist_u + weight
            if v not in distances or new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(heap, (new_dist, next(counter), v))

    return distances, predecessors


def shortest_path(graph: Graph, start: Hashable, end: Hashable) -> Optional[List[Hashable]]:
    """Return the list of nodes on a shortest path from ``start`` to ``end``.

    Args:
        graph: Weighted adjacency mapping.
        start: Source node.
        end: Target node.

    Returns:
        The ordered list of nodes from ``start`` to ``end`` (``[start]`` when
        they are the same node), or ``None`` if ``end`` is unreachable.

    Raises:
        KeyError: if ``start`` is not a node in ``graph``.
        ValueError: if a negative edge weight is encountered.
    """
    distances, predecessors = dijkstra(graph, start, end)
    if end not in distances:
        return None  # unreachable

    path: List[Hashable] = [end]
    while path[-1] != start:
        node = path[-1]
        if node not in predecessors:  # defensive; unreachable in practice
            return None
        path.append(predecessors[node])
    path.reverse()
    return path
