"""Pure string-mutation techniques. Each yields (mutated_string, technique_name)."""

from __future__ import annotations

from collections.abc import Iterator

from .data import (
    ASCII_HOMOGLYPHS,
    KEYBOARD_NEIGHBOURS,
    UNICODE_HOMOGLYPHS,
    VOWELS,
)

Mutation = tuple[str, str]


def omission(s: str) -> Iterator[Mutation]:
    for i in range(len(s)):
        yield s[:i] + s[i + 1 :], "omission"


def repetition(s: str) -> Iterator[Mutation]:
    for i, ch in enumerate(s):
        yield s[:i] + ch + s[i:], "repetition"


def transposition(s: str) -> Iterator[Mutation]:
    for i in range(len(s) - 1):
        if s[i] != s[i + 1]:
            yield s[:i] + s[i + 1] + s[i] + s[i + 2 :], "transposition"


def replacement(s: str) -> Iterator[Mutation]:
    for i, ch in enumerate(s):
        for n in sorted(KEYBOARD_NEIGHBOURS.get(ch.lower(), ())):
            yield s[:i] + n + s[i + 1 :], "replacement"


def insertion(s: str) -> Iterator[Mutation]:
    for i, ch in enumerate(s):
        for n in sorted(KEYBOARD_NEIGHBOURS.get(ch.lower(), ())):
            yield s[:i] + n + s[i:], "insertion"
            yield s[: i + 1] + n + s[i + 1 :], "insertion"


def vowel_swap(s: str) -> Iterator[Mutation]:
    for i, ch in enumerate(s):
        if ch.lower() in VOWELS:
            for v in VOWELS:
                if v != ch.lower():
                    yield s[:i] + v + s[i + 1 :], "vowel_swap"


def hyphenation(s: str) -> Iterator[Mutation]:
    for i in range(1, len(s)):
        yield s[:i] + "-" + s[i:], "hyphenation"


def bitsquatting(s: str) -> Iterator[Mutation]:
    """Single-bit flips that still give a DNS-legal character."""
    for i, ch in enumerate(s):
        for bit in range(8):
            flipped = chr(ord(ch) ^ (1 << bit))
            if flipped.isascii() and (flipped.isalnum() or flipped == "-") and flipped != ch:
                yield s[:i] + flipped.lower() + s[i + 1 :], "bitsquatting"


def homoglyph_ascii(s: str) -> Iterator[Mutation]:
    for i, ch in enumerate(s):
        for rep in ASCII_HOMOGLYPHS.get(ch.lower(), ()):
            yield s[:i] + rep + s[i + 1 :], "homoglyph_ascii"


def homoglyph_unicode(s: str) -> Iterator[Mutation]:
    """One-character IDN homograph substitutions (caller punycode-encodes)."""
    for i, ch in enumerate(s):
        for rep in UNICODE_HOMOGLYPHS.get(ch.lower(), ()):
            yield s[:i] + rep + s[i + 1 :], "homoglyph_unicode"


def to_ace(label: str) -> str | None:
    """Unicode label -> punycode ('xn--...'), or None if not encodable."""
    if label.isascii():
        return label
    try:
        return label.encode("idna").decode("ascii")
    except UnicodeError:
        return None


def is_valid_label(label: str) -> bool:
    return (
        0 < len(label) <= 63
        and not label.startswith("-")
        and not label.endswith("-")
        and (label[2:4] != "--" or label.startswith("xn--"))  # only real punycode may use '--'
        and all(c.isascii() and (c.isalnum() or c == "-") for c in label)
    )
