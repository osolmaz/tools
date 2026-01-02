use clap::Parser;
use image::{DynamicImage, ImageBuffer, Rgba, RgbaImage};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

#[derive(Parser, Debug)]
#[command(
    name = "padify",
    version,
    about = "Add padding to images with auto padding and background."
)]
struct Args {
    /// Input image path (png, jpg, etc.)
    input: PathBuf,

    /// Output path (defaults to <input>_pad.<ext>)
    output: Option<PathBuf>,

    /// Horizontal padding in pixels (left/right). If set, vertical padding matches it.
    #[arg(long, value_name = "PX", conflicts_with = "all")]
    pad_x: Option<u32>,

    /// Vertical padding in pixels (top/bottom). If set, horizontal padding matches it.
    #[arg(long, value_name = "PX", conflicts_with = "all")]
    pad_y: Option<u32>,

    /// Set both horizontal and vertical padding
    #[arg(long, value_name = "PX", alias = "pad")]
    all: Option<u32>,

    /// Background color: "auto", "transparent", or hex (#RRGGBB or #RRGGBBAA)
    #[arg(long, value_name = "HEX", default_value = "auto")]
    bg: String,

    /// Disable auto-cropping of partial bottom artifacts
    #[arg(long)]
    no_crop: bool,

    /// Print crop decisions to stderr
    #[arg(long)]
    debug_crop: bool,
}

#[derive(Debug)]
struct PadifyError(String);

impl std::fmt::Display for PadifyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for PadifyError {}

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> Result<()> {
    let args = Args::parse();

    let input = &args.input;
    let output = args
        .output
        .clone()
        .unwrap_or_else(|| default_output_path(input));

    let image = image::open(input)?;
    let rgba = image.to_rgba8();
    let bg = if args.bg.trim().eq_ignore_ascii_case("auto") {
        deduce_background(&rgba)
    } else {
        parse_color(&args.bg)?
    };
    let crop_result = if args.no_crop {
        CropResult::no_crop(rgba.clone(), "disabled")
    } else {
        auto_crop_bottom_partial(&rgba, bg)
    };
    if args.debug_crop {
        eprintln!(
            "padify: crop {} -> {} ({})",
            crop_result.report.original_height,
            crop_result.report.new_height,
            crop_result.report.reason
        );
    }
    let cropped = crop_result.image;
    let (pad_x, pad_y) = resolve_padding(&args, cropped.dimensions())?;
    let (new_w, new_h) = padded_dimensions(cropped.dimensions(), pad_x, pad_y)?;
    let mut canvas = ImageBuffer::from_pixel(new_w, new_h, bg);

    image::imageops::replace(&mut canvas, &cropped, pad_x.into(), pad_y.into());

    DynamicImage::ImageRgba8(canvas).save(&output)?;
    println!("{}", output.display());
    Ok(())
}

fn padded_dimensions((w, h): (u32, u32), pad_x: u32, pad_y: u32) -> Result<(u32, u32)> {
    let pad_x2 = pad_x
        .checked_mul(2)
        .ok_or_else(|| PadifyError("horizontal padding is too large".into()))?;
    let pad_y2 = pad_y
        .checked_mul(2)
        .ok_or_else(|| PadifyError("vertical padding is too large".into()))?;
    let new_w = w
        .checked_add(pad_x2)
        .ok_or_else(|| PadifyError("resulting width is too large".into()))?;
    let new_h = h
        .checked_add(pad_y2)
        .ok_or_else(|| PadifyError("resulting height is too large".into()))?;
    Ok((new_w, new_h))
}

fn auto_pad(value: u32, ratio: f32, min: u32, max: u32) -> u32 {
    let scaled = ((value as f32) * ratio).round() as u32;
    clamp_u32(scaled, min, max)
}

