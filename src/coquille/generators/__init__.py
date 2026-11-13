"""Variant generation: domains and brand names."""

from __future__ import annotations

from ..models import Brand, Variant
from . import data, techniques as t

# Plausibility weight per technique: higher = more likely to be seen in the wild,
# so it survives the per-brand cap first.
WEIGHTS = {
    "homoglyph_unicode": 0.90,
    "homoglyph_ascii": 0.90,
    "combosquat": 0.85,
    "tld_swap": 0.80,
    "omission": 0.70,
    "transposition": 0.70,
    "repetition": 0.65,
    "hyphenation": 0.60,
    "replacement": 0.60,
    "insertion": 0.55,
    "vowel_swap": 0.50,
    "bitsquatting": 0.40,
    "display_name": 0.85,
    "leet": 0.60,
    "casing": 0.30,
    "spacing": 0.55,
}

DEFAULT_DOMAIN_CAP = 1000
DEFAULT_NAME_CAP = 300
# Priority keywords get a small bonus so they survive the cap.
_TOP_KEYWORDS = {"login", "secure", "support", "account", "verify", "update", "signin"}


def _label_mutations(label: str):
    for fn in (
        t.omission, t.repetition, t.transposition, t.replacement, t.insertion,
        t.vowel_swap, t.hyphenation, t.bitsquatting, t.homoglyph_ascii,
        t.homoglyph_unicode,
    ):
        yield from fn(label)


def _keep_best(best: dict[str, Variant], value: str, technique: str, score: float) -> None:
    cur = best.get(value)
    if cur is None or score > cur.score:
        best[value] = Variant(value, technique, score)


def _finalise(best: dict[str, Variant], cap: int) -> list[Variant]:
    """Pick up to `cap` variants, round-robin across techniques (best score first inside
    each), so one prolific technique (e.g. combosquatting) cannot crowd out the others.
    Output is sorted best-first and fully deterministic."""
    if len(best) <= cap:
        return sorted(best.values(), key=lambda v: (-v.score, v.value))
    by_tech: dict[str, list[Variant]] = {}
    for v in sorted(best.values(), key=lambda v: (-v.score, v.value)):
        by_tech.setdefault(v.technique, []).append(v)
    order = sorted(by_tech, key=lambda k: (-WEIGHTS[k], k))
    picked: list[Variant] = []
    depth = 0
    while len(picked) < cap:
        progressed = False
        for tech in order:
            if depth < len(by_tech[tech]) and len(picked) < cap:
                picked.append(by_tech[tech][depth])
                progressed = True
        if not progressed:
            break
        depth += 1
    return sorted(picked, key=lambda v: (-v.score, v.value))


def generate_domains(brand: Brand, cap: int = DEFAULT_DOMAIN_CAP) -> list[Variant]:
    """Typosquatted domains for a brand, best-first, capped, legit domains excluded."""
    best: dict[str, Variant] = {}
    legit = brand.legit_set
    tld = brand.primary_tld
    risk = tuple(brand.tlds_risk) or data.RISK_TLDS
    labels = {brand.label} | {a.lower().replace(" ", "") for a in brand.aliases}

    for base in sorted(labels):
        # 1. label mutations on the brand's own TLD
        for mutated, technique in _label_mutations(base):
            ace = t.to_ace(mutated)
            if ace and t.is_valid_label(ace):
                _keep_best(best, f"{ace}.{tld}", technique, WEIGHTS[technique])
        # 2. TLD swap (same label, risky TLD)
        for r in risk:
            _keep_best(best, f"{base}.{r}", "tld_swap", WEIGHTS["tld_swap"])
        # 3. combosquatting: label + keyword (3 patterns) on own TLD and top risk TLDs
        kws = tuple(brand.keywords) + data.COMBO_KEYWORDS
        for kw in kws:
            bonus = 0.05 if kw in _TOP_KEYWORDS or kw in brand.keywords else 0.0
            for combo in (f"{base}-{kw}", f"{kw}-{base}", f"{base}{kw}"):
                if not t.is_valid_label(combo):
                    continue
                for tl in (tld, *risk[:4]):
                    # own TLD is the most plausible; risky TLDs rank slightly lower
                    penalty = 0.0 if tl == tld else 0.03
                    _keep_best(best, f"{combo}.{tl}", "combosquat",
                               WEIGHTS["combosquat"] + bonus - penalty)

    for d in list(best):
        if d in legit:
            del best[d]
    return _finalise(best, cap)


def _leet(name: str):
    table = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
    for i, ch in enumerate(name):
        if ch.lower() in table:
            yield name[:i] + table[ch.lower()] + name[i + 1 :], "leet"


def generate_names(brand: Brand, cap: int = DEFAULT_NAME_CAP) -> list[Variant]:
    """Typosquatted *names* (handles, app names, e-mail display names)."""
    best: dict[str, Variant] = {}
    originals = {brand.name} | set(brand.aliases)

    for base in sorted(originals):
        low = base.lower()
        for fn in (t.omission, t.repetition, t.transposition, t.replacement,
                   t.homoglyph_ascii, t.homoglyph_unicode):
            for mutated, technique in fn(base):
                _keep_best(best, mutated, technique, WEIGHTS[technique])
        for mutated, technique in _leet(base):
            _keep_best(best, mutated, technique, WEIGHTS[technique])
        # casing / spacing
        _keep_best(best, base.upper(), "casing", WEIGHTS["casing"])
        _keep_best(best, base.lower(), "casing", WEIGHTS["casing"])
        for i in range(1, len(low)):
            for sep in (" ", "-", ".", "_"):
                _keep_best(best, base[:i] + sep + base[i:], "spacing", WEIGHTS["spacing"])
        # display-name spoofing
        for suf in data.DISPLAY_SUFFIXES:
            for v in (f"{base} {suf}", f"{base}-{suf.replace(' ', '')}",
                      f"{base}{suf.replace(' ', '')}", f"{base} ™", f"{base}®"):
                _keep_best(best, v, "display_name", WEIGHTS["display_name"])

    for o in originals:
        best.pop(o, None)
    return _finalise(best, cap)
