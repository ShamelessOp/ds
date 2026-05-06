"""
SaaS Cloud Storage Controller
==============================
Mini-project for Cloud Computing (SPPU BE CS Sem VI)
Implements HDFS-style chunking + AES encryption over LAN.

Run:  python app.py
Open: http://localhost:5000
"""

import os
import json
import math
import hashlib
import base64
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_file, abort
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend

# ─── Config ────────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 1 * 1024 * 1024          # 1 MB per chunk (like HDFS block)
STORAGE_ROOT  = Path("cloud_storage")    # simulated HDFS datanode root
META_FILE     = STORAGE_ROOT / "metadata.json"
SECRET_KEY    = b"SpPuClOuD2024!@#"     # 16-byte AES key (change in prod)
IV            = b"InitVector123456"      # 16-byte IV  (change in prod)

STORAGE_ROOT.mkdir(exist_ok=True)

# ─── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1000 * 1024 * 1024   # 1000 MB max upload


# ─── Metadata helpers ──────────────────────────────────────────────────────────
def load_meta() -> dict:
    if META_FILE.exists():
        with open(META_FILE) as f:
            return json.load(f)
    return {}

def save_meta(meta: dict):
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)


# ─── Encryption helpers ────────────────────────────────────────────────────────
def encrypt_bytes(data: bytes) -> bytes:
    """AES-CBC encrypt with PKCS7 padding."""
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(IV), backend=default_backend())
    enc = cipher.encryptor()
    return enc.update(padded) + enc.finalize()

def decrypt_bytes(data: bytes) -> bytes:
    """AES-CBC decrypt and unpad."""
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(IV), backend=default_backend())
    dec = cipher.decryptor()
    padded = dec.update(data) + dec.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


# ─── HDFS-style chunking ───────────────────────────────────────────────────────
def split_and_store(file_bytes: bytes, filename: str) -> dict:
    """
    Divide file into CHUNK_SIZE blocks, encrypt each block,
    store as separate files. Returns metadata dict.
    """
    total_size  = len(file_bytes)
    num_chunks  = math.ceil(total_size / CHUNK_SIZE)
    file_id     = hashlib.md5(f"{filename}{datetime.now()}".encode()).hexdigest()[:12]
    chunk_dir   = STORAGE_ROOT / file_id
    chunk_dir.mkdir(exist_ok=True)

    chunk_names = []
    for i in range(num_chunks):
        chunk_data    = file_bytes[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
        enc_chunk     = encrypt_bytes(chunk_data)
        chunk_file    = chunk_dir / f"chunk_{i:04d}.bin"
        chunk_file.write_bytes(enc_chunk)
        chunk_names.append(chunk_file.name)

    meta_entry = {
        "file_id"    : file_id,
        "filename"   : filename,
        "size"       : total_size,
        "num_chunks" : num_chunks,
        "chunk_size" : CHUNK_SIZE,
        "chunks"     : chunk_names,
        "uploaded_at": datetime.now().isoformat(),
        "checksum"   : hashlib.md5(file_bytes).hexdigest(),
    }
    return meta_entry


def reassemble(file_id: str) -> bytes:
    """Decrypt and reassemble all chunks for a file."""
    meta = load_meta()
    if file_id not in meta:
        raise KeyError("File not found")
    entry     = meta[file_id]
    chunk_dir = STORAGE_ROOT / file_id
    result    = b""
    for name in entry["chunks"]:
        enc_chunk = (chunk_dir / name).read_bytes()
        result   += decrypt_bytes(enc_chunk)
    return result


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    file_bytes = f.read()

    if file_bytes == b"":
        return jsonify({"error": "Empty file not allowed"}), 400
    if len(file_bytes) > app.config["MAX_CONTENT_LENGTH"]:
        return jsonify({"error": "File too large"}), 400

    meta_entry = split_and_store(file_bytes, f.filename) # type: ignore

    meta = load_meta()
    meta[meta_entry["file_id"]] = meta_entry
    save_meta(meta)

    return jsonify({
        "success"    : True,
        "file_id"    : meta_entry["file_id"],
        "filename"   : meta_entry["filename"],
        "size"       : meta_entry["size"],
        "num_chunks" : meta_entry["num_chunks"],
        "checksum"   : meta_entry["checksum"],
        "uploaded_at": meta_entry["uploaded_at"],
    })


@app.route("/api/files", methods=["GET"])
def list_files():
    meta = load_meta()
    files = []
    for fid, entry in meta.items():
        files.append({
            "file_id"    : fid,
            "filename"   : entry["filename"],
            "size"       : entry["size"],
            "num_chunks" : entry["num_chunks"],
            "uploaded_at": entry["uploaded_at"],
            "checksum"   : entry["checksum"],
        })
    files.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return jsonify(files)


@app.route("/api/download/<file_id>", methods=["GET"])
def download(file_id):
    meta = load_meta()
    if file_id not in meta:
        abort(404)
    entry = meta[file_id]
    try:
        data = reassemble(file_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # write to a temp file then send
    tmp = STORAGE_ROOT / f"_tmp_{file_id}"
    tmp.write_bytes(data)
    return send_file(
        str(tmp),
        as_attachment=True,
        download_name=entry["filename"]
    )


@app.route("/api/delete/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    meta = load_meta()
    if file_id not in meta:
        return jsonify({"error": "Not found"}), 404

    chunk_dir = STORAGE_ROOT / file_id
    if chunk_dir.exists():
        shutil.rmtree(chunk_dir)

    del meta[file_id]
    save_meta(meta)
    return jsonify({"success": True})


@app.route("/api/info/<file_id>", methods=["GET"])
def file_info(file_id):
    meta = load_meta()
    if file_id not in meta:
        abort(404)
    return jsonify(meta[file_id])


@app.route("/api/stats", methods=["GET"])
def stats():
    meta = load_meta()
    total_files  = len(meta)
    total_bytes  = sum(e["size"] for e in meta.values())
    total_chunks = sum(e["num_chunks"] for e in meta.values())

    # Disk usage of storage root
    used = sum(
        f.stat().st_size
        for f in STORAGE_ROOT.rglob("*")
        if f.is_file()
    )
    return jsonify({
        "total_files" : total_files,
        "total_bytes" : total_bytes,
        "total_chunks": total_chunks,
        "disk_used"   : used,
        "chunk_size"  : CHUNK_SIZE,
    })


if __name__ == "__main__":
    print("=" * 55)
    print("  SaaS Cloud Controller — SPPU CC Mini Project")
    print("  http://localhost:5000")
    print("  Share on LAN: http://<your-ip>:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=True)
