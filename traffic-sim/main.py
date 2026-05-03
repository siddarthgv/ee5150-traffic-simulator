"""
main.py — Traffic Network Simulator
=====================================
Network topology from the assignment diagram:

  Sources : S1,S4 (top-left)  |  S2,S5 (mid-left)  |  S3 (mid-right)
  Sinks   : K2 (top-right)    |  K1,K5 (bot-right)  |  K3,K4 (bot-left)

  Grid junctions (labelled by grid position):
      J_TL (top-left)   J_TR (top-right)
      J_ML (mid-left)   J_MR (mid-right)
      J_BL (bot-left)   J_BR (bot-right)

  All roads are bi-directional (one lane each direction) as shown in the
  diagram, so we model each bi-directional segment as TWO Road objects.

Usage:
    python3 main.py
"""

import json
import os
import sys

from traffic_sim import SimEngine, Junction, Source, Sink, Road
from traffic_sim.visualizer import animate, plot_statistics

# =============================================================================
# 1.  SIMULATION PARAMETERS  (change these freely)
# =============================================================================
SIM_STEPS      = 300      # total simulation steps
RECORD_EVERY   = 2        # record snapshot every N steps (smaller = larger GIF)
GIF_FPS        = 10       # animation frames per second
MAX_FRAMES     = 120      # cap GIF length

ROAD_LENGTH    = 1.0      # length of each road segment (uniform)
ROAD_SPEED     = 1.0      # speed limit (steps to traverse = length/speed)
ROAD_CAPACITY  = 8        # max vehicles per directional road at once

# Arrival rate (vehicles/step, Poisson) for each source
RATE_S1_S4 = 0.30
RATE_S2_S5 = 0.25
RATE_S3    = 0.20

# =============================================================================
# 2.  BUILD NETWORK
# =============================================================================
def build_network() -> SimEngine:
    engine = SimEngine()

    # ------------------------------------------------------------------
    # 2a. Junctions  (x, y positions for visualisation – a 2×3 grid)
    # ------------------------------------------------------------------
    #   x: 2  4  6        y: 4  2  0
    J = {
        "TL": Junction("TL", x=2, y=4, ways=3),
        "TR": Junction("TR", x=6, y=4, ways=3),
        "ML": Junction("ML", x=2, y=2, ways=4),
        "MR": Junction("MR", x=6, y=2, ways=4),
        "BL": Junction("BL", x=2, y=0, ways=3),
        "BR": Junction("BR", x=6, y=0, ways=3),
    }

    # ------------------------------------------------------------------
    # 2b. Sources and Sinks
    # ------------------------------------------------------------------
    # Sources can send to any sink; randomised per vehicle
    ALL_SINKS = ["K2", "K1_K5", "K3_K4"]

    S = {
        "S1_S4": Source("S1_S4", destination_ids=ALL_SINKS,
                         rate=RATE_S1_S4, mode="poisson", x=0, y=4),
        "S2_S5": Source("S2_S5", destination_ids=ALL_SINKS,
                         rate=RATE_S2_S5, mode="poisson", x=0, y=2),
        "S3":    Source("S3",    destination_ids=ALL_SINKS,
                         rate=RATE_S3,    mode="poisson", x=8, y=2),
    }

    K = {
        "K2":    Sink("K2",    x=8, y=4),
        "K1_K5": Sink("K1_K5", x=8, y=0),
        "K3_K4": Sink("K3_K4", x=0, y=0),
    }

    # Register all nodes
    for node in list(J.values()) + list(S.values()) + list(K.values()):
        engine.add_node(node)

    # ------------------------------------------------------------------
    # 2c. Roads  (each bi-directional link → two Road objects)
    # ------------------------------------------------------------------
    def bi_road(id_prefix, a, b):
        """Add two directional roads between nodes a and b."""
        engine.add_road(Road(f"{id_prefix}_fwd", a, b,
                              length=ROAD_LENGTH, speed_limit=ROAD_SPEED,
                              capacity=ROAD_CAPACITY))
        engine.add_road(Road(f"{id_prefix}_bwd", b, a,
                              length=ROAD_LENGTH, speed_limit=ROAD_SPEED,
                              capacity=ROAD_CAPACITY))

    def one_road(id_prefix, a, b):
        """Add one directional road from a to b."""
        engine.add_road(Road(f"{id_prefix}", a, b,
                              length=ROAD_LENGTH, speed_limit=ROAD_SPEED,
                              capacity=ROAD_CAPACITY))

    # Horizontal roads (bi-directional)
    bi_road("H_S14_TL",  S["S1_S4"], J["TL"])
    bi_road("H_TL_TR",   J["TL"],    J["TR"])
    bi_road("H_TR_K2",   J["TR"],    K["K2"])

    bi_road("H_S25_ML",  S["S2_S5"], J["ML"])
    bi_road("H_ML_MR",   J["ML"],    J["MR"])
    bi_road("H_MR_S3",   J["MR"],    S["S3"])

    bi_road("H_K34_BL",  K["K3_K4"], J["BL"])
    bi_road("H_BL_BR",   J["BL"],    J["BR"])
    bi_road("H_BR_K15",  J["BR"],    K["K1_K5"])

    # Vertical roads (bi-directional)
    bi_road("V_TL_ML",   J["TL"],    J["ML"])
    bi_road("V_ML_BL",   J["ML"],    J["BL"])

    bi_road("V_TR_MR",   J["TR"],    J["MR"])
    bi_road("V_MR_BR",   J["MR"],    J["BR"])

    # ------------------------------------------------------------------
    # 2d. Build router
    # ------------------------------------------------------------------
    engine.build()
    return engine


