"""Tests for the high-level envault.vault module."""

import pytest
from cryptography.fernet import InvalidToken

from envault.vault import _deserialize, _serialize, is_locked, lock, unlock

SAMPLE_ENV = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "SECRET_KEY": "supersecret",
    "DEBUG": "false",
}
PASSPHRASE = "correct-horse-battery-staple"


def test_serialize_deserialize_roundtrip():
    text = _serialize(SAMPLE_ENV)
    result = _deserialize(text)
    assert result == SAMPLE_ENV


def test_serialize_sorts_keys():
    text = _serialize({"Z": "last", "A": "first"})
    assert text.index("A=") < text.index("Z=")


def test_deserialize_ignores_blank_lines():
    text = "\nFOO=bar\n\nBAZ=qux\n"
    assert _deserialize(text) == {"FOO": "bar", "BAZ": "qux"}


def test_deserialize_value_with_equals_sign():
    text = "TOKEN=abc=def=ghi"
    assert _deserialize(text) == {"TOKEN": "abc=def=ghi"}


def test_lock_creates_vault_file(tmp_path):
    path = lock(SAMPLE_ENV, PASSPHRASE, directory=str(tmp_path))
    assert path.exists()
    assert path.name == ".envault"


def test_lock_unlock_roundtrip(tmp_path):
    lock(SAMPLE_ENV, PASSPHRASE, directory=str(tmp_path))
    recovered = unlock(PASSPHRASE, directory=str(tmp_path))
    assert recovered == SAMPLE_ENV


def test_unlock_wrong_passphrase_raises(tmp_path):
    lock(SAMPLE_ENV, PASSPHRASE, directory=str(tmp_path))
    with pytest.raises(InvalidToken):
        unlock("wrong-passphrase", directory=str(tmp_path))


def test_unlock_missing_vault_raises(tmp_path):
    from envault.storage import VaultNotFoundError
    with pytest.raises(VaultNotFoundError):
        unlock(PASSPHRASE, directory=str(tmp_path))


def test_is_locked_false_before_lock(tmp_path):
    assert is_locked(directory=str(tmp_path)) is False


def test_is_locked_true_after_lock(tmp_path):
    lock(SAMPLE_ENV, PASSPHRASE, directory=str(tmp_path))
    assert is_locked(directory=str(tmp_path)) is True
