"""Static tables used by the generators."""

# Keyboard neighbourhoods (QWERTY + AZERTY) - typos land on adjacent keys.
_ROWS = {
    "qwerty": ["1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"],
    "azerty": ["1234567890", "azertyuiop", "qsdfghjklm", "wxcvbn"],
}


def _neighbours() -> dict[str, frozenset[str]]:
    out: dict[str, set[str]] = {}
    for rows in _ROWS.values():
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                adj = out.setdefault(ch, set())
                if c > 0:
                    adj.add(row[c - 1])
                if c < len(row) - 1:
                    adj.add(row[c + 1])
                for dr in (-1, 1):
                    rr = r + dr
                    if 0 <= rr < len(rows):
                        for dc in (-1, 0, 1):
                            cc = c + dc
                            if 0 <= cc < len(rows[rr]):
                                adj.add(rows[rr][cc])
    return {k: frozenset(v - {k}) for k, v in out.items()}


KEYBOARD_NEIGHBOURS = _neighbours()

# ASCII look-alikes (single char -> replacements, multi char sequences).
ASCII_HOMOGLYPHS: dict[str, tuple[str, ...]] = {
    "a": ("4", "@"),
    "b": ("d", "6"),
    "c": ("e",),
    "d": ("b", "cl"),
    "e": ("c", "3"),
    "g": ("q", "9"),
    "i": ("1", "l"),
    "l": ("1", "i"),
    "m": ("rn", "nn"),
    "n": ("m", "r"),
    "o": ("0",),
    "q": ("g",),
    "s": ("5", "z"),
    "t": ("7",),
    "u": ("v",),
    "v": ("u",),
    "w": ("vv",),
    "z": ("s", "2"),
}

# Unicode confusables (mostly Cyrillic/Greek) - used for IDN homograph variants.
UNICODE_HOMOGLYPHS: dict[str, tuple[str, ...]] = {
    "a": ("а", "à", "á", "ä"),  # cyrillic a, a-grave, a-acute, a-diaeresis
    "c": ("с", "ç"),  # cyrillic es, c-cedilla
    "e": ("е", "è", "é", "ë"),
    "i": ("і", "ì", "í", "ï"),
    "j": ("ј",),
    "l": ("ӏ",),
    "o": ("о", "ο", "ò", "ó", "ö"),
    "p": ("р",),
    "s": ("ѕ",),
    "u": ("ù", "ú", "ü"),
    "x": ("х",),
    "y": ("у", "ý"),
}

VOWELS = "aeiou"

# TLDs frequently seen in abusive registrations (cheap / low-friction).
RISK_TLDS = (
    "xyz", "top", "icu", "shop", "click", "support", "online", "site", "live", "vip",
    "club", "info", "buzz", "work", "store", "tech", "app", "link", "cc", "ru",
    "cn", "tk", "ml", "ga", "cf", "gq", "pw", "ws", "biz", "net", "org", "co",
)

# Generic phishing combosquat words (EN + FR).
COMBO_KEYWORDS = (
    "login", "signin", "secure", "security", "support", "help", "account", "verify",
    "verification", "update", "service", "online", "official", "billing", "payment",
    "wallet", "mail", "web", "app", "portal", "id", "auth", "alert", "confirm",
    "connexion", "compte", "assistance", "securite", "client", "espace", "mon",
)

# Suffixes used for display-name / handle spoofing of the brand *name*.
DISPLAY_SUFFIXES = (
    "Support", "Security", "Service", "Customer Service", "Help", "Team", "Official",
    "Billing", "Notification", "Alert", "Service Client", "Assistance",
)
