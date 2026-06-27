"""
config.py — config.yaml va .env fayllarini o'qib, bitta qulay obyektga jamlaydi.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class CameraConfig:
    name: str
    source: object  # int (USB) yoki str (RTSP)


@dataclass
class DetectionConfig:
    model: str = "yolov8n-pose.pt"
    device: str = "cpu"
    conf: float = 0.40
    keypoint_conf: float = 0.30
    process_every_n_frames: int = 2
    imgsz: int = 640
    hand_ground_ratio: float = 0.25
    torso_bend_angle: float = 45.0
    knee_bend_angle: float = 110.0
    sustain_frames: int = 6
    cooldown_seconds: float = 30.0          # bitta ODAM (track ID) uchun cooldown
    global_cooldown_seconds: float = 10.0   # kamera bo'yicha UMUMIY cooldown (ID o'zgarsa ham spam bo'lmaydi)

    # --- Harakatga asoslangan "engashish" (yaqin kadr / stol oldida ham ishlaydi) ---
    # Butun gavda ko'rinmasa ham, yelka/boshning keskin PASTGA tushishini aniqlaydi.
    enable_motion_bend: bool = True          # harakatli engashish aniqlovchini yoqish
    drop_trigger_ratio: float = 0.18         # yelka kadr balandligining shuncha qismi pastga tushsa -> engashish
    drop_window_frames: int = 12             # "yuqori holat"ni eslab turish oynasi (kadr)

    # --- Hodisani turga ajratish (olish/qoyish/komish/noaniq) ---
    classify_enabled: bool = True            # obyekt-delta klassifikatsiyasi yoqilganmi
    classify_model: str = "yolov8n.pt"       # ikkinchi (detect) model
    classify_imgsz: int = 480                # tejamkorlik uchun kichikroq imgsz
    classify_obj_conf: float = 0.30          # obyekt ishonch chegarasi
    classify_before_lag_frames: int = 3      # "before" kadri necha kadr orqada
    classify_rise_frames: int = 3            # tiklanish necha kadr tasdiqlanadi
    classify_max_wait_frames: int = 40       # "after" ni kutish chegarasi (timeout)
    classify_hand_radius_px: float = 90.0    # bilak atrofidagi radius (piksel)
    classify_ground_band_px: float = 70.0    # yer chizig'i atrofidagi tasma (piksel)
    classify_komish_dwell_frames: int = 25   # "ko'mish" uchun uzoq turish chegarasi


@dataclass
class TelegramConfig:
    enabled: bool = True
    bot_token: str = ""
    chat_ids: list[str] = field(default_factory=list)


@dataclass
class OllamaConfig:
    enabled: bool = False
    url: str = "http://localhost:11434"
    model: str = "llava"
    timeout_seconds: int = 30


@dataclass
class AppConfig:
    cameras: list[CameraConfig]
    detection: DetectionConfig
    telegram: TelegramConfig
    ollama: OllamaConfig
    snapshots_dir: str = "snapshots"
    show_window: bool = True
    save_video_clips: bool = False
    sound_alert: bool = True
    fullscreen: bool = True
    capture_width: int = 1280
    capture_height: int = 720


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    """config.yaml + .env ni o'qib AppConfig qaytaradi."""
    # .env dan maxfiy tokenlarni yuklaymiz (agar fayl bo'lsa).
    load_dotenv()

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"'{config_path}' topilmadi. config.yaml fayl loyiha papkasida bo'lishi kerak."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # --- Kameralar ---
    cameras = []
    for c in raw.get("cameras", []):
        cameras.append(CameraConfig(name=str(c.get("name", "Kamera")), source=c.get("source", 0)))
    if not cameras:
        # Hech bo'lmaganda standart USB kamera.
        cameras = [CameraConfig(name="Asosiy kamera", source=0)]

    # --- Detection ---
    d = raw.get("detection", {}) or {}
    detection = DetectionConfig(
        model=d.get("model", "yolov8n-pose.pt"),
        device=str(d.get("device", "cpu")),
        conf=float(d.get("conf", 0.40)),
        keypoint_conf=float(d.get("keypoint_conf", 0.30)),
        process_every_n_frames=int(d.get("process_every_n_frames", 2)),
        imgsz=int(d.get("imgsz", 640)),
        hand_ground_ratio=float(d.get("hand_ground_ratio", 0.25)),
        torso_bend_angle=float(d.get("torso_bend_angle", 45.0)),
        knee_bend_angle=float(d.get("knee_bend_angle", 110.0)),
        sustain_frames=int(d.get("sustain_frames", 6)),
        cooldown_seconds=float(d.get("cooldown_seconds", 30.0)),
        global_cooldown_seconds=float(d.get("global_cooldown_seconds", 10.0)),
        enable_motion_bend=bool(d.get("enable_motion_bend", True)),
        drop_trigger_ratio=float(d.get("drop_trigger_ratio", 0.18)),
        drop_window_frames=int(d.get("drop_window_frames", 12)),
        classify_enabled=bool(d.get("classify_enabled", True)),
        classify_model=str(d.get("classify_model", "yolov8n.pt")),
        classify_imgsz=int(d.get("classify_imgsz", 480)),
        classify_obj_conf=float(d.get("classify_obj_conf", 0.30)),
        classify_before_lag_frames=int(d.get("classify_before_lag_frames", 3)),
        classify_rise_frames=int(d.get("classify_rise_frames", 3)),
        classify_max_wait_frames=int(d.get("classify_max_wait_frames", 40)),
        classify_hand_radius_px=float(d.get("classify_hand_radius_px", 90.0)),
        classify_ground_band_px=float(d.get("classify_ground_band_px", 70.0)),
        classify_komish_dwell_frames=int(d.get("classify_komish_dwell_frames", 25)),
    )

    # --- Telegram (token/chat .env dan) ---
    t = raw.get("telegram", {}) or {}
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_raw = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    chat_ids = [x.strip() for x in chat_raw.split(",") if x.strip()]
    telegram = TelegramConfig(
        enabled=bool(t.get("enabled", True)),
        bot_token=token,
        chat_ids=chat_ids,
    )

    # --- Ollama ---
    o = raw.get("ollama", {}) or {}
    ollama = OllamaConfig(
        enabled=bool(o.get("enabled", False)),
        url=str(o.get("url", "http://localhost:11434")).rstrip("/"),
        model=str(o.get("model", "llava")),
        timeout_seconds=int(o.get("timeout_seconds", 30)),
    )

    return AppConfig(
        cameras=cameras,
        detection=detection,
        telegram=telegram,
        ollama=ollama,
        snapshots_dir=str(raw.get("snapshots_dir", "snapshots")),
        show_window=bool(raw.get("show_window", True)),
        save_video_clips=bool(raw.get("save_video_clips", False)),
        sound_alert=bool(raw.get("sound_alert", True)),
        fullscreen=bool(raw.get("fullscreen", True)),
        capture_width=int(raw.get("capture_width", 1280)),
        capture_height=int(raw.get("capture_height", 720)),
    )
