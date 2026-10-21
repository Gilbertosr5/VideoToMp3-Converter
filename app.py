from __future__ import annotations

import ipaddress
import os
import re
import socket
import sqlite3
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import imageio_ffmpeg
import yt_dlp
from flask import Flask, abort, jsonify, render_template, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "history.sqlite3"
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # request body limit

tasks: dict[str, dict] = {}
tasks_lock = threading.Lock()
ALLOWED_BITRATES = {"128", "192", "320"}


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                bitrate TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT
            )
        """)


def validate_url(raw_url: str) -> str:
    """Accept public HTTP(S) URLs only; reject local/private destinations."""
    value = (raw_url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Informe um link HTTP ou HTTPS válido.")
    if parsed.username or parsed.password:
        raise ValueError("Links com usuário/senha embutidos não são aceitos.")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise ValueError("Links para endereços locais não são aceitos.")

    # If the hostname resolves to a private, loopback, link-local, or reserved IP,
    # reject it. Use only links you trust; redirects are ultimately controlled by the source.
    try:
        results = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        for result in results:
            ip = ipaddress.ip_address(result[4][0].split("%")[0])
            if not ip.is_global:
                raise ValueError("O link aponta para um endereço de rede privado ou reservado.")
    except socket.gaierror:
        # Some extractor-supported URLs may resolve through the extractor's own logic.
        # A hostname that cannot resolve locally is still passed to yt-dlp.
        pass
    return value


def set_task(task_id: str, **updates):
    with tasks_lock:
        if task_id in tasks:
            tasks[task_id].update(updates)


def worker(task_id: str, url: str, bitrate: str):
    output_template = str(DOWNLOAD_DIR / f"{task_id}-%(title).150B.%(ext)s")
    task_title = "Processando link"
    final_file = None

    def progress_hook(data):
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            percent = round(downloaded * 100 / total, 1) if total else None
            set_task(
                task_id,
                state="downloading",
                progress=percent,
                downloaded=downloaded,
                total=total,
                speed=data.get("speed"),
                eta=data.get("eta"),
                message="Baixando mídia…",
            )
        elif status == "finished":
            set_task(task_id, state="converting", progress=100, message="Convertendo para MP3…")

    def postprocessor_hook(data):
        set_task(task_id, state="converting", message="Convertendo áudio para MP3…")

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": FFMPEG_PATH,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate,
        }],
        "restrictfilenames": True,
        "windowsfilenames": True,
        "socket_timeout": 20,
        "retries": 2,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            task_title = info.get("title") or "Áudio convertido"

        # The task ID is the prefix, so locate the generated MP3 safely.
        matches = list(DOWNLOAD_DIR.glob(f"{task_id}-*.mp3"))
        if not matches:
            raise RuntimeError("A conversão terminou, mas o arquivo MP3 não foi localizado.")
        final_file = max(matches, key=lambda p: p.stat().st_mtime)
        filename = final_file.name

        with db_connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO history
                (id, source_url, title, filename, bitrate, created_at, status, error)
                VALUES (?, ?, ?, ?, ?, ?, 'completed', NULL)
            """, (task_id, url, task_title, filename, bitrate, datetime.now().astimezone().isoformat(timespec="seconds")))

        set_task(task_id, state="completed", progress=100, title=task_title,
                 filename=filename, message="Conversão concluída.")
    except Exception as exc:
        message = str(exc).strip() or "Falha desconhecida."
        # Keep UI errors useful but avoid dumping a full traceback.
        if len(message) > 500:
            message = message[:500] + "…"
        with db_connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO history
                (id, source_url, title, filename, bitrate, created_at, status, error)
                VALUES (?, ?, ?, '', ?, ?, 'failed', ?)
            """, (task_id, url, task_title, bitrate, datetime.now().astimezone().isoformat(timespec="seconds"), message))
        set_task(task_id, state="failed", message=message, error=message)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/convert")
def start_conversion():
    payload = request.get_json(silent=True) or {}
    try:
        url = validate_url(payload.get("url", ""))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    bitrate = str(payload.get("bitrate", "192"))
    if bitrate not in ALLOWED_BITRATES:
        return jsonify({"error": "Escolha uma qualidade válida: 128, 192 ou 320 kbps."}), 400

    task_id = uuid.uuid4().hex
    with tasks_lock:
        tasks[task_id] = {
            "id": task_id, "state": "queued", "progress": 0,
            "message": "Na fila…", "title": None, "filename": None,
            "created_at": time.time()
        }

    thread = threading.Thread(target=worker, args=(task_id, url, bitrate), daemon=True)
    thread.start()
    return jsonify({"id": task_id}), 202


@app.get("/api/tasks/<task_id>")
def task_status(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            abort(404)
        result = dict(task)
    return jsonify(result)


@app.get("/api/history")
def history():
    with db_connect() as conn:
        rows = conn.execute("""
            SELECT id, source_url, title, filename, bitrate, created_at, status, error
            FROM history ORDER BY created_at DESC LIMIT 100
        """).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/downloads/<path:filename>")
def download(filename):
    # send_from_directory prevents path traversal outside DOWNLOAD_DIR.
    if not re.fullmatch(r"[a-f0-9]{32}-.+\.mp3", filename, flags=re.IGNORECASE):
        abort(404)
    path = DOWNLOAD_DIR / filename
    if not path.is_file():
        abort(404)
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True, mimetype="audio/mpeg")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    print("\nConversor local iniciado: http://127.0.0.1:5000")
    print("Mantenha esta janela aberta enquanto usa o conversor.\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
