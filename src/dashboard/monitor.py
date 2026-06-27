"""
monitor.py — har bir kamera uchun kuzatuv ishchisi (dashboard uchun).

Mavjud aniqlash quvurini (pose + detector) qayta ishlatadi, lekin Telegram'ga
darhol yubormaydi — har hodisani BAZAGA yozadi (rasm + AI bahosi + yuz),
keyin dashboard'dan AI filtr orqali agentga yuboriladi.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime

import cv2

from ..camera import CameraStream
from ..pose import (PoseEstimator, draw_overlay,
                    L_HIP, R_HIP, L_ANKLE, R_ANKLE, L_WRIST, R_WRIST)
from ..detector import GroundInteractionDetector
from .face import detect_face
from .aifilter import score_event
from . import db

CAPTURE_DIR = "captures"


class CameraMonitor:
    def __init__(self, cam_row: dict, cfg):
        self.cam = cam_row
        self.cfg = cfg
        src = cam_row["source"]
        # USB index ("0") yoki RTSP url
        source = int(src) if str(src).isdigit() else src
        self.camera = CameraStream(source, name=cam_row["name"],
                                   width=1280, height=720)
        self.pose = PoseEstimator(cfg.model, cfg.device, cfg.conf, cfg.imgsz)
        self.detector = GroundInteractionDetector(cam_row["name"], cfg)
        self._running = False
        self._thread = None
        self._frame_idx = 0
        self.latest_jpg = None      # jonli ko'rinish uchun
        self.online = False
        os.makedirs(CAPTURE_DIR, exist_ok=True)

    def start(self):
        if self._running:
            return
        self.camera.start()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name=f"mon-{self.cam['id']}")
        self._thread.start()

    def _loop(self):
        every = max(1, self.cfg.process_every_n_frames)
        while self._running:
            frame = self.camera.read()
            if frame is None:
                self.online = False
                time.sleep(0.05)
                continue
            self.online = True
            self._frame_idx += 1
            if self._frame_idx % every != 0:
                continue

            persons = self.pose.detect(frame)
            events = self.detector.update(persons, frame_h=frame.shape[0])

            overlay = draw_overlay(frame, persons,
                                   self.detector.active_interacting_ids,
                                   self.cfg.keypoint_conf)
            cv2.putText(overlay, datetime.now().strftime("%H:%M:%S"),
                        (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            ok, buf = cv2.imencode(".jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                self.latest_jpg = buf.tobytes()

            for ev in events:
                self._save_event(ev, frame, overlay, persons)

    def _save_event(self, ev, frame, overlay, persons):
        person = next((p for p in persons if p.track_id == ev.track_id), None)
        kpc = self.cfg.keypoint_conf

        full_body = face_present = hand_low = False
        kp_quality = 0.0
        face_crop = None

        if person is not None:
            kp = person.keypoints
            def vis(i): return kp[i, 2] >= kpc
            hips = vis(L_HIP) or vis(R_HIP)
            ankles = vis(L_ANKLE) or vis(R_ANKLE)
            full_body = hips and ankles
            kp_quality = float((kp[:, 2] >= kpc).sum()) / 17.0
            x1, y1, x2, y2 = person.box
            box_h = max(1.0, float(y2 - y1))
            for wi in (L_WRIST, R_WRIST):
                if vis(wi) and (kp[wi, 1] - y1) / box_h >= (1.0 - self.cfg.hand_ground_ratio):
                    hand_low = True
            face_crop, face_present = detect_face(frame, person.box)

        motion_only = "keskin pastga" in (ev.reason or "")
        result = score_event(full_body, face_present, hand_low, kp_quality, motion_only)

        ts = datetime.fromtimestamp(ev.timestamp)
        stamp = ts.strftime("%Y%m%d_%H%M%S")
        base = f"{stamp}_cam{self.cam['id']}_id{ev.track_id}"
        snap_path = os.path.join(CAPTURE_DIR, base + ".jpg")
        cv2.imwrite(snap_path, overlay)

        face_path = None
        if face_crop is not None and face_crop.size > 0:
            face_path = os.path.join(CAPTURE_DIR, base + "_face.jpg")
            cv2.imwrite(face_path, face_crop)

        identity = "Yuz aniqlandi (ID bazasi ulanmagan)" if face_present else "Yuz topilmadi"

        db.add_event(
            camera_id=self.cam["id"], camera_name=self.cam["name"],
            ts=ts.strftime("%Y-%m-%d %H:%M:%S"),
            snapshot=snap_path, face=face_path, reason=ev.reason,
            det_conf=round(kp_quality, 2), ai_score=result.score,
            ai_recommend=result.recommend, identity=identity, status="new")
        print(f"[Monitor] Hodisa: cam{self.cam['id']} id{ev.track_id} "
              f"AI={result.score} ({'YUBORISH' if result.recommend else 'ushlab'})")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.camera.stop()


class MonitorManager:
    """Barcha kamera monitorlarini boshqaradi."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.monitors: dict[int, CameraMonitor] = {}

    def start(self, cam_row: dict):
        cid = cam_row["id"]
        if cid in self.monitors:
            return
        m = CameraMonitor(cam_row, self.cfg)
        self.monitors[cid] = m
        m.start()

    def stop(self, cid: int):
        m = self.monitors.pop(cid, None)
        if m:
            m.stop()

    def latest(self, cid: int):
        m = self.monitors.get(cid)
        return m.latest_jpg if m else None

    def is_running(self, cid: int) -> bool:
        return cid in self.monitors

    def stop_all(self):
        for m in list(self.monitors.values()):
            m.stop()
        self.monitors.clear()
