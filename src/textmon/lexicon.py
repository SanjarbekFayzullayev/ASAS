"""
lexicon.py — narko/qurol JARGON, kod va tijorat-signal lug'ati (ANIQLASH uchun).

Har element: (so'z, toifa, og'irlik 0..1).
  - Aniq, bir ma'noli jargon -> yuqori og'irlik (0.6–0.8).
  - Ko'p ma'noli so'zlar (sol, plan, trava, muka, sneg) -> PAST og'irlik (0.2–0.35),
    chunki ular oddiy matnda ham uchraydi (yolg'on signalni kamaytirish).
  - Tijorat / yollash / aloqa signallari -> qo'shimcha og'irlik (yakka o'zi xavf emas).

Kirilcha va lotincha so'zlar normalizatsiyada bir xil "kanon"ga tushadi
(masalan "наркотик" -> "narkotik"), shuning uchun ko'pchilik so'z bir marta yoziladi.
Bu MUDOFAA (content-moderation) lug'ati — kontentni filtrlash uchun. Oson kengaytiriladi.
"""
from __future__ import annotations

from dataclasses import dataclass

from .normalizer import normalize, collapse

# (so'z, toifa, og'irlik)
_RAW = [
    # ====================== NARKOTIK ======================
    # --- Tashlama / zakladka tizimi (aniq jargon) ---
    ("закладка", "narkotik", 0.70), ("закладки", "narkotik", 0.70), ("заклад", "narkotik", 0.55),
    ("закладчик", "narkotik", 0.80), ("кладмен", "narkotik", 0.70), ("кладовщик", "narkotik", 0.65),
    ("прикоп", "narkotik", 0.65), ("тайник", "narkotik", 0.45), ("схрон", "narkotik", 0.50),
    ("клад готов", "narkotik", 0.65), ("без палева", "narkotik", 0.55), ("реал клад", "narkotik", 0.60),
    ("минёр", "narkotik", 0.50), ("фасовщик", "narkotik", 0.60), ("фасовка", "narkotik", 0.45),
    ("магнит", "narkotik", 0.30), ("прятки", "narkotik", 0.30), ("координаты", "narkotik", 0.30),

    # --- To'g'ridan-to'g'ri so'zlar ---
    ("наркотик", "narkotik", 0.70), ("наркотики", "narkotik", 0.70), ("наркота", "narkotik", 0.60),
    ("psixotrop", "narkotik", 0.60), ("психотроп", "narkotik", 0.60), ("дурь", "narkotik", 0.50),
    ("замес", "narkotik", 0.45), ("стафф", "narkotik", 0.45), ("вещество", "narkotik", 0.30),

    # --- Amfetamin / mefedron / stimulyatorlar ---
    ("мефедрон", "narkotik", 0.80), ("меф", "narkotik", 0.55), ("мяу-мяу", "narkotik", 0.70),
    ("амфетамин", "narkotik", 0.80), ("амф", "narkotik", 0.55), ("фен", "narkotik", 0.40),
    ("метамфетамин", "narkotik", 0.80), ("первитин", "narkotik", 0.80), ("винт", "narkotik", 0.50),
    ("спиды", "narkotik", 0.55), ("скорость", "narkotik", 0.45), ("альфа пвп", "narkotik", 0.70),
    ("соль", "narkotik", 0.35), ("соли", "narkotik", 0.35), ("кристалл", "narkotik", 0.45),
    ("кристаллы", "narkotik", 0.45), ("лёд", "narkotik", 0.35), ("айс", "narkotik", 0.45),

    # --- Opioidlar ---
    ("героин", "narkotik", 0.80), ("гера", "narkotik", 0.45), ("героинчик", "narkotik", 0.70),
    ("ширка", "narkotik", 0.60), ("ханка", "narkotik", 0.55), ("метадон", "narkotik", 0.75),
    ("морфин", "narkotik", 0.70), ("морфий", "narkotik", 0.70), ("опий", "narkotik", 0.65),
    ("опиум", "narkotik", 0.65), ("маковая", "narkotik", 0.50), ("трамадол", "narkotik", 0.55),

    # --- Kokain ---
    ("кокаин", "narkotik", 0.80), ("кокс", "narkotik", 0.45), ("кока", "narkotik", 0.40),
    ("мука", "narkotik", 0.25), ("снег", "narkotik", 0.25), ("дорожка", "narkotik", 0.35),

    # --- Kanabis / gashish ---
    ("гашиш", "narkotik", 0.70), ("гаш", "narkotik", 0.45), ("гашик", "narkotik", 0.50),
    ("шишки", "narkotik", 0.50), ("бошки", "narkotik", 0.50), ("бошка", "narkotik", 0.45),
    ("ганджубас", "narkotik", 0.70), ("ганджа", "narkotik", 0.60), ("ганжа", "narkotik", 0.60),
    ("конопля", "narkotik", 0.60), ("каннабис", "narkotik", 0.70), ("марихуана", "narkotik", 0.75),
    ("травка", "narkotik", 0.45), ("трава", "narkotik", 0.30), ("зелень", "narkotik", 0.25),
    ("косяк", "narkotik", 0.40), ("химка", "narkotik", 0.50), ("гидропоника", "narkotik", 0.60),
    ("план", "narkotik", 0.30), ("дудка", "narkotik", 0.30),

    # --- Ekstazi / psixodeliklar ---
    ("экстази", "narkotik", 0.70), ("мдма", "narkotik", 0.75), ("колёса", "narkotik", 0.35),
    ("таблы", "narkotik", 0.45), ("марка", "narkotik", 0.30), ("марки", "narkotik", 0.40),
    ("лсд", "narkotik", 0.70), ("кислота", "narkotik", 0.30), ("грибы", "narkotik", 0.40),
    ("мухоморы", "narkotik", 0.45), ("психоделик", "narkotik", 0.55),
    ("спайс", "narkotik", 0.70), ("спайсы", "narkotik", 0.70), ("реагент", "narkotik", 0.55),
    ("микс", "narkotik", 0.35), ("миксы", "narkotik", 0.40),

    # --- O'zbekcha ---
    ("nasha", "narkotik", 0.60), ("ko'knori", "narkotik", 0.60), ("chars", "narkotik", 0.40),
    ("giyohvand", "narkotik", 0.35), ("giyohvandlik", "narkotik", 0.55),
    ("giyohvand modda", "narkotik", 0.65), ("giyoh", "narkotik", 0.30), ("afyun", "narkotik", 0.65),
    ("ko'st", "narkotik", 0.40), ("bang", "narkotik", 0.35), ("morfiy", "narkotik", 0.65),
    ("narkotik", "narkotik", 0.70), ("narkotika", "narkotik", 0.70), ("narkota", "narkotik", 0.55),
    ("dori-darmon", "narkotik", 0.15), ("dozasi", "narkotik", 0.25),

    # ====================== QUROL ======================
    ("ствол", "qurol", 0.55), ("стволы", "qurol", 0.55), ("оружие", "qurol", 0.45),
    ("пистолет", "qurol", 0.45), ("пистолет макаров", "qurol", 0.70), ("макаров", "qurol", 0.70),
    ("патрон", "qurol", 0.45), ("патроны", "qurol", 0.60), ("боеприпасы", "qurol", 0.60),
    ("глушитель", "qurol", 0.60), ("травмат", "qurol", 0.55), ("травматик", "qurol", 0.50),
    ("газовый пистолет", "qurol", 0.45), ("обрез", "qurol", 0.65), ("ружьё", "qurol", 0.45),
    ("ружье", "qurol", 0.45), ("дробовик", "qurol", 0.55), ("карабин", "qurol", 0.55),
    ("винтовка", "qurol", 0.55), ("калашников", "qurol", 0.75), ("ак 47", "qurol", 0.75),
    ("калаш", "qurol", 0.65), ("автомат", "qurol", 0.35), ("граната", "qurol", 0.70),
    ("гранаты", "qurol", 0.70), ("тротил", "qurol", 0.75), ("взрывчатка", "qurol", 0.75),
    ("динамит", "qurol", 0.75), ("детонатор", "qurol", 0.70), ("кастет", "qurol", 0.55),
    ("холодное оружие", "qurol", 0.50),
    ("qurol", "qurol", 0.45), ("o'q-dori", "qurol", 0.55), ("o'qotar", "qurol", 0.45),
    ("to'pponcha", "qurol", 0.55), ("miltiq", "qurol", 0.55), ("snayper", "qurol", 0.50),
    ("portlovchi", "qurol", 0.55), ("portlovchi modda", "qurol", 0.65), ("granata", "qurol", 0.60),

    # ====================== TIJORAT (savdo signallari) ======================
    ("sotiladi", "tijorat", 0.25), ("sotaman", "tijorat", 0.30), ("sotamiz", "tijorat", 0.25),
    ("sotuv", "tijorat", 0.20), ("продам", "tijorat", 0.30), ("продаю", "tijorat", 0.30),
    ("продается", "tijorat", 0.25), ("куплю", "tijorat", 0.20), ("оптом", "tijorat", 0.25),
    ("опт", "tijorat", 0.25), ("розница", "tijorat", 0.25), ("в наличии", "tijorat", 0.35),
    ("под заказ", "tijorat", 0.35), ("есть в наличии", "tijorat", 0.40), ("завоз", "tijorat", 0.35),
    ("новый завоз", "tijorat", 0.40), ("свежий товар", "tijorat", 0.35), ("прайс", "tijorat", 0.30),
    ("оплата", "tijorat", 0.20), ("биткоин", "tijorat", 0.30), ("btc", "tijorat", 0.25),
    ("qiwi", "tijorat", 0.25), ("киви", "tijorat", 0.25), ("крипта", "tijorat", 0.30),
    ("перевод на карту", "tijorat", 0.30), ("гарант", "tijorat", 0.30), ("без кидалова", "tijorat", 0.45),
    ("без предоплаты", "tijorat", 0.30), ("проверенный", "tijorat", 0.20), ("топ качество", "tijorat", 0.30),

    # ====================== YOLLASH (kuryer yollash hiylasi) ======================
    ("работа курьером", "yollash", 0.50), ("требуется курьер", "yollash", 0.50), ("курьер", "yollash", 0.25),
    ("минёр требуется", "yollash", 0.65), ("подработка", "yollash", 0.20), ("вакансия", "yollash", 0.20),
    ("высокая зарплата", "yollash", 0.25), ("быстрый заработок", "yollash", 0.30),
    ("лёгкие деньги", "yollash", 0.35), ("ищем работников", "yollash", 0.30), ("работа в телеграм", "yollash", 0.30),

    # --- O'zbekcha yollash / kuryer-zakladka tuzog'i ---
    # Umumiy (past og'irlik — yakka o'zi shubha emas, lekin birikkanda signal):
    ("kuryer kerak", "yollash", 0.18), ("kuryer", "yollash", 0.12), ("kurier", "yollash", 0.12),
    ("kurer", "yollash", 0.12), ("ish kerak", "yollash", 0.08), ("xodim kerak", "yollash", 0.10),
    ("ishga olamiz", "yollash", 0.12), ("ishga kerak", "yollash", 0.10), ("kuniga", "yollash", 0.08),
    ("tajriba shart emas", "yollash", 0.18), ("tajriba talab etilmaydi", "yollash", 0.18),
    ("yuqori maosh", "yollash", 0.18), ("katta maosh", "yollash", 0.18), ("yuqori daromad", "yollash", 0.20),
    ("18 dan katta", "yollash", 0.12),
    # Kuchli tuzoq belgilari (narko-kuryer e'lonlariga xos):
    ("hech narsa sotmaysiz", "yollash", 0.55), ("hech narsa sotmaysan", "yollash", 0.55),
    ("hech nima sotmaysiz", "yollash", 0.55), ("sotish shart emas", "yollash", 0.45),
    ("paket tashiysiz", "yollash", 0.40), ("paket tashish", "yollash", 0.32),
    ("paketni tashlash", "yollash", 0.40), ("paket tashlab", "yollash", 0.40),
    ("faqat tashiysiz", "yollash", 0.40), ("faqat tashlaysiz", "yollash", 0.40),
    ("tashlab kel", "yollash", 0.35), ("joyiga tashlab", "yollash", 0.35),
    ("oson pul", "yollash", 0.40), ("yengil pul", "yollash", 0.40), ("tez pul", "yollash", 0.35),
    ("tezkor daromad", "yollash", 0.30), ("anonim ish", "yollash", 0.35), ("anonim", "yollash", 0.15),

    # ====================== KANAL / ALOQA ======================
    ("пиши в лс", "kanal", 0.25), ("жми старт", "kanal", 0.30), ("оператор", "kanal", 0.20),
    ("наш бот", "kanal", 0.25), ("заказ в боте", "kanal", 0.35), ("пиши в бот", "kanal", 0.30),
    ("телеграм бот", "kanal", 0.20),
]

