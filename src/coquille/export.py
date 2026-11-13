"""Writers for per-brand files and aggregated artefacts."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import Brand, Variant

DOMAIN_FIELDS = ["domain", "technique", "score", "registered", "first_seen", "sources"]


def write_brand(out: Path, brand: Brand, domains: list[Variant], names: list[Variant]) -> None:
    (out / "domains").mkdir(parents=True, exist_ok=True)
    (out / "names").mkdir(parents=True, exist_ok=True)

    with (out / "domains" / f"{brand.slug}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(DOMAIN_FIELDS)
        for v in domains:
            # enrichment columns stay empty until `coquille enrich` fills them
            w.writerow([v.value, v.technique, f"{v.score:.2f}", "", "", ""])

    with (out / "names" / f"{brand.slug}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["name", "technique", "score"])
        for v in names:
            w.writerow([v.value, v.technique, f"{v.score:.2f}"])


def write_index(out: Path, stats: dict[str, dict[str, int]]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "brands": len(stats),
        "total_domains": sum(s["domains"] for s in stats.values()),
        "total_names": sum(s["names"] for s in stats.values()),
        "per_brand": stats,
    }
    (out / "index.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_domains(out: Path) -> list[str]:
    """All generated domains, deduplicated and sorted (reads data/domains/*.csv)."""
    seen: set[str] = set()
    for path in sorted((out / "domains").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                seen.add(row["domain"])
    return sorted(seen)


def write_aggregates(out: Path, dist: Path) -> dict[str, int]:
    """Aggregated blocklists for GitHub Releases (not committed)."""
    dist.mkdir(parents=True, exist_ok=True)
    domains = read_domains(out)
    (dist / "all-domains.txt").write_text("\n".join(domains) + "\n", encoding="utf-8")
    (dist / "hosts").write_text(
        "".join(f"0.0.0.0 {d}\n" for d in domains), encoding="utf-8"
    )
    # RPZ: NXDOMAIN for the name and every subdomain
    serial = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    lines = [
        "$TTL 300",
        f"@ IN SOA localhost. root.localhost. ({serial} 3600 600 86400 300)",
        "  IN NS localhost.",
    ]
    for d in domains:
        lines.append(f"{d} CNAME .")
        lines.append(f"*.{d} CNAME .")
    (dist / "coquille.rpz").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"domains": len(domains)}