# =============================================================================
# 3.  RUN
# =============================================================================
def main():
    print("=" * 60)
    print("  Traffic Network Simulator")
    print("=" * 60)

    engine = build_network()

    node_summary = (
        f"  Sources  : {[s.node_id for s in engine.sources]}\n"
        f"  Sinks    : {[sk.node_id for sk in engine.sinks]}\n"
        f"  Junctions: {[j.node_id for j in engine.junctions]}\n"
        f"  Roads    : {len(engine.roads)} directional segments"
    )
    print(node_summary)
    print(f"\nRunning {SIM_STEPS} steps …")

    engine.run(steps=SIM_STEPS, record_every=RECORD_EVERY)

    # ------------------------------------------------------------------
    # 4.  Statistics
    # ------------------------------------------------------------------
    stats = engine.statistics()
    print("\n--- Summary Statistics ---")
    print(f"  Total generated : {stats['total_generated']}")
    print(f"  Total arrived   : {stats['total_arrived']}")
    print(f"  Completion rate : {stats['completion_rate']:.1%}")
    print(f"  Avg travel time : {stats['avg_travel_time']:.2f} steps")
    print("\n  Per-sink breakdown:")
    for sid, info in stats["per_sink"].items():
        print(f"    {sid:12s} → received={info['received']:4d},"
              f" avg_tt={info['avg_travel_time']:.1f}")
    print("\n  Per-source generated:")
    for sid, count in stats["per_source"].items():
        print(f"    {sid:12s} → generated={count:4d}")

    # Save JSON stats
    stats_path = "statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n  Detailed stats saved → {stats_path}")

    # ------------------------------------------------------------------
    # 5.  Visualisation
    # ------------------------------------------------------------------
    print("\nGenerating animation …")
    gif_path = "simulation.gif"
    animate(engine, output_path=gif_path, fps=GIF_FPS, max_frames=MAX_FRAMES)

    print("Generating statistics plot …")
    plot_statistics(engine, output_path="statistics.png")

    print("\nDone! Output files:")
    for f in [gif_path, "statistics.png", stats_path]:
        if os.path.exists(f):
            size = os.path.getsize(f) // 1024
            print(f"  {f:25s} ({size} KB)")

    print("=" * 60)


if __name__ == "__main__":
    main()
