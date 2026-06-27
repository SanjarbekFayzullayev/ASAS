"""
detector.py — tizimning "miyasi".

Skelet nuqtalaridan foydalanib, odam YER BILAN SHUBHALI MULOQOT qilayotganini aniqlaydi:
  - engashish (tana tikkadan egiladi),
  - yoki cho'kkalash (tizza bukiladi),
  + qo'l(lar) yerga yaqinlashadi.

Bu uchta vaziyatni (olish / qo'yish / ko'mish) bitta "yer bilan muloqot" hodisasi
sifatida qaraydi, chunki faqat skelet bilan ularni 100% farqlash qiyin.
ANIQ nima bo'lganini (ixtiyoriy) Ollama rasmni ko'rib aytib beradi.

Yolg'on signallarni kamaytirish uchun:
  - hodisa bir necha kadr DAVOM etishi shart (sustain_frames),
  - bir odam uchun xabarlar orasida "sovish vaqti" (cooldown) bor.
"""
from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass

import numpy as np

from .config import DetectionConfig
from .pose import (
    Person, NOSE,
    L_SHOULDER, R_SHOULDER, L_WRIST, R_WRIST,
    L_HIP, R_HIP, L_KNEE, R_KNEE, L_ANKLE, R_ANKLE,
)


@dataclass
class DetectionEvent:
    camera_name: str
    track_id: int
    timestamp: float
    reason: str            # qisqa o'zbekcha sabab


# ---------- Yordamchi geometrik funksiyalar ----------

def _pt(kp: np.ndarray, idx: int, conf: float):
    """Keypoint ishonchli bo'lsa (x, y) qaytaradi, aks holda None."""
    if kp[idx, 2] >= conf:
        return float(kp[idx, 0]), float(kp[idx, 1])
    return None


def _mid(a, b):
    """Ikki nuqtaning o'rtasi (biri yo'q bo'lsa ikkinchisini, ikkalasi yo'q bo'lsa None)."""
    if a and b:
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return a or b


def _angle_from_vertical(top, bottom) -> float | None:
    """
    'bottom'->'top' vektorining tikka (vertikal) o'qdan og'ish burchagi (gradus).
    Tik turganda ~0°, gorizontal (to'liq engashgan) bo'lsa ~90°.
    """
    if not top or not bottom:
        return None
    dx = top[0] - bottom[0]
    dy = top[1] - bottom[1]
    return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))


def _joint_angle(a, b, c) -> float | None:
    """b nuqtadagi burchak (a-b-c). Masalan tizza burchagi: son-tizza-to'piq."""
    if not a or not b or not c:
        return None
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return None
    cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    cosang = max(-1.0, min(1.0, cosang))
    return math.degrees(math.acos(cosang))


# ---------- Bitta odamning holatini kuzatuvchi ----------

class _PersonState:
    def __init__(self, drop_window: int = 12):
        self.sustain = 0          # ketma-ket "muloqot" kadrlari soni
        self.miss = 0             # ketma-ket "muloqot yo'q" kadrlari
        self.in_episode = False   # hozir bir hodisa ichidamizmi (qayta-qayta xabar bermaslik uchun)
        self.last_event_ts = 0.0  # oxirgi xabar vaqti (cooldown uchun)
        # Yelka (yoki bosh) balandligi tarixi — harakatli engashishni aniqlash uchun.
        self.y_hist: deque = deque(maxlen=max(3, drop_window))


