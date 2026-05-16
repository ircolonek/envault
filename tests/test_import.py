"""Tests for envault.import_env and envault.cli_import."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.import_env import parse_dotenv, import_env, ImportError as EnvImportError
from envault.vault import unlock
from envault.cli_import import cmd_import, register_import_commands


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_dotenv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# parse_dotenv
# ---------------------------------------------------------------------------

def test_parse_dotenv_basic(tmp_dir: Path) -> None:
    f = _write_dotenv(tmp_dir / ".env", "FOO=bar\nBAZ=qux\n")
    assert parse_dotenv(f) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_dotenv_strips_quotes(tmp_dir: Path) -> None:
    f = _write_dotenv(tmp_dir / ".env", 'KEY="hello world"\n')
    assert parse_dotenv(f)["KEY"] == "hello world"


def test_parse_dotenv_skips_comments_and_blanks(tmp_dir: Path) -> None:
    content = "# comment\n\nA=1\n"
    f = _write_dotenv(tmp_dir / ".env", content)
    result = parse_dotenv(f)
    assert result == {"A": "1"}


def test_parse_dotenv_value_with_equals(tmp_dir: Path) -> None:
    f = _write_dotenv(tmp_dir / ".env", "URL=http://x.com?a=1&b=2\n")
    assert parse_dotenv(f)["URL"] == "http://x.com?a=1&b=2"


def test_parse_dotenv_missing_file(tmp_dir: Path) -> None:
    with pytest.raises(EnvImportError):
        parse_dotenv(tmp_dir / "nonexistent.env")


# ---------------------------------------------------------------------------
# import_env
# ---------------------------------------------------------------------------

def test_import_env_creates_vault(tmp_dir: Path) -> None:
    f = _write_dotenv(tmp_dir / ".env", "SECRET=abc\n")
    count = import_env(f, "pass", directory=tmp_dir)
    assert count == 1
    env = unlock("pass", directory=tmp_dir)
    assert env["SECRET"] == "abc"


def test_import_env_merge_no_overwrite(tmp_dir: Path) -> None:
    from envault.vault import lock
    lock({"SECRET": "original"}, "pass", directory=tmp_dir)
    f = _write_dotenv(tmp_dir / ".env", "SECRET=new\nEXTRA=yes\n")
    import_env(f, "pass", directory=tmp_dir, overwrite=False)
    env = unlock("pass", directory=tmp_dir)
    assert env["SECRET"] == "original"  # not overwritten
    assert env["EXTRA"] == "yes"


def test_import_env_merge_with_overwrite(tmp_dir: Path) -> None:
    from envault.vault import lock
    lock({"SECRET": "original"}, "pass", directory=tmp_dir)
    f = _write_dotenv(tmp_dir / ".env", "SECRET=new\n")
    import_env(f, "pass", directory=tmp_dir, overwrite=True)
    env = unlock("pass", directory=tmp_dir)
    assert env["SECRET"] == "new"


def test_import_env_empty_file_returns_zero(tmp_dir: Path) -> None:
    f = _write_dotenv(tmp_dir / ".env", "# only comments\n")
    assert import_env(f, "pass", directory=tmp_dir) == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_import_commands(sub)
    return p


def test_register_creates_import_subcommand(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args(["import", "my.env", "--passphrase", "s"])
    assert args.source == "my.env"
    assert args.passphrase == "s"
    assert args.overwrite is False


def test_cmd_import_prints_count(tmp_dir: Path, capsys: pytest.CaptureFixture) -> None:
    f = _write_dotenv(tmp_dir / ".env", "K=V\n")
    args = argparse.Namespace(
        source=str(f), passphrase="pw", dir=str(tmp_dir), overwrite=False
    )
    cmd_import(args)
    out = capsys.readouterr().out
    assert "Imported" in out


def test_cmd_import_missing_file_exits(tmp_dir: Path) -> None:
    args = argparse.Namespace(
        source=str(tmp_dir / "missing.env"), passphrase="pw", dir=str(tmp_dir), overwrite=False
    )
    with pytest.raises(SystemExit):
        cmd_import(args)
