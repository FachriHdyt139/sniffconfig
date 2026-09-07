# Integrasi v3.1: tombol UNLOCK HC di bot + webhook unlock dari web (statis)
import os, sys, time, base64, json, threading, urllib.request, urllib.parse

BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE, "engine"))

LOCK = threading.Lock()

def unlock_hc_file(data: bytes) -> bytes:
    """Bungkus engine HC_UNLOCK dengan lock thread (engine modul-global)."""
    with LOCK:
        import HC_UNLOCK
        return HC_UNLOCK.unlock_hc(data)

def register(server_mod):
    """Tambah route POST /api/unlock-hc di server Flask."""
    from flask import request, jsonify, send_file
    import io

    @server_mod.app.route("/api/unlock-hc", methods=["POST"])
    def unlock_hc_route():
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "No file selected."})
        data = f.read()
        if not data: return jsonify({"ok": False, "error": "File kosong."})
        if len(data) > 5 * 1024 * 1024:
            return jsonify({"ok": False, "error": "File terlalu besar (maks 5MB)."})
        try:
            out = unlock_hc_file(data)
        except ValueError as e:
            return jsonify({"ok": False, "error": f"Format nggak didukung: {e}"})
        except Exception:
            return jsonify({"ok": False, "error": "Unlock gagal — config pakai key non-standar."})
        buf = io.BytesIO(out)
        name = f.filename.rsplit(".", 1)[0] + ".unlocked.hc"
        return send_file(buf, as_attachment=True, download_name=name,
                         mimetype="application/octet-stream")
    print("unlock: route /api/unlock-hc terpasang ✅", flush=True)
