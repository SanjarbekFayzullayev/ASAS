"""
links.py — reklama matnidan ONLAYN NARKODO'KON HAVOLALARINI ajratadi.

20-topshiriq: reklamalarda giyohvandlik vositasi reklamasi bilan birga
onlayn do'kon havolalari beriladi (t.me/..., @do'kon, sayt). Bu modul shu
havolalarni topadi — buzib yozilgan ko'rinishlarini ham:
   "t(dot)me/shop", "t . me / shop", "телеграм: @best24", "shop[.]site"
"""
from __future__ import annotations

import re

# "dot/nuqta/(.)" -> ".",  ko'rinmas belgilarni olib tashlash
_INVIS = re.compile(r"[​‌‍﻿⁠­]")
_DOT_WORDS = re.compile(r"\(\s*dot\s*\)|\[\s*dot\s*\]|\bdot\b|\bточка\b|\bnuqta\b|\(\s*\.\s*\)|\[\s*\.\s*\]", re.IGNORECASE)


def _deobf(text: str) -> str:
    t = _INVIS.sub("", text)
    t = _DOT_WORDS.sub(".", t)
    # nuqta va slash atrofidagi bo'shliqlarni yopamiz: "t . me / shop" -> "t.me/shop"
    t = re.sub(r"\s*\.\s*", ".", t)
    t = re.sub(r"\s*/\s*", "/", t)
    return t


_TME = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog|tg://)/?(?:joinchat/|resolve\?domain=)?[\w+/-]{2,}", re.IGNORECASE)
_URL = re.compile(r"(?:https?://|www\.)[^\s,)<>\"']{3,}", re.IGNORECASE)
_SHOP_DOMAIN = re.compile(r"\b[\w-]{2,}\.(?:shop|store|site|biz|to|cc|onion|xyz|top|ru|uz|com)\b", re.IGNORECASE)
_HANDLE = re.compile(r"(?<![\w@/.])@([a-zA-Z][\w]{3,31})")


def extract_links(text: str) -> list[dict]:
    """[{'type': 'telegram|url|domen|handle', 'value': '...'}] qaytaradi."""
    if not text:
        return []
    t = _deobf(text)
    found: list[dict] = []
    seen: set = set()

    def add(kind: str, val: str):
        v = val.strip().rstrip(".,);:")
        key = (kind, v.lower())
        if v and key not in seen:
            seen.add(key)
            found.append({"type": kind, "value": v})

    for m in _TME.finditer(t):
        add("telegram", m.group(0))
    for m in _URL.finditer(t):
        if "t.me" not in m.group(0).lower():
            add("url", m.group(0))
    for m in _SHOP_DOMAIN.finditer(t):
        low = m.group(0).lower()
        if not low.startswith(("t.me", "telegram.")):
            add("domen", m.group(0))
    for m in _HANDLE.finditer(t):
        add("handle", "@" + m.group(1))
    return found
