"""Tests for envault.cli_snapshot."""

from __future__ import annotations

import argparse

import pytest

from envault.cli_snapshot import register_snapshot_commands
from envault.snapshot import save_snapshot
from envault.vault import lock

PASSPHRASE = "cli-snap-pass"


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    register_snapshot_commands(sub)
    return p


@pytest.fixture()
def vault_dir(tmp_path):
    env = {"FOO": "bar", "BAZ": "qux"}
    lock(env, PASSPHRASE, directory=str(tmp_path))
    return tmp_path


def test_register_creates_snapshot_subcommand(parser):
    args = parser.parse_args(["snapshot", "list", "--dir", "."])
    assert args.command == "snapshot"


def test_cmd_snapshot_save(vault_dir, capsys):
    args_ns = argparse.Namespace(
        name="snap1",
        passphrase=PASSPHRASE,
        dir=str(vault_dir),
        file=".env.vault",
        func=None,
    )
    from envault.cli_snapshot import cmd_snapshot_save
    cmd_snapshot_save(args_ns)
    captured = capsys.readouterr()
    assert "snap1" in captured.out
    assert "2 variable(s)" in captured.out


def test_cmd_snapshot_list_empty(tmp_path, capsys):
    args_ns = argparse.Namespace(dir=str(tmp_path))
    from envault.cli_snapshot import cmd_snapshot_list
    cmd_snapshot_list(args_ns)
    captured = capsys.readouterr()
    assert "No snapshots" in captured.out


def test_cmd_snapshot_list_shows_names(vault_dir, capsys):
    save_snapshot("release-a", PASSPHRASE, directory=str(vault_dir))
    args_ns = argparse.Namespace(dir=str(vault_dir))
    from envault.cli_snapshot import cmd_snapshot_list
    cmd_snapshot_list(args_ns)
    captured = capsys.readouterr()
    assert "release-a" in captured.out


def test_cmd_snapshot_restore(vault_dir, capsys):
    save_snapshot("v1", PASSPHRASE, directory=str(vault_dir))
    lock({"ONLY": "this"}, PASSPHRASE, directory=str(vault_dir))
    args_ns = argparse.Namespace(
        name="v1",
        passphrase=PASSPHRASE,
        dir=str(vault_dir),
        file=".env.vault",
    )
    from envault.cli_snapshot import cmd_snapshot_restore
    cmd_snapshot_restore(args_ns)
    captured = capsys.readouterr()
    assert "restored" in captured.out


def test_cmd_snapshot_delete(vault_dir, capsys):
    save_snapshot("temp", PASSPHRASE, directory=str(vault_dir))
    args_ns = argparse.Namespace(name="temp", dir=str(vault_dir))
    from envault.cli_snapshot import cmd_snapshot_delete
    cmd_snapshot_delete(args_ns)
    captured = capsys.readouterr()
    assert "deleted" in captured.out


def test_cmd_snapshot_restore_missing_exits(vault_dir):
    args_ns = argparse.Namespace(
        name="no-such-snap",
        passphrase=PASSPHRASE,
        dir=str(vault_dir),
        file=".env.vault",
    )
    from envault.cli_snapshot import cmd_snapshot_restore
    with pytest.raises(SystemExit):
        cmd_snapshot_restore(args_ns)
