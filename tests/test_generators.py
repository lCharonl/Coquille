from coquille.generators import generate_domains, generate_names
from coquille.generators import techniques as t
from coquille.models import Brand, validate_brands


def paypal() -> Brand:
    return Brand(
        slug="paypal", name="PayPal", category="payments",
        legit_domains=("paypal.com", "paypal.me"), keywords=("resolution",),
        sources=("test",),
    )


def values(variants):
    return {v.value for v in variants}


def test_expected_domain_variants_present():
    d = values(generate_domains(paypal(), cap=100000))
    assert "paypa1.com" in d  # homoglyph_ascii
    assert "paypall.com" in d  # repetition
    assert "paypla.com" in d  # transposition
    assert "paypal.xyz" in d  # tld_swap
    assert "paypal-secure.com" in d  # combosquat
    assert "paypal-resolution.com" in d  # brand keyword
    assert any(x.startswith("xn--") for x in d)  # punycode homograph


def test_legit_domains_and_originals_never_listed():
    d = values(generate_domains(paypal(), cap=100000))
    assert "paypal.com" not in d and "paypal.me" not in d


def test_cap_and_determinism():
    a = generate_domains(paypal(), cap=500)
    b = generate_domains(paypal(), cap=500)
    assert len(a) == 500 and a == b
    scores = [v.score for v in a]
    assert scores == sorted(scores, reverse=True)


def test_all_domains_are_ascii_valid():
    for v in generate_domains(paypal(), cap=100000):
        label, _, tld = v.value.partition(".")
        assert v.value.isascii() and t.is_valid_label(label) and tld


def test_names():
    n = values(generate_names(paypal()))
    assert "PayPal Support" in n
    assert "PayPal" not in n
    assert "PayPla" in n  # transposition
    assert "Pay Pal" in n  # spacing


def test_idna_roundtrip():
    assert t.to_ace("pаypal") == "xn--pypal-4ve"


def test_validate_catches_problems():
    bad = Brand(slug="Bad Slug", name="", category="x", legit_domains=("not a domain",))
    errs = validate_brands([bad, bad])
    joined = " ".join(errs)
    assert "invalid slug" in joined and "empty name" in joined
    assert "invalid domain" in joined and "duplicate slug" in joined and "source" in joined


def test_cap_keeps_every_technique_represented():
    big = Brand(
        slug="microsoft", name="Microsoft", category="tech",
        legit_domains=("microsoft.com",), aliases=("Office 365", "Outlook"), sources=("test",),
    )
    techs = {v.technique for v in generate_domains(big, cap=300)}
    assert {"omission", "transposition", "tld_swap", "combosquat", "homoglyph_ascii"} <= techs
