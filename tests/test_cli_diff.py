"""Tests for envault.cli_diff."""

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.cli_diff import cmd_diff, register_diff_commands
from envault.storage import VaultNotFoundError


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_diff_commands(sub)
    return p


def make_args(**kwargs):
    defaults = {
        "old": "/tmp/old.vault",
        "new": "/tmp/new.vault",
        "passphrase": "secret",
        "all": False,
        "summary": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_register_creates_diff_subcommand(parser):
    args = parser.parse_args(["diff", "a.vault", "b.vault", "-p", "pw"])
    assert args.old == "a.vault"
    assert args.new == "b.vault"
    assert args.passphrase == "pw"


def test_cmd_diff_no_changes(capsys):
    env = {"A": "1"}
    with patch("envault.cli_diff.unlock", return_value=env):
        cmd_diff(make_args())
    out = capsys.readouterr().out
    assert "No differences" in out


def test_cmd_diff_shows_added(capsys):
    with patch("envault.cli_diff.unlock", side_effect=[{}, {"NEW_KEY": "val"}]):
        cmd_diff(make_args())
    out = capsys.readouterr().out
    assert "+ NEW_KEY=val" in out


def test_cmd_diff_shows_summary(capsys):
    with patch("envault.cli_diff.unlock", side_effect=[{"A": "1"}, {"B": "2"}]):
        cmd_diff(make_args(summary=True))
    out = capsys.readouterr().out
    assert "Summary:" in out


def test_cmd_diff_vault_not_found_exits(capsys):
    with patch("envault.cli_diff.unlock", side_effect=VaultNotFoundError):
        with pytest.raises(SystemExit) as exc:
            cmd_diff(make_args())
    assert exc.value.code == 1


def test_parser_all_flag(parser):
    args = parser.parse_args(["diff", "a.vault", "b.vault", "-p", "pw", "--all"])
    assert args.all is True


def test_parser_summary_flag(parser):
    args = parser.parse_args(["diff", "a.vault", "b.vault", "-p", "pw", "--summary"])
    assert args.summary is True
