"""
analytics.py — 2-MODUL: narkotik jinoyatlarini TAHLIL va BASHORAT.

Agentlik statistikasi (hudud × oy × jinoyat soni) asosida:
  hududiy tahlil, vaqt dinamikasi, mavsumiy xavf xaritasi, kelajak prognozi,
  profilaktika tavsiyalari.

MA'LUMOT MANBASI:
  - Agar `data/crime_data.json` mavjud bo'lsa (agentlik CSV yuklagan) — REAL ma'lumot.
  - Aks holda — NAMUNA (sintetik) ma'lumot (14 viloyat × 24 oy).
Bashorat: oxirgi davr o'rtachasi × mavsumiy koeffitsient × trend (izohli, qora quti emas).
"""
from __future__ import annotations

import csv
import io
import json
import os
import random
from collections import defaultdict

REGIONS = [
    "Toshkent sh.", "Toshkent vil.", "Samarqand", "Farg'ona", "Andijon",
    "Namangan", "Buxoro", "Xorazm", "Qashqadaryo", "Surxondaryo",
    "Jizzax", "Sirdaryo", "Navoiy", "Qoraqalpog'iston",
]
_BASE = {
    "Toshkent sh.": 42, "Toshkent vil.": 30, "Samarqand": 28, "Farg'ona": 31,
    "Andijon": 26, "Namangan": 22, "Buxoro": 18, "Xorazm": 14, "Qashqadaryo": 21,
    "Surxondaryo": 17, "Jizzax": 12, "Sirdaryo": 8, "Navoiy": 10, "Qoraqalpog'iston": 13,
}
SEASONS = ["Bahor", "Yoz", "Kuz", "Qish"]
_SEASON_OF = {1: "Qish", 2: "Qish", 3: "Bahor", 4: "Bahor", 5: "Bahor",
              6: "Yoz", 7: "Yoz", 8: "Yoz", 9: "Kuz", 10: "Kuz", 11: "Kuz", 12: "Qish"}
_SEASON_FACTOR = {"Bahor": 1.08, "Yoz": 1.28, "Kuz": 1.0, "Qish": 0.82}
_AVG_FACTOR = sum(_SEASON_FACTOR.values()) / 4

DATA_FILE = "data/crime_data.json"


def _generate(months: int = 24, start_year: int = 2024):
    rnd = random.Random(42)
    data = {}
    for r in REGIONS:
        base = _BASE[r]
        series = []
        for i in range(months):
            month = (i % 12) + 1
            year = start_year + i // 12
            trend = 1 + 0.012 * i
            noise = rnd.uniform(0.85, 1.15)
            count = max(0, round(base * trend * _SEASON_FACTOR[_SEASON_OF[month]] * noise))
            series.append({"year": year, "month": month,
                           "season": _SEASON_OF[month], "count": count})
        data[r] = series
    return data


