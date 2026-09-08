# HC Unlocker v4 — "PLAIN-TOKEN SURGICAL" (2026-09-08)
# TEMUAN KUNCI (forensik file asli v645): field proteksi (lockAllConfig, blockedByHwid,
# expiryTime, dll) disimpan sebagai token TEKS POLOS di dalam xy — BUKAN terenkripsi.
# Engine unlock lama me-encrypt-ulang token2 itu -> app HC baca mentah -> "file tidak valid".
# Strategi v4: decrypt xy (ChaCha key[1], static nonce), ganti token polos sesuai posisi,
# re-encrypt xy dengan parameter IDENTIK, tulis ulang outer JSON persis gaya asli
# (indent=2, ensure_ascii=False), encode file dengan chain mojibake yang sama.
import base64, json

XOR_HEADER = "e382e4b8adc386f09f9293"

# posisi token -> nilai BARU (teks polos, sama gaya dgn aslinya)
UNLOCK_VALUES = {
    2:  "false",   # lockAllConfig
    5:  "true",    # noteEnabled
    6:  "\U0001F434 UNLOCKED by @BleackCoderr\nhttps://sniffconfig.onrender.com",  # notes
    15: "false",   # blockedByHwid
    19: "false",   # blockArea
    21: "false",   # blockedByPassword
}

def _abc_encrypt(plaintext: str, key: bytes, nonce: bytes) -> str:
    from Crypto.Cipher import ChaCha20
    cipher = ChaCha20.new(key=key, nonce=nonce)
    cipher.seek(64)
    return (cipher.encrypt(plaintext.encode()) + bytes(16)).hex()

def unlock_hc(original_file: bytes) -> bytes:
    """Surgical v4: token polos diganti polos, kriptografi tidak disentuh sama sekali."""
    import HTTPCUSTOM as HC
    d = HC.HCDecryptor
    K = HC.HCConstants

    hex_payload = d._extract_initial_payload(original_file, XOR_HEADER)
    if not hex_payload:
        raise ValueError("header file bukan .hc")
    outer = d._abc_decrypt(hex_payload, K.CHACHA_KEYS[5])
    if not outer or not outer.startswith("{"):
        raise ValueError("decrypt luar gagal")
    j = json.loads(outer)

    a = j.get("a") if isinstance(j.get("a"), dict) else {}
    xy_cipher = a.get("xy") or j.get("xy")
    split = a.get("uv") or j.get("uv")
    if not xy_cipher or not split:
        raise ValueError("struktur file bukan format HC lama (a.xy/a.uv tidak ada)")

    # decrypt xy pakai parameter PERSIS seperti engine baca (key[1] + static nonce)
    xy_dec = d._abc_decrypt(str(xy_cipher), K.CHACHA_KEYS[1])
    if not xy_dec:
        raise ValueError("isi config tidak ke-decrypt")
    tokens = xy_dec.split(str(split))
    if len(tokens) < 22:
        raise ValueError(f"jumlah token aneh ({len(tokens)}) — bukan HC standar")

    # verifikasi token yang mau diubah memang teks polos (bukan hex/base64)
    import re
    for i in UNLOCK_VALUES:
        if i < len(tokens) and tokens[i] and re.fullmatch(r"[0-9a-fA-F]{32,}", tokens[i]):
            raise ValueError(f"token posisi {i} terenkripsi — file varian baru, lapor @BleackCoderr")

    for i, new_val in UNLOCK_VALUES.items():
        if i < len(tokens):
            tokens[i] = new_val
    # expiryTime (4) biarkan apa adanya kalau sudah lifeTime; kalau angka/iso -> lifeTime
    if len(tokens) > 4 and tokens[4] and tokens[4] != "lifeTime":
        tokens[4] = "lifeTime"

    new_xy = str(split).join(tokens)
    # re-encrypt dengan key+nonce IDENTIK -> app HC decrypt normal, token polos terbaca
    a["xy"] = _abc_encrypt(new_xy, K.CHACHA_KEYS[1], K.STATIC_NONCE)

    # outer JSON: gaya penulisan sama persis dgn file asli (pretty indent=2)
    outer_json = json.dumps(j, indent=2, ensure_ascii=False)
    hex_outer = _abc_encrypt(outer_json, K.CHACHA_KEYS[5], K.STATIC_NONCE)
    key_bytes = bytes.fromhex(XOR_HEADER)
    xored = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(hex_outer.encode("utf-8")))
    return xored.decode("latin-1").encode("utf-8")
