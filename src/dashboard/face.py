"""
face.py — FACEID: shubhali odamning YUZINI aniqlaydi va ajratib oladi.

OpenCV'ning tayyor yuz detektoridan (Haar cascade) foydalanadi — qo'shimcha
kutubxona yoki internet kerak emas.

Eslatma: yuzni ANIQLASH va kesib olish shu yerda. Yuzni MA'LUM shaxsga
moslash (real FACEID bazasi) — keyingi bosqich integratsiyasi; bu modul shu
uchun tayyor kesimni beradi. Watchlist papkasi kelajakda shu yerga ulanadi.
"""
from __future__ import annotations

import cv2

_cascade = None


def _get_cascade():
    global _cascade
    if _cascade is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _cascade = cv2.CascadeClassifier(path)
    return _cascade


def detect_face(frame, box=None):
    """
    Kadrdan (yoki odam ramkasi ichidan) eng katta yuzni topadi.
    Qaytaradi: (face_crop yoki None, topildimi).
    box = [x1,y1,x2,y2] berilsa, faqat shu sohada qidiradi (tezroq, aniqroq).
    """
    if frame is None:
        return None, False
    img = frame
    ox, oy = 0, 0
    if box is not None:
        x1, y1, x2, y2 = [int(v) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
        if x2 > x1 and y2 > y1:
            img = frame[y1:y2, x1:x2]
            ox, oy = x1, y1

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _get_cascade().detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                            minSize=(30, 30))
    if len(faces) == 0:
        return None, False

    # Eng katta yuz
    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    # Biroz kengaytirib kesamiz
    pad = int(0.2 * fh)
    y1 = max(0, fy - pad); y2 = min(img.shape[0], fy + fh + pad)
    x1 = max(0, fx - pad); x2 = min(img.shape[1], fx + fw + pad)
    crop = img[y1:y2, x1:x2].copy()
    return crop, True