def load_data():
    """(data, is_real) qaytaradi."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                d = json.load(f)
            if d:
                return d, True
        except Exception:
            pass
    return _generate(), False


def ingest_csv(text: str) -> int:
    """CSV (ustunlar: region/hudud, year/yil, month/oy, count/soni) ni o'qib saqlaydi.
    Yozuvlar sonini qaytaradi (0 = xato)."""
    reader = csv.DictReader(io.StringIO(text))
    data = defaultdict(list)
    n = 0
    for row in reader:
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        region = row.get("region") or row.get("hudud") or row.get("viloyat")
        if not region:
            continue
        try:
            year = int(float(row.get("year") or row.get("yil") or 2025))
            month = int(float(row.get("month") or row.get("oy") or 1))
            count = int(float(row.get("count") or row.get("soni") or row.get("jinoyat") or 0))
        except ValueError:
            continue
        month = min(12, max(1, month))
        data[region].append({"year": year, "month": month,
                              "season": _SEASON_OF[month], "count": max(0, count)})
        n += 1
    if not data:
        return 0
    for r in data:
        data[r].sort(key=lambda x: (x["year"], x["month"]))
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dict(data), f, ensure_ascii=False)
    return n


def reset_data() -> None:
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)


def _level(ratio: float) -> str:
    return "Yuqori" if ratio <= 0.30 else ("O'rta" if ratio <= 0.65 else "Past")


def build_report() -> dict:
    data, is_real = load_data()
    regions = list(data.keys())

    region_totals = sorted(
        [{"region": r, "total": sum(x["count"] for x in s)} for r, s in data.items()],
        key=lambda d: d["total"], reverse=True)

    # Oylik dinamika — (yil,oy) bo'yicha jamlash
    mt = defaultdict(int)
    for s in data.values():
        for x in s:
            mt[(x["year"], x["month"])] += x["count"]
    keys = sorted(mt.keys())
    labels = [f"{y}-{m:02d}" for (y, m) in keys]
    monthly_counts = [mt[k] for k in keys]

    # Mavsumiy o'rtacha (hudud × mavsum)
    heat = {}
    for r, s in data.items():
        by = {sea: [] for sea in SEASONS}
        for x in s:
            by[x["season"]].append(x["count"])
        heat[r] = {sea: round(sum(v) / len(v), 1) if v else 0 for sea, v in by.items()}

    # Trend va o'sayotgan hududlar
    trend, rising = {}, []
    for r, s in data.items():
        ss = sorted(s, key=lambda x: (x["year"], x["month"]))
        if len(ss) >= 12:
            last = sum(x["count"] for x in ss[-6:]) / 6
            prev = sum(x["count"] for x in ss[-12:-6]) / 6
        elif len(ss) >= 2:
            h = len(ss) // 2
            last = sum(x["count"] for x in ss[h:]) / max(1, len(ss) - h)
            prev = sum(x["count"] for x in ss[:h]) / max(1, h)
        else:
            last = prev = (ss[0]["count"] if ss else 0)
        pct = round((last - prev) / prev * 100, 1) if prev else 0.0
        trend[r] = pct
        if pct >= 5:
            rising.append({"region": r, "pct": pct})
    rising.sort(key=lambda d: d["pct"], reverse=True)

    last_month = keys[-1][1] if keys else 12
    next_season = SEASONS[(SEASONS.index(_SEASON_OF[last_month]) + 1) % 4]

    forecast = []
    for r, s in data.items():
        ss = sorted(s, key=lambda x: (x["year"], x["month"]))
        recent = ss[-6:] if len(ss) >= 6 else ss
        recent_avg = sum(x["count"] for x in recent) / max(1, len(recent))
        tmult = max(0.8, min(1.3, 1 + trend[r] / 100))
        expected = recent_avg * (_SEASON_FACTOR[next_season] / _AVG_FACTOR) * tmult
        forecast.append({"region": r, "expected": round(expected, 1)})
    forecast.sort(key=lambda d: d["expected"], reverse=True)
    mx = forecast[0]["expected"] if forecast else 1
    for i, f in enumerate(forecast):
        f["risk"] = round(f["expected"] / mx * 100) if mx else 0
        f["level"] = _level(i / len(forecast)) if forecast else "Past"

    season_totals = {sea: 0 for sea in SEASONS}
    for s in data.values():
        for x in s:
            season_totals[x["season"]] += x["count"]

    reco = {sea: sorted(regions, key=lambda r: heat[r][sea], reverse=True)[:3] for sea in SEASONS}

    return {
        "is_real": is_real,
        "grand_total": sum(monthly_counts),
        "region_totals": region_totals,
        "monthly": {"labels": labels, "counts": monthly_counts},
        "heat": heat, "seasons": SEASONS, "regions": regions,
        "trend": trend, "rising": rising,
        "next_season": next_season, "forecast": forecast,
        "top_region": region_totals[0]["region"] if region_totals else "—",
        "reco": reco, "season_totals": season_totals,
    }
