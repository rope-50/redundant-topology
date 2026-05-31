# DWDM Network Optimizer

A heuristic that reduces the number of fiber links in a **DWDM optical network**
while keeping the network **redundant** - every pair of nodes stays connected by
two routes, so the network survives any single link failure.

## Background

**DWDM** (Dense Wavelength Division Multiplexing) is the optical technology that
lets a single fiber carry many independent channels at once, each on a different
wavelength of light. It is the backbone of long-haul and metro telecom networks.

Laying fiber is expensive, so a network operator wants to deploy **as few links
as possible** - but not so few that a single cut isolates part of the network.
The sweet spot is a topology that is *minimal* yet *2-connected*: between any two
nodes there are two independent routes.

This project models the network as a weighted graph (nodes = sites, edge weights
= e.g. fiber length or cost) and applies a greedy heuristic to pick a small,
redundant subset of all the candidate links.

## How the heuristic works

Starting from a graph that contains **every candidate link**, for each ordered
pair of nodes `(source, target)`:

1. **Shortest path.** Compute the shortest path from `source` to `target` with
   Dijkstra's algorithm. Keep its links in the final topology.
2. **Disjoint alternative.** Temporarily remove that path's links and compute the
   shortest path again. This second, link-disjoint route is the redundant backup.
   Keep its links too.
3. **Encourage reuse.** Set the *working* weight of every link just selected to
   `0`, so later iterations prefer to route over links that are already part of
   the topology instead of adding new ones.
4. Repeat for the next pair.

Because step 3 biases later decisions, the result depends on the order in which
node pairs are processed (pairs are visited in natural node order, so the output
is deterministic). The returned graph reports the **original** link weights.

> The heuristic is greedy and does not guarantee the global optimum, but it
> produces a compact, redundant topology quickly.

## Install

No third-party dependencies are required to use the optimizer - only Python 3.8+.

```bash
git clone https://github.com/rope-50/DWDM-Network-Optimizer.git
cd DWDM-Network-Optimizer
```

Optionally install it as a package (and the dev tools for running tests):

```bash
pip install -e ".[dev]"
```

## Usage

A graph is a dictionary mapping each node to a dictionary of `{neighbor: weight}`.
It must be **undirected** (symmetric) with **non-negative** weights:

```python
from dwdm_optimizer import DWDMNetworkOptimizer, count_links

graph = {
    "1": {"2": 15.7, "3": 1.5},
    "2": {"1": 15.7, "3": 14.5},
    "3": {"1": 1.5,  "2": 14.5},
}

optimizer = DWDMNetworkOptimizer()
optimized = optimizer.optimize(graph)   # the input graph is never modified

print(optimized)
print(f"{count_links(graph)} -> {count_links(optimized)} links")
```

Run the bundled 20-node example, which prints the topology before and after and
the percentage of links removed:

```bash
python example.py
```

You can also use the dependency-free Dijkstra directly:

```python
from dwdm_optimizer import shortest_path
shortest_path(graph, "1", "2")   # -> ['1', '3', '2'] or None if unreachable
```

## Graph format

```python
{
    "A": {"B": 1.5, "C": 4.0},   # node "A" links to "B" (weight 1.5) and "C" (4.0)
    "B": {"A": 1.5, "C": 2.0},
    "C": {"A": 4.0, "B": 2.0},
}
```

`optimize()` validates the input and raises `ValueError` if the graph is not
symmetric, has negative weights, contains a self-loop, or references an
undefined node.

## Running the tests

```bash
pip install pytest
pytest
```

## Limitations & notes

- The algorithm is a **heuristic**, not an exact optimizer.
- Output depends on node ordering (deterministic, by natural order).
- The graph must be connected for full redundancy; disconnected pairs are
  skipped gracefully.
- Complexity is roughly `O(V² · (E + V log V))`, which is fine for the small
  topologies typical of optical backbones.

## Acknowledgements

The shortest-path routine implements **Dijkstra's algorithm**. The original
version of this project used the priority-dictionary recipe by David Eppstein
(UC Irvine, 2002); it has since been rewritten on top of the standard library's
`heapq`, removing the external dependency.
