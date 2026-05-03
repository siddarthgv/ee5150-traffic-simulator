"""
Visualizer: produces an animated GIF or MP4 of the simulation.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
NODE_COLORS = {
    "source":   "#27ae60",
    "sink":     "#e74c3c",
    "junction": "#ecf0f1",
}
ROAD_COLOR   = "#2c3e50"
ROAD_ALPHA   = 0.35
VEHICLE_SIZE = 60


def _node_type(node_id, sources, sinks):
    if node_id in sources:
        return "source"
    if node_id in sinks:
        return "sink"
    return "junction"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def animate(engine, output_path: str = "simulation.gif",
            fps: int = 8, max_frames: int = 200):
    """
    Render the simulation history as an animated GIF.

    Parameters
    ----------
    engine      : SimEngine (after run())
    output_path : file to write
    fps         : frames per second
    max_frames  : cap total frames (subsample history if needed)
    """
    history = engine.history
    if not history:
        print("[Visualizer] No history to animate.")
        return

    # Build node position maps
    nodes = engine.nodes
    source_ids = {s.node_id for s in engine.sources}
    sink_ids   = {sk.node_id for sk in engine.sinks}

    positions = {nid: (n.x, n.y) for nid, n in nodes.items()}

    # Subsample history
    step_indices = list(range(len(history)))
    if len(step_indices) > max_frames:
        step_indices = step_indices[:: len(step_indices) // max_frames]

    fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.set_aspect("equal")
    ax.axis("off")

    # Compute limits with padding
    xs = [v[0] for v in positions.values()]
    ys = [v[1] for v in positions.values()]
    pad = 1.5
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)

    # --- Draw static road edges ---
    for road in engine.roads:
        x0, y0 = positions[road.from_node.node_id]
        x1, y1 = positions[road.to_node.node_id]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#4a4a6a",
                                   lw=1.5, mutation_scale=12))

    # --- Draw static nodes ---
    for nid, (x, y) in positions.items():
        ntype = _node_type(nid, source_ids, sink_ids)
        color = NODE_COLORS[ntype]
        edge  = "#ffffff"
        if ntype == "junction":
            circ = plt.Circle((x, y), 0.25, color=color, ec=edge, lw=1.5, zorder=3)
            ax.add_patch(circ)
        else:
            rect = mpatches.FancyBboxPatch(
                (x - 0.35, y - 0.25), 0.7, 0.5,
                boxstyle="round,pad=0.05",
                facecolor=color, edgecolor=edge, linewidth=1.5, zorder=3)
            ax.add_patch(rect)
        ax.text(x, y, nid, ha="center", va="center",
                fontsize=6, fontweight="bold", color="#1a1a2e" if ntype != "junction" else "#2c3e50",
                zorder=4)

    # --- Legend ---
    legend_elements = [
        mpatches.Patch(facecolor=NODE_COLORS["source"], label="Source"),
        mpatches.Patch(facecolor=NODE_COLORS["sink"],   label="Sink"),
        mpatches.Patch(facecolor=NODE_COLORS["junction"], edgecolor="white", label="Junction"),
    ]
    # Add destination colours
    dest_colors = {}
    for frame in history:
        for rd in frame["roads"].values():
            for _, dest_id, color, _ in rd["vehicles"]:
                dest_colors[dest_id] = color
    for dest_id, color in dest_colors.items():
        legend_elements.append(
            mpatches.Patch(facecolor=color, label=f"→ {dest_id}"))
    ax.legend(handles=legend_elements, loc="upper right",
              fontsize=7, facecolor="#2c3e50", labelcolor="white",
              edgecolor="#4a4a6a", framealpha=0.8)

    # --- Dynamic artists ---
    vehicle_scatter = ax.scatter([], [], s=VEHICLE_SIZE, zorder=5,
                                 edgecolors="white", linewidths=0.5)
    step_text = ax.text(0.02, 0.97, "", transform=ax.transAxes,
                        fontsize=9, color="#a0a0c0", va="top",
                        fontfamily="monospace")

    def _update(frame_idx):
        frame = history[frame_idx]
        vx, vy, vc = [], [], []

        for road in engine.roads:
            rid = road.road_id
            if rid not in frame["roads"]:
                continue
            road_data = frame["roads"][rid]
            x0, y0 = positions[road.from_node.node_id]
            x1, y1 = positions[road.to_node.node_id]
            dx, dy = x1 - x0, y1 - y0
            length = math.sqrt(dx*dx + dy*dy) or 1

            # Perpendicular offset to separate bi-directional lanes
            perp_x, perp_y = -dy / length * 0.12, dx / length * 0.12

            n_veh = len(road_data["vehicles"])
            cap   = road_data["capacity"]
            for i, (vid, dest_id, color, steps_left) in enumerate(road_data["vehicles"]):
                # Position along road: vehicles spread evenly
                t = (i + 0.5) / max(n_veh, 1)
                vx.append(x0 + t * dx + perp_x)
                vy.append(y0 + t * dy + perp_y)
                vc.append(color)

        if vx:
            vehicle_scatter.set_offsets(np.c_[vx, vy])
            vehicle_scatter.set_facecolor(vc)
        else:
            vehicle_scatter.set_offsets(np.empty((0, 2)))

        gen  = sum(frame["sources"].values())
        arr  = sum(frame["sinks"].values())
        step_text.set_text(
            f"Step {frame['step']:4d} | Generated: {gen:4d} | Arrived: {arr:4d}")
        return vehicle_scatter, step_text

    anim = FuncAnimation(fig, _update, frames=step_indices,
                         interval=1000 // fps, blit=False)

    writer = PillowWriter(fps=fps)
    anim.save(output_path, writer=writer, dpi=120)
    plt.close(fig)
    print(f"[Visualizer] Saved animation → {output_path}")


# ---------------------------------------------------------------------------
# Static statistics plot
# ---------------------------------------------------------------------------
def plot_statistics(engine, output_path: str = "statistics.png"):
    """Save a static statistics dashboard."""
    stats = engine.statistics()
    history = engine.history
    steps = [f["step"] for f in history]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#1a1a2e")
    fig.suptitle("Traffic Network Statistics", color="white",
                 fontsize=14, fontweight="bold")

    for ax in axes.flat:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#a0a0c0")
        for spine in ax.spines.values():
            spine.set_edgecolor("#4a4a6a")
        ax.title.set_color("white")
        ax.xaxis.label.set_color("#a0a0c0")
        ax.yaxis.label.set_color("#a0a0c0")

    # 1. Cumulative generated vs arrived
    gen_hist = [sum(f["sources"].values()) for f in history]
    arr_hist = [sum(f["sinks"].values()) for f in history]
    axes[0, 0].plot(steps, gen_hist, color="#27ae60", label="Generated", lw=2)
    axes[0, 0].plot(steps, arr_hist, color="#e74c3c", label="Arrived",   lw=2)
    axes[0, 0].set_title("Vehicles Generated vs Arrived")
    axes[0, 0].legend(facecolor="#2c3e50", labelcolor="white")
    axes[0, 0].set_xlabel("Step")
    axes[0, 0].set_ylabel("Cumulative count")

    # 2. Road throughput bar
    road_ids = list(stats["road_throughput"].keys())
    throughputs = list(stats["road_throughput"].values())
    colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(road_ids)))
    axes[0, 1].bar(road_ids, throughputs, color=colors)
    axes[0, 1].set_title("Total Throughput per Road")
    axes[0, 1].set_xlabel("Road ID")
    axes[0, 1].set_ylabel("Vehicles entered")
    axes[0, 1].tick_params(axis="x", rotation=45)

    # 3. Junction wait steps
    jids = list(stats["junction_wait_steps"].keys())
    waits = list(stats["junction_wait_steps"].values())
    axes[1, 0].bar(jids, waits, color="#3498db")
    axes[1, 0].set_title("Total Wait Steps per Junction")
    axes[1, 0].set_xlabel("Junction ID")
    axes[1, 0].set_ylabel("Cumulative wait steps")

    # 4. Per-sink received
    sink_ids = list(stats["per_sink"].keys())
    received = [stats["per_sink"][s]["received"] for s in sink_ids]
    avg_tt   = [stats["per_sink"][s]["avg_travel_time"] for s in sink_ids]
    x = np.arange(len(sink_ids))
    w = 0.35
    axes[1, 1].bar(x - w/2, received, w, label="Received", color="#e67e22")
    axes[1, 1].bar(x + w/2, avg_tt,   w, label="Avg travel time", color="#9b59b6")
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(sink_ids)
    axes[1, 1].set_title("Per-Sink: Received & Avg Travel Time")
    axes[1, 1].set_xlabel("Sink ID")
    axes[1, 1].legend(facecolor="#2c3e50", labelcolor="white")

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[Visualizer] Saved statistics plot → {output_path}")
