# Traffic Network Simulator

Welcome to the traffic simulator for A6!

## Project Structure

```
traffic_sim/          ← reusable library
  __init__.py
  road.py             ← directional road with capacity + queue
  junction.py         ← 2/3/4-way junction with round-robin scheduler
  vehicle.py          ← vehicle agent (source, destination, route)
  source_sink.py      ← traffic sources (Poisson) and sinks
  router.py           ← Dijkstra shortest-path routing
  engine.py           ← discrete time-step simulation engine
  visualizer.py       ← animated GIF + statistics plot

main.py               ← defines the test network and runs the simulation
```

## Network Topology (from diagram)

```
[S1,S4] ──── J_TL ──────── J_TR ──── [K2]
              |                |
[S2,S5] ──── J_ML ──────── J_MR ──── [S3]
              |                |
[K3,K4] ──── J_BL ──────── J_BR ──── [K1,K5]
```

All inter-junction/source/sink links are **bi-directional** (modelled as two
directional Road objects, one lane each direction).

## Usage

```bash
pip install matplotlib numpy
python3 main.py
```

Outputs:
- `simulation.gif`   — animated network visualisation
- `statistics.png`   — throughput, road utilisation, junction wait times
- `statistics.json`  — machine-readable statistics

## Design Decisions

| Question | Choice |
|---|---|
| Vehicle routing | Dijkstra on weighted graph (weight = length/speed) |
| Queuing | On roads (capacity-limited FIFO) + at junctions (waiting buffer) |
| Scheduling | FIFO within each junction; vehicles advance when next road has space |
| Arrival process | Poisson (configurable rate per source) |
| Travel time | `ceil(length / speed_limit)` steps per road |

## Extending for a New Topology

Only modify `main.py`:

1. Instantiate `Junction`, `Source`, `Sink` objects with positions.
2. Add them with `engine.add_node(...)`.
3. Add `Road` objects with `engine.add_road(...)`.
4. Call `engine.build()` then `engine.run(steps=N)`.

## Statistics Collected

- Total vehicles generated / arrived / completion rate
- Average travel time per vehicle (and per sink)
- Per-road throughput (total vehicles entered)
- Per-junction cumulative wait steps
- Time-series of generated vs arrived (plotted)
