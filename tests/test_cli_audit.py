"""Tests for envault.cli_audit module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envault.audit import record, AUDIT_FILENAME
from envault.cli_audit import cmd_audit_log, cmd_audit_clear, register_audit_commands


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {"dir": None, "action": None, "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_audit_log_empty(audit_dir, capsys):
    cmd_audit_log(make_args(dir=str(audit_dir)))
    out = capsys.readouterr().out
    assert "No audit entries" in out


def test_cmd_audit_log_shows_entries(audit_dir, capsys):
    record("lock", actor="alice", directory=str(audit_dir))
    record("unlock", actor="bob", directory=str(audit_dir))
    cmd_audit_log(make_args(dir=str(audit_dir)))
    out = capsys.readouterr().out
    assert "alice" in out
    assert "lock" in out
    assert "bob" in out
    assert "unlock" in out


def test_cmd_audit_log_filter_by_action(audit_dir, capsys):
    record("lock", actor="alice", directory=str(audit_dir))
    record("push", actor="alice", directory=str(audit_dir))
    cmd_audit_log(make_args(dir=str(audit_dir), action="push"))
    out = capsys.readouterr().out
    assert "push" in out
    assert "lock" not in out


def test_cmd_audit_log_json_output(audit_dir, capsys):
    record("pull", actor="ci", directory=str(audit_dir))
    cmd_audit_log(make_args(dir=str(audit_dir), json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["action"] == "pull"


def test_cmd_audit_clear_removes_log(audit_dir, capsys):
    record("lock", actor="alice", directory=str(audit_dir))
    cmd_audit_clear(make_args(dir=str(audit_dir)))
    assert not (audit_dir / AUDIT_FILENAME).exists()
    out = capsys.readouterr().out
    assert "cleared" in out.lower()


def test_register_audit_commands_parses_log():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    register_audit_commands(subparsers)
    args = parser.parse_args(["audit", "log", "--action", "lock", "--json"])
    assert args.action == "lock"
    assert args.json is True


def test_register_audit_commands_parses_clear():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    register_audit_commands(subparsers)
    args = parser.parse_args(["audit", "clear", "--dir", "/tmp"])
    assert args.dir == "/tmp"
    assert args.func == cmd_audit_clear
