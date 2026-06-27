r"""
dashboard.py — ASAS markaziy boshqaruv paneli (web).

Ishga tushirish:  .\.venv\Scripts\python.exe dashboard.py
Brauzerda:        http://localhost:5000
"""
import json
import os
import threading
import time
from datetime import datetime

from flask import (Flask, render_template, request, redirect,
                   url_for, send_file, abort, Response, jsonify, session)

from src.config import load_config
from src.dashboard import db
from src.dashboard.monitor import MonitorManager
from src.dashboard.analytics import build_report, ingest_csv, reset_data
from src.dashboard.assistant import chat_reply

app = Flask(__name__)
app.secret_key = os.getenv("ASAS_SECRET", "asas-secret-key-2026")

# Kirish ma'lumotlari (.env orqali o'zgartirish mumkin: ASAS_USER / ASAS_PASS)
AUTH_USER = os.getenv("ASAS_USER", "admin")
AUTH_PASS = os.getenv("ASAS_PASS", "asas2026")
AUTH_NAME = os.getenv("ASAS_NAME", "Akmal Karimov")
AUTH_ROLE = os.getenv("ASAS_ROLE", "Operator")

CFG = load_config("config.yaml")
db.init_db()
MGR = MonitorManager(CFG.detection)

for _c in db.list_cameras():
    if _c["active"]:
        try:
            MGR.start(_c)
        except Exception as e:
            print(f"[Dashboard] kamera {_c['id']} ishga tushmadi: {e}")


def send_to_agents(ev: dict) -> bool:
    # Telegram bot ISHLATILMAYDI — hodisa shu dashboardda agentlarga taqdim etiladi (qayd qilinadi).
    print(f"[Dashboard] Hodisa #{ev.get('id')} agentlarga qayd etildi.")
    return True


def _dispatcher():
    """AVTOMATIK YUBORISH: yoqilganda AI filtridan o'tgan yangi hodisalarni
    o'zi agentlarga yuboradi. O'tmaganlari ushlanib qoladi."""
    while True:
        try:
            if db.get_setting("auto_send", "0") == "1":
                for e in db.list_events(300, status="new"):
                    if e["ai_recommend"]:
                        send_to_agents(e)
                        db.set_event_status(e["id"], "sent")
                        print(f"[Avto-yuborish] Hodisa #{e['id']} agentga yuborildi")
        except Exception as ex:
            print(f"[Dispatcher] xato: {ex}")
        time.sleep(3)


threading.Thread(target=_dispatcher, daemon=True, name="dispatcher").start()


# =================== Ikonlar (SVG, Lucide uslubi — internetsiz) ===================
def _svg(p, size=18):
    return (f'<svg class="ico" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


_PATHS = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
    "video": '<path d="m22 8-6 4 6 4V8z"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
    "camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3z"/><circle cx="12" cy="13" r="3.5"/>',
    "layers": '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/>',
    "checkc": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.2a1.6 1.6 0 0 0-2.7-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 4.6 15H4a2 2 0 1 1 0-4h.2a1.6 1.6 0 0 0 1.1-2.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H10a1.6 1.6 0 0 0 1-1.5V4a2 2 0 1 1 4 0v.2a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.2a1.6 1.6 0 0 0-1.4 1z"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "plus": '<path d="M5 12h14M12 5v14"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "badge": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M14 9h4M14 13h4M6 16h12"/>',
    "trash": '<path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2"/>',
    "play": '<polygon points="6 4 20 12 6 20 6 4"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "chart": '<path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="6"/><rect x="12" y="7" width="3" height="10"/><rect x="17" y="14" width="3" height="3"/>',
    "bulb": '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1V17h6v-.2c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
}
ICONS = {k: _svg(v) for k, v in _PATHS.items()}


# =================== Shablonlarga umumiy o'zgaruvchilar ===================
@app.context_processor
def _inject_globals():
    parts = AUTH_NAME.split()
    initials = (parts[0][:1] + (parts[1][:1] if len(parts) > 1 else "")).upper()
    return {"ic": ICONS, "user_name": AUTH_NAME, "user_role": AUTH_ROLE, "initials": initials}


