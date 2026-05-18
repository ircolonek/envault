"""Tests for envault.snapshot."""

from __future__ import annotations

import json
import time

import pytest

from envault.snapshot import (
    SnapshotError,
    _snapshot_path,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)
from envault.vault import lock

PASSPHRASE = "test-passphrase-123"


@pytest.fixture()
def vault_dir(tmp_path):
    env = {"API_KEY": "abc123", "DB_URL": "postgres://localhost/db"}
    lock(env, PASSPHRASE, directory=str(tmp_path))
    return tmp_path


def test_save_snapshot_returns_variable_count(vault_dir):
    count = save_snapshot("v1", PASSPHRASE, directory=str(vault_dir))
    assert count == 2


def test_save_snapshot_creates_file(vault_dir):
    save_snapshot("release-1", PASSPHRASE, directory=str(vault_dir))
    path = _snapshot_path("release-1", directory=str(vault_dir))
    assert path.exists()


def test_save_snapshot_file_contains_variables(vault_dir):
    save_snapshot("v1", PASSPHRASE, directory=str(vault_dir))
    path = _snapshot_path("v1", directory=str(vault_dir))
    data = json.loads(path.read_text())
    assert data["variables"]["API_KEY"] == "abc123"
    assert data["variables"]["DB_URL"] == "postgres://localhost/db"


def test_save_snapshot_records_name_and_timestamp(vault_dir):
    before = time.time()
    save_snapshot("v1", PASSPHRASE, directory=str(vault_dir))
    after = time.time()
    path = _snapshot_path("v1", directory=str(vault_dir))
    data = json.loads(path.read_text())
    assert data["name"] == "v1"
    assert before <= data["created_at"] <= after


def test_restore_snapshot_overwrites_vault(vault_dir):
    save_snapshot("v1", PASSPHRASE, directory=str(vault_dir))
    # Overwrite vault with different data
    lock({"NEW_KEY": "new_value"}, PASSPHRASE, directory=str(vault_dir))
    restored = restore_snapshot("v1", PASSPHRASE, directory=str(vault_dir))
    assert restored == 2
    from envault.vault import unlock
    env = unlock(PASSPHRASE, directory=str(vault_dir))
    assert env["API_KEY"] == "abc123"
    assert "NEW_KEY" not in env


def test_restore_snapshot_missing_raises(vault_dir):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot("nonexistent", PASSPHRASE, directory=str(vault_dir))


def test_list_snapshots_empty_when_none(tmp_path):
    assert list_snapshots(directory=str(tmp_path)) == []


def test_list_snapshots_returns_entries(vault_dir):
    save_snapshot("alpha", PASSPHRASE, directory=str(vault_dir))
    save_snapshot("beta", PASSPHRASE, directory=str(vault_dir))
    entries = list_snapshots(directory=str(vault_dir))
    names = [e["name"] for e in entries]
    assert "alpha" in names
    assert "beta" in names


def test_list_snapshots_sorted_by_time(vault_dir):
    save_snapshot("first", PASSPHRASE, directory=str(vault_dir))
    time.sleep(0.05)
    save_snapshot("second", PASSPHRASE, directory=str(vault_dir))
    entries = list_snapshots(directory=str(vault_dir))
    assert entries[0]["name"] == "first"
    assert entries[1]["name"] == "second"


def test_delete_snapshot_removes_file(vault_dir):
    save_snapshot("to-delete", PASSPHRASE, directory=str(vault_dir))
    delete_snapshot("to-delete", directory=str(vault_dir))
    assert not _snapshot_path("to-delete", directory=str(vault_dir)).exists()


def test_delete_snapshot_missing_raises(vault_dir):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot("ghost", directory=str(vault_dir))
