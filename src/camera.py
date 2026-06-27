"""
camera.py — kameradan kadrlarni o'qiydi.

Muhim xususiyatlar (24/7 ishlash uchun):
  * Alohida oqimda (thread) o'qiydi -> har doim eng SO'NGGI kadrni beradi (RTSP'da kechikish bo'lmaydi).
  * Ulanish uzilsa, avtomatik qayta ulanadi.
  * USB (raqam) va RTSP (manzil) — ikkalasini ham qo'llaydi.
"""
from __future__ import annotations

import threading
import time

import cv2


class CameraStream:
    def __init__(self, source, name: str = "Kamera", reconnect_delay: float = 3.0,
                 width: int = 0, height: int = 0):
        self.source = source
        self.name = name
        self.reconnect_delay = reconnect_delay
        self.width = width      # 0 = kameraning standart o'lchami
        self.height = height

        self._cap: cv2.VideoCapture | None = None
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._connected = False

    def _open(self) -> bool:
        """Kamerani ochishga urinadi."""
        # Tarmoq manbalari (rtsp:// , http:// , https:// — telefon/IP kamera) uchun FFMPEG.
        if isinstance(self.source, str) and "://" in self.source:
            cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
        else:
            cap = cv2.VideoCapture(self.source)

        # Buferni kichik tutamiz -> eng yangi kadr.
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        # So'ralgan aniqlikni qo'yamiz (kamera qo'llab-quvvatlasa).
        if self.width and self.height:
            try:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            except Exception:
                pass

        if cap.isOpened():
            self._cap = cap
            self._connected = True
            print(f"[Kamera:{self.name}] ✅ Ulandi.")
            return True
        cap.release()
        self._connected = False
        return False

    def _loop(self):
        """Fon oqimi: doimiy ravishda kadr o'qiydi."""
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                if not self._open():
                    print(f"[Kamera:{self.name}] ⚠️ Ulanmadi, {self.reconnect_delay}s dan keyin qayta urinaman...")
                    time.sleep(self.reconnect_delay)
                    continue

            ok, frame = self._cap.read()
            if not ok or frame is None:
                print(f"[Kamera:{self.name}] ⚠️ Kadr o'qilmadi. Qayta ulanmoqda...")
                self._connected = False
                if self._cap:
                    self._cap.release()
                self._cap = None
                time.sleep(self.reconnect_delay)
                continue

            with self._lock:
                self._frame = frame

    def start(self) -> "CameraStream":
        if self._running:
            return self
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"cam-{self.name}")
        self._thread.start()
        return self

    def read(self):
        """Eng so'nggi kadrni qaytaradi (yoki None, agar hali tayyor bo'lmasa)."""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    @property
    def connected(self) -> bool:
        return self._connected

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._cap is not None:
            self._cap.release()
            self._cap = None
