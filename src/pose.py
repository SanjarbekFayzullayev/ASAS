"""
pose.py — YOLOv8-pose modelini yuklaydi va kadrdagi odamlarni skeleti bilan aniqlaydi.

YOLOv8-pose har bir odam uchun 17 ta "keypoint" (skelet nuqtasi) qaytaradi (COCO formati):
  0 burun, 1 chap ko'z, 2 o'ng ko'z, 3 chap quloq, 4 o'ng quloq,
  5 chap yelka, 6 o'ng yelka, 7 chap tirsak, 8 o'ng tirsak,
  9 chap bilak, 10 o'ng bilak, 11 chap son, 12 o'ng son,
  13 chap tizza, 14 o'ng tizza, 15 chap to'piq, 16 o'ng to'piq
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from ultralytics import YOLO

# Keypoint indekslari uchun qulay nomlar.
NOSE = 0
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16

# Skeletni chizish uchun nuqtalarni bog'lovchi chiziqlar.
SKELETON = [
    (L_SHOULDER, R_SHOULDER), (L_SHOULDER, L_ELBOW), (L_ELBOW, L_WRIST),
    (R_SHOULDER, R_ELBOW), (R_ELBOW, R_WRIST),
    (L_SHOULDER, L_HIP), (R_SHOULDER, R_HIP), (L_HIP, R_HIP),
    (L_HIP, L_KNEE), (L_KNEE, L_ANKLE),
    (R_HIP, R_KNEE), (R_KNEE, R_ANKLE),
]


@dataclass
class Person:
    """Bitta aniqlangan odam: ID, ramka (box) va skelet nuqtalari."""
    track_id: int
    box: np.ndarray            # [x1, y1, x2, y2]
    keypoints: np.ndarray      # shakli (17, 3): har qator [x, y, ishonch]


class PoseEstimator:
    def __init__(self, model_path: str = "yolov8n-pose.pt", device: str = "cpu",
                 conf: float = 0.40, imgsz: int = 640):
        self.device = device
        self.conf = conf
        self.imgsz = imgsz
        print(f"[Pose] '{model_path}' modeli yuklanmoqda (device={device})... "
              f"(birinchi marta internetdan yuklab oladi)")
        self.model = YOLO(model_path)
        print("[Pose] ✅ Model tayyor.")

    def detect(self, frame) -> list[Person]:
        """
        Kadrdan odamlarni topadi va ID bilan kuzatadi (tracking).
        model.track(...) ByteTrack yordamida har bir odamga barqaror ID beradi.
        """
        results = self.model.track(
            frame,
            persist=True,            # ID'larni kadrlar orasida saqlaydi
            tracker="bytetrack.yaml",
            conf=self.conf,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )
        if not results:
            return []

        r = results[0]
        if r.keypoints is None or r.boxes is None or len(r.boxes) == 0:
            return []

        kpts = r.keypoints.data.cpu().numpy()      # (N, 17, 3)
        boxes = r.boxes.xyxy.cpu().numpy()         # (N, 4)
        ids = r.boxes.id
        ids = ids.cpu().numpy().astype(int) if ids is not None else np.arange(len(boxes))

        persons: list[Person] = []
        for i in range(len(boxes)):
            persons.append(Person(track_id=int(ids[i]), box=boxes[i], keypoints=kpts[i]))
        return persons


def draw_overlay(frame, persons: list[Person], highlight_ids: set[int],
                 kp_conf: float = 0.3):
    """
    Kadr ustiga skelet, ramka va ID chizadi.
    Shubhali (highlight_ids) odamlar QIZIL, oddiylari YASHIL rangda.
    Yangi kadr nusxasini qaytaradi (asl kadr o'zgarmaydi).
    """
    img = frame.copy()
    for p in persons:
        flagged = p.track_id in highlight_ids
        color = (0, 0, 255) if flagged else (0, 200, 0)  # BGR: qizil yoki yashil

        x1, y1, x2, y2 = p.box.astype(int)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        label = f"ID {p.track_id}" + (" - SHUBHALI!" if flagged else "")
        cv2.putText(img, label, (x1, max(0, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        kp = p.keypoints
        # Chiziqlar (suyaklar)
        for a, b in SKELETON:
            if kp[a, 2] >= kp_conf and kp[b, 2] >= kp_conf:
                pa = (int(kp[a, 0]), int(kp[a, 1]))
                pb = (int(kp[b, 0]), int(kp[b, 1]))
                cv2.line(img, pa, pb, color, 2)
        # Nuqtalar (bo'g'imlar)
        for j in range(len(kp)):
            if kp[j, 2] >= kp_conf:
                cv2.circle(img, (int(kp[j, 0]), int(kp[j, 1])), 3, (255, 255, 0), -1)
    return img
