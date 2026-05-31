"""Run the heuristic on a small, non-optical example and report the savings.

The optimizer is domain-agnostic. Here the nodes are cities and the weights are
driving distances (km); the same code applies to fiber links, power lines,
pipelines, logistics routes, or any weighted network.

Usage::

    python example.py
"""

from redundant_topology import RedundantTopologyOptimizer, count_links


def undirected(edges):
    """Build a symmetric adjacency map from ``(a, b, weight)`` tuples."""
    graph = {}
    for a, b, weight in edges:
        graph.setdefault(a, {})[b] = weight
        graph.setdefault(b, {})[a] = weight
    return graph


# Candidate direct routes between cities, with approximate distances in km.
CITY_DISTANCES = undirected([
    ("Madrid", "Barcelona", 620),
    ("Madrid", "Valencia", 355),
    ("Madrid", "Sevilla", 530),
    ("Madrid", "Bilbao", 395),
    ("Madrid", "Zaragoza", 310),
    ("Barcelona", "Valencia", 350),
    ("Barcelona", "Bilbao", 610),
    ("Barcelona", "Zaragoza", 310),
    ("Valencia", "Sevilla", 660),
    ("Valencia", "Zaragoza", 310),
    ("Sevilla", "Bilbao", 935),
    ("Bilbao", "Zaragoza", 305),
])


def main() -> None:
    print("CANDIDATE NETWORK (all known direct routes):")
    for node in sorted(CITY_DISTANCES):
        print(f"  {node}: {CITY_DISTANCES[node]}")
    before = count_links(CITY_DISTANCES)
    print(f"TOTAL: {before} links\n")

    optimized = RedundantTopologyOptimizer().optimize(CITY_DISTANCES)

    print("REDUNDANT BACKBONE (every pair still reachable by two routes):")
    for node in sorted(optimized):
        print(f"  {node}: {optimized[node]}")
    after = count_links(optimized)
    print(f"TOTAL: {after} links\n")

    reduction = 100.0 * (before - after) / before if before else 0.0
    print(f"Reduction: {before} -> {after} links ({reduction:.1f}% fewer)")


if __name__ == "__main__":
    main()
