#!/usr/bin/env python3
"""Vendor a pinned Modular LLM Inference Handbook checkout as plain Markdown."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, urlunsplit

UPSTREAM_REPOSITORY = "https://github.com/modular/llm-inference-handbook"
PINNED_COMMIT = "317b9816ec3080031333ed9ee44dfce919763bf7"
RAW_ROOT = (
    "https://raw.githubusercontent.com/modular/llm-inference-handbook/"
    f"{PINNED_COMMIT}"
)
RENDERED_ROOT = "https://handbook.modular.com"

WRAPPER_TAGS = {"Features", "LinkList"}
OMITTED_COMPONENTS = {"DocCardList", "StackQuiz"}
INTERACTIVE_COMPONENTS = {
    "AutoregressiveDecodeStepper": "token-by-token decode visualizer",
    "BatchingSimulator": "batching simulator",
    "ChunkedPrefillVisualizer": "chunked prefill visualizer",
    "ContextWindowSimulator": "context-window simulator",
    "GPUMemoryCalculator": "GPU memory calculator",
    "GPUExecutionVisualizer": "GPU execution visualizer",
    "GPUTable": "GPU comparison table",
    "KVCacheCalculator": "KV-cache calculator",
    "LatencyMetrics": "latency metrics playground",
    "LatencyTimelineVisualizer": "latency timeline visualizer",
    "LLMLifecycleMap": "LLM lifecycle visualizer",
    "ModelExplorer": "model explorer",
    "QuantizationVisualizer": "quantization visualizer",
    "RequestLifecycle": "request lifecycle visualizer",
    "TopPvsTopK": "top-p and top-k visualizer",
}

DIAGRAM_RE = re.compile(r'^<Diagram name="([^"]+)" alt="([^"]+)"\s*/>$')
REQUIRE_IMAGE_RE = re.compile(
    r"^\s*<img src=\{require\('([^']+)'\)\.default\} alt=\"([^\"]+)\"\s*/>\s*$"
)
SELF_CLOSING_COMPONENT_RE = re.compile(r"^<([A-Z][A-Za-z0-9]*)\s*/>$")
MARKDOWN_LINK_RE = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")


def git_output(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args], text=True
    ).strip()


def output_path(source_relative: PurePosixPath) -> PurePosixPath:
    if source_relative.suffix == ".mdx":
        return source_relative.with_suffix(".md")
    return source_relative


def route_map(markdown_files: list[Path], docs_root: Path) -> dict[str, PurePosixPath]:
    routes: dict[str, PurePosixPath] = {}
    for source_file in markdown_files:
        relative = PurePosixPath(source_file.relative_to(docs_root).as_posix())
        target = output_path(relative)
        if relative.stem == "index":
            route = "/" + relative.parent.as_posix().strip(".")
        else:
            route = "/" + relative.with_suffix("").as_posix()
        route = route.rstrip("/") or "/"
        routes[route] = target
    return routes


def rendered_page(relative: PurePosixPath) -> str:
    if relative.stem == "index":
        route = relative.parent.as_posix().strip(".")
    else:
        route = relative.with_suffix("").as_posix()
    if not route:
        return f"{RENDERED_ROOT}/"
    return f"{RENDERED_ROOT}/{route}/"


def strip_site_components(text: str, relative: PurePosixPath) -> str:
    output: list[str] = []
    in_fence = False
    skipping_import = False
    skipping_mdx_block = False
    unwrapped_tag: str | None = None
    page_url = rendered_page(relative)

    for line in text.splitlines():
        stripped = line.strip()
        if skipping_mdx_block:
            if stripped == "```":
                skipping_mdx_block = False
            continue
        if stripped == "```mdx-code-block" and not in_fence:
            skipping_mdx_block = True
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            output.append(line)
            continue

        if not in_fence:
            if skipping_import:
                if stripped.endswith(";"):
                    skipping_import = False
                continue
            if stripped.startswith("import "):
                skipping_import = not stripped.endswith(";")
                continue
            opening_tag = next(
                (tag for tag in WRAPPER_TAGS if stripped == f"<{tag}>"), None
            )
            if opening_tag:
                unwrapped_tag = opening_tag
                continue
            if unwrapped_tag and stripped == f"</{unwrapped_tag}>":
                unwrapped_tag = None
                continue
            if unwrapped_tag and line.startswith("  "):
                line = line[2:]
                stripped = line.strip()

            diagram = DIAGRAM_RE.fullmatch(stripped)
            if diagram:
                name, alt = diagram.groups()
                output.append(
                    f"![{alt}]({RAW_ROOT}/static/img/diagrams/{name}.svg)"
                )
                continue

            required_image = REQUIRE_IMAGE_RE.fullmatch(line)
            if required_image:
                image_path, alt = required_image.groups()
                source_path = (relative.parent / image_path).as_posix()
                output.append(f"![{alt}]({RAW_ROOT}/docs/{source_path})")
                continue

            component = SELF_CLOSING_COMPONENT_RE.fullmatch(stripped)
            if component:
                name = component.group(1)
                if name in OMITTED_COMPONENTS:
                    continue
                if name in INTERACTIVE_COMPONENTS:
                    label = INTERACTIVE_COMPONENTS[name]
                    output.append(
                        f"> The [{label}]({page_url}) is available on the "
                        "rendered handbook."
                    )
                    continue
                raise ValueError(f"Unhandled MDX component {name} in {relative}")

        output.append(line)

    transformed = "\n".join(output).rstrip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", transformed)


def split_target(target: str) -> tuple[str, str, str]:
    parsed = urlsplit(target)
    return parsed.path, parsed.query, parsed.fragment


def rebuild_target(path: str, query: str, fragment: str) -> str:
    return urlunsplit(("", "", path, query, fragment))


def rewrite_target(
    target: str,
    current_source: PurePosixPath,
    current_output: PurePosixPath,
    routes: dict[str, PurePosixPath],
    source_files: set[PurePosixPath],
    is_image: bool,
) -> str:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return target

    path, query, fragment = split_target(target)
    if not path:
        return target

    if path.startswith("/"):
        route = path.rstrip("/") or "/"
        destination = routes.get(route)
        if destination is None:
            return target
    else:
        resolved = PurePosixPath(
            os.path.normpath((current_source.parent / path).as_posix())
        )
        if is_image and resolved in source_files:
            raw = f"{RAW_ROOT}/docs/{resolved.as_posix()}"
            return rebuild_target(raw, query, fragment)

        route = "/" + resolved.as_posix().rstrip("/")
        if resolved.suffix in {".md", ".mdx"}:
            route = "/" + resolved.with_suffix("").as_posix()
        destination = routes.get(route)
        if destination is None:
            return target

    relative_target = os.path.relpath(
        destination.as_posix(), start=current_output.parent.as_posix() or "."
    )
    return rebuild_target(relative_target, query, fragment)


def rewrite_links(
    text: str,
    current_source: PurePosixPath,
    routes: dict[str, PurePosixPath],
    source_files: set[PurePosixPath],
) -> str:
    current_output = output_path(current_source)
    output: list[str] = []
    in_fence = False

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            output.append(line)
            continue
        if in_fence:
            output.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            label, target = match.groups()
            rewritten = rewrite_target(
                target,
                current_source,
                current_output,
                routes,
                source_files,
                is_image=label.startswith("!"),
            )
            return f"{label}({rewritten})"

        output.append(MARKDOWN_LINK_RE.sub(replace, line))

    return "\n".join(output).rstrip() + "\n"


def validate_references(root: Path) -> None:
    errors: list[str] = []
    markdown_files = sorted(root.rglob("*.md"))

    for markdown_file in markdown_files:
        relative = markdown_file.relative_to(root)
        in_fence = False
        for line_number, line in enumerate(
            markdown_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            if stripped.startswith("import ") or "require(" in stripped:
                errors.append(f"{relative}:{line_number}: site-only import remains")
            if DIAGRAM_RE.fullmatch(stripped) or SELF_CLOSING_COMPONENT_RE.fullmatch(
                stripped
            ):
                errors.append(f"{relative}:{line_number}: MDX component remains")

            for match in MARKDOWN_LINK_RE.finditer(line):
                target = match.group(2)
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path, _, _ = split_target(target)
                if not path:
                    continue
                if path.startswith("/"):
                    errors.append(
                        f"{relative}:{line_number}: root-relative link remains: "
                        f"{target}"
                    )
                    continue
                resolved = (markdown_file.parent / path).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    errors.append(
                        f"{relative}:{line_number}: link escapes references: {target}"
                    )
                    continue
                if not resolved.is_file():
                    errors.append(
                        f"{relative}:{line_number}: missing local target: {target}"
                    )

    if errors:
        details = "\n".join(errors)
        raise ValueError(f"Vendored reference validation failed:\n{details}")


def vendor(source: Path, destination: Path) -> None:
    source = source.resolve()
    docs_root = source / "docs"
    if not docs_root.is_dir():
        raise ValueError(f"Missing docs directory: {docs_root}")

    actual_commit = git_output(source, "rev-parse", "HEAD")
    if actual_commit != PINNED_COMMIT:
        raise ValueError(
            f"Expected checkout {PINNED_COMMIT}, found {actual_commit}. "
            "Update PINNED_COMMIT deliberately before importing a newer snapshot."
        )

    markdown_files = sorted(
        path
        for path in docs_root.rglob("*")
        if path.is_file() and path.suffix in {".md", ".mdx"}
    )
    routes = route_map(markdown_files, docs_root)
    source_files = {
        PurePosixPath(path.relative_to(docs_root).as_posix())
        for path in docs_root.rglob("*")
        if path.is_file()
    }

    with tempfile.TemporaryDirectory(prefix="modular-handbook-") as temporary:
        staging = Path(temporary) / "references"
        staging.mkdir()
        shutil.copy2(docs_root / "LICENSE", staging / "LICENSE")

        for source_file in markdown_files:
            relative = PurePosixPath(source_file.relative_to(docs_root).as_posix())
            target = staging / output_path(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            text = source_file.read_text(encoding="utf-8")
            text = strip_site_components(text, relative)
            text = rewrite_links(text, relative, routes, source_files)
            target.write_text(text, encoding="utf-8")

        validate_references(staging)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(staging, destination)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vendor the pinned Modular LLM Inference Handbook checkout."
    )
    parser.add_argument(
        "source",
        type=Path,
        help=f"Path to a checkout of {UPSTREAM_REPOSITORY}",
    )
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "references"
    vendor(args.source, destination)
    print(f"Vendored {PINNED_COMMIT} into {destination}")


if __name__ == "__main__":
    main()
