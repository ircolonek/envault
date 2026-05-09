"""Encryption and decryption utilities for envault using AES-256-GCM."""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


NONCE_SIZE = 12  # 96-bit nonce recommended for GCM
KEY_SIZE = 32   # 256-bit key


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        iterations=600_000,
        dklen=KEY_SIZE,
    )


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext with the given passphrase.

    Returns a base64-encoded string: salt (16 bytes) + nonce (12 bytes) + ciphertext.
    """
    salt = os.urandom(16)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(encoded: str, passphrase: str) -> str:
    """Decrypt a base64-encoded payload produced by :func:`encrypt`.

    Raises:
        ValueError: If the payload is malformed or the passphrase is wrong.
    """
    try:
        payload = base64.b64decode(encoded.encode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid base64 payload.") from exc

    if len(payload) < 16 + NONCE_SIZE:
        raise ValueError("Payload is too short to be valid.")

    salt = payload[:16]
    nonce = payload[16:16 + NONCE_SIZE]
    ciphertext = payload[16 + NONCE_SIZE:]
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed. Wrong passphrase or corrupted data.") from exc
    return plaintext.decode("utf-8")
