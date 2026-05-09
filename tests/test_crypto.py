"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt, derive_key


PASSPHRASE = "super-secret-passphrase-123!"
SAMPLE_PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db\nSECRET_KEY=abc123"


def test_encrypt_returns_string():
    result = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_decrypt_roundtrip():
    token = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    recovered = decrypt(token, PASSPHRASE)
    assert recovered == SAMPLE_PLAINTEXT


def test_encrypt_produces_unique_ciphertexts():
    """Same plaintext encrypted twice should yield different ciphertexts (random nonce)."""
    token1 = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    token2 = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert token1 != token2


def test_decrypt_wrong_passphrase_raises():
    token = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, "wrong-passphrase")


def test_decrypt_corrupted_payload_raises():
    token = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    corrupted = token[:-4] + "AAAA"  # tamper with last bytes
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSPHRASE)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid base64"):
        decrypt("!!!not-base64!!!", PASSPHRASE)


def test_decrypt_too_short_payload_raises():
    import base64
    short = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short, PASSPHRASE)


def test_derive_key_length():
    key = derive_key(PASSPHRASE, b"saltsalt")
    assert len(key) == 32


def test_derive_key_deterministic():
    salt = b"fixed-salt-value"
    key1 = derive_key(PASSPHRASE, salt)
    key2 = derive_key(PASSPHRASE, salt)
    assert key1 == key2


def test_encrypt_empty_string():
    token = encrypt("", PASSPHRASE)
    assert decrypt(token, PASSPHRASE) == ""
