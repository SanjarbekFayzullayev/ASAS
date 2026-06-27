"""
assistant.py — 3-MODUL: tezkor qaror qabul qilishga yordam beruvchi AI.

Xodim vaziyatni matn bilan kiritadi -> tizim:
  - vaziyatni tahlil qiladi (narko/qurol signallari + holat turi),
  - xavf darajasini baholaydi,
  - bir nechta TAVSIYA ETILGAN harakatni beradi,
  - ogohlantirishlarni ko'rsatadi.

MUHIM: yakuniy qaror DOIM mas'ul xodimda. AI faqat tavsiya va tahlil beradi.
"""
from __future__ import annotations

from src.textmon.analyzer import analyze
from src.textmon.normalizer import normalize, collapse
from src.dashboard import db
from src.dashboard.analytics import build_report

# Holat turini aniqlash uchun kalit so'zlar (normalizatsiyadan keyin tekshiriladi).
_CAT_KEYS = {
    "qurol": ["qurol", "stvol", "pistolet", "avtomat", "granata", "patron", "oqotar",
              "portlovchi", "oruzhie", "stvol", "granata", "vzryv", "miltiq", "topponcha"],
    "zakladchik": ["zakladka", "zaklad", "klad", "tashlama", "komib", "komish", "komi",
                   "komdi", "komd", "komgan", "komg", "komadi", "komaman", "kommoq",
                   "kokdi", "yashir", "taynik", "prikop", "yerga kom", "yashirib"],
    "narkotik": ["narkotik", "giyohvand", "nasha", "geroin", "kokain", "mef", "amfetamin",
                 "narko", "gashish", "marixuana", "modda", "kukun", "oq kukun", "kristall",
                 "tabletka", "shpris", "doza"],
    "onlayn": ["kanal", "bot", "telegram", "onlayn", "sayt", "havola", "tme"],
    "kuryer": ["kuryer", "kurer", "vakansiya", "ishga", "zarplata", "rabota", "podrabotka", "ish elon"],
}
_PRIORITY = ["qurol", "zakladchik", "narkotik", "onlayn", "kuryer"]

_ACTIONS = {
    "qurol": [
        "Shaxsiy xavfsizlikni ta'minlang — qurolga tegmang, uchini nazorat qiling",
        "Portlovchi shubhasi bo'lsa masofani saqlang va pirotexnika xizmatini chaqiring",
        "Hududni o'rab oling, begonalarni uzoqlashtiring",
        "Holatni foto/videoga oling, guvohlarni belgilang, bayonnoma tuzing",
        "Maxsus bo'linma va rahbarni darhol xabardor qiling",
    ],
    "zakladchik": [
        "Tashlama joyini o'zgartirmasdan o'rab oling",
        "Shaxs bo'lsa — ushlab turing va hujjatini tekshiring",
        "Joyni va topilmani geolokatsiya bilan fotosuratga oling",
        "Ekspert-kriminalist va guvohlarni chaqiring",
        "Dalillarni qayd etib, rahbarga yetkazing",
    ],
    "narkotik": [
        "Hududni o'rab oling, begona shaxslarni uzoqlashtiring",
        "Moddaga qo'l tegizmang — qo'lqop ishlating, fotosuratga oling",
        "Ekspert-kriminalist va guvohlarni chaqiring",
        "Bayonnoma rasmiylashtiring, vaqt va joyni qayd eting",
        "Navbatchi qism va rahbarni xabardor qiling",
    ],
    "onlayn": [
        "Kanal/bot havolasi, username va postlarni skrinshot qiling",
        "Dalillarni vaqt belgisi bilan saqlang",
        "Telegramga shikoyat (abuse) yuboring",
        "Kiberjinoyat bo'linmasi va rahbarni xabardor qiling",
    ],
    "kuryer": [
        "Shaxsni aniqlang, hujjatlarini tekshiring",
        "Ish e'loni, telefon va yozishmalarni dalil sifatida saqlang",
        "Yoshni jinoiy guruh aldagani ehtimolini hisobga oling",
        "Kiberjinoyatlarga qarshi bo'linmani xabardor qiling",
        "Tushuntirish va bayonnoma oling",
    ],
    "umumiy": [
        "Vaziyatni baholang va xavfsizlikni ta'minlang",
        "Dalillarni qayd eting (foto/video/bayonnoma)",
        "Guvohlarni belgilang",
        "Navbatchi qism va rahbarni xabardor qiling",
    ],
}