# =================== Kirish (login) ===================
@app.before_request
def _require_login():
    if request.endpoint in ("login", "static") or request.endpoint is None:
        return
    if not session.get("auth"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if (request.form.get("username", "") == AUTH_USER
                and request.form.get("password", "") == AUTH_PASS):
            session["auth"] = True
            return redirect(url_for("home"))
        error = "Login yoki parol noto'g'ri"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =================== Boshqaruv paneli ===================
@app.route("/")
def home():
    return render_template("home.html", title="Boshqaruv paneli", page="home")


# =================== Kameralar ===================
@app.route("/cameras")
def cameras():
    cams = db.list_cameras()
    running = {c["id"]: MGR.is_running(c["id"]) for c in cams}
    return render_template("cameras.html", title="Kameralar", page="cameras",
                           cams=cams, running=running)


@app.route("/cameras/add", methods=["POST"])
def add_camera():
    name = request.form.get("name", "Kamera")
    source = request.form.get("source", "0")
    loc = request.form.get("location", "")
    cid = db.add_camera(name, source, loc)
    try:
        MGR.start(db.get_camera(cid))
    except Exception as e:
        print(f"[Dashboard] start xato: {e}")
    return redirect(url_for("cameras"))


@app.route("/cameras/<int:cid>/start", methods=["POST"])
def cam_start(cid):
    cam = db.get_camera(cid)
    if cam:
        db.set_camera_active(cid, True)
        MGR.start(cam)
    return redirect(url_for("cameras"))


@app.route("/cameras/<int:cid>/stop", methods=["POST"])
def cam_stop(cid):
    MGR.stop(cid)
    db.set_camera_active(cid, False)
    return redirect(url_for("cameras"))


@app.route("/cameras/<int:cid>/delete", methods=["POST"])
def cam_delete(cid):
    MGR.stop(cid)
    db.delete_camera(cid)
    return redirect(url_for("cameras"))


# =================== Media + API ===================
@app.route("/live/<int:cid>")
def live(cid):
    jpg = MGR.latest(cid)
    if not jpg:
        abort(404)
    return Response(jpg, mimetype="image/jpeg")


@app.route("/stream/<int:cid>")
def stream(cid):
    """Uzluksiz JONLI video (MJPEG) — haqiqiy CCTV kabi."""
    def gen():
        while True:
            jpg = MGR.latest(cid)
            if jpg:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n"
                       b"Content-Length: " + str(len(jpg)).encode() + b"\r\n\r\n"
                       + jpg + b"\r\n")
            time.sleep(0.07)
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/snap/<int:eid>")
def snap(eid):
    e = db.get_event(eid)
    if not e or not e["snapshot"] or not os.path.exists(e["snapshot"]):
        abort(404)
    return send_file(e["snapshot"], mimetype="image/jpeg")


@app.route("/face/<int:eid>")
def face(eid):
    e = db.get_event(eid)
    if not e or not e["face"] or not os.path.exists(e["face"]):
        abort(404)
    return send_file(e["face"], mimetype="image/jpeg")


@app.route("/api/stats")
def api_stats():
    s = db.stats()
    s["auto_send"] = db.get_setting("auto_send", "0") == "1"
    return jsonify(s)


@app.route("/settings/autosend", methods=["POST"])
def toggle_autosend():
    cur = db.get_setting("auto_send", "0")
    db.set_setting("auto_send", "0" if cur == "1" else "1")
    return ("", 204)


@app.route("/api/events")
def api_events():
    evs = db.list_events(60)
    return jsonify({"events": [{
        "id": e["id"], "camera_name": e["camera_name"], "ts": e["ts"],
        "reason": e["reason"], "ai_score": e["ai_score"] or 0,
        "ai_recommend": bool(e["ai_recommend"]), "identity": e["identity"],
        "status": e["status"], "has_face": bool(e["face"]),
    } for e in evs]})


@app.route("/events/<int:eid>/send", methods=["POST"])
def send_one(eid):
    e = db.get_event(eid)
    if e:
        send_to_agents(e)
        db.set_event_status(eid, "sent")
    return ("", 204)


@app.route("/events/<int:eid>/dismiss", methods=["POST"])
def dismiss(eid):
    db.set_event_status(eid, "dismiss")
    return ("", 204)


@app.route("/events/send_recommended", methods=["POST"])
def send_recommended():
    sent = 0
    for e in db.list_events(500, status="new"):
        if e["ai_recommend"]:
            send_to_agents(e)
            db.set_event_status(e["id"], "sent")
            sent += 1
    return jsonify({"sent": sent})


# =================== Tahlil & Bashorat (2-modul) ===================
@app.route("/analytics")
def analytics():
    a = build_report()
    maxheat = max(max(v.values()) for v in a["heat"].values()) or 1
    data_json = json.dumps({"region_totals": a["region_totals"], "monthly": a["monthly"],
                            "season_totals": a["season_totals"], "rising": a["rising"],
                            "forecast": a["forecast"], "next_season": a["next_season"],
                            "top_region": a["top_region"], "grand_total": a["grand_total"],
                            "trend": a["trend"], "heat": a["heat"], "seasons": a["seasons"]},
                           ensure_ascii=False)
    return render_template("analytics.html", title="Tahlil & Bashorat", page="analytics",
                           a=a, maxheat=maxheat, data_json=data_json)


@app.route("/analytics/upload", methods=["POST"])
def analytics_upload():
    f = request.files.get("file")
    if f:
        try:
            ingest_csv(f.read().decode("utf-8-sig", errors="ignore"))
        except Exception as e:
            print(f"[Analytics] CSV yuklash xatosi: {e}")
    return redirect(url_for("analytics"))


@app.route("/analytics/reset", methods=["POST"])
def analytics_reset():
    reset_data()
    return redirect(url_for("analytics"))


# =================== AI yordamchi (3-modul) ===================
@app.route("/assistant")
def assistant():
    return render_template("assistant.html", title="AI yordamchi", page="assistant")


@app.route("/assistant/chat", methods=["POST"])
def assistant_chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"reply": "Iltimos, vaziyatni yozing.", "mode": "rule"})
    return jsonify(chat_reply(msg, data.get("history") or []))


if __name__ == "__main__":
    print("=" * 54)
    print("  ASAS Dashboard:  http://localhost:5000")
    print("=" * 54)
    app.run(host="127.0.0.1", port=5000, threaded=True, debug=False)
