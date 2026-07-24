use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fmt;
use std::path::Path;

const PNG_SIGNATURE: &[u8; 8] = b"\x89PNG\r\n\x1a\n";
const REMOVABLE_CHUNKS: &[[u8; 4]] = &[*b"caBX", *b"eXIf", *b"iTXt", *b"tEXt", *b"tIME", *b"zTXt"];
const RENDERING_ANCILLARY_CHUNKS: &[[u8; 4]] = &[
    *b"bKGD", *b"cHRM", *b"gAMA", *b"hIST", *b"iCCP", *b"pHYs", *b"sBIT", *b"sPLT", *b"sRGB",
    *b"tRNS",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PngError(String);

impl PngError {
    fn new(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

impl fmt::Display for PngError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl std::error::Error for PngError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Inspection {
    pub size: usize,
    pub chunks: Vec<String>,
    pub metadata_chunks: Vec<String>,
    pub c2pa_detected: bool,
    pub openai_detected: bool,
    pub trailing_bytes: usize,
    pub idat_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SanitizeResult {
    pub input_size: usize,
    pub output_size: usize,
    pub removed_chunks: Vec<String>,
    pub removed_bytes: usize,
    pub trailing_bytes_removed: usize,
    pub idat_sha256: String,
    pub image_data_unchanged: bool,
}

#[derive(Debug, Clone, Copy)]
struct Chunk<'a> {
    kind: [u8; 4],
    data: &'a [u8],
    raw: &'a [u8],
}

impl Chunk<'_> {
    fn name(self) -> Result<String, PngError> {
        std::str::from_utf8(&self.kind)
            .map(str::to_owned)
            .map_err(|_| PngError::new("PNG chunk type is not ASCII"))
    }
}

#[derive(Debug)]
struct ParsedPng<'a> {
    chunks: Vec<Chunk<'a>>,
    trailing_bytes: usize,
}

fn read_u32(content: &[u8], offset: usize) -> Result<u32, PngError> {
    let bytes = content
        .get(offset..offset + 4)
        .ok_or_else(|| PngError::new(format!("truncated PNG value at byte {offset}")))?;
    Ok(u32::from_be_bytes(bytes.try_into().map_err(|_| {
        PngError::new("invalid four-byte PNG value")
    })?))
}

fn crc32(parts: &[&[u8]]) -> u32 {
    let mut crc = u32::MAX;
    for byte in parts.iter().flat_map(|part| part.iter().copied()) {
        crc ^= u32::from(byte);
        for _ in 0..8 {
            let mask = 0_u32.wrapping_sub(crc & 1);
            crc = (crc >> 1) ^ (0xedb8_8320 & mask);
        }
    }
    !crc
}

fn validate_chunk_type(kind: &[u8; 4], offset: usize) -> Result<(), PngError> {
    if kind.iter().all(u8::is_ascii_alphabetic) {
        Ok(())
    } else {
        Err(PngError::new(format!(
            "invalid PNG chunk type at byte {offset}"
        )))
    }
}

fn read_chunk(content: &[u8], offset: usize) -> Result<(Chunk<'_>, usize), PngError> {
    if content.len().saturating_sub(offset) < 12 {
        return Err(PngError::new(format!(
            "truncated PNG chunk at byte {offset}"
        )));
    }

    let length = usize::try_from(read_u32(content, offset)?)
        .map_err(|_| PngError::new("PNG chunk length does not fit this platform"))?;
    let end = offset
        .checked_add(12)
        .and_then(|value| value.checked_add(length))
        .ok_or_else(|| PngError::new("PNG chunk length overflow"))?;
    if end > content.len() {
        return Err(PngError::new(format!(
            "PNG chunk at byte {offset} exceeds file length"
        )));
    }

    let kind: [u8; 4] = content[offset + 4..offset + 8]
        .try_into()
        .map_err(|_| PngError::new("invalid PNG chunk type length"))?;
    validate_chunk_type(&kind, offset)?;
    let data = &content[offset + 8..offset + 8 + length];
    let expected_crc = read_u32(content, offset + 8 + length)?;
    if crc32(&[&kind, data]) != expected_crc {
        let name = String::from_utf8_lossy(&kind);
        return Err(PngError::new(format!(
            "CRC mismatch in {name} chunk at byte {offset}"
        )));
    }

    Ok((
        Chunk {
            kind,
            data,
            raw: &content[offset..end],
        },
        end,
    ))
}

fn parse_png(content: &[u8]) -> Result<ParsedPng<'_>, PngError> {
    if !content.starts_with(PNG_SIGNATURE) {
        return Err(PngError::new("not a PNG file"));
    }

    let mut chunks = Vec::new();
    let mut offset = PNG_SIGNATURE.len();
    let mut saw_iend = false;
    while offset < content.len() {
        let (chunk, end) = read_chunk(content, offset)?;
        chunks.push(chunk);
        offset = end;
        if chunk.kind == *b"IEND" {
            saw_iend = true;
            break;
        }
    }

    if !saw_iend {
        return Err(PngError::new("PNG is missing IEND"));
    }
    if chunks.first().map(|chunk| chunk.kind) != Some(*b"IHDR") {
        return Err(PngError::new("PNG does not start with IHDR"));
    }

    Ok(ParsedPng {
        chunks,
        trailing_bytes: content.len() - offset,
    })
}