class GroundInteractionDetector:
    """Har bir kamera uchun alohida nusxa yaratiladi."""

    def __init__(self, camera_name: str, cfg: DetectionConfig):
        self.camera_name = camera_name
        self.cfg = cfg
        self._states: dict[int, _PersonState] = {}
        self._last_global_ts = 0.0   # kamera bo'yicha oxirgi hodisa vaqti (umumiy cooldown)

    def _analyze_pose(self, p: Person) -> tuple[bool, str]:
        """
        Bitta odam shu kadrda yer bilan muloqotda emasmi — tekshiradi.
        Qaytaradi: (muloqotda_mi, sabab_matni).
        """
        kp = p.keypoints
        kpc = self.cfg.keypoint_conf

        x1, y1, x2, y2 = p.box
        box_h = max(1.0, float(y2 - y1))

        shoulder = _mid(_pt(kp, L_SHOULDER, kpc), _pt(kp, R_SHOULDER, kpc))
        hip = _mid(_pt(kp, L_HIP, kpc), _pt(kp, R_HIP, kpc))
        l_wrist = _pt(kp, L_WRIST, kpc)
        r_wrist = _pt(kp, R_WRIST, kpc)

        # --- 1) Qo'l(lar) yerga yaqinmi? ---
        # Ramka ichida nisbiy balandlik: 0 = tepa, 1 = pastki chek (yerga eng yaqin).
        wrist_ratios = []
        for w in (l_wrist, r_wrist):
            if w:
                wrist_ratios.append((w[1] - y1) / box_h)
        hand_low = bool(wrist_ratios) and max(wrist_ratios) >= (1.0 - self.cfg.hand_ground_ratio)

        # --- 2) Tana engashganmi? ---
        torso_angle = _angle_from_vertical(shoulder, hip)
        bent = torso_angle is not None and torso_angle >= self.cfg.torso_bend_angle

        # --- 3) Cho'kkalaganmi (tizza bukilgan)? ---
        l_knee_ang = _joint_angle(_pt(kp, L_HIP, kpc), _pt(kp, L_KNEE, kpc), _pt(kp, L_ANKLE, kpc))
        r_knee_ang = _joint_angle(_pt(kp, R_HIP, kpc), _pt(kp, R_KNEE, kpc), _pt(kp, R_ANKLE, kpc))
        knee_angles = [a for a in (l_knee_ang, r_knee_ang) if a is not None]
        crouched = bool(knee_angles) and min(knee_angles) <= self.cfg.knee_bend_angle

        # --- Yakuniy qaror ---
        # Qo'l yerga yaqin BO'LISHI shart, ustiga tana egilgan yoki cho'kkalagan bo'lsa.
        interacting = hand_low and (bent or crouched)

        if interacting:
            if bent and crouched:
                reason = "engashib va cho'kkalab yerga qo'l cho'zdi"
            elif bent:
                reason = "yerga engashdi va qo'l cho'zdi"
            else:
                reason = "cho'kkalab yerga qo'l cho'zdi"
        else:
            reason = ""
        return interacting, reason

    def _analyze_motion(self, st: "_PersonState", p: Person, frame_h) -> tuple[bool, str]:
        """
        Harakatga asoslangan engashish: butun gavda ko'rinmasa ham (stol oldida,
        yaqin kadr), yelka (yoki bosh) keskin PASTGA tushsa — bu engashishdir.
        Qaytaradi: (engashdimi, sabab).
        """
        if not getattr(self.cfg, "enable_motion_bend", True) or not frame_h:
            return False, ""

        kp = p.keypoints
        kpc = self.cfg.keypoint_conf
        ref = _mid(_pt(kp, L_SHOULDER, kpc), _pt(kp, R_SHOULDER, kpc))
        if ref is None:
            ref = _pt(kp, NOSE, kpc)   # yelka ko'rinmasa, boshdan foydalanamiz
        if ref is None:
            return False, ""

        y = ref[1]
        st.y_hist.append(y)
        if len(st.y_hist) < 3:
            return False, ""

        recent_high = min(st.y_hist)   # eng yuqori holat (eng kichik y = tik turish)
        drop = (y - recent_high) / float(frame_h)
        if drop >= getattr(self.cfg, "drop_trigger_ratio", 0.18):
            return True, "gavda keskin pastga egildi (engashish)"
        return False, ""

    def update(self, persons: list[Person], frame_h=None) -> list[DetectionEvent]:
        """
        Har kadr chaqiriladi. Tasdiqlangan yangi hodisalar ro'yxatini qaytaradi.
        frame_h — kadr balandligi (harakatli engashish uchun); berilmasa o'tkazib yuboriladi.
        """
        now = time.time()
        events: list[DetectionEvent] = []
        seen_ids = set()

        for p in persons:
            seen_ids.add(p.track_id)
            st = self._states.setdefault(
                p.track_id, _PersonState(getattr(self.cfg, "drop_window_frames", 12)))

            pose_interacting, reason = self._analyze_pose(p)
            motion_ducked, mreason = self._analyze_motion(st, p, frame_h)
            interacting = pose_interacting or motion_ducked
            if not pose_interacting and motion_ducked:
                reason = mreason

            if interacting:
                st.sustain += 1
                st.miss = 0
            else:
                # Bitta-ikkita kadr yo'qolishiga chidamli bo'lamiz.
                st.miss += 1
                if st.miss >= 2:
                    st.sustain = 0
                    st.in_episode = False  # epizod tugadi -> keyingi engashish yangi hodisa

            confirmed = st.sustain >= self.cfg.sustain_frames
            cooled = (now - st.last_event_ts) >= self.cfg.cooldown_seconds
            # UMUMIY cooldown: ID tez-tez o'zgarsa ham, kamera bo'yicha spam bo'lmaydi.
            global_cd = getattr(self.cfg, "global_cooldown_seconds", 0.0)
            global_ok = (now - self._last_global_ts) >= global_cd

            if confirmed and not st.in_episode and cooled and global_ok:
                st.in_episode = True
                st.last_event_ts = now
                self._last_global_ts = now
                events.append(DetectionEvent(
                    camera_name=self.camera_name,
                    track_id=p.track_id,
                    timestamp=now,
                    reason=reason or "yer bilan shubhali muloqot",
                ))

        # Kadrdan g'oyib bo'lgan ID'lar holatini tozalab boramiz (xotira o'smasligi uchun).
        for tid in list(self._states.keys()):
            if tid not in seen_ids:
                self._states[tid].miss += 1
                if self._states[tid].miss > 100:
                    del self._states[tid]

        return events

    @property
    def active_interacting_ids(self) -> set[int]:
        """Hozir muloqotda deb hisoblanayotgan ID'lar (chizishda qizil bo'ladi)."""
        return {tid for tid, st in self._states.items() if st.sustain > 0}