fn resolve_padding(args: &Args, (w, h): (u32, u32)) -> Result<(u32, u32)> {
    let auto = auto_pad(w.min(h), 0.06, 48, 320);
    let pad = if let Some(all) = args.all {
        all
    } else {
        match (args.pad_x, args.pad_y) {
            (Some(x), Some(y)) => {
                if x != y {
                    return Err(Box::new(PadifyError(
                        "pad-x and pad-y must be equal (or use --all/--pad)".into(),
                    )));
                }
                x
            }
            (Some(x), None) => x,
            (None, Some(y)) => y,
            (None, None) => auto,
        }
    };
    Ok((pad, pad))
}

fn default_output_path(input: &Path) -> PathBuf {
    let parent = input.parent().unwrap_or_else(|| Path::new("."));
    let stem = input
        .file_stem()
        .map(|s| s.to_string_lossy().into_owned())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "output".to_string());
    let ext = input.extension().map(|s| s.to_string_lossy());

    let file_name = match ext {
        Some(ext) if !ext.is_empty() => format!("{stem}_pad.{ext}"),
        _ => format!("{stem}_pad.png"),
    };

    parent.join(file_name)
}

fn parse_color(input: &str) -> Result<Rgba<u8>> {
    let trimmed = input.trim();
    if trimmed.eq_ignore_ascii_case("transparent") {
        return Ok(Rgba([0, 0, 0, 0]));
    }

    let hex = trimmed.strip_prefix('#').unwrap_or(trimmed);
    if hex.len() != 6 && hex.len() != 8 {
        return Err(Box::new(PadifyError(
            "color must be #RRGGBB, #RRGGBBAA, or 'transparent'".into(),
        )));
    }

    let r = parse_hex_byte(&hex[0..2])?;
    let g = parse_hex_byte(&hex[2..4])?;
    let b = parse_hex_byte(&hex[4..6])?;
    let a = if hex.len() == 8 {
        parse_hex_byte(&hex[6..8])?
    } else {
        255
    };

    Ok(Rgba([r, g, b, a]))
}

fn parse_hex_byte(s: &str) -> Result<u8> {
    u8::from_str_radix(s, 16).map_err(|_| {
        Box::new(PadifyError(format!(
            "invalid color component '{s}', expected hex"
        ))) as Box<dyn std::error::Error>
    })
}

struct CropReport {
    original_height: u32,
    new_height: u32,
    reason: &'static str,
}

struct CropResult {
    image: RgbaImage,
    report: CropReport,
}

impl CropResult {
    fn no_crop(image: RgbaImage, reason: &'static str) -> Self {
        let original_height = image.height();
        Self {
            image,
            report: CropReport {
                original_height,
                new_height: original_height,
                reason,
            },
        }
    }

    fn cropped(image: RgbaImage, original_height: u32, reason: &'static str) -> Self {
        let new_height = image.height();
        Self {
            image,
            report: CropReport {
                original_height,
                new_height,
                reason,
            },
        }
    }
}