# Emoji signallari (matnda to'g'ridan-to'g'ri qidiriladi).
_EMOJI = [
    ("❄", "narkotik", 0.30), ("🍁", "narkotik", 0.35), ("💊", "narkotik", 0.30),
    ("🔌", "narkotik", 0.25), ("🧪", "narkotik", 0.25), ("🌿", "narkotik", 0.25),
    ("🍄", "narkotik", 0.30), ("💉", "narkotik", 0.30), ("🧊", "narkotik", 0.30),
    ("💎", "narkotik", 0.22), ("⛄", "narkotik", 0.25), ("🌱", "narkotik", 0.22),
    ("🔫", "qurol", 0.45), ("💣", "qurol", 0.50), ("🔪", "qurol", 0.30),
]


@dataclass
class LexEntry:
    term: str
    category: str
    weight: float
    canon: str
    canon_collapsed: str
    is_emoji: bool = False


def _build() -> list[LexEntry]:
    out: list[LexEntry] = []
    seen: set[str] = set()
    for term, cat, w in _RAW:
        c = normalize(term)
        if not c or c in seen:
            continue  # bir xil kanonni takrorlamaymiz
        seen.add(c)
        out.append(LexEntry(term, cat, w, c, collapse(c)))
    for sym, cat, w in _EMOJI:
        out.append(LexEntry(sym, cat, w, sym, sym, is_emoji=True))
    return out


LEXICON = _build()
