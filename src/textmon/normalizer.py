"""
normalizer.py — matnni DE-OBFUSKATSIYA qiladi (yashirish hiyalarini ochadi).

Sotuvchilar filtrlardan qochish uchun so'zlarni buzadi:
  - kirilcha/lotincha aralashtirish (homoglif):  "kлад", "оплата"
  - leetspeak / raqamlar:  "z@kl@dk@", "skoros7", "s0l"
  - ajratish:  "к л а д", "s.o.l", "м_е_ф"
  - ko'rinmas belgilar:  "за​клад"
  - takror harflar:  "соооль"

Bu modul matnni yagona "kanonik" ko'rinishga keltiradi, shunda lug'at bilan
solishtirish ishonchli bo'ladi.
"""
from __future__ import annotations

import re
import unicodedata

# Kirilcha -> lotincha (jargon ko'pincha rus tilida yoziladi).
_CYR2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "і": "i", "ї": "i", "є": "e", "ґ": "g",
}

# Leetspeak va belgilar -> harf.
_LEET = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b",
    "@": "a", "$": "s", "€": "e", "|": "i", "!": "i", "9": "g",
}

# Ko'rinmas / qo'shimcha boshqaruv belgilari.
_INVISIBLE = {"​", "‌", "‍", "﻿", "­", "⁠", "᠎"}


def normalize(text: str) -> str:
    """Matnni kanonik (lotin, leetsiz, ko'rinmas belgilarsiz) ko'rinishga keltiradi."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text).lower()
    # ko'rinmas va format belgilarini olib tashlaymiz
    t = "".join(ch for ch in t
                if ch not in _INVISIBLE and unicodedata.category(ch) != "Cf")
    # kirilcha -> lotincha
    t = "".join(_CYR2LAT.get(ch, ch) for ch in t)
    # leetspeak
    t = "".join(_LEET.get(ch, ch) for ch in t)
    # diakritik (urg'u) belgilarini olib tashlaymiz
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    # 3+ takror harfni bittaga (sоооль -> sol)
    t = re.sub(r"(.)\1{2,}", r"\1", t)
    return t


def collapse(text: str) -> str:
    """
    Harf/raqamdan boshqa HAMMA narsani olib tashlaydi.
    "к л а д" -> "klad",  "s.o.l" -> "sol",  "м_е_ф" -> "mef".
    (normalize qilingan matnga qo'llanadi.)
    """
    return re.sub(r"[^a-z0-9]+", "", text)
