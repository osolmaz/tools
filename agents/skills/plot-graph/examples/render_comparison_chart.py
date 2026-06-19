#!/usr/bin/env python3
"""Example renderer for a polished multi-panel comparison chart.

This script is intentionally self-contained. Replace DEFAULT_DATA or pass a JSON
file with the same shape:

    python render_comparison_chart.py metrics.json --out chart.svg --png chart.png
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle


DEFAULT_DATA = {
    "models": [
        {
            "id": "gemma",
            "label": "Gemma",
            "precision": 0.706,
            "recall": 0.904,
            "single_worker_output_tokens_per_second": 25.0,
            "aggregate_output_tokens_per_second": 402.6,
            "concurrency": 16,
            "total_parameters_b": 26,
            "active_parameters_b": 4,
        },
        {
            "id": "qwen",
            "label": "Qwen",
            "precision": 0.834,
            "recall": 0.812,
            "single_worker_output_tokens_per_second": 50.0,
            "aggregate_output_tokens_per_second": 145.3,
            "concurrency": 4,
            "total_parameters_b": 35,
            "active_parameters_b": 3,
        },
        {
            "id": "deepseek",
            "label": "DeepSeek",
            "precision": 0.938,
            "recall": 0.714,
            "single_worker_output_tokens_per_second": 13.0,
            "aggregate_output_tokens_per_second": 13.0,
            "concurrency": 1,
            "total_parameters_b": 284,
            "active_parameters_b": 13,
        },
    ]
}


PANEL_METRICS = [
    ("Precision", "precision", "higher is better", "{:.3f}"),
    ("Recall", "recall", "higher is better", "{:.3f}"),
]

GROUP_STEP = 0.8
SIDE_PADDING = 0.55
SINGLE_BAR_WIDTH = 0.50
GROUPED_BAR_WIDTH = 0.22


def model_positions(models):
    return [i * GROUP_STEP for i in range(len(models))]


def set_model_axis(ax, positions, names):
    ax.set_xlim(positions[0] - SIDE_PADDING, positions[-1] + SIDE_PADDING)
    ax.set_xticks(positions)
    ax.set_xticklabels(names)


def max_axis_value(values):
    return max(values) / 0.9 if values and max(values) else 1


def style_axis(ax):
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", length=0, colors="#4b5563")
    ax.grid(axis="y", color="#e9edf3", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_facecolor("#ffffff")
    ax.patch.set_alpha(1)
    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            transform=ax.transAxes,
            fill=False,
            linewidth=0.8,
            edgecolor="#d8dee8",
            clip_on=False,
            zorder=10,
        )
    )


def rounded_bar(ax, x, height, width, color, radius_px=7):
    """Draw a bar with circular top corners in display pixels.

    Matplotlib data-unit rounding is distorted by axis scaling; building the
    path in display coordinates keeps the radius visually circular.
    """
    left, bottom = ax.transData.transform((x - width / 2, 0))
    right, top = ax.transData.transform((x + width / 2, height))
    radius = min(radius_px, (right - left) / 2, (top - bottom) / 2)
    inv = ax.transData.inverted()

    points = [(left, bottom), (left, top - radius)]
    points.extend(
        (
            left + radius + radius * math.cos(angle),
            top - radius + radius * math.sin(angle),
        )
        for angle in [math.pi - i * (math.pi / 2) / 8 for i in range(9)]
    )
    points.append((right - radius, top))
    points.extend(
        (
            right - radius + radius * math.cos(angle),
            top - radius + radius * math.sin(angle),
        )
        for angle in [math.pi / 2 - i * (math.pi / 2) / 8 for i in range(9)]
    )
    points.extend([(right, bottom), (left, bottom)])

    data_points = inv.transform(points)
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(data_points) - 2) + [MplPath.CLOSEPOLY]
    patch = PathPatch(
        MplPath(data_points, codes),
        linewidth=0,
        facecolor=color,
        edgecolor="none",
        clip_on=True,
    )
    ax.add_patch(patch)
    return patch


def annotate_value(ax, x, value, text, is_best=False):
    ax.annotate(
        text,
        xy=(x, value),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold" if is_best else "normal",
        color="#111827",
    )


def render_metric_panel(ax, models, names, title, key, direction_label, value_format):
    positions = model_positions(models)
    values = [model[key] for model in models]
    finite_values = [value for value in values if value is not None]
    best = max(finite_values)

    set_model_axis(ax, positions, names)
    ax.set_title(title, loc="left", pad=10, color="#1f2328")
    ax.text(
        1.0,
        1.06,
        direction_label,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.5,
        color="#687385",
    )
    ymax = max_axis_value(finite_values)
    ax.set_ylim(0, ymax)
    ax.set_yticks([0, ymax])
    ax.set_yticklabels(["0", ""])
    style_axis(ax)

    for x, value in zip(positions, values):
        if value is None:
            annotate_value(ax, x, 0, "n/a")
            continue
        color = "#2563eb" if value == best else "#aeb7c5"
        rounded_bar(ax, x, value, SINGLE_BAR_WIDTH, color)
        annotate_value(ax, x, value, value_format.format(value), is_best=value == best)


def render_throughput_panel(ax, models, names):
    group_x = model_positions(models)
    width = GROUPED_BAR_WIDTH
    single_values = [model["single_worker_output_tokens_per_second"] for model in models]
    aggregate_values = [model["aggregate_output_tokens_per_second"] for model in models]
    single_x = [x - width / 2 for x in group_x]
    aggregate_x = [x + width / 2 for x in group_x]

    ax.set_title("Output tok/s", loc="left", pad=10, color="#1f2328")
    ax.text(1.0, 1.06, "higher is better", transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color="#687385")
    set_model_axis(ax, group_x, names)
    ymax = max_axis_value(single_values + aggregate_values)
    ax.set_ylim(0, ymax)
    ax.set_yticks([0, ymax])
    ax.set_yticklabels(["0", ""])
    style_axis(ax)

    for x, value in zip(single_x, single_values):
        rounded_bar(ax, x, value, width, "#93c5fd", radius_px=6)
        annotate_value(ax, x, value, f"{value:.0f}")
    for x, value in zip(aggregate_x, aggregate_values):
        rounded_bar(ax, x, value, width, "#2563eb", radius_px=6)
        annotate_value(ax, x, value, f"{value:.0f}", is_best=value == max(aggregate_values))

    ax.bar([], [], width=width, color="#93c5fd", edgecolor="none", label="Per single worker")
    ax.bar([], [], width=width, color="#2563eb", edgecolor="none", label="Aggregate")
    ax.legend(loc="upper right", frameon=False, fontsize=7.2, ncols=1, handlelength=1.2)


def render_single_bar_panel(ax, models, names, title, key, value_format="{:.0f}"):
    positions = model_positions(models)
    values = [model[key] for model in models]
    best = max(values)
    set_model_axis(ax, positions, names)
    ax.set_title(title, loc="left", pad=10, color="#1f2328")
    ymax = max_axis_value(values)
    ax.set_ylim(0, ymax)
    ax.set_yticks([0, ymax])
    ax.set_yticklabels(["0", ""])
    style_axis(ax)

    for x, value in zip(positions, values):
        color = "#2563eb" if value == best else "#aeb7c5"
        rounded_bar(ax, x, value, SINGLE_BAR_WIDTH, color)
        annotate_value(ax, x, value, value_format.format(value), is_best=value == best)


def render_parameter_panel(ax, models, names):
    group_x = model_positions(models)
    width = GROUPED_BAR_WIDTH
    total_values = [model["total_parameters_b"] for model in models]
    active_values = [model["active_parameters_b"] for model in models]
    total_x = [x - width / 2 for x in group_x]
    active_x = [x + width / 2 for x in group_x]

    ax.set_title("Parameters", loc="left", pad=10, color="#1f2328")
    set_model_axis(ax, group_x, names)
    ymax = max_axis_value(total_values + active_values)
    ax.set_ylim(0, ymax)
    ax.set_yticks([0, ymax])
    ax.set_yticklabels(["0", ""])
    style_axis(ax)

    for x, value in zip(total_x, total_values):
        rounded_bar(ax, x, value, width, "#2563eb", radius_px=6)
        annotate_value(ax, x, value, f"{value:.0f}B", is_best=value == max(total_values + active_values))
    for x, value in zip(active_x, active_values):
        rounded_bar(ax, x, value, width, "#93c5fd", radius_px=6)
        annotate_value(ax, x, value, f"{value:.0f}B")

    ax.bar([], [], width=width, color="#2563eb", edgecolor="none", label="Total")
    ax.bar([], [], width=width, color="#93c5fd", edgecolor="none", label="Active")
    ax.legend(loc="upper left", frameon=False, fontsize=7.5, ncols=2, handlelength=1.2, columnspacing=0.8)


def create_axes(fig):
    """Create 3-over-2 centered layout with preserved panel aspect ratio."""
    fig_width, fig_height = fig.get_size_inches()
    panel_width = 2.754807692307692
    panel_height = 2.88
    panel_gap = 0.50
    row_gap = 0.86
    bottom_margin = 0.55

    def add_axis(left_in, bottom_in):
        return fig.add_axes(
            [
                left_in / fig_width,
                bottom_in / fig_height,
                panel_width / fig_width,
                panel_height / fig_height,
            ]
        )

    top_width = panel_width * 3 + panel_gap * 2
    bottom_width = panel_width * 2 + panel_gap
    top_left = (fig_width - top_width) / 2
    bottom_left = (fig_width - bottom_width) / 2
    bottom_y = bottom_margin
    top_y = bottom_y + panel_height + row_gap
    return [
        add_axis(top_left, top_y),
        add_axis(top_left + panel_width + panel_gap, top_y),
        add_axis(top_left + (panel_width + panel_gap) * 2, top_y),
        add_axis(bottom_left, bottom_y),
        add_axis(bottom_left + panel_width + panel_gap, bottom_y),
    ]


def render(data, out_path, png_path):
    models = data["models"]
    names = [model["label"] for model in models]
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Arial", "DejaVu Sans"],
            "axes.titleweight": "bold",
            "axes.titlesize": 11,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "svg.fonttype": "none",
        }
    )

    fig = plt.figure(figsize=(16.5, 7.6), constrained_layout=False)
    fig.patch.set_alpha(0)
    axes = create_axes(fig)

    for ax, metric in zip(axes[:2], PANEL_METRICS):
        render_metric_panel(ax, models, names, *metric)
    render_throughput_panel(axes[2], models, names)
    render_single_bar_panel(axes[3], models, names, "Concurrency", "concurrency")
    render_parameter_panel(axes[4], models, names)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=180, bbox_inches="tight")
    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data", nargs="?", type=Path, help="JSON data file. Uses embedded sample data if omitted.")
    parser.add_argument("--out", type=Path, default=Path("comparison-chart.svg"))
    parser.add_argument("--png", type=Path, default=Path("comparison-chart.png"))
    args = parser.parse_args()

    data = json.loads(args.data.read_text()) if args.data else DEFAULT_DATA
    fig = render(data, args.out, args.png)

    for i, ax in enumerate(fig.axes, start=1):
        bbox = ax.get_position()
        width_in = bbox.width * fig.get_figwidth()
        height_in = bbox.height * fig.get_figheight()
        print(f"panel {i}: {width_in:.3f}in x {height_in:.3f}in ratio={width_in / height_in:.3f}")
    print(args.out)
    print(args.png)


if __name__ == "__main__":
    main()