fn auto_crop_bottom_partial(image: &RgbaImage, bg: Rgba<u8>) -> CropResult {
    let (w, h) = image.dimensions();
    if w == 0 || h == 0 {
        return CropResult::no_crop(image.clone(), "empty");
    }

    let stride_x = std::cmp::max(1, w / 400) as usize;
    let diff_threshold = 18u16;
    let major_threshold = 0.02f32;
    let minor_threshold = 0.005f32;

    let mut ratios = Vec::with_capacity(h as usize);
    for y in 0..h {
        let mut samples = 0u32;
        let mut non_bg = 0u32;
        for x in (0..w).step_by(stride_x) {
            samples += 1;
            let pixel = image.get_pixel(x, y);
            if !is_background(*pixel, bg, diff_threshold) {
                non_bg += 1;
            }
        }
        let ratio = if samples == 0 {
            0.0
        } else {
            non_bg as f32 / samples as f32
        };
        ratios.push(ratio);
    }

    let major_rows: Vec<bool> = ratios.iter().map(|&r| r > major_threshold).collect();
    let minor_rows: Vec<bool> = ratios.iter().map(|&r| r > minor_threshold).collect();

    let mut clusters: Vec<(u32, u32)> = Vec::new();
    let mut in_cluster = false;
    let mut start = 0u32;
    for (i, &has_content) in major_rows.iter().enumerate() {
        if has_content && !in_cluster {
            start = i as u32;
            in_cluster = true;
        } else if !has_content && in_cluster {
            let end = i.saturating_sub(1) as u32;
            clusters.push((start, end));
            in_cluster = false;
        }
    }
    if in_cluster {
        clusters.push((start, h.saturating_sub(1)));
    }

    if clusters.is_empty() {
        return CropResult::no_crop(image.clone(), "no_clusters");
    }

    let bottom_margin_major = major_rows
        .iter()
        .rev()
        .take_while(|&&has_content| !has_content)
        .count() as u32;

    let mut heights: Vec<u32> = clusters
        .iter()
        .take(clusters.len().saturating_sub(1))
        .map(|(s, e)| e.saturating_sub(*s) + 1)
        .filter(|h| *h >= 4)
        .collect();

    if heights.is_empty() {
        heights = clusters
            .iter()
            .map(|(s, e)| e.saturating_sub(*s) + 1)
            .collect();
    }

    let median = median_u32(&mut heights).unwrap_or(0.0);

    if clusters.len() >= 2 && bottom_margin_major <= 2 && median > 0.0 {
        let (last_start, last_end) = *clusters.last().unwrap();
        let last_height = last_end.saturating_sub(last_start) + 1;
        if (last_height as f32) < median * 0.7 {
            if last_start > 0 {
                let cropped = image::imageops::crop_imm(image, 0, 0, w, last_start).to_image();
                return CropResult::cropped(cropped, h, "partial_line");
            }
        }
    }

    let last_major = major_rows.iter().rposition(|&v| v);
    let last_minor = minor_rows.iter().rposition(|&v| v);
    if let (Some(last_major), Some(last_minor)) = (last_major, last_minor) {
        if last_minor > last_major {
            let mut start_minor = last_minor;
            while start_minor > 0 && minor_rows[start_minor - 1] {
                start_minor -= 1;
            }
            let block_height = (last_minor - start_minor + 1) as u32;
            let gap = start_minor.saturating_sub(last_major + 1) as u32;
            let line_height = if median > 0.0 {
                median
            } else {
                clamp_u32(h / 30, 12, 28) as f32
            };
            let thin_block = (block_height as f32) < line_height * 0.35;
            let min_gap = std::cmp::max(2, (line_height * 0.2).round() as u32);
            let gap_ok = gap >= min_gap || (thin_block && gap >= 1);
            if gap_ok && (block_height as f32) < line_height * 0.6 {
                let cropped =
                    image::imageops::crop_imm(image, 0, 0, w, start_minor as u32).to_image();
                return CropResult::cropped(cropped, h, "cursor_residue");
            }
        }
    }

    CropResult::no_crop(image.clone(), "clean")
}

fn is_background(pixel: Rgba<u8>, bg: Rgba<u8>, threshold: u16) -> bool {
    let dr = (pixel[0] as i16 - bg[0] as i16).abs() as u16;
    let dg = (pixel[1] as i16 - bg[1] as i16).abs() as u16;
    let db = (pixel[2] as i16 - bg[2] as i16).abs() as u16;
    let da = (pixel[3] as i16 - bg[3] as i16).abs() as u16;
    dr + dg + db + da <= threshold
}

fn median_u32(values: &mut [u32]) -> Option<f32> {
    if values.is_empty() {
        return None;
    }
    values.sort_unstable();
    let mid = values.len() / 2;
    if values.len() % 2 == 1 {
        Some(values[mid] as f32)
    } else {
        Some((values[mid - 1] as f32 + values[mid] as f32) / 2.0)
    }
}

#[derive(Default, Clone, Copy)]
struct Bucket {
    count: u32,
    sum_r: u64,
    sum_g: u64,
    sum_b: u64,
    sum_a: u64,
}

