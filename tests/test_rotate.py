"""Tests for envault.rotate."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.rotate import rotate, RotationError


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_vault(directory: Path, passphrase: str, env_vars: dict) -> None:
    """Helper: create a real vault file for integration-style tests."""
    from envault.vault import lock
    lock(env_vars=env_vars, passphrase=passphrase, directory=directory)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_rotate_returns_variable_count(vault_dir: Path) -> None:
    env_vars = {"KEY1": "value1", "KEY2": "value2"}
    _make_vault(vault_dir, "old-pass", env_vars)

    count = rotate("old-pass", "new-pass", directory=vault_dir)

    assert count == 2


def test_rotate_vault_decryptable_with_new_passphrase(vault_dir: Path) -> None:
    env_vars = {"SECRET": "s3cr3t", "TOKEN": "tok"}
    _make_vault(vault_dir, "old-pass", env_vars)

    rotate("old-pass", "new-pass", directory=vault_dir)

    from envault.vault import unlock
    result = unlock(passphrase="new-pass", directory=vault_dir)
    assert result == env_vars


def test_rotate_old_passphrase_no_longer_works(vault_dir: Path) -> None:
    _make_vault(vault_dir, "old-pass", {"A": "1"})
    rotate("old-pass", "new-pass", directory=vault_dir)

    from envault.vault import unlock
    with pytest.raises(Exception):
        unlock(passphrase="old-pass", directory=vault_dir)


def test_rotate_records_audit_entry(vault_dir: Path) -> None:
    _make_vault(vault_dir, "pass", {"X": "y"})

    rotate("pass", "new-pass", directory=vault_dir)

    from envault.audit import get_log
    entries = get_log(directory=vault_dir)
    assert any(e["action"] == "rotate" for e in entries)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_rotate_raises_when_no_vault(vault_dir: Path) -> None:
    with pytest.raises(RotationError, match="[Vv]ault"):
        rotate("pass", "new-pass", directory=vault_dir)


def test_rotate_raises_on_wrong_old_passphrase(vault_dir: Path) -> None:
    _make_vault(vault_dir, "correct-pass", {"K": "v"})

    with pytest.raises(RotationError):
        rotate("wrong-pass", "new-pass", directory=vault_dir)


def test_rotate_raises_when_lock_fails(vault_dir: Path) -> None:
    _make_vault(vault_dir, "pass", {"K": "v"})

    with patch("envault.rotate.lock", side_effect=RuntimeError("disk full")):
        with pytest.raises(RotationError, match="re-encrypt"):
            rotate("pass", "new-pass", directory=vault_dir)
