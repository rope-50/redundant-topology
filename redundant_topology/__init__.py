"""Redundant Topology Optimizer.

Heuristic designer for minimal, redundant network topologies, with a
dependency-free Dijkstra implementation. Domain-agnostic: works on any weighted,
undirected graph (optical links, roads, power grids, logistics, etc.).
"""

from .dijkstra import dijkstra, shortest_path
from .optimizer import RedundantTopologyOptimizer, count_links

__all__ = ["dijkstra", "shortest_path", "RedundantTopologyOptimizer", "count_links"]
__version__ = "2.0.0"