fn deduce_background(image: &RgbaImage) -> Rgba<u8> {
    let (w, h) = image.dimensions();
    if w == 0 || h == 0 {
        return Rgba([0, 0, 0, 0]);
    }

    let stride_x = std::cmp::max(1, w / 200) as usize;
    let stride_y = std::cmp::max(1, h / 200) as usize;
    let band = clamp_u32(std::cmp::min(w, h) / 20, 8, 64);

    let border = dominant_sample(image, stride_x, stride_y, |x, y| {
        x < band || x >= w.saturating_sub(band) || y < band || y >= h.saturating_sub(band)
    });

    if let Some(color) = border.color_if_confident(0.2) {
        return color;
    }

    if border.transparent_ratio() >= 0.6 {
        return Rgba([0, 0, 0, 0]);
    }

    let overall = dominant_sample(image, stride_x, stride_y, |_x, _y| true);
    overall
        .color_if_confident(0.1)
        .unwrap_or_else(|| Rgba([0, 0, 0, 0]))
}

struct SampleResult {
    total: u32,
    transparent: u32,
    best: Option<Bucket>,
}

impl SampleResult {
    fn color_if_confident(&self, threshold: f32) -> Option<Rgba<u8>> {
        let non_transparent = self.total.saturating_sub(self.transparent);
        if non_transparent == 0 {
            return None;
        }

        let bucket = self.best?;
        let ratio = bucket.count as f32 / non_transparent as f32;
        if ratio < threshold {
            return None;
        }

        let count = bucket.count as u64;
        Some(Rgba([
            (bucket.sum_r / count) as u8,
            (bucket.sum_g / count) as u8,
            (bucket.sum_b / count) as u8,
            (bucket.sum_a / count) as u8,
        ]))
    }

    fn transparent_ratio(&self) -> f32 {
        if self.total == 0 {
            return 1.0;
        }
        self.transparent as f32 / self.total as f32
    }
}

fn dominant_sample<F>(
    image: &RgbaImage,
    stride_x: usize,
    stride_y: usize,
    include: F,
) -> SampleResult
where
    F: Fn(u32, u32) -> bool,
{
    let (w, h) = image.dimensions();
    let mut buckets: HashMap<u32, Bucket> = HashMap::new();
    let mut total: u32 = 0;
    let mut transparent: u32 = 0;

    for y in (0..h).step_by(stride_y) {
        for x in (0..w).step_by(stride_x) {
            if !include(x, y) {
                continue;
            }
            let pixel = image.get_pixel(x, y);
            total = total.saturating_add(1);
            if pixel[3] <= 5 {
                transparent = transparent.saturating_add(1);
                continue;
            }

            let key = quantize_key(*pixel);
            let entry = buckets.entry(key).or_insert_with(Bucket::default);
            entry.count = entry.count.saturating_add(1);
            entry.sum_r += pixel[0] as u64;
            entry.sum_g += pixel[1] as u64;
            entry.sum_b += pixel[2] as u64;
            entry.sum_a += pixel[3] as u64;
        }
    }

    let mut best: Option<Bucket> = None;
    let mut best_count = 0u32;
    for bucket in buckets.values() {
        if bucket.count > best_count {
            best_count = bucket.count;
            best = Some(*bucket);
        }
    }

    SampleResult {
        total,
        transparent,
        best,
    }
}

fn clamp_u32(value: u32, min: u32, max: u32) -> u32 {
    if value < min {
        min
    } else if value > max {
        max
    } else {
        value
    }
}

fn quantize_key(pixel: Rgba<u8>) -> u32 {
    let r = (pixel[0] >> 3) as u32;
    let g = (pixel[1] >> 3) as u32;
    let b = (pixel[2] >> 3) as u32;
    let a = (pixel[3] >> 3) as u32;
    (r << 15) | (g << 10) | (b << 5) | a
}
