"""Tests for envault.diff."""

import pytest
from envault.diff import DiffEntry, diff_envs, summarise


OLD = {"A": "1", "B": "2", "C": "3"}
NEW = {"A": "1", "B": "99", "D": "4"}


def test_added_key_detected():
    entries = diff_envs(OLD, NEW)
    added = [e for e in entries if e.status == "added"]
    assert len(added) == 1
    assert added[0].key == "D"
    assert added[0].new_value == "4"


def test_removed_key_detected():
    entries = diff_envs(OLD, NEW)
    removed = [e for e in entries if e.status == "removed"]
    assert len(removed) == 1
    assert removed[0].key == "C"
    assert removed[0].old_value == "3"


def test_changed_key_detected():
    entries = diff_envs(OLD, NEW)
    changed = [e for e in entries if e.status == "changed"]
    assert len(changed) == 1
    assert changed[0].key == "B"
    assert changed[0].old_value == "2"
    assert changed[0].new_value == "99"


def test_unchanged_excluded_by_default():
    entries = diff_envs(OLD, NEW)
    assert all(e.status != "unchanged" for e in entries)


def test_unchanged_included_when_flag_set():
    entries = diff_envs(OLD, NEW, include_unchanged=True)
    unchanged = [e for e in entries if e.status == "unchanged"]
    assert len(unchanged) == 1
    assert unchanged[0].key == "A"


def test_empty_dicts_produce_no_entries():
    assert diff_envs({}, {}) == []


def test_identical_dicts_produce_no_entries():
    assert diff_envs(OLD, OLD) == []


def test_keys_are_sorted():
    entries = diff_envs({"Z": "1", "A": "2"}, {"M": "3"})
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_summarise_counts():
    entries = diff_envs(OLD, NEW, include_unchanged=True)
    counts = summarise(entries)
    assert counts["added"] == 1
    assert counts["removed"] == 1
    assert counts["changed"] == 1
    assert counts["unchanged"] == 1


def test_diff_entry_repr_added():
    e = DiffEntry("FOO", "added", new_value="bar")
    assert repr(e) == "+ FOO=bar"


def test_diff_entry_repr_removed():
    e = DiffEntry("FOO", "removed", old_value="bar")
    assert repr(e) == "- FOO=bar"


def test_diff_entry_repr_changed():
    e = DiffEntry("FOO", "changed", old_value="old", new_value="new")
    assert repr(e) == "~ FOO: 'old' -> 'new'"
