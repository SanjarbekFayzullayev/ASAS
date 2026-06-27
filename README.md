# 👁️ Yer-muloqot kuzatuv tizimi

Kameraga ulangan kompyuter atrofni **24/7 kuzatadi**. Har bir odamni va uning
**skeletini (tana holatini)** real vaqtda taniydi. Agar kimdir **yerga engashsa,
yerdan nimadir olsa yoki yerga nimadir qo'ysa/ko'msa** — tizim buni avtomatik
aniqlaydi va sizga **Telegram orqali rasm + ogohlantirish** yuboradi.

Kameraga doim qarab o'tirish shart emas — tizim faqat haqiqiy hodisa bo'lganda bezovta qiladi.

## Qanday ishlaydi?

```
 Kamera (USB/RTSP) ──► YOLOv8-pose (skelet) ──► Tahlil (engashish + qo'l yerda?) ──► Telegram (rasm + matn)
                                                          │
                                                          └─► (ixtiyoriy) Ollama: rasmni o'zbekcha tasvirlaydi
```

- **YOLOv8-pose** — har bir odamning 17 ta skelet nuqtasini topadi (bepul, ochiq kod).
- **Tahlil mantiqi** — tana egilgan/cho'kkalagan + qo'l yerga yaqin bo'lsa → "yer bilan muloqot".
- **Yolg'on signalga qarshi** — hodisa bir necha kadr davom etishi shart + "sovish vaqti" (cooldown).
- **Ollama (ixtiyoriy)** — hodisa rasmiga qarab "odam yerga qora paket ko'mmoqda" kabi izoh beradi.

Hammasi **bepul** va **lokal** (internet faqat Telegram xabari uchun kerak).

---

## ✅ HOZIRGI HOLAT — o'rnatish TUGADI

Bu kompyuterda men quyidagilarni allaqachon bajarib qo'ydim:
- ✅ **Python 3.12** o'rnatildi
- ✅ **Virtual muhit** (`.venv`) yaratildi
- ✅ **Barcha kutubxonalar** (PyTorch, YOLO, OpenCV...) o'rnatildi
- ✅ **Microsoft Visual C++ Redistributable** o'rnatildi (PyTorch'ga kerak edi)
- ✅ **Modellar sinovdan o'tdi:** CPU'da **~9.7 FPS** (real vaqt uchun yetarli)

**Sizga qolgan atigi 2 qadam:**
1. **Telegram token** oling va `.env`ga yozing (pastda 4-qadam) — `python telegram_setup.py` yordam beradi.
2. **Ishga tushiring:** `.\.venv\Scripts\python.exe main.py`

> Buyruqlarni har safar `.\.venv\Scripts\python.exe` bilan yozing (virtual muhit), yoki avval `.\.venv\Scripts\Activate.ps1` qiling, keyin oddiy `python`.

## ⚠️ ANIQLIK HAQIDA HALOL GAP (muhim!)

Tizim **"kimdir yerga engashib qo'l cho'zdi"** hodisasini **ishonchli** aniqlaydi va sizga rasm yuboradi — bu asosiy, mustahkam funksiya.

Lekin **"aynan oldimi / qo'ydimi / ko'mdimi"** ni faqat skelet va arzon kameradan **100% ishonchli ajratib bo'lmaydi** (4 ta mustaqil yondashuv sinovdan o'tkazildi — hammasi cheklangan). Sabab: oddiy obyekt-modeli qora paket, tugun, ko'milgan buyumni ko'rmaydi. Shuning uchun tizim ko'pincha **"NOANIQ"** deb belgilashi mumkin — bu **xato emas, halollik**.

**Aniq "nima bo'ldi"ni bilishning eng yaxshi yo'li — Ollama'ni yoqish** (pastda). Vision-model rasmni ko'rib *"odam yerga qora paket ko'mmoqda"* deb haqiqatan tasvirlab beradi. Yoki shunchaki kelgan **rasmga o'zingiz qaraysiz** — baribir har hodisada rasm keladi.

Agar noto'g'ri yorliqlar bezovta qilsa: `config.yaml` da `classify_enabled: false` — tizim faqat ishonchli hodisa + rasm yuboradi.

---

## 1-qadam: Python 3.12 o'rnatish

⚠️ Kompyuteringizda **Python 3.14** bor, lekin YOLO/PyTorch unga hali to'liq mos emas.
Ishonchli bo'lishi uchun **Python 3.12** o'rnating (eski 3.14 o'chirilmaydi, yonma-yon turadi):

PowerShell'da:
```powershell
winget install -e --id Python.Python.3.12
```
O'rnatgach, PowerShell'ni qayta oching va tekshiring:
```powershell
py -3.12 --version    # "Python 3.12.x" chiqishi kerak
```

## 2-qadam: Loyihani tayyorlash

Loyiha papkasida (`AiHakatonProjekt`) PowerShell oching:

```powershell
# Virtual muhit yaratamiz (3.12 bilan)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Kutubxonalarni o'rnatamiz (bir necha daqiqa, ~1-2 GB yuklab oladi)
pip install --upgrade pip
pip install -r requirements.txt
```

> Agar `Activate.ps1` "running scripts is disabled" xatosini bersa, bir marta:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

## 3-qadam: Tekshirish (kamera + modellar)

Modellar CPU'da ishlashini tekshirish (kamerasiz, tezlikni ko'rsatadi):
```powershell
.\.venv\Scripts\python.exe smoke_test.py
```

