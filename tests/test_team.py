"""Tests for envault.team module."""

import json
import pytest

from envault.team import (
    TeamError,
    _get_team_path,
    add_member,
    get_token,
    list_members,
    remove_member,
)


@pytest.fixture
def team_dir(tmp_path):
    return str(tmp_path)


def test_get_team_path_defaults_to_cwd():
    path = _get_team_path()
    assert path.name == ".envault-team.json"


def test_get_team_path_with_directory(team_dir):
    path = _get_team_path(team_dir)
    assert path.parent == pytest.importorskip("pathlib").Path(team_dir)


def test_list_members_empty_when_no_file(team_dir):
    members = list_members(team_dir)
    assert members == []


def test_add_member_creates_file(team_dir):
    add_member("alice@example.com", "tok_abc", team_dir)
    path = _get_team_path(team_dir)
    assert path.exists()


def test_add_member_stores_email_and_token(team_dir):
    add_member("alice@example.com", "tok_abc", team_dir)
    members = list_members(team_dir)
    assert len(members) == 1
    assert members[0]["email"] == "alice@example.com"
    assert members[0]["token"] == "tok_abc"


def test_add_multiple_members(team_dir):
    add_member("alice@example.com", "tok_a", team_dir)
    add_member("bob@example.com", "tok_b", team_dir)
    emails = [m["email"] for m in list_members(team_dir)]
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails


def test_add_duplicate_member_raises(team_dir):
    add_member("alice@example.com", "tok_abc", team_dir)
    with pytest.raises(TeamError, match="already exists"):
        add_member("alice@example.com", "tok_xyz", team_dir)


def test_remove_member(team_dir):
    add_member("alice@example.com", "tok_abc", team_dir)
    remove_member("alice@example.com", team_dir)
    assert list_members(team_dir) == []


def test_remove_nonexistent_member_raises(team_dir):
    with pytest.raises(TeamError, match="not found"):
        remove_member("ghost@example.com", team_dir)


def test_get_token_returns_correct_token(team_dir):
    add_member("alice@example.com", "tok_abc", team_dir)
    assert get_token("alice@example.com", team_dir) == "tok_abc"


def test_get_token_unknown_email_raises(team_dir):
    with pytest.raises(TeamError, match="not found"):
        get_token("nobody@example.com", team_dir)


def test_team_file_is_valid_json(team_dir):
    add_member("alice@example.com", "tok_abc", team_dir)
    path = _get_team_path(team_dir)
    data = json.loads(path.read_text())
    assert "members" in data
