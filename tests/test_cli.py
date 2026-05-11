"""Tests for the envault CLI."""

import pytest
from unittest.mock import patch, mock_open, MagicMock

from envault.cli import build_parser, cmd_lock, cmd_unlock, cmd_status
from envault.storage import VaultNotFoundError, VaultCorruptedError


PASSPHRASE = "test-secret-passphrase"
ENV_CONTENT = "API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture
def parser():
    return build_parser()


def make_args(command, env_file=".env", directory=None):
    args = MagicMock()
    args.command = command
    args.env_file = env_file
    args.dir = directory
    return args


def test_parser_lock_defaults(parser):
    args = parser.parse_args(["lock"])
    assert args.command == "lock"
    assert args.env_file == ".env"
    assert args.dir is None


def test_parser_unlock_custom_file(parser):
    args = parser.parse_args(["unlock", "production.env"])
    assert args.command == "unlock"
    assert args.env_file == "production.env"


def test_parser_status(parser):
    args = parser.parse_args(["status"])
    assert args.command == "status"


def test_parser_with_dir_flag(parser):
    args = parser.parse_args(["--dir", "/tmp/project", "status"])
    assert args.dir == "/tmp/project"


def test_cmd_lock_success(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = make_args("lock", env_file=str(env_file), directory=str(tmp_path))

    with patch("envault.cli.getpass.getpass", side_effect=[PASSPHRASE, PASSPHRASE]), \
         patch("envault.cli.lock") as mock_lock:
        result = cmd_lock(args)

    assert result == 0
    mock_lock.assert_called_once_with(ENV_CONTENT, PASSPHRASE, directory=str(tmp_path))


def test_cmd_lock_passphrase_mismatch():
    args = make_args("lock")
    with patch("envault.cli.getpass.getpass", side_effect=["aaa", "bbb"]):
        result = cmd_lock(args)
    assert result == 1


def test_cmd_lock_missing_env_file():
    args = make_args("lock", env_file="/nonexistent/.env")
    with patch("envault.cli.getpass.getpass", side_effect=[PASSPHRASE, PASSPHRASE]):
        result = cmd_lock(args)
    assert result == 1


def test_cmd_unlock_success(tmp_path):
    args = make_args("unlock", env_file=str(tmp_path / ".env"), directory=str(tmp_path))
    with patch("envault.cli.getpass.getpass", return_value=PASSPHRASE), \
         patch("envault.cli.unlock", return_value=ENV_CONTENT) as mock_unlock:
        result = cmd_unlock(args)
    assert result == 0
    assert (tmp_path / ".env").read_text() == ENV_CONTENT


def test_cmd_unlock_vault_not_found():
    args = make_args("unlock")
    with patch("envault.cli.getpass.getpass", return_value=PASSPHRASE), \
         patch("envault.cli.unlock", side_effect=VaultNotFoundError):
        result = cmd_unlock(args)
    assert result == 1


def test_cmd_unlock_wrong_passphrase():
    args = make_args("unlock")
    with patch("envault.cli.getpass.getpass", return_value="wrong"), \
         patch("envault.cli.unlock", side_effect=ValueError("bad decrypt")):
        result = cmd_unlock(args)
    assert result == 1


def test_cmd_status_locked():
    args = make_args("status")
    with patch("envault.cli.is_locked", return_value=True):
        result = cmd_status(args)
    assert result == 0


def test_cmd_status_no_vault():
    args = make_args("status")
    with patch("envault.cli.is_locked", return_value=False):
        result = cmd_status(args)
    assert result == 0
