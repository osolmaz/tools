from pathlib import Path

import pytest
from PIL import Image

from tilekit.cli import main
from tilekit.core import PRESETS, CanvasSize, build_shadow, scale_preset
from tilekit.images import load_tile


def test_canvas_size_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError, match="positive"):
        CanvasSize(width=0, height=1080)


def test_preset_scales_with_canvas() -> None:
    scaled = scale_preset(PRESETS["denser-even"], CanvasSize(width=1920, height=1080))

    assert scaled.width_bands[0][1] == pytest.approx(194)
    assert scaled.bleed_x == 160
    assert scaled.ideal_clearance == pytest.approx(25)


def test_load_tile_crops_transparent_space(tmp_path: Path) -> None:
    source = tmp_path / "tile.png"
    image = Image.new("RGBA", (30, 20), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (8, 5, 24, 16))
    image.save(source)

    loaded = load_tile(source)

    assert loaded.size == (16, 11)


def test_load_tile_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError) as error:
        load_tile(missing)

    assert error.value.args == (missing,)


def test_load_tile_rejects_fully_transparent_image(tmp_path: Path) -> None:
    source = tmp_path / "transparent.png"
    Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(source)

    with pytest.raises(ValueError, match="^input image has no visible pixels$"):
        load_tile(source)


def test_load_tile_supports_svg(tmp_path: Path) -> None:
    source = tmp_path / "tile.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10">'
        '<rect x="2" y="1" width="16" height="8" fill="red"/>'
        "</svg>",
        encoding="utf-8",
    )

    loaded = load_tile(source)

    assert loaded.size == (1280, 640)
    assert loaded.mode == "RGBA"


def test_load_tile_rejects_missing_svg_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "tile.svg"
    source.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    monkeypatch.setattr("tilekit.images.cairosvg.svg2png", lambda **_kwargs: None)

    with pytest.raises(RuntimeError, match="^SVG renderer did not return image data$"):
        load_tile(source)


def test_load_tile_converts_rgb_raster_to_rgba(tmp_path: Path) -> None:
    source = tmp_path / "rgb.png"
    Image.new("RGB", (12, 8), (255, 0, 0)).save(source)

    loaded = load_tile(source)

    assert loaded.mode == "RGBA"


def test_shadow_uses_rotated_tile_silhouette() -> None:
    unrotated = Image.new("RGBA", (42, 18), (255, 255, 255, 255))
    tile = unrotated.rotate(90, expand=True)

    shadow, pad = build_shadow(tile, width=180)

    assert shadow.size == (tile.width + pad * 2, tile.height + pad * 2)
    assert shadow.height > shadow.width


def test_cli_renders_a_custom_canvas(tmp_path: Path) -> None:
    source = tmp_path / "tile.png"
    output = tmp_path / "pattern.png"
    Image.new("RGBA", (64, 64), (255, 200, 0, 255)).save(source)

    main(
        [
            str(source),
            "--preset",
            "denser-even",
            "--width",
            "640",
            "--height",
            "360",
            "--output",
            str(output),
        ]
    )

    with Image.open(output) as rendered:
        assert rendered.size == (640, 360)
