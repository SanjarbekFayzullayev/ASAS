"""
analyzer.py — matnni tahlil qilib XAVF BAHOSI va QARORni chiqaradi.

Quvur:  matn -> normalize (de-obfuskatsiya) -> lug'at bilan solishtirish ->
        og'irliklar yig'indisi -> xavf (0..1) + toifa + qaror.

Qaror:
  >= 0.70  -> BLOK      (yuqori xavf)
  >= 0.40  -> SHUBHALI  (tekshirilsin + dalil)
  >= 0.20  -> KUZATUV   (zaif signal)
  <  0.20  -> TOZA
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .normalizer import normalize, collapse
from .lexicon import LEXICON, LexEntry
from .links import extract_links


@dataclass
class Verdict:
    text: str
    risk: float            # 0..1
    category: str          # narkotik | qurol | tijorat | ... | toza
    decision: str          # BLOK | SHUBHALI | KUZATUV | TOZA
    matches: list          # mos kelgan LexEntry'lar
    links: list            # topilgan havolalar [{'type','value'}]
    is_shop_ad: bool = False   # narko-signal + havola = narkodo'kon reklamasi


def _hit(e: LexEntry, canon: str, coll: str, raw: str) -> bool:
    if e.is_emoji:
        return e.term in raw
    tc = e.canon
    if not tc:
        return False
    # Qisqa so'zlar (<=3 harf): faqat so'z chegarasi bilan (noto'g'ri mosликни kamaytirish).
    if len(tc) <= 3:
        return re.search(r"(?<![a-z0-9])" + re.escape(tc) + r"(?![a-z0-9])", canon) is not None
    # Oddiy: kanonik matnda bo'lsa
    if tc in canon:
        return True
    # Ajratib yozilgan: "k l a d" -> collapsed "klad"
    if len(e.canon_collapsed) >= 4 and e.canon_collapsed in coll:
        return True
    return False


def analyze(text: str) -> Verdict:
    canon = normalize(text)
    coll = collapse(canon)

    matched = [e for e in LEXICON if _hit(e, canon, coll, text or "")]
    links = extract_links(text or "")

    risk = sum(e.weight for e in matched)

    # Narko/qurol signali bo'lsa va matnda havola bo'lsa -> narkodo'kon reklamasi.
    has_drug_signal = any(e.category in ("narkotik", "qurol") for e in matched) \
        or any(e.is_emoji for e in matched)
    is_shop_ad = bool(has_drug_signal and links)
    if is_shop_ad:
        risk += 0.30   # havola jiddiy ogohlantirish belgisi

    risk = min(1.0, risk)

    cat_w: dict[str, float] = {}
    for e in matched:
        cat_w[e.category] = cat_w.get(e.category, 0.0) + e.weight
    # Toifani eng "og'ir" guruh bo'yicha (tijorat/yollash/kanal yordamchi hisoblanadi).
    primary = {k: v for k, v in cat_w.items() if k in ("narkotik", "qurol")}
    if primary:
        category = max(primary, key=primary.get)
    elif cat_w:
        category = max(cat_w, key=cat_w.get)
    else:
        category = "toza"

    if risk >= 0.70:
        decision = "BLOK"
    elif risk >= 0.40:
        decision = "SHUBHALI"
    elif risk >= 0.20:
        decision = "KUZATUV"
    else:
        decision = "TOZA"
        if not matched:
            category = "toza"

    return Verdict(text=text, risk=round(risk, 2), category=category,
                   decision=decision, matches=matched, links=links,
                   is_shop_ad=is_shop_ad)
