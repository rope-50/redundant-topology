# Redundant Topology Optimizer

A heuristic that builds a **minimal, redundant network topology** from a weighted
graph: it keeps the fewest links possible while ensuring every pair of nodes
stays connected by **two independent routes**, so the network survives any single
link failure.

It is **domain-agnostic**. The nodes and weights can model anything you can draw
as a weighted network:

- optical / fiber links (DWDM backbones),
- roads between cities,
- power lines, water or gas pipelines,
- logistics routes between warehouses,
- computer or mesh networks, and so on.

## The problem it solves

Adding links is expensive, so you want **as few as possible**, but not so few that
a single failure isolates part of the network. The sweet spot is a topology that
is *minimal* yet *2-connected*: between any two nodes there are two independent
routes. This is a flavor of the classic **survivable network design** problem.

The network is modeled as a weighted graph (nodes = sites, edge weights =
distance / cost / latency) and a greedy heuristic picks a small, redundant subset
of all the candidate links.

## How the heuristic works

Starting from a graph that contains **every candidate link**, for each ordered
pair of nodes `(source, target)`:

1. **Shortest path.** Compute the shortest path with Dijkstra's algorithm and keep
   its links.
2. **Disjoint alternative.** Temporarily remove that path's links and compute the
   shortest path again; this link-disjoint route is the redundant backup. Keep it.
3. **Encourage reuse.** Set the *working* weight of every link just chosen to `0`,
   so later iterations prefer reusing links already in the topology rather than
   adding new ones.
4. Repeat for the next pair.

Because step 3 biases later decisions, the result depends on node order (pairs are
visited in natural order, so the output is deterministic). The returned graph
reports the **original** link weights.

> The heuristic is greedy and does not guarantee the global optimum, but it
> produces a compact, redundant topology quickly.

## Install

No third-party dependencies are needed to use it, only Python 3.8+.

```bash
git clone https://github.com/rope-50/redundant-topology.git
cd redundant-topology
```

Optionally install it as a package (with dev tools for the tests):

```bash
pip install -e ".[dev]"
```

## Usage

A graph is a dict mapping each node to `{neighbor: weight}`. It must be
**undirected** (symmetric) with **non-negative** weights:

```python
from redundant_topology import RedundantTopologyOptimizer, count_links

# Cities and driving distances (km), but it could be any weighted network.
graph = {
    "Madrid":   {"Valencia": 355, "Bilbao": 395, "Zaragoza": 310},
    "Valencia": {"Madrid": 355, "Zaragoza": 310},
    "Bilbao":   {"Madrid": 395, "Zaragoza": 305},
    "Zaragoza": {"Madrid": 310, "Valencia": 310, "Bilbao": 305},
}

optimized = RedundantTopologyOptimizer().optimize(graph)  # input is never modified
print(optimized)
print(f"{count_links(graph)} -> {count_links(optimized)} links")
```

Run the bundled example (a small cities network), which prints the topology
before and after plus the percentage of links removed:

```bash
python example.py
```

You can also use the dependency-free Dijkstra directly:

```python
from redundant_topology import shortest_path
shortest_path(graph, "Madrid", "Bilbao")   # list of nodes, or None if unreachable
```

## Graph format

```python
{
    "A": {"B": 1.5, "C": 4.0},   # node A links to B (weight 1.5) and C (4.0)
    "B": {"A": 1.5, "C": 2.0},
    "C": {"A": 4.0, "B": 2.0},
}
```

`optimize()` validates the input and raises `ValueError` if the graph is not
symmetric, has negative weights, contains a self-loop, or references an undefined
node.

## Running the tests

```bash
pip install pytest
pytest
```

## Limitations & notes

- The algorithm is a **heuristic**, not an exact optimizer.
- It provides **two** routes per pair (resilience to a single failure), not `k`.
- Output depends on node ordering (deterministic, by natural order).
- The graph must be connected for full redundancy; disconnected pairs are skipped.
- Step 3 assumes reusing an already-chosen link has no extra cost (shared
  infrastructure); adapt it if reuse is not free in your domain.
- Complexity is roughly `O(V² · (E + V log V))`, fine for the modest topologies
  typical of backbone planning.

## Acknowledgements

The shortest-path routine implements **Dijkstra's algorithm**. The original
version used the priority-dictionary recipe by David Eppstein (UC Irvine, 2002);
it has since been rewritten on top of the standard library's `heapq`, removing the
external dependency.