fn idat_sha256(chunks: &[Chunk<'_>]) -> Result<String, PngError> {
    let mut digest = Sha256::new();
    let mut saw_idat = false;
    for chunk in chunks {
        if chunk.kind == *b"IDAT" {
            digest.update(chunk.data);
            saw_idat = true;
        }
    }
    if !saw_idat {
        return Err(PngError::new("PNG has no IDAT chunks"));
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn contains_ascii(haystack: &[u8], needle: &[u8]) -> bool {
    haystack
        .windows(needle.len())
        .any(|window| window == needle)
}

fn is_removable(kind: [u8; 4], aggressive: bool) -> bool {
    if REMOVABLE_CHUNKS.contains(&kind) {
        return true;
    }
    aggressive && kind[0] & 0x20 != 0 && !RENDERING_ANCILLARY_CHUNKS.contains(&kind)
}

pub fn inspect_bytes(content: &[u8]) -> Result<Inspection, PngError> {
    let parsed = parse_png(content)?;
    let mut c2pa_detected = false;
    let mut openai_detected = false;
    let mut metadata_chunks = Vec::new();
    for chunk in &parsed.chunks {
        if REMOVABLE_CHUNKS.contains(&chunk.kind) {
            metadata_chunks.push((*chunk).name()?);
        }
        if chunk.kind == *b"caBX" {
            c2pa_detected = true;
            openai_detected |= contains_ascii(chunk.data, b"OpenAI");
        }
    }

    Ok(Inspection {
        size: content.len(),
        chunks: parsed
            .chunks
            .iter()
            .copied()
            .map(Chunk::name)
            .collect::<Result<Vec<_>, _>>()?,
        metadata_chunks,
        c2pa_detected,
        openai_detected,
        trailing_bytes: parsed.trailing_bytes,
        idat_sha256: idat_sha256(&parsed.chunks)?,
    })
}

pub fn inspect_file(path: &Path) -> Result<Inspection, PngError> {
    let content = std::fs::read(path)
        .map_err(|error| PngError::new(format!("cannot read {}: {error}", path.display())))?;
    inspect_bytes(&content)
}

pub fn sanitize_bytes(
    content: &[u8],
    aggressive: bool,
) -> Result<(Vec<u8>, SanitizeResult), PngError> {
    let parsed = parse_png(content)?;
    let input_hash = idat_sha256(&parsed.chunks)?;
    let mut output = Vec::with_capacity(content.len());
    output.extend_from_slice(PNG_SIGNATURE);
    let mut kept = Vec::new();
    let mut removed_chunks = Vec::new();
    for chunk in parsed.chunks {
        if is_removable(chunk.kind, aggressive) {
            removed_chunks.push(chunk.name()?);
        } else {
            output.extend_from_slice(chunk.raw);
            kept.push(chunk);
        }
    }

    let output_hash = idat_sha256(&kept)?;
    let image_data_unchanged = input_hash == output_hash;
    if !image_data_unchanged {
        return Err(PngError::new("sanitization changed IDAT image data"));
    }

    Ok((
        output.clone(),
        SanitizeResult {
            input_size: content.len(),
            output_size: output.len(),
            removed_chunks,
            removed_bytes: content.len() - output.len(),
            trailing_bytes_removed: parsed.trailing_bytes,
            idat_sha256: output_hash,
            image_data_unchanged,
        },
    ))
}

pub fn sanitize_file(path: &Path, aggressive: bool) -> Result<(Vec<u8>, SanitizeResult), PngError> {
    let content = std::fs::read(path)
        .map_err(|error| PngError::new(format!("cannot read {}: {error}", path.display())))?;
    sanitize_bytes(&content, aggressive)
}

pub fn rendering_ancillary_chunks() -> BTreeSet<String> {
    RENDERING_ANCILLARY_CHUNKS
        .iter()
        .map(|kind| String::from_utf8_lossy(kind).into_owned())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn chunk(kind: [u8; 4], data: &[u8]) -> Vec<u8> {
        let mut output = Vec::new();
        output.extend_from_slice(
            &u32::try_from(data.len())
                .expect("test chunk fits u32")
                .to_be_bytes(),
        );
        output.extend_from_slice(&kind);
        output.extend_from_slice(data);
        output.extend_from_slice(&crc32(&[&kind, data]).to_be_bytes());
        output
    }

    fn png(trailing: &[u8]) -> Vec<u8> {
        let mut output = PNG_SIGNATURE.to_vec();
        output.extend(chunk(*b"IHDR", &[0, 0, 0, 1, 0, 0, 0, 1, 8, 2, 0, 0, 0]));
        output.extend(chunk(*b"caBX", b"c2pa OpenAI Media Service"));
        output.extend(chunk(*b"tEXt", b"prompt\0private"));
        output.extend(chunk(*b"pHYs", &[0, 0, 11, 19, 0, 0, 11, 19, 1]));
        output.extend(chunk(*b"IDAT", b"compressed pixels"));
        output.extend(chunk(*b"IEND", b""));
        output.extend_from_slice(trailing);
        output
    }

    #[test]
    fn detects_openai_c2pa_metadata() {
        let inspection = inspect_bytes(&png(b"hidden")).expect("valid PNG");
        assert!(inspection.c2pa_detected);
        assert!(inspection.openai_detected);
        assert_eq!(inspection.metadata_chunks, ["caBX", "tEXt"]);
        assert_eq!(inspection.trailing_bytes, 6);
    }

    #[test]
    fn removes_metadata_without_changing_idat() {
        let source = png(b"hidden");
        let original = inspect_bytes(&source).expect("valid PNG");
        let (cleaned, result) = sanitize_bytes(&source, false).expect("sanitize PNG");
        let inspection = inspect_bytes(&cleaned).expect("valid sanitized PNG");

        assert_eq!(result.removed_chunks, ["caBX", "tEXt"]);
        assert_eq!(result.trailing_bytes_removed, 6);
        assert!(result.image_data_unchanged);
        assert_eq!(inspection.metadata_chunks, Vec::<String>::new());
        assert_eq!(inspection.trailing_bytes, 0);
        assert!(inspection.chunks.contains(&"pHYs".to_owned()));
        assert_eq!(inspection.idat_sha256, original.idat_sha256);
    }

    #[test]
    fn aggressive_mode_removes_unknown_ancillary_chunks() {
        let source = png(b"");
        let idat = chunk(*b"IDAT", b"compressed pixels");
        let insertion = [chunk(*b"vpAg", b"private"), idat.clone()].concat();
        let source = source
            .windows(idat.len())
            .position(|window| window == idat)
            .map(|index| {
                let mut result = source.clone();
                result.splice(index..index + idat.len(), insertion);
                result
            })
            .expect("IDAT chunk present");

        let (cleaned, result) = sanitize_bytes(&source, true).expect("sanitize PNG");
        let inspection = inspect_bytes(&cleaned).expect("valid sanitized PNG");

        assert!(result.removed_chunks.contains(&"vpAg".to_owned()));
        assert!(!inspection.chunks.contains(&"vpAg".to_owned()));
        assert!(inspection.chunks.contains(&"pHYs".to_owned()));
    }

    #[test]
    fn rejects_non_png_data() {
        assert_eq!(
            inspect_bytes(b"not png")
                .expect_err("must reject")
                .to_string(),
            "not a PNG file"
        );
    }

    #[test]
    fn rejects_crc_mismatch() {
        let mut source = png(b"");
        let crc_index = source.len() - 1;
        source[crc_index] ^= 0xff;
        assert!(
            inspect_bytes(&source)
                .expect_err("must reject")
                .to_string()
                .contains("CRC mismatch")
        );
    }

    #[test]
    fn exposes_rendering_chunk_allowlist() {
        let chunks = rendering_ancillary_chunks();
        assert!(chunks.contains("pHYs"));
        assert!(chunks.contains("tRNS"));
    }
}
