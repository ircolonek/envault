"""Tests for envault.storage module."""

import json
import pytest
from pathlib import Path

from envault.storage import (
    VaultCorruptedError,
    VaultNotFoundError,
    get_vault_path,
    read_vault,
    vault_exists,
    write_vault,
)


def test_get_vault_path_defaults_to_cwd():
    path = get_vault_path()
    assert path.name == ".envault"
    assert path.parent == Path.cwd()


def test_get_vault_path_with_directory(tmp_path):
    path = get_vault_path(directory=str(tmp_path))
    assert path == tmp_path / ".envault"


def test_write_and_read_vault_roundtrip(tmp_path):
    vault_path = tmp_path / ".envault"
    ciphertext = "abc123encryptedpayload=="
    write_vault(ciphertext, vault_path)
    assert vault_path.exists()
    recovered = read_vault(vault_path)
    assert recovered == ciphertext


def test_write_vault_creates_parent_dirs(tmp_path):
    nested_path = tmp_path / "a" / "b" / ".envault"
    write_vault("payload", nested_path)
    assert nested_path.exists()


def test_write_vault_stores_valid_json(tmp_path):
    vault_path = tmp_path / ".envault"
    write_vault("some_cipher", vault_path)
    data = json.loads(vault_path.read_text())
    assert data["version"] == 1
    assert data["ciphertext"] == "some_cipher"


def test_read_vault_raises_if_missing(tmp_path):
    with pytest.raises(VaultNotFoundError):
        read_vault(tmp_path / "nonexistent.envault")


def test_read_vault_raises_on_invalid_json(tmp_path):
    bad_file = tmp_path / ".envault"
    bad_file.write_text("not json at all", encoding="utf-8")
    with pytest.raises(VaultCorruptedError, match="not valid JSON"):
        read_vault(bad_file)


def test_read_vault_raises_on_missing_ciphertext_key(tmp_path):
    bad_file = tmp_path / ".envault"
    bad_file.write_text(json.dumps({"version": 1}), encoding="utf-8")
    with pytest.raises(VaultCorruptedError, match="missing 'ciphertext'"):
        read_vault(bad_file)


def test_vault_exists_true(tmp_path):
    vault_path = tmp_path / ".envault"
    write_vault("payload", vault_path)
    assert vault_exists(vault_path) is True


def test_vault_exists_false(tmp_path):
    assert vault_exists(tmp_path / ".envault") is False
