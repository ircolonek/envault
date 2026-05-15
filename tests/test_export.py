"""Tests for envault.export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import ExportError, export_env
from envault.vault import lock


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    env = {"API_KEY": "secret123", "DB_URL": "postgres://localhost/db", "DEBUG": "true"}
    lock(env, passphrase="hunter2", directory=tmp_path)
    return tmp_path


def test_export_dotenv_format(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="dotenv")
    assert 'API_KEY="secret123"' in result
    assert 'DB_URL="postgres://localhost/db"' in result
    assert 'DEBUG="true"' in result


def test_export_shell_format(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="shell")
    assert 'export API_KEY="secret123"' in result
    assert 'export DEBUG="true"' in result


def test_export_json_format(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="json")
    data = json.loads(result)
    assert data["API_KEY"] == "secret123"
    assert data["DB_URL"] == "postgres://localhost/db"
    assert data["DEBUG"] == "true"


def test_export_keys_filter(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="json", keys=["API_KEY"])
    data = json.loads(result)
    assert list(data.keys()) == ["API_KEY"]


def test_export_keys_filter_dotenv(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="dotenv", keys=["DEBUG"])
    assert "DEBUG" in result
    assert "API_KEY" not in result


def test_export_wrong_passphrase_raises(vault_dir: Path) -> None:
    with pytest.raises(ExportError, match="Failed to decrypt vault"):
        export_env("wrongpass", directory=vault_dir)


def test_export_unknown_format_raises(vault_dir: Path) -> None:
    with pytest.raises(ExportError, match="Unknown format"):
        export_env("hunter2", directory=vault_dir, fmt="yaml")  # type: ignore[arg-type]


def test_export_dotenv_sorted(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="dotenv")
    keys = [line.split("=")[0] for line in result.splitlines()]
    assert keys == sorted(keys)


def test_export_empty_keys_filter(vault_dir: Path) -> None:
    result = export_env("hunter2", directory=vault_dir, fmt="json", keys=[])
    data = json.loads(result)
    assert data == {}
