"""Tests for envault.sync (push/pull integration with mocked remote)."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.storage import VaultCorruptedError, VaultNotFoundError
from envault.sync import sync_push, sync_pull

VALID_VAULT = json.dumps({"version": 1, "payload": "abc123=="})


@pytest.fixture()
def vault_dir(tmp_path):
    vault_file = tmp_path / ".envault.json"
    vault_file.write_text(VALID_VAULT, encoding="utf-8")
    return tmp_path


def test_sync_push_calls_push_vault(vault_dir):
    with patch("envault.sync.push_vault") as mock_push:
        path = sync_push("my-project", str(vault_dir))
        mock_push.assert_called_once_with("my-project", VALID_VAULT)
        assert path.name == ".envault.json"


def test_sync_push_raises_when_no_vault(tmp_path):
    with patch("envault.sync.push_vault"):
        with pytest.raises(VaultNotFoundError):
            sync_push("my-project", str(tmp_path))


def test_sync_pull_writes_vault_file(tmp_path):
    with patch("envault.sync.pull_vault", return_value=VALID_VAULT):
        path = sync_pull("my-project", str(tmp_path))
        assert path.exists()
        assert json.loads(path.read_text()) == json.loads(VALID_VAULT)


def test_sync_pull_creates_parent_dirs(tmp_path):
    nested = tmp_path / "deep" / "nested"
    with patch("envault.sync.pull_vault", return_value=VALID_VAULT):
        path = sync_pull("my-project", str(nested))
        assert path.exists()


def test_sync_pull_raises_on_invalid_json(tmp_path):
    with patch("envault.sync.pull_vault", return_value="not-json"):
        with pytest.raises(VaultCorruptedError, match="not valid JSON"):
            sync_pull("my-project", str(tmp_path))


def test_sync_pull_raises_on_missing_keys(tmp_path):
    bad_payload = json.dumps({"version": 1})  # missing 'payload'
    with patch("envault.sync.pull_vault", return_value=bad_payload):
        with pytest.raises(VaultCorruptedError, match="missing required keys"):
            sync_pull("my-project", str(tmp_path))


def test_sync_push_returns_correct_path(vault_dir):
    with patch("envault.sync.push_vault"):
        path = sync_push("proj", str(vault_dir))
        assert isinstance(path, Path)
        assert path.suffix == ".json"
