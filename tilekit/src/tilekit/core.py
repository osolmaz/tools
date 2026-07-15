#!/usr/bin/env python3
from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np
from PIL import Image, ImageFilter

REFERENCE_WIDTH = 3840
REFERENCE_HEIGHT = 2160


@dataclass(frozen=True)
class CanvasSize:
    width: int = REFERENCE_WIDTH
    height: int = REFERENCE_HEIGHT

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("canvas dimensions must be positive")


@dataclass(frozen=True)
class RenderResult:
    image: Image.Image
    placed_count: int
    prepared_count: int
    source_counts: tuple[int, ...]
    metrics: dict[str, float]
    failures: tuple[str, ...]


@dataclass(frozen=True)
class Preset:
    name: str
    seed: int
    count: int
    min_clearance: float
    soft_clearance: float
    radius_padding: float
    ideal_clearance: float | None
    bleed_x: int
    bleed_y: int
    width_bands: tuple[tuple[float, float, float], ...]
    angle_limit: float


@dataclass
class PreparedTile:
    width: float
    angle: float
    image: Image.Image
    radius: float
    target_x: float | None
    target_y: float | None


@dataclass
class PlacedTile(PreparedTile):
    x: float
    y: float


def place_prepared(tile: PreparedTile, x: float, y: float) -> PlacedTile:
    return PlacedTile(
        width=tile.width,
        angle=tile.angle,
        image=tile.image,
        radius=tile.radius,
        target_x=tile.target_x,
        target_y=tile.target_y,
        x=x,
        y=y,
    )


PRESETS = {
    "size-aware-dense": Preset(
        name="size-aware-dense",
        seed=84218,
        count=58,
        min_clearance=14,
        soft_clearance=16,
        radius_padding=16,
        ideal_clearance=None,
        bleed_x=350,
        bleed_y=285,
        width_bands=(
            (0.10, 320, 390),
            (0.34, 245, 315),
            (0.75, 165, 240),
            (1.00, 115, 160),
        ),
        angle_limit=50,
    ),
    "closer": Preset(
        name="closer",
        seed=84220,
        count=62,
        min_clearance=4,
        soft_clearance=6,
        radius_padding=10,
        ideal_clearance=None,
        bleed_x=365,
        bleed_y=295,
        width_bands=(
            (0.12, 405, 515),
            (0.42, 295, 395),
            (0.84, 195, 290),
            (1.00, 125, 185),
        ),
        angle_limit=52,
    ),
    "denser-variance": Preset(
        name="denser-variance",
        seed=84223,
        count=74,
        min_clearance=0,
        soft_clearance=4,
        radius_padding=9,
        ideal_clearance=None,
        bleed_x=380,
        bleed_y=305,
        width_bands=(
            (0.12, 388, 560),
            (0.42, 280, 410),
            (0.84, 181, 304),
            (1.00, 116, 194),
        ),
        angle_limit=52,
    ),
    "denser-even": Preset(
        name="denser-even",
        seed=84237,
        count=74,
        min_clearance=8,
        soft_clearance=28,
        radius_padding=9,
        ideal_clearance=50,
        bleed_x=320,
        bleed_y=260,
        width_bands=(
            (0.12, 388, 560),
            (0.42, 280, 410),
            (0.84, 181, 304),
            (1.00, 116, 194),
        ),
        angle_limit=52,
    ),
}


def scale_preset(preset: Preset, canvas_size: CanvasSize) -> Preset:
    """Scale the 4K-tuned layout measurements to another canvas size."""
    scale = min(
        canvas_size.width / REFERENCE_WIDTH,
        canvas_size.height / REFERENCE_HEIGHT,
    )
    return replace(
        preset,
        min_clearance=preset.min_clearance * scale,
        soft_clearance=preset.soft_clearance * scale,
        radius_padding=preset.radius_padding * scale,
        ideal_clearance=(
            preset.ideal_clearance * scale if preset.ideal_clearance is not None else None
        ),
        bleed_x=max(1, round(preset.bleed_x * scale)),
        bleed_y=max(1, round(preset.bleed_y * scale)),
        width_bands=tuple(
            (threshold, low * scale, high * scale) for threshold, low, high in preset.width_bands
        ),
    )


