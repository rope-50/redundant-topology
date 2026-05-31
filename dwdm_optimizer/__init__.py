"""DWDM Network Optimizer.

Heuristic link minimization for DWDM optical network topologies, with a
dependency-free Dijkstra implementation.
"""

from .dijkstra import dijkstra, shortest_path
from .optimizer import DWDMNetworkOptimizer, count_links

__all__ = ["dijkstra", "shortest_path", "DWDMNetworkOptimizer", "count_links"]
__version__ = "1.0.0"
