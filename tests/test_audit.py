"""Tests for envault.audit module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import record, get_log, clear_log, AUDIT_FILENAME


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_creates_audit_file(audit_dir):
    record("lock", actor="alice", directory=str(audit_dir))
    assert (audit_dir / AUDIT_FILENAME).exists()


def test_record_entry_fields(audit_dir):
    record("lock", actor="alice", directory=str(audit_dir), vault="prod")
    entries = get_log(directory=str(audit_dir))
    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "lock"
    assert entry["actor"] == "alice"
    assert entry["vault"] == "prod"
    assert "timestamp" in entry


def test_record_appends_multiple_entries(audit_dir):
    record("lock", actor="alice", directory=str(audit_dir))
    record("unlock", actor="bob", directory=str(audit_dir))
    record("push", actor="alice", directory=str(audit_dir))
    entries = get_log(directory=str(audit_dir))
    assert len(entries) == 3
    assert entries[0]["action"] == "lock"
    assert entries[1]["action"] == "unlock"
    assert entries[2]["action"] == "push"


def test_get_log_returns_empty_when_no_file(audit_dir):
    entries = get_log(directory=str(audit_dir))
    assert entries == []


def test_get_log_returns_empty_on_corrupt_file(audit_dir):
    audit_file = audit_dir / AUDIT_FILENAME
    audit_file.write_text("not valid json", encoding="utf-8")
    entries = get_log(directory=str(audit_dir))
    assert entries == []


def test_clear_log_removes_file(audit_dir):
    record("lock", actor="alice", directory=str(audit_dir))
    clear_log(directory=str(audit_dir))
    assert not (audit_dir / AUDIT_FILENAME).exists()


def test_clear_log_no_error_when_missing(audit_dir):
    # Should not raise even if file doesn't exist
    clear_log(directory=str(audit_dir))


def test_record_uses_env_user_as_default_actor(audit_dir, monkeypatch):
    monkeypatch.setenv("USER", "ci-bot")
    record("pull", directory=str(audit_dir))
    entries = get_log(directory=str(audit_dir))
    assert entries[0]["actor"] == "ci-bot"


def test_audit_file_is_valid_json(audit_dir):
    record("lock", actor="alice", directory=str(audit_dir))
    raw = (audit_dir / AUDIT_FILENAME).read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, list)
