"""
Source: injects vehicles into the network.
Sink  : removes vehicles from the network and records statistics.
"""
import random
from .vehicle import Vehicle


class Source:
    """
    Generates vehicles at a given rate (vehicles/step) using either a
    constant or Poisson arrival process.
    """

    def __init__(self, node_id: str, destination_ids: list,
                 rate: float = 0.3, mode: str = "poisson",
                 x: float = 0.0, y: float = 0.0):
        """
        Parameters
        ----------
        node_id         : identifier (e.g. 'S1')
        destination_ids : list of sink node_ids this source targets
        rate            : average vehicles spawned per step
        mode            : 'poisson' or 'constant'
        x, y            : position for visualisation
        """
        self.node_id = node_id
        self.destination_ids = list(destination_ids)
        self.rate = rate
        self.mode = mode
        self.x = x
        self.y = y

        self.outgoing_roads: list = []   # roads leaving this source
        self.incoming_roads: list = []   # (unused but kept for API symmetry)

        self._sim = None                 # set by engine
        self.total_generated = 0

    # ------------------------------------------------------------------
    def add_incoming(self, road):
        self.incoming_roads.append(road)

    def add_outgoing(self, road):
        self.outgoing_roads.append(road)

    def outgoing_to(self, node_id: str):
        for r in self.outgoing_roads:
            if r.to_node.node_id == node_id:
                return r
        return None

    def _spawn_count(self) -> int:
        if self.mode == "poisson":
            return random.poisson(self.rate) if hasattr(random, "poisson") \
                   else _poisson(self.rate)
        else:  # constant – deterministic floor/ceiling
            return int(self.rate) + (1 if random.random() < (self.rate % 1) else 0)

    def step(self, current_step: int) -> list:
        """
        Generate vehicles and place them on outgoing roads.
        Returns list of Vehicle objects that successfully entered.
        """
        spawned = []
        n = _poisson(self.rate)
        for _ in range(n):
            dest = random.choice(self.destination_ids)
            v = Vehicle(source_id=self.node_id, destination_id=dest)
            v.birth_step = current_step

            # Route will be filled in by the engine; for now put vehicle
            # at source, waiting for a route
            spawned.append(v)
            self.total_generated += 1
        return spawned

    def __repr__(self):
        return f"Source({self.node_id}, rate={self.rate}, dests={self.destination_ids})"


class Sink:
    """Absorbs vehicles that have reached their destination."""

    def __init__(self, node_id: str, x: float = 0.0, y: float = 0.0):
        self.node_id = node_id
        self.x = x
        self.y = y

        self.incoming_roads: list = []
        self.outgoing_roads: list = []   # empty for sinks

        self.arrived_vehicles: list = []

    # ------------------------------------------------------------------
    def add_incoming(self, road):
        self.incoming_roads.append(road)

    def add_outgoing(self, road):
        self.outgoing_roads.append(road)

    def receive(self, vehicle, current_step: int):
        vehicle.death_step = current_step
        vehicle.current_road = None
        self.arrived_vehicles.append(vehicle)

    @property
    def total_received(self) -> int:
        return len(self.arrived_vehicles)

    @property
    def avg_travel_time(self) -> float:
        times = [v.travel_time for v in self.arrived_vehicles if v.travel_time >= 0]
        return sum(times) / len(times) if times else 0.0

    def __repr__(self):
        return f"Sink({self.node_id}, received={self.total_received})"


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _poisson(lam: float) -> int:
    """Pure-Python Poisson draw."""
    import math
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1