def build_background(canvas_size: CanvasSize) -> Image.Image:
    x = np.linspace(0, 1, canvas_size.width, dtype=np.float32)
    y = np.linspace(0, 1, canvas_size.height, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)

    left = np.array([42, 151, 238], dtype=np.float32)
    right = np.array([188, 228, 247], dtype=np.float32)
    upper = np.array([18, 130, 229], dtype=np.float32)

    bg = left * (1 - xx[..., None]) + right * xx[..., None]
    bg = bg * 0.80 + (upper * (1 - yy[..., None]) + right * yy[..., None]) * 0.20
    radius = np.sqrt(((xx - 0.56) / 0.80) ** 2 + ((yy - 0.47) / 0.92) ** 2)
    bg += np.clip(1 - radius, 0, 1)[..., None] * 14
    bg += (
        np.random.default_rng(31)
        .normal(
            0,
            1.35,
            (canvas_size.height, canvas_size.width, 1),
        )
        .astype(np.float32)
    )

    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")


def choose_widths(preset: Preset, rng: random.Random) -> list[float]:
    widths: list[float] = []
    for _ in range(preset.count):
        roll = rng.random()
        for threshold, lo, hi in preset.width_bands:
            if roll < threshold:
                widths.append(rng.uniform(lo, hi))
                break
    widths.sort(reverse=True)
    return widths


def choose_angles(count: int, angle_limit: float, rng: random.Random) -> list[float]:
    """Build a balanced tilt mix with a deliberately stronger left lean."""
    neutral_angles = [rng.triangular(-angle_limit, angle_limit, 0) for _ in range(count)]
    return [angle * (1.70 if angle > 0 else 0.70) for angle in neutral_angles]


def prepare_tile(
    tile: Image.Image,
    width: float,
    angle: float,
    radius_padding: float,
) -> PreparedTile | None:
    image = tile.resize(
        (int(width), int(tile.height * width / tile.width)),
        Image.Resampling.LANCZOS,
    )
    image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return None

    box_w = bbox[2] - bbox[0]
    box_h = bbox[3] - bbox[1]
    return PreparedTile(
        width=width,
        angle=angle,
        image=image,
        radius=0.50 * max(box_w, box_h) + radius_padding,
        target_x=None,
        target_y=None,
    )


def prepare_items(
    tile: Image.Image,
    preset: Preset,
    rng: random.Random,
    canvas_size: CanvasSize,
) -> list[PreparedTile]:
    items: list[PreparedTile] = []
    widths = choose_widths(preset, rng)
    angles = choose_angles(len(widths), preset.angle_limit, rng)
    for width, angle in zip(widths, angles, strict=False):
        prepared = prepare_tile(tile, width, angle, preset.radius_padding)
        if prepared is not None:
            items.append(prepared)

    assign_size_targets(items, preset, rng, canvas_size)

    return items


def assign_size_targets(
    items: list[PreparedTile],
    preset: Preset,
    rng: random.Random,
    canvas_size: CanvasSize,
) -> None:
    if preset.ideal_clearance is None:
        return

    cols = 10
    rows = 8
    zone_cols = 5
    zone_rows = 2
    zones: list[list[tuple[float, float]]] = [[] for _ in range(zone_cols * zone_rows)]

    # Include the bleed area in the target lattice. Keeping every target inside
    # the canvas makes large marks expensive near the edge while small marks,
    # placed later, drift into the bleed and creates a measurable center-size
    # bias even when every coarse zone receives the same size mix.
    target_x_min = -0.32 * preset.bleed_x
    target_x_max = canvas_size.width + 0.32 * preset.bleed_x
    target_y_min = -0.32 * preset.bleed_y
    target_y_max = canvas_size.height + 0.32 * preset.bleed_y
    target_width = target_x_max - target_x_min
    target_height = target_y_max - target_y_min

    for row in range(rows):
        for col in range(cols):
            x = target_x_min + (col + 0.5) * target_width / cols
            y = target_y_min + (row + 0.5) * target_height / rows
            jitter_x = rng.uniform(-0.20, 0.20) * target_width / cols
            jitter_y = rng.uniform(-0.20, 0.20) * target_height / rows
            zone_col = col // (cols // zone_cols)
            zone_row = row // (rows // zone_rows)
            zone = zone_row * zone_cols + zone_col
            zones[zone].append(
                (
                    min(max(x + jitter_x, target_x_min), target_x_max),
                    min(max(y + jitter_y, target_y_min), target_y_max),
                )
            )

    # Items arrive largest-first. Split them into consecutive groups of ten and
    # send one item from each group to every region of the canvas. This preserves
    # organic local variation while preventing a large-to-small directional drift.
    for zone_points in zones:
        rng.shuffle(zone_points)

    for group_start in range(0, len(items), len(zones)):
        group = items[group_start : group_start + len(zones)]
        zone_order = list(range(len(zones)))
        rng.shuffle(zone_order)
        for item, zone_index in zip(group, zone_order, strict=False):
            target_x, target_y = zones[zone_index].pop()
            item.target_x = target_x
            item.target_y = target_y


