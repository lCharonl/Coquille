"""Data models and brands.yml loading/validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


@dataclass(frozen=True)
class Brand:
    slug: str
    name: str
    category: str
    legit_domains: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    tlds_risk: tuple[str, ...] = ()
    rank: int | None = None
    sources: tuple[str, ...] = ()

    @property
    def primary_domain(self) -> str:
        return self.legit_domains[0]

    @property
    def label(self) -> str:
        """Second-level label of the primary domain (e.g. 'paypal')."""
        return split_domain(self.primary_domain)[0]

    @property
    def primary_tld(self) -> str:
        return split_domain(self.primary_domain)[1]

    @property
    def legit_set(self) -> frozenset[str]:
        return frozenset(d.lower() for d in self.legit_domains)


@dataclass(frozen=True)
class Variant:
    value: str
    technique: str
    score: float


def split_domain(domain: str) -> tuple[str, str]:
    """Split 'paypal.co.uk' -> ('paypal', 'co.uk'); naive: first label vs rest."""
    label, _, tld = domain.lower().partition(".")
    return label, tld


def _tuple(value) -> tuple[str, ...]:
    return tuple(str(v) for v in (value or ()))


def load_brands(path: str | Path) -> list[Brand]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    brands = []
    for entry in raw.get("brands", []):
        brands.append(
            Brand(
                slug=entry["slug"],
                name=entry["name"],
                category=entry.get("category", "other"),
                legit_domains=_tuple(entry.get("legit_domains")),
                aliases=_tuple(entry.get("aliases")),
                keywords=_tuple(entry.get("keywords")),
                tlds_risk=_tuple(entry.get("tlds_risk")),
                rank=entry.get("rank"),
                sources=_tuple(entry.get("sources")),
            )
        )
    return brands


def validate_brands(brands: list[Brand], *, expected: int | None = None) -> list[str]:
    """Return a list of human-readable problems (empty list == valid)."""
    errors: list[str] = []
    seen_slugs: set[str] = set()
    seen_domains: dict[str, str] = {}
    if expected is not None and len(brands) != expected:
        errors.append(f"expected {expected} brands, found {len(brands)}")
    for b in brands:
        where = f"[{b.slug or '?'}]"
        if not SLUG_RE.match(b.slug):
            errors.append(f"{where} invalid slug")
        if b.slug in seen_slugs:
            errors.append(f"{where} duplicate slug")
        seen_slugs.add(b.slug)
        if not b.name.strip():
            errors.append(f"{where} empty name")
        if not b.legit_domains:
            errors.append(f"{where} needs at least one legit_domain")
        for d in b.legit_domains:
            if not DOMAIN_RE.match(d):
                errors.append(f"{where} invalid domain {d!r}")
            elif d in seen_domains and seen_domains[d] != b.slug:
                errors.append(f"{where} domain {d} already belongs to {seen_domains[d]}")
            seen_domains.setdefault(d, b.slug)
        if not b.sources:
            errors.append(f"{where} needs at least one source")
    return errors
