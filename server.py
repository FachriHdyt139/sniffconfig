# Sniff Config — web decryptor multi-format (HC/EHI/SSC/NPV/NPVT/DARK)
# Engine: ENIGMATIC-MAN/DECRYPTION_SCRIPTS (MIT) | Watermark: @BleackCoderr
import os, json, time
from flask import Flask, request, jsonify, render_template, send_from_directory

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))
import HTTPCUSTOM, HTTPINJECTOR, NPVTUNNEL, SSCCUSTOM, DARKTUNNEL

app = Flask(__name__, static_folder="static")
STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")

# --- daftar parser per format (urut = prioritas deteksi) ---
PARSERS = [
    ("HC",   HTTPCUSTOM.run),
    ("EHI",  HTTPINJECTOR.run),
    ("NPVT", NPVTUNNEL.run),
    ("SSC",  SSCCUSTOM.run),
    ("DARK", DARKTUNNEL.run),
]

def load_stats():
    try:
        return json.load(open(STATS_FILE))
    except Exception:
        return {"total": 0, "success": 0, "failed": 0}

def save_stats(s):
    try:
        json.dump(s, open(STATS_FILE, "w"))
    except Exception:
        pass

def detect_by_ext(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "hc": "HC", "ehi": "EHI",
        "npv": "NPVT", "npvt": "NPVT",
        "ssc": "SSC", "dark": "DARK",
    }.get(ext)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/robots.txt")
def robots():
    host = request.host_url.rstrip("/")
    return f"User-agent: *\nAllow: /\nSitemap: {host}/sitemap.xml\n", 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap():
    host = request.host_url.rstrip("/")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{host}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
</urlset>""", 200, {"Content-Type": "application/xml"}

@app.route("/api/stats")
def stats():
    return jsonify(load_stats())

@app.route("/api/decrypt", methods=["POST"])
def decrypt():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No file selected."})

    data = f.read()
    if len(data) == 0:
        return jsonify({"ok": False, "error": "File kosong."})
    if len(data) > 5 * 1024 * 1024:
        return jsonify({"ok": False, "error": "File terlalu besar (maks 5MB)."})

    stats = load_stats()
    stats["total"] += 1

    # 1) coba sesuai ekstensi dulu, 2) sisanya fallback auto-detect
    hint = detect_by_ext(f.filename)
    order = ([p for p in PARSERS if p[0] == hint] +
             [p for p in PARSERS if p[0] != hint])

    for fmt, fn in order:
        try:
            result = fn(data)
        except Exception:
            result = None
        if result:
            stats["success"] += 1
            save_stats(stats)
            return jsonify({
                "ok": True,
                "format": fmt,
                "filename": f.filename,
                "result": result,
                "watermark": "@BleackCoderr",
                "tg": "https://t.me/BleackCoderr",
            })

    stats["failed"] += 1
    save_stats(stats)
    return jsonify({"ok": False, "error": "Format tidak dikenali / config terkunci versi baru."})

if __name__ == "__main__":
    # Render ngasih port lewat env var PORT; lokal default 3000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