Kamerani sinash:
```powershell
.\.venv\Scripts\python.exe test_camera.py
```
USB kamerangiz ochilib, oynada ko'rinsa — tayyor. RTSP uchun:
```powershell
.\.venv\Scripts\python.exe test_camera.py "rtsp://login:parol@192.168.1.10:554/stream"
```

## 4-qadam: Telegram botni sozlash

1. Telegram'da **@BotFather** ga yozing → `/newbot` → bot nomini bering → **token** oling.
2. Yangi botingizga biror xabar yozing (masalan "salom").
3. Brauzerda oching (TOKEN o'rniga o'z tokeningiz):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Javobdagi `"chat":{"id": ... }` sonini ko'chiring — bu sizning **chat ID**'ingiz.
4. `.env.example` faylini **`.env`** deb nusxalang va to'ldiring:
   ```
   TELEGRAM_BOT_TOKEN=sizning_tokeningiz
   TELEGRAM_CHAT_ID=sizning_chat_id
   ```

PowerShell'da nusxalash:
```powershell
Copy-Item .env.example .env
notepad .env
```

## 5-qadam: Kameralarni `config.yaml` da sozlash

`config.yaml` faylini oching va `cameras` ro'yxatini moslang:
```yaml
cameras:
  - name: "Asosiy kamera"
    source: 0                       # USB kamera raqami
  - name: "Hovli"
    source: "rtsp://admin:parol@192.168.1.64:554/Streaming/Channels/101"
```

## 6-qadam: Ishga tushirish 🚀

```powershell
.\.venv\Scripts\python.exe main.py
```

- Ekranda jonli oyna ochiladi (skelet bilan). **Shubhali odam qizil** rangda.
- Hodisa aniqlanganda — Telegram'ga rasm + xabar keladi, rasm `snapshots/` papkasiga ham saqlanadi.
- To'xtatish: oynada **`q`** yoki konsolda **Ctrl+C**.

> 24/7 server rejimida oynani o'chirish uchun `config.yaml` da `show_window: false` qiling.

---

## ⚙️ Sozlash (yolg'on signal ko'p yoki kam bo'lsa)

`config.yaml` → `detection` bo'limidagi qiymatlar:

| Sozlama | Vazifasi | Ko'p signal bo'lsa | Kam signal bo'lsa |
|---|---|---|---|
| `hand_ground_ratio` | Qo'l "yerga yaqin" deyilishi (0.25 = pastki 25%) | kichraytiring (0.18) | kattalashtiring (0.30) |
| `torso_bend_angle` | Engashish burchagi (gradus) | kattalashtiring (55) | kichraytiring (35) |
| `sustain_frames` | Hodisa necha kadr davom etsin | kattalashtiring (10) | kichraytiring (4) |
| `cooldown_seconds` | Xabarlar orasidagi minimal vaqt | kattalashtiring | kichraytiring |
| `process_every_n_frames` | CPU sekin bo'lsa kattalashtiring (3-4) | — | — |

## 🧠 Ollama (ixtiyoriy) — rasmni tasvirlash

1. [ollama.com](https://ollama.com) dan Ollama o'rnating.
2. Vision modelni yuklang:
   ```powershell
   ollama pull llava
   ```
3. `config.yaml` da yoqing:
   ```yaml
   ollama:
     enabled: true
     model: "llava"
   ```
Endi har bir xabarga "🧠 Tavsif:" qatori qo'shiladi.

## 📁 Loyiha tuzilishi

```
AiHakatonProjekt/
├── main.py              # Ishga tushiruvchi
├── test_camera.py       # Kamerani tekshirish
├── config.yaml          # Sozlamalar
├── .env                 # Maxfiy tokenlar (o'zingiz yaratasiz)
├── requirements.txt
└── src/
    ├── config.py        # Sozlamalarni o'qish
    ├── camera.py        # Kamera (USB/RTSP, avto qayta ulanish)
    ├── pose.py          # YOLOv8-pose + skelet chizish
    ├── detector.py      # "Yer bilan muloqot" mantiqi (miya)
    ├── notifier.py      # Telegram xabar
    ├── describer.py     # Ollama izohi (ixtiyoriy)
    └── pipeline.py      # Hammasini bog'lovchi quvur
```


```
