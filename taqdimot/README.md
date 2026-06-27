# ASAS — Investorlar taqdimot sahifasi

Bu papkada investorlar uchun ikkita tayyor variant bor:

| Fayl | Nima uchun |
|------|-----------|
| **`index.html`** | Bir sahifalik **veb-sayt** (scroll qilinadigan landing page) |
| **`slaydlar.html`** | **Slaydlar** — `Ctrl+P` → PDF qilish uchun (11 ta slayd) |
| **`PITCH.md`** | **2 daqiqalik nutq** (hikoyadan boshlanadi) — taqdimotda o'qiysiz |

Hech qanday o'rnatish yoki "build" kerak emas — oddiy brauzerda ochiladi.
Brend rangi: **binafsha** (logo bilan mos).

## Slaydlarni PDF qilish (`slaydlar.html`)

1. `slaydlar.html` ni Chrome yoki Edge'da oching.
2. Yuqoridagi **"PDF saqlash"** tugmasini bosing (yoki `Ctrl+P`).
3. Print oynasida:
   - **Destination / Maqsad:** *Save as PDF*
   - **Margins / Chekka:** *None* (Yo'q)
   - **Background graphics / Fon grafikasi:** ☑ **yoqilgan** bo'lsin
4. **Save** → 11 ta slayd, har biri alohida sahifa bo'lib PDF bo'ladi.

> Skrinshotlar `slaydlar.html` da ham `index.html` dagi **bir xil** rasm fayllaridan
> foydalanadi — `images/` ga rasm qo'ysangiz, ikkalasida ham ko'rinadi.

## Skrinshotlar (`images/` papkasi)

Rasmlarni shu nomlar bilan `images/` ichiga tashlang — avtomatik ko'rinadi:

Dashboardni ishga tushiring (`.\.venv\Scripts\python.exe dashboard.py` → http://localhost:5000)
va har bir sahifani screenshot qiling:

| Fayl nomi | Qaysi sahifadan (dashboard) | Qayerda ko'rinadi |
|-----------|------------------------------|-------------------|
| `dashboard.png` | **Boshqaruv paneli** (`/`) | Veb-sayt yuqorisi |
| `tizim.png`     | **Kameralar** (`/cameras`) | Veb-sayt "Yechim" |
| `kamera.png`    | **Jonli kamera** (`/live/<id>`) | Slayd 4 + sayt 1-modul |
| `tahlil.png`    | **Tahlil & Bashorat** (`/analytics`) | Slayd 5 + sayt 2-modul |
| `yordamchi.png` | **AI yordamchi** (`/assistant`) | Sayt 3-modul |
| `team1.png` … `team4.png` | Jamoa a'zolari fotosi | Jamoa bo'limi |

> **SLAYDLAR (PDF) uchun faqat 2 ta rasm kerak:** `kamera.png` va `tahlil.png`.
> Qolganlari faqat veb-saytda ishlatiladi.
>
> 4-modul (onlayn nazorat) uchun alohida sahifa yo'q — uning rasmi olib tashlangan,
> matn o'zi yetarli.
>
> Hamma rasm shart emas. Qaysi birini qo'shsangiz, o'sha joy to'ladi.

## Onlayn joylashtirish (havola olish)

Eng oson — **Netlify Drop**: [app.netlify.com/drop](https://app.netlify.com/drop)
ga kiring va butun **`taqdimot`** papkasini sahifaga sudrab tashlang → bir necha
soniyada havola olasiz (masalan `https://asas.netlify.app`).
