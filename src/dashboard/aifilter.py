"""
aifilter.py — AI FILTR: har bir shubhali hodisani baholaydi va
"agentga yuborishga arziydimi?" degan tavsiya beradi.

Maqsad: operatorni va agentlarni KAM, lekin ASOSLI signallar bilan bezovta qilish.
Yolg'on/zaif hodisalar past ball oladi va avtomatik yuborilmaydi.

Ball (0..1) omillari:
  - to'liq gavda ko'rindimi (son+to'piq) -> haqiqiy yer bilan muloqot, kuchli dalil
  - yuz aniqlandimi (FACEID uchun zarur)
  - qo'l haqiqatan yerga yaqinmi (shunchaki egilish emas)
  - skelet sifati (nechta nuqta ishonchli)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FilterResult:
    score: float        # 0..1
    recommend: bool     # agentga yuborish tavsiya etiladimi
    reason: str         # qisqa izoh


def score_event(full_body: bool, face_present: bool, hand_low: bool,
                kp_quality: float, motion_only: bool,
                threshold: float = 0.55) -> FilterResult:
    s = 0.20
    parts = []
    if full_body:
        s += 0.35; parts.append("to'liq gavda")
    if hand_low:
        s += 0.20; parts.append("qo'l yerda")
    if face_present:
        s += 0.20; parts.append("yuz aniqlandi")
    s += 0.15 * max(0.0, min(1.0, kp_quality))  # skelet sifati
    if motion_only:
        s -= 0.10; parts.append("faqat harakat (yaqin kadr)")

    s = max(0.0, min(1.0, s))
    recommend = s >= threshold
    reason = ", ".join(parts) if parts else "zaif signal"
    if recommend:
        reason = "Yuborish tavsiya etiladi — " + reason
    else:
        reason = "Ushlab turildi — " + reason
    return FilterResult(score=round(s, 2), recommend=recommend, reason=reason)
