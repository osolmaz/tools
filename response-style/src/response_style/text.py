from __future__ import annotations

import re

_TRIGGER = re.compile(r"(?<!\w)(amk|plain)(?!\w)", re.IGNORECASE)
_WORD = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_REVISION_SIGNALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("awkward", re.compile(r"(?<!\w)awkward(?!\w)", re.IGNORECASE)),
    ("brief", re.compile(r"(?<!\w)brief(?:er)?(?!\w)", re.IGNORECASE)),
    ("clearer", re.compile(r"(?<!\w)clearer(?!\w)", re.IGNORECASE)),
    ("concise", re.compile(r"(?<!\w)concise(?:ly)?(?!\w)", re.IGNORECASE)),
    ("direct", re.compile(r"(?<!\w)more\s+direct(?!\w)", re.IGNORECASE)),
    ("rephrase", re.compile(r"(?<!\w)rephras(?:e|ed|ing)(?!\w)", re.IGNORECASE)),
    ("rewrite", re.compile(r"(?<!\w)rewrit(?:e|ten|ing)(?!\w)", re.IGNORECASE)),
    ("shorter", re.compile(r"(?<!\w)shorter(?!\w)", re.IGNORECASE)),
    ("simpler", re.compile(r"(?<!\w)simpler(?!\w)", re.IGNORECASE)),
    ("summarize", re.compile(r"(?<!\w)summari[sz](?:e|ed|ing)(?!\w)", re.IGNORECASE)),
    ("tldr", re.compile(r"(?<!\w)tl\s*;?\s*dr(?!\w)", re.IGNORECASE)),
    ("too_long", re.compile(r"(?<!\w)too\s+long(?!\w)", re.IGNORECASE)),
    ("verbose", re.compile(r"(?<!\w)verbose(?!\w)", re.IGNORECASE)),
    ("weirdly_phrased", re.compile(r"(?<!\w)weirdly\s+phrased(?!\w)", re.IGNORECASE)),
    ("wordy", re.compile(r"(?<!\w)wordy(?!\w)", re.IGNORECASE)),
)


def clean_text(parts: list[str]) -> str | None:
    text = "\n\n".join(part.strip() for part in parts if part.strip()).strip()
    return text or None


def trigger_terms(text: str) -> tuple[str, ...]:
    found = {match.group(1).lower() for match in _TRIGGER.finditer(text)}
    return tuple(term for term in ("amk", "plain") if term in found)


def revision_signals(text: str) -> tuple[str, ...]:
    signals = [name for name, pattern in _REVISION_SIGNALS if pattern.search(text)]
    for term in trigger_terms(text):
        if term not in signals:
            signals.append(term)
    return tuple(sorted(signals))


def word_count(text: str) -> int:
    return len(_WORD.findall(text))
