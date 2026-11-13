"""coquille CLI: validate | generate | build."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import export
from .generators import generate_domains, generate_names
from .models import load_brands, validate_brands

DEFAULT_BRANDS = Path("brands/brands.yml")
DEFAULT_DATA = Path("data")
DEFAULT_DIST = Path("dist")


def _select(brands, slug: str | None):
    if slug is None:
        return brands
    picked = [b for b in brands if b.slug == slug]
    if not picked:
        sys.exit(f"unknown brand slug: {slug}")
    return picked


def cmd_validate(args) -> int:
    brands = load_brands(args.brands)
    errors = validate_brands(brands, expected=args.expect)
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    print(f"{len(brands)} brands, {len(errors)} problem(s)")
    return 1 if errors else 0


def cmd_generate(args) -> int:
    brands = load_brands(args.brands)
    errors = validate_brands(brands)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return 1
    stats: dict[str, dict[str, int]] = {}
    for b in _select(brands, args.brand):
        domains = generate_domains(b, cap=args.cap)
        names = generate_names(b)
        export.write_brand(args.data, b, domains, names)
        stats[b.slug] = {"domains": len(domains), "names": len(names)}
        print(f"{b.slug}: {len(domains)} domains, {len(names)} names")
    if args.brand is None:  # index only meaningful for a full run
        export.write_index(args.data, stats)
    return 0


def cmd_build(args) -> int:
    counts = export.write_aggregates(args.data, args.dist)
    print(f"wrote {counts['domains']} domains to {args.dist}/ (all-domains.txt, hosts, coquille.rpz)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="coquille", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check brands.yml")
    v.add_argument("--brands", type=Path, default=DEFAULT_BRANDS)
    v.add_argument("--expect", type=int, default=None, help="expected number of brands")
    v.set_defaults(func=cmd_validate)

    g = sub.add_parser("generate", help="generate variants into data/")
    g.add_argument("--brands", type=Path, default=DEFAULT_BRANDS)
    g.add_argument("--data", type=Path, default=DEFAULT_DATA)
    g.add_argument("--brand", help="only this brand slug")
    g.add_argument("--cap", type=int, default=1000, help="max domains per brand")
    g.set_defaults(func=cmd_generate)

    b = sub.add_parser("build", help="aggregate blocklists (hosts, RPZ, txt) into dist/")
    b.add_argument("--data", type=Path, default=DEFAULT_DATA)
    b.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    b.set_defaults(func=cmd_build)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