def prepare_items_from_widths(
    tile: Image.Image,
    widths: list[float],
    angle_limit: float,
    radius_padding: float,
    rng: random.Random,
) -> list[PreparedTile]:
    items: list[PreparedTile] = []
    angles = choose_angles(len(widths), angle_limit, rng)
    for width, angle in zip(widths, angles, strict=False):
        prepared = prepare_tile(tile, width, angle, radius_padding)
        if prepared is not None:
            items.append(prepared)

    return items


def balanced_source_indices(  # noqa: C901 -- assignment scoring combines spatial constraints
    placed: list[PlacedTile],
    source_count: int,
    preset: Preset,
    canvas_size: CanvasSize,
) -> list[int]:
    """Assign equally represented sources while mixing neighbors and regions."""
    if source_count <= 0:
        raise ValueError("source count must be positive")
    if source_count == 1 or len(placed) <= 1:
        return [0] * len(placed)

    total = len(placed)
    quotas = np.full(source_count, total // source_count, dtype=int)
    quotas[: total % source_count] += 1
    points = np.array([(point.x, point.y) for point in placed], dtype=float)
    widths = np.array([point.width for point in placed], dtype=float)
    distances = np.hypot(
        points[:, None, 0] - points[None, :, 0],
        points[:, None, 1] - points[None, :, 1],
    )
    np.fill_diagonal(distances, np.inf)

    edge_weights: dict[tuple[int, int], float] = {}
    neighbor_count = min(6, total - 1)
    for first in range(total):
        for second_value in np.argsort(distances[first])[:neighbor_count]:
            second = int(second_value)
            edge = (min(first, second), max(first, second))
            edge_weights[edge] = max(
                edge_weights.get(edge, 0.0),
                1.0 / (1.0 + distances[edge] / 300.0),
            )
    edge_first = np.array([edge[0] for edge in edge_weights], dtype=int)
    edge_second = np.array([edge[1] for edge in edge_weights], dtype=int)
    weights = np.array(list(edge_weights.values()), dtype=float)

    columns = np.clip((points[:, 0] / (canvas_size.width / 5)).astype(int), 0, 4)
    rows = np.clip((points[:, 1] / (canvas_size.height / 2)).astype(int), 0, 1)
    zones = rows * 5 + columns
    overall_width = float(widths.mean())

    def assignment_cost(labels: np.ndarray) -> float:
        neighbor_cost = float(weights[labels[edge_first] == labels[edge_second]].sum())
        regional_cost = 0.0
        for zone in range(10):
            zone_labels = labels[zones == zone]
            if len(zone_labels) == 0:
                continue
            counts = np.bincount(zone_labels, minlength=source_count)
            expected = len(zone_labels) * quotas / total
            regional_cost += float(np.square(counts - expected).sum())

        width_cost = 0.0
        for source_index in range(source_count):
            source_widths = widths[labels == source_index]
            if len(source_widths):
                width_cost += ((float(source_widths.mean()) - overall_width) / 100.0) ** 2
        return neighbor_cost + regional_cost * 1.8 + width_cost * 0.5

    rng = random.Random(preset.seed + 211)
    seed_labels = [
        source_index for source_index, quota in enumerate(quotas) for _ in range(int(quota))
    ]
    best_labels: np.ndarray | None = None
    best_cost = math.inf
    for _ in range(12):
        rng.shuffle(seed_labels)
        labels = np.array(seed_labels, dtype=int)
        current_cost = assignment_cost(labels)
        for _ in range(max(1200, total * 45)):
            first = rng.randrange(total)
            second = rng.randrange(total)
            if labels[first] == labels[second]:
                continue
            labels[first], labels[second] = labels[second], labels[first]
            candidate_cost = assignment_cost(labels)
            if candidate_cost <= current_cost:
                current_cost = candidate_cost
            else:
                labels[first], labels[second] = labels[second], labels[first]
        if current_cost < best_cost:
            best_cost = current_cost
            best_labels = labels.copy()

    if best_labels is None:
        raise RuntimeError("unable to assign tile sources")
    return [int(value) for value in best_labels]


def replace_tile_sources(
    placed: list[PlacedTile],
    tiles: Sequence[Image.Image],
    source_indices: Sequence[int],
    preset: Preset,
) -> None:
    for point, source_index in zip(placed, source_indices, strict=True):
        replacement = prepare_tile(
            tiles[source_index],
            point.width,
            point.angle,
            preset.radius_padding,
        )
        if replacement is None:
            raise ValueError("input image has no visible pixels")
        point.image = replacement.image
        point.radius = replacement.radius


def place_items(  # noqa: C901 -- candidate scoring intentionally combines layout constraints
    items: list[PreparedTile],
    preset: Preset,
    rng: random.Random,
    canvas_size: CanvasSize,
) -> list[PlacedTile]:
    scale = min(
        canvas_size.width / REFERENCE_WIDTH,
        canvas_size.height / REFERENCE_HEIGHT,
    )
    edge_margin = 80 * scale
    x_min = -preset.bleed_x
    y_min = -preset.bleed_y
    x_max = canvas_size.width + preset.bleed_x
    y_max = canvas_size.height + preset.bleed_y
    placed: list[PlacedTile] = []

    for idx, obj in enumerate(items):
        radius = obj.radius
        best: tuple[float, float] | None = None
        best_score = -1e9
        attempts = 7000 if idx < 20 else 4300

        for _ in range(attempts):
            x = rng.uniform(x_min, x_max)
            y = rng.uniform(y_min, y_max)
            if (
                x + radius < -edge_margin
                or x - radius > canvas_size.width + edge_margin
                or y + radius < -edge_margin
                or y - radius > canvas_size.height + edge_margin
            ):
                continue

            outside = x < 0 or x > canvas_size.width or y < 0 or y > canvas_size.height
            outside_skip = 0.54 if preset.ideal_clearance is not None else 0.34
            if outside and rng.random() < outside_skip:
                continue

            if placed:
                min_clearance = 1e9
                min_ratio = 1e9
                align_penalty = 0.0
                for other in placed:
                    distance = math.hypot(x - other.x, y - other.y)
                    needed = radius + other.radius
                    min_clearance = min(min_clearance, distance - needed)
                    min_ratio = min(min_ratio, distance / needed)
                    if distance < 1050 * scale:
                        if abs(x - other.x) < 72 * scale:
                            align_penalty += 24
                        if abs(y - other.y) < 72 * scale:
                            align_penalty += 24
                        if abs((x - other.x) - (y - other.y)) < 80 * scale:
                            align_penalty += 10

                if min_clearance < preset.min_clearance:
                    continue
                if preset.ideal_clearance is None:
                    score = min_ratio * 220 + min_clearance / scale * 0.48
                else:
                    # For dense patterns, reserve enough room for the scaled object but
                    # stop rewarding excess empty space once the target gap is reached.
                    # Only penalize gaps that are too tight. Penalizing excess
                    # clearance makes every new mark cling to the already placed
                    # cluster and overwhelms its spatial size target.
                    clearance_shortfall = max(0.0, preset.ideal_clearance - min_clearance)
                    score = (
                        min_ratio * 18
                        - clearance_shortfall / scale * 1.8
                        + min(min_clearance, preset.ideal_clearance) / scale * 0.16
                    )
                score += -align_penalty + rng.uniform(-12, 12)
            else:
                score = rng.uniform(0, 1)

            edge_bias = 1.2 if preset.ideal_clearance is not None else 5
            score += (
                abs((x - canvas_size.width / 2) / canvas_size.width)
                + abs((y - canvas_size.height / 2) / canvas_size.height)
            ) * edge_bias
            if outside:
                score += -6 if preset.ideal_clearance is not None else 10
            if obj.target_x is not None and obj.target_y is not None:
                target_distance = math.hypot(x - obj.target_x, y - obj.target_y)
                score -= target_distance / scale * 0.52
            if score > best_score:
                best_score = score
                best = (x, y)

        if best is not None:
            placed.append(place_prepared(obj, best[0], best[1]))

    even_out_distribution(placed, preset, x_min, y_min, x_max, y_max)
    relax_size_aware(placed, preset, x_min, y_min, x_max, y_max)
    return placed


def fill_voids_with_small_items(  # noqa: C901 -- void scoring balances geometry and regions
    placed: list[PlacedTile],
    tile: Image.Image,
    preset: Preset,
    rng: random.Random,
    count: int,
    canvas_size: CanvasSize,
) -> list[PlacedTile]:
    x_min = -preset.bleed_x
    y_min = -preset.bleed_y
    x_max = canvas_size.width + preset.bleed_x
    y_max = canvas_size.height + preset.bleed_y
    scale = min(
        canvas_size.width / REFERENCE_WIDTH,
        canvas_size.height / REFERENCE_HEIGHT,
    )
    widths = sorted(
        (rng.uniform(72, 145) * scale for _ in range(count)),
        reverse=True,
    )
    fillers = prepare_items_from_widths(
        tile,
        widths,
        preset.angle_limit,
        preset.radius_padding,
        rng,
    )

    samples = np.column_stack(
        (
            np.random.default_rng(preset.seed + 7).uniform(
                -80 * scale,
                canvas_size.width + 80 * scale,
                42000,
            ),
            np.random.default_rng(preset.seed + 11).uniform(
                -70 * scale,
                canvas_size.height + 70 * scale,
                42000,
            ),
        )
    ).astype(np.float32)
    filler_zone_counts = [0] * 10

    def filler_zone(x: float, y: float) -> int:
        col = min(4, max(0, int(x / (canvas_size.width / 5))))
        row = min(1, max(0, int(y / (canvas_size.height / 2))))
        return row * 5 + col

    for obj in fillers:
        radius = obj.radius
        best: tuple[float, float] | None = None
        best_score = -1e9

        # Try the emptiest visible pockets first, with a little randomness so
        # filler marks do not become a second grid.
        scored_samples: list[tuple[float, float, float]] = []
        for sample_x, sample_y in samples[::8]:
            min_clearance = 1e9
            for other in placed:
                distance = math.hypot(float(sample_x) - other.x, float(sample_y) - other.y)
                min_clearance = min(min_clearance, distance - (radius + other.radius))
            zone = filler_zone(float(sample_x), float(sample_y))
            balance_bonus = (max(filler_zone_counts) - filler_zone_counts[zone]) * 520
            scored_samples.append(
                (
                    min_clearance + balance_bonus + rng.uniform(-25, 25),
                    float(sample_x),
                    float(sample_y),
                )
            )
        scored_samples.sort(reverse=True)

        for _, x, y in scored_samples[:1200]:
            if (
                x + radius < -80 * scale
                or x - radius > canvas_size.width + 80 * scale
                or y + radius < -80 * scale
                or y - radius > canvas_size.height + 80 * scale
            ):
                continue
            min_clearance = 1e9
            align_penalty = 0.0
            for other in placed:
                distance = math.hypot(x - other.x, y - other.y)
                min_clearance = min(min_clearance, distance - (radius + other.radius))
                if distance < 880 * scale:
                    if abs(x - other.x) < 64 * scale:
                        align_penalty += 18
                    if abs(y - other.y) < 64 * scale:
                        align_penalty += 18

            if min_clearance < preset.min_clearance:
                continue
            target = 30 * scale
            zone = filler_zone(x, y)
            balance_bonus = (max(filler_zone_counts) - filler_zone_counts[zone]) * 520
            score = (
                -abs(min_clearance - target) / scale * 1.2
                - align_penalty
                + balance_bonus
                + rng.uniform(-8, 8)
            )
            if score > best_score:
                best_score = score
                best = (x, y)

        if best is not None:
            placed.append(place_prepared(obj, best[0], best[1]))
            filler_zone_counts[filler_zone(best[0], best[1])] += 1

    relax_size_aware(placed, preset, x_min, y_min, x_max, y_max)
    return placed


def relax_size_aware(
    placed: list[PlacedTile],
    preset: Preset,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
) -> None:
    for _ in range(40):
        forces = [{"x": 0.0, "y": 0.0} for _ in placed]
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                a = placed[i]
                b = placed[j]
                dx = a.x - b.x
                dy = a.y - b.y
                distance = math.hypot(dx, dy) or 1
                needed = a.radius + b.radius + preset.soft_clearance
                if distance >= needed:
                    continue
                push = (needed - distance) * 0.45
                ux = dx / distance
                uy = dy / distance
                forces[i]["x"] += ux * push
                forces[i]["y"] += uy * push
                forces[j]["x"] -= ux * push
                forces[j]["y"] -= uy * push

        for point, force in zip(placed, forces, strict=False):
            point.x = min(max(point.x + force["x"], x_min), x_max)
            point.y = min(max(point.y + force["y"], y_min), y_max)


def alpha_overlap_pixels(
    first: PlacedTile,
    second: PlacedTile,
    mask_cache: dict[int, np.ndarray] | None = None,
) -> int:
    """Return opaque pixels shared by two rendered marks."""
    first_image = first.image
    second_image = second.image

    first_x = round(first.x - first_image.width / 2)
    first_y = round(first.y - first_image.height / 2)
    second_x = round(second.x - second_image.width / 2)
    second_y = round(second.y - second_image.height / 2)
    left = max(first_x, second_x)
    top = max(first_y, second_y)
    right = min(first_x + first_image.width, second_x + second_image.width)
    bottom = min(first_y + first_image.height, second_y + second_image.height)
    if left >= right or top >= bottom:
        return 0

    cache = mask_cache if mask_cache is not None else {}
    first_mask = cache.setdefault(id(first_image), np.asarray(first_image.getchannel("A")) > 32)
    second_mask = cache.setdefault(id(second_image), np.asarray(second_image.getchannel("A")) > 32)
    first_crop = first_mask[top - first_y : bottom - first_y, left - first_x : right - first_x]
    second_crop = second_mask[
        top - second_y : bottom - second_y, left - second_x : right - second_x
    ]
    return int(np.count_nonzero(first_crop & second_crop))


def resolve_alpha_overlaps(
    placed: list[PlacedTile],
    preset: Preset,
    canvas_size: CanvasSize,
) -> None:
    """Separate any silhouettes missed by the fast circular placement model."""
    scale = min(
        canvas_size.width / REFERENCE_WIDTH,
        canvas_size.height / REFERENCE_HEIGHT,
    )
    mask_cache: dict[int, np.ndarray] = {}
    x_min = -preset.bleed_x
    y_min = -preset.bleed_y
    x_max = canvas_size.width + preset.bleed_x
    y_max = canvas_size.height + preset.bleed_y

    for _ in range(80):
        pushes = [{"x": 0.0, "y": 0.0} for _ in placed]
        overlap_count = 0
        for first_index in range(len(placed)):
            for second_index in range(first_index + 1, len(placed)):
                first = placed[first_index]
                second = placed[second_index]
                overlap = alpha_overlap_pixels(first, second, mask_cache)
                if overlap == 0:
                    continue
                overlap_count += 1
                dx = first.x - second.x
                dy = first.y - second.y
                distance = math.hypot(dx, dy) or 1.0
                step = max(2.0 * scale, min(18.0 * scale, math.sqrt(overlap) * 0.35))
                push_x = dx / distance * step
                push_y = dy / distance * step
                pushes[first_index]["x"] += push_x
                pushes[first_index]["y"] += push_y
                pushes[second_index]["x"] -= push_x
                pushes[second_index]["y"] -= push_y

        if overlap_count == 0:
            return
        for point, push in zip(placed, pushes, strict=False):
            point.x = min(max(point.x + push["x"], x_min), x_max)
            point.y = min(max(point.y + push["y"], y_min), y_max)

    raise RuntimeError("unable to resolve all rendered-tile overlaps")


def even_out_distribution(
    placed: list[PlacedTile],
    preset: Preset,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
) -> None:
    if preset.ideal_clearance is None or not placed:
        return

    rng = np.random.default_rng(preset.seed + 101)
    sample_count = max(18000, len(placed) * 320)
    samples = np.column_stack(
        (
            rng.uniform(x_min, x_max, sample_count),
            rng.uniform(y_min, y_max, sample_count),
        )
    )

    for _ in range(18):
        centers = np.array([(point.x, point.y) for point in placed], dtype=np.float32)
        radii = np.array([point.radius for point in placed], dtype=np.float32)
        dx = samples[:, 0, None] - centers[None, :, 0]
        dy = samples[:, 1, None] - centers[None, :, 1]
        # Assign space to the closest visible edge so larger marks naturally
        # claim more territory than smaller ones.
        owner = np.argmin(np.hypot(dx, dy) - radii[None, :], axis=1)

        for index, point in enumerate(placed):
            cell = samples[owner == index]
            if len(cell) < 12:
                continue
            target_x = float(cell[:, 0].mean())
            target_y = float(cell[:, 1].mean())
            if point.target_x is not None and point.target_y is not None:
                target_x = target_x * 0.62 + point.target_x * 0.38
                target_y = target_y * 0.62 + point.target_y * 0.38
            point.x = min(max(point.x * 0.66 + target_x * 0.34, x_min), x_max)
            point.y = min(max(point.y * 0.66 + target_y * 0.34, y_min), y_max)

        relax_size_aware(placed, preset, x_min, y_min, x_max, y_max)


def build_shadow(
    item: Image.Image,
    width: int,
    scale: float = 1.0,
) -> tuple[Image.Image, int]:
    """Build a blurred shadow from the already-rotated mark silhouette."""
    reference_width = width / scale
    blur = max(1, round((7 + max(0, reference_width - 180) // 38) * scale))
    shadow_pad = blur * 3
    alpha = Image.new(
        "L",
        (item.width + shadow_pad * 2, item.height + shadow_pad * 2),
    )
    alpha.paste(item.getchannel("A"), (shadow_pad, shadow_pad))
    alpha = alpha.filter(ImageFilter.GaussianBlur(blur))
    shadow = Image.new("RGBA", alpha.size, (10, 36, 70, 30))
    shadow.putalpha(alpha.point(lambda value: int(value * 0.145)))
    return shadow, shadow_pad


def composite(
    canvas: Image.Image,
    placed: list[PlacedTile],
    canvas_size: CanvasSize,
) -> None:
    scale = min(
        canvas_size.width / REFERENCE_WIDTH,
        canvas_size.height / REFERENCE_HEIGHT,
    )
    for point in placed:
        item = point.image
        width = int(point.width)
        shadow, shadow_pad = build_shadow(item, width, scale)

        x = int(point.x - item.width / 2)
        y = int(point.y - item.height / 2)
        shadow_x = int(point.x - item.width / 2 - shadow_pad)
        shadow_y = int(point.y - item.height / 2 - shadow_pad + max(9 * scale, width * 0.045))
        canvas.alpha_composite(shadow, (shadow_x, shadow_y))
        canvas.alpha_composite(item, (x, y))


def min_clearance(placed: list[PlacedTile]) -> float:
    minimum = float("inf")
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a = placed[i]
            b = placed[j]
            distance = math.hypot(a.x - b.x, a.y - b.y)
            minimum = min(minimum, distance - (a.radius + b.radius))
    return minimum


def layout_metrics(
    placed: list[PlacedTile],
    canvas_size: CanvasSize,
) -> dict[str, float]:
    """Measure size balance and size-aware spacing for a finished layout."""
    centers = np.array([(point.x, point.y) for point in placed])
    widths = np.array([point.width for point in placed])
    radii = np.array([point.radius for point in placed])
    angles = np.array([point.angle for point in placed])

    normalized_radius = np.hypot(
        (centers[:, 0] - canvas_size.width / 2) / (canvas_size.width / 2),
        (centers[:, 1] - canvas_size.height / 2) / (canvas_size.height / 2),
    )
    radial_size_correlation = float(np.corrcoef(widths, normalized_radius)[0, 1])
    largest = np.argsort(widths)[-10:]
    largest_radial_ratio = float(normalized_radius[largest].mean() / normalized_radius.mean())

    distances = np.hypot(
        centers[:, None, 0] - centers[None, :, 0],
        centers[:, None, 1] - centers[None, :, 1],
    )
    np.fill_diagonal(distances, np.inf)
    surface_gaps = distances - radii[:, None] - radii[None, :]
    nearest_gaps = surface_gaps.min(axis=1)

    ranks = np.argsort(np.argsort(widths)).astype(float) / max(1, len(widths) - 1)
    neighbors = np.argsort(distances, axis=1)[:, :4]
    local_size_correlation = float(
        np.corrcoef(np.repeat(ranks, neighbors.shape[1]), ranks[neighbors].ravel())[0, 1]
    )

    zone_means: list[float] = []
    for row in range(2):
        for col in range(5):
            in_zone = (
                (centers[:, 0] >= col * canvas_size.width / 5)
                & (centers[:, 0] < (col + 1) * canvas_size.width / 5)
                & (centers[:, 1] >= row * canvas_size.height / 2)
                & (centers[:, 1] < (row + 1) * canvas_size.height / 2)
            )
            if in_zone.any():
                zone_means.append(float(widths[in_zone].mean()))

    mask_cache: dict[int, np.ndarray] = {}
    alpha_overlap_pairs = sum(
        alpha_overlap_pixels(placed[first], placed[second], mask_cache) > 0
        for first in range(len(placed))
        for second in range(first + 1, len(placed))
    )
    left_tilts = angles[angles >= 10]
    right_tilts = angles[angles <= -10]

    return {
        "radial_size_correlation": radial_size_correlation,
        "largest_radial_ratio": largest_radial_ratio,
        "local_size_correlation": local_size_correlation,
        "zone_mean_size_cv": float(np.std(zone_means) / np.mean(zone_means)),
        "min_clearance": float(nearest_gaps.min()),
        "nearest_gap_cv": float(nearest_gaps.std() / nearest_gaps.mean()),
        "nearest_gap_p50": float(np.percentile(nearest_gaps, 50)),
        "nearest_gap_p90": float(np.percentile(nearest_gaps, 90)),
        "alpha_overlap_pairs": float(alpha_overlap_pairs),
        "mean_tilt_degrees": float(angles.mean()),
        "left_tilt_share": float(len(left_tilts) / len(angles)),
        "left_tilt_strength_ratio": float(left_tilts.mean() / abs(right_tilts.mean())),
    }


def metric_failures(metrics: dict[str, float], preset: Preset) -> list[str]:
    checks = {
        "radial size correlation": abs(metrics["radial_size_correlation"]) <= 0.15,
        "largest-mark radial balance": 0.90 <= metrics["largest_radial_ratio"] <= 1.10,
        "local size mixing": abs(metrics["local_size_correlation"]) <= 0.25,
        "regional mean-size variation": metrics["zone_mean_size_cv"] <= 0.12,
        "minimum clearance": metrics["min_clearance"] >= preset.min_clearance - 0.05,
        "nearest-gap variation": metrics["nearest_gap_cv"] <= 1.25,
        "rendered-tile overlap": metrics["alpha_overlap_pairs"] == 0,
    }
    if preset.name == "denser-even":
        checks.update(
            {
                "left-tilt representation": 0.30 <= metrics["left_tilt_share"] <= 0.45,
                "left-tilt strength": 1.75 <= metrics["left_tilt_strength_ratio"] <= 2.05,
            }
        )
    return [name for name, passed in checks.items() if not passed]


def render_tiles(
    tiles: Image.Image | Sequence[Image.Image],
    preset: Preset,
    canvas_size: CanvasSize,
) -> RenderResult:
    sources = (tiles,) if isinstance(tiles, Image.Image) else tuple(tiles)
    if not sources:
        raise ValueError("at least one input image is required")

    scaled_preset = scale_preset(preset, canvas_size)
    rng = random.Random(scaled_preset.seed)
    canvas = build_background(canvas_size)
    layout_tile = max(sources, key=lambda source: max(source.width, source.height) / source.width)
    items = prepare_items(layout_tile, scaled_preset, rng, canvas_size)
    placed = place_items(items, scaled_preset, rng, canvas_size)
    filler_count = 14 if scaled_preset.name == "denser-even" else 0
    if filler_count:
        filler_rng = random.Random(scaled_preset.seed + 3)
        placed = fill_voids_with_small_items(
            placed,
            layout_tile,
            scaled_preset,
            filler_rng,
            filler_count,
            canvas_size,
        )
    source_indices = balanced_source_indices(
        placed,
        len(sources),
        scaled_preset,
        canvas_size,
    )
    replace_tile_sources(placed, sources, source_indices, scaled_preset)
    resolve_alpha_overlaps(placed, scaled_preset, canvas_size)
    composite(canvas, placed, canvas_size)

    metrics = layout_metrics(placed, canvas_size)
    failures = tuple(metric_failures(metrics, scaled_preset))
    return RenderResult(
        image=canvas,
        placed_count=len(placed),
        prepared_count=len(items) + filler_count,
        source_counts=tuple(source_indices.count(index) for index in range(len(sources))),
        metrics=metrics,
        failures=failures,
    )