_CAT_LABEL = {
    "qurol": "Qurol bilan bog'liq holat", "zakladchik": "Yashirin tashlama (zakladka)",
    "narkotik": "Narkotik modda holati", "onlayn": "Onlayn savdo/kanal",
    "kuryer": "Shubhali kuryer/yollash", "umumiy": "Umumiy holat",
}


def _detect_category(canon: str) -> str:
    coll = collapse(canon)
    for cat in _PRIORITY:
        for kw in _CAT_KEYS[cat]:
            k = normalize(kw)
            kc = collapse(k)
            # kanonik moslik yoki ajratuvchisiz (apostrof/bo'shliq) moslik
            if k in canon or (len(kc) >= 4 and kc in coll):
                return cat
    return "umumiy"


def _context_strings(rep, region, fc) -> list:
    """LOCAL ma'lumotlar (hududiy tahlil + baza + kanallar) asosida kontekst matnlari."""
    ctx = []
    if region and fc:
        ctx.append(f"{region} hududi — kelgusi mavsumda xavf darajasi: {fc['level']} ({fc['risk']}%).")
        tr = rep["trend"].get(region, 0)
        if abs(tr) >= 5:
            ctx.append(f"{region}da jinoyatlar oxirgi davrda {abs(int(tr))}% "
                       + ("ortgan" if tr > 0 else "kamaygan") + ".")
    if rep:
        ctx.append(f"Mamlakat bo'yicha eng yuqori xavfli hudud: {rep['top_region']}.")
    try:
        total = db.stats().get("total", 0)
        if total:
            ctx.append(f"Bazada jami {total} ta shubhali kamera hodisasi qayd etilgan.")
    except Exception:
        pass
    return ctx


def analyze_situation(text: str) -> dict:
    v = analyze(text)
    canon = normalize(text)
    category = _detect_category(canon)

    score = v.risk
    if category == "qurol":
        score = max(score, 0.78)
    elif category in ("zakladchik", "narkotik"):
        score = max(score, 0.55)
    elif category in ("onlayn", "kuryer"):
        score = max(score, 0.40)

    # LOCAL TAHLILNI HISOBGA OLISH — hududiy prognoz xavfni oshirishi mumkin
    region, region_fc, rep = None, None, None
    try:
        rep = build_report()
        region = next((r for r in rep["regions"] if normalize(r.split()[0]) in canon), None)
        if region:
            region_fc = next((f for f in rep["forecast"] if f["region"] == region), None)
    except Exception:
        pass

    if region_fc and region_fc["level"] == "Yuqori":
        score += 0.15   # yuqori xavfli hududda ehtiyotkorlik oshiriladi

    score = min(1.0, score)
    level = "Yuqori" if score >= 0.7 else ("O'rta" if score >= 0.4 else "Past")

    signals = sorted({e.term for e in v.matches})

    cautions = ["Yakuniy qaror mas'ul xodim tomonidan qabul qilinadi — AI faqat tavsiya beradi.",
                "Qonun va ichki tartib-qoidalarga rioya qiling."]
    if category == "qurol":
        cautions.insert(0, "DIQQAT: shaxsiy xavfsizlikni birinchi o'ringa qo'ying.")
    if region_fc and region_fc["level"] == "Yuqori":
        cautions.insert(0, f"{region} prognoz bo'yicha YUQORI xavfli hudud — kuchaytirilgan e'tibor talab etiladi.")

    return {
        "level": level, "score": round(score * 100),
        "category": category, "category_label": _CAT_LABEL[category],
        "signals": signals, "actions": _ACTIONS[category], "cautions": cautions,
        "context": _context_strings(rep, region, region_fc),
    }


