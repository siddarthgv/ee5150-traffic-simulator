"""
SimEngine: discrete time-step simulation engine.
"""
from .router import Router


class SimEngine:
    """
    Drives the simulation forward one step at a time.

    Order of operations each step
    --------------------------------
    1. Sources generate new vehicles and assign routes.
    2. Roads advance vehicle positions (decrement travel counters).
    3. Roads deliver ready vehicles to their next node (junction or sink).
    4. Junctions try to forward waiting vehicles onto outgoing roads.
    5. Statistics snapshot is recorded.
    """

    def __init__(self):
        self.nodes: dict = {}    # node_id → Junction | Source | Sink
        self.roads: list = []    # all Road objects
        self.sources: list = []
        self.sinks: list = []
        self.junctions: list = []

        self.router = Router()
        self.step_number: int = 0

        # History for post-sim analysis / animation
        # Each entry: {step, road_snapshots, junction_queues, sink_totals}
        self.history: list = []
        self._record_every: int = 1   # record every N steps

    # ------------------------------------------------------------------
    # Network construction helpers
    # ------------------------------------------------------------------
    def add_node(self, node):
        from .source_sink import Source, Sink
        from .junction import Junction
        self.nodes[node.node_id] = node
        if isinstance(node, Source):
            self.sources.append(node)
            node._sim = self
        elif isinstance(node, Sink):
            self.sinks.append(node)
        elif isinstance(node, Junction):
            self.junctions.append(node)

    def add_road(self, road):
        self.roads.append(road)
        road.from_node.add_outgoing(road)
        road.to_node.add_incoming(road)

    def build(self):
        """Call after all nodes and roads are added."""
        self.router.build(self.nodes, self.roads)

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def run(self, steps: int, record_every: int = 1):
        self._record_every = record_every
        for _ in range(steps):
            self._tick()

    def _tick(self):
        s = self.step_number

        # 1. Sources → generate vehicles and assign routes
        new_vehicles = []
        for source in self.sources:
            spawned = source.step(s)
            for v in spawned:
                path = self.router.shortest_path(source.node_id, v.destination_id)
                if len(path) < 2:
                    continue   # no path found, drop vehicle
                v.route = path
                v.route_index = 1   # index 0 is source itself
                # Place vehicle on first outgoing road
                first_road = source.outgoing_to(path[1])
                if first_road and first_road.try_enter(v):
                    v.advance_route()
                    v.current_road = first_road
                    new_vehicles.append(v)

        # 2. Roads advance positions
        for road in self.roads:
            road.step()

        # 3. Roads deliver ready vehicles
        from .source_sink import Sink, Source
        for road in self.roads:
            ready = road.pop_ready()
            for vehicle in ready:
                arrived_node = road.to_node
                vehicle.current_road = None
                if isinstance(arrived_node, Sink):
                    arrived_node.receive(vehicle, s)
                elif isinstance(arrived_node, Source):
                    pass  # drop
                else:
                    arrived_node.receive(vehicle)

        # 4. Junctions schedule departures
        for junction in self.junctions:
            junction.step()

        # 5. Record snapshot
        if s % self._record_every == 0:
            self._snapshot()

        self.step_number += 1

    # ------------------------------------------------------------------
    def _snapshot(self):
        road_data = {}
        for r in self.roads:
            road_data[r.road_id] = {
                "occupancy": r.occupancy,
                "capacity": r.capacity,
                "vehicles": [(v.vehicle_id, v.destination_id, v.color(), steps)
                             for v, steps in r.snapshot()],
            }
        junction_data = {j.node_id: j.queue_length for j in self.junctions}
        sink_data = {sk.node_id: sk.total_received for sk in self.sinks}
        source_data = {sr.node_id: sr.total_generated for sr in self.sources}

        self.history.append({
            "step": self.step_number,
            "roads": road_data,
            "junctions": junction_data,
            "sinks": sink_data,
            "sources": source_data,
        })

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    def statistics(self) -> dict:
        total_gen = sum(s.total_generated for s in self.sources)
        total_arr = sum(sk.total_received for sk in self.sinks)
        travel_times = []
        for sk in self.sinks:
            travel_times.extend(v.travel_time for v in sk.arrived_vehicles
                                if v.travel_time >= 0)
        avg_tt = sum(travel_times) / len(travel_times) if travel_times else 0

        road_util = {r.road_id: r.total_entered for r in self.roads}
        junction_wait = {j.node_id: j.total_wait_steps for j in self.junctions}

        return {
            "total_generated": total_gen,
            "total_arrived": total_arr,
            "completion_rate": total_arr / total_gen if total_gen else 0,
            "avg_travel_time": avg_tt,
            "road_throughput": road_util,
            "junction_wait_steps": junction_wait,
            "per_sink": {sk.node_id: {
                "received": sk.total_received,
                "avg_travel_time": sk.avg_travel_time,
            } for sk in self.sinks},
            "per_source": {sr.node_id: sr.total_generated for sr in self.sources},
        }


# ---------------------------------------------------------------------------
def _deliver_to_sink(vehicle, sinks, step):
    for sk in sinks:
        if sk.node_id == vehicle.destination_id:
            sk.receive(vehicle, step)
            return
