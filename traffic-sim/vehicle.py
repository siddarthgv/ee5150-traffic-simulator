"""
Vehicle: an agent travelling from a source to a sink.
"""
_counter = 0


def _next_id():
    global _counter
    _counter += 1
    return _counter


class Vehicle:
    """A single vehicle with a fixed origin/destination pair."""

    # Colour palette indexed by destination id (assigned lazily)
    _dest_colors: dict = {}
    _palette = [
        "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
        "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
    ]

    def __init__(self, source_id: str, destination_id: str):
        self.vehicle_id = _next_id()
        self.source_id = source_id
        self.destination_id = destination_id

        self.route: list = []          # ordered list of node_ids
        self.route_index: int = 0      # next junction index in route

        self.birth_step: int = 0       # simulation step when created
        self.death_step: int = -1      # simulation step when arrived
        self.current_road = None       # Road object or None

    # ------------------------------------------------------------------
    def color(self) -> str:
        dest = self.destination_id
        if dest not in Vehicle._dest_colors:
            idx = len(Vehicle._dest_colors) % len(Vehicle._palette)
            Vehicle._dest_colors[dest] = Vehicle._palette[idx]
        return Vehicle._dest_colors[dest]

    @property
    def travel_time(self) -> int:
        if self.death_step >= 0:
            return self.death_step - self.birth_step
        return -1

    @property
    def next_node_id(self):
        """The next node the vehicle needs to reach."""
        if self.route_index < len(self.route):
            return self.route[self.route_index]
        return None

    def advance_route(self):
        self.route_index += 1

    def __repr__(self):
        return (f"Vehicle(id={self.vehicle_id}, "
                f"{self.source_id}→{self.destination_id})")
