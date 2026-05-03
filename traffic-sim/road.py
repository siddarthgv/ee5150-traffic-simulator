"""
Road: directional road segment with capacity and a vehicle queue.
"""
from collections import deque


class Road:
    """A directional road from one node to another."""

    def __init__(self, road_id: str, from_node, to_node,
                 length: float = 1.0, speed_limit: float = 1.0,
                 capacity: int = 10):
        """
        Parameters
        ----------
        road_id    : unique identifier
        from_node  : source Junction / Source node
        to_node    : destination Junction / Sink node
        length     : road length (arbitrary units)
        speed_limit: vehicles per time-step that can *exit* the road
        capacity   : maximum number of vehicles on road at once
        """
        self.road_id = road_id
        self.from_node = from_node
        self.to_node = to_node
        self.length = length
        self.speed_limit = speed_limit
        self.capacity = capacity

        # Vehicles on this road: deque of (vehicle, steps_remaining)
        self._queue: deque = deque()

        # Statistics
        self.total_entered = 0
        self.total_exited = 0
        self.total_wait_steps = 0   # cumulative congestion steps (capacity full)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def occupancy(self) -> int:
        return len(self._queue)

    @property
    def is_full(self) -> bool:
        return self.occupancy >= self.capacity

    @property
    def utilization(self) -> float:
        return self.occupancy / self.capacity if self.capacity else 0.0

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------
    def try_enter(self, vehicle) -> bool:
        """Attempt to place vehicle on this road. Returns True on success."""
        if self.is_full:
            return False
        travel_steps = max(1, round(self.length / self.speed_limit))
        self._queue.append([vehicle, travel_steps])
        self.total_entered += 1
        return True

    def step(self):
        """Advance all vehicles by one time-step (decrement travel counters)."""
        if self.is_full:
            self.total_wait_steps += 1
        for entry in self._queue:
            entry[1] = max(0, entry[1] - 1)

    def peek_ready(self):
        """Return vehicles at the front that have finished travelling (steps==0)."""
        ready = []
        for entry in self._queue:
            if entry[1] == 0:
                ready.append(entry[0])
            else:
                break          # queue is ordered; stop at first not-ready
        return ready

    def pop_ready(self) -> list:
        """Remove and return all vehicles at front that have finished travelling."""
        result = []
        while self._queue and self._queue[0][1] == 0:
            result.append(self._queue.popleft()[0])
            self.total_exited += 1
        return result

    def snapshot(self) -> list:
        """Return list of (vehicle, steps_remaining) for visualisation."""
        return [(e[0], e[1]) for e in self._queue]

    def __repr__(self):
        return (f"Road({self.road_id}: {self.from_node.node_id}"
                f" → {self.to_node.node_id}, occ={self.occupancy}/{self.capacity})")
