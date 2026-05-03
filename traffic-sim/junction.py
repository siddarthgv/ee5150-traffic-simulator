"""
Junction: a node in the road network (2-way, 3-way, or 4-way).
Vehicles arriving here are scheduled to depart on their next road.
"""
from collections import deque


class Junction:
    """
    A junction holds vehicles briefly while they wait to enter the next road.
    A simple round-robin scheduler is used when multiple incoming roads compete.
    """

    def __init__(self, node_id: str, x: float = 0.0, y: float = 0.0,
                 ways: int = 4):
        """
        Parameters
        ----------
        node_id : unique identifier string
        x, y    : position for visualisation
        ways    : 2, 3 or 4
        """
        self.node_id = node_id
        self.x = x
        self.y = y
        self.ways = ways

        self.incoming_roads: list = []   # Road objects ending here
        self.outgoing_roads: list = []   # Road objects starting here

        # Internal queue: vehicles waiting to leave this junction
        self._waiting: deque = deque()

        # Statistics
        self.total_passed = 0
        self.total_wait_steps = 0  # cumulative steps vehicles spend here

    # ------------------------------------------------------------------
    def add_incoming(self, road):
        self.incoming_roads.append(road)

    def add_outgoing(self, road):
        self.outgoing_roads.append(road)

    def outgoing_to(self, node_id: str):
        """Return the outgoing Road that leads to node_id, or None."""
        for r in self.outgoing_roads:
            if r.to_node.node_id == node_id:
                return r
        return None

    # ------------------------------------------------------------------
    def receive(self, vehicle):
        """Called when a vehicle arrives at this junction from a road."""
        self._waiting.append([vehicle, 0])   # [vehicle, wait_steps]

    def step(self):
        """
        One simulation step: try to forward each waiting vehicle onto its
        next road.  Vehicles that cannot move yet stay in the queue.
        """
        still_waiting = deque()
        for entry in self._waiting:
            vehicle, waited = entry
            next_node = vehicle.next_node_id
            if next_node is None:
                # Route exhausted while at this junction — drop
                still_waiting.append(entry)
                continue

            road = self.outgoing_to(next_node)
            if road is None:
                still_waiting.append(entry)
                continue

            if road.try_enter(vehicle):
                vehicle.advance_route()
                vehicle.current_road = road
                self.total_passed += 1
                self.total_wait_steps += waited
            else:
                entry[1] += 1
                still_waiting.append(entry)

        self._waiting = still_waiting

    @property
    def queue_length(self) -> int:
        return len(self._waiting)

    def __repr__(self):
        return f"Junction({self.node_id}, {self.ways}-way, q={self.queue_length})"
