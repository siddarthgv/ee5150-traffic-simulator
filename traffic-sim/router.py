"""
Router: computes shortest paths through the network using Dijkstra's algorithm.
"""
import heapq


class Router:
    """
    Precomputes shortest paths between all source/junction/sink pairs.
    Call build() once after the network is fully assembled.
    """

    def __init__(self):
        # graph[node_id] = list of (neighbour_id, weight)
        self._graph: dict = {}
        # cache[(src, dst)] = list of node_ids (full path including endpoints)
        self._cache: dict = {}

    def build(self, nodes: dict, roads: list):
        """
        Parameters
        ----------
        nodes : dict  node_id → node object (Junction / Source / Sink)
        roads : list  of Road objects
        """
        self._graph = {nid: [] for nid in nodes}
        for road in roads:
            src = road.from_node.node_id
            dst = road.to_node.node_id
            weight = road.length / road.speed_limit   # travel time
            self._graph[src].append((dst, weight))

        self._cache.clear()

    def shortest_path(self, source_id: str, dest_id: str) -> list:
        """Return ordered list of node_ids from source_id to dest_id (inclusive).
        Returns [] if no path exists."""
        key = (source_id, dest_id)
        if key in self._cache:
            return self._cache[key]

        path = self._dijkstra(source_id, dest_id)
        self._cache[key] = path
        return path

    # ------------------------------------------------------------------
    def _dijkstra(self, src: str, dst: str) -> list:
        dist = {src: 0.0}
        prev = {}
        heap = [(0.0, src)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist.get(u, float("inf")):
                continue
            if u == dst:
                break
            for v, w in self._graph.get(u, []):
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(heap, (nd, v))

        if dst not in dist:
            return []

        path = []
        node = dst
        while node != src:
            path.append(node)
            node = prev[node]
        path.append(src)
        path.reverse()
        return path