# ============ 4-MODUL: yoshlar uchun ish e'lonini tekshirish ============
_RECRUIT_KW = ["kuryer", "kurer", "vakansiya", "zarplata", "rabota", "podrabotka",
               "ishga olamiz", "ish bor", "ish elon", "rabota kuryerom"]
_LURE_KW = ["yuqori maosh", "tez pul", "oson pul", "legkie dengi", "vysokaya zarplata",
            "bystryy zarabotok", "tezda boyish", "kunlik tolov", "anonim"]


def youth_check(text: str) -> dict:
    """Ish e'loni noqonuniy kuryerlik (narkotik tashish) tuzog'imi — tekshiradi."""
    v = analyze(text)
    canon = normalize(text)
    recruit = any(normalize(k) in canon for k in _RECRUIT_KW)
    lure = any(normalize(k) in canon for k in _LURE_KW)
    drug_signal = (v.decision in ("BLOK", "SHUBHALI")
                   or any(e.category in ("narkotik", "yollash") for e in v.matches))

    reasons = []
    if recruit:
        reasons.append("ish/kuryer taklifi bor")
    if lure:
        reasons.append("g'ayritabiiy yuqori/oson daromad va'dasi")
    if v.links:
        reasons.append("Telegram bot/havola orqali aloqa")
    if drug_signal:
        reasons.append("narkotik/yollash bilan bog'liq so'zlar")

    if (recruit and (drug_signal or lure or v.links)) or v.decision == "BLOK":
        level = "Xavfli"
        message = ("Bu e'lon NOQONUNIY KURYERLIK (narkotik tashish) tuzog'i bo'lishi mumkin! "
                   "Hech qanday holatda manzil/paket olib bormang, huquq idoralariga xabar bering.")
    elif recruit and (lure or v.decision != "TOZA"):
        level = "Shubhali"
        message = "Bu e'lon shubhali. Kompaniyani tekshiring, hech qachon noma'lum paket tashimang."
    else:
        level = "Toza"
        message = "Aniq xavf belgisi topilmadi. Baribir ehtiyot bo'ling va kompaniyani tekshiring."

    return {"level": level, "message": message,
            "reasons": reasons or ["aniq belgi yo'q"]}


# ============ Real CHAT (ishonchli dvigatel — toza o'zbekcha) ============
def chat_reply(message: str, history=None) -> dict:
    """Ishonchli dvigatel (TOZA o'zbekcha): vaziyatni aniqlab — xavf darajasi +
    aniq harakatlar + local ma'lumot beradi. Deterministik, tez, sifat barqaror.
    (LLM o'zbekchani buzgani uchun Ollama o'rniga shu rejim ishlatiladi.)"""
    m = message.strip().lower()
    if len(m) < 4 or m in ("salom", "assalom", "assalomu alaykum", "hi", "salam", "hello"):
        return {"reply": "Assalomu alaykum! Operativ vaziyatni yozing — men xavf darajasini "
                         "baholab, aniq harakat tavsiyalarini beraman.", "mode": "engine", "context": []}

    a = analyze_situation(message)
    lines = [f"Xavf darajasi: {a['level']} ({a['score']}%) — {a['category_label']}."]
    if a["signals"]:
        lines.append("Aniqlangan signallar: " + ", ".join(a["signals"]) + ".")
    lines += ["", "Tavsiya etilgan harakatlar:"]
    lines += [f"{i + 1}. {x}" for i, x in enumerate(a["actions"])]
    if a.get("context"):
        lines += ["", "Local ma'lumotlar asosida:"]
        lines += ["• " + c for c in a["context"]]
    lines += ["", "Eslatma: yakuniy qaror mas'ul xodimda — bu faqat tahliliy tavsiya."]
    return {"reply": "\n".join(lines), "mode": "engine", "context": a["context"]}