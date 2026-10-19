# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from pathlib import Path

import pytest

from colab_cli import profiles


def _redirect_profile_root(monkeypatch, tmp_path: Path):
    root = tmp_path / "cfg"
    monkeypatch.setattr(profiles, "_CONFIG_ROOT", root)
    monkeypatch.setattr(profiles, "_PROFILES_ROOT", root / "profiles")
    monkeypatch.setattr(profiles, "_SELECTION_PATH", root / "profile.json")
    return root


def test_named_profile_paths_are_isolated(monkeypatch, tmp_path):
    root = _redirect_profile_root(monkeypatch, tmp_path)
    profiles.ensure_profile("account1")
    profiles.ensure_profile("account2")

    assert profiles.token_path("account1") == str(root / "profiles" / "account1" / "token.json")
    assert profiles.token_path("account2") == str(root / "profiles" / "account2" / "token.json")
    assert profiles.sessions_path("account1") != profiles.sessions_path("account2")


def test_default_profile_selection_round_trip(monkeypatch, tmp_path):
    _redirect_profile_root(monkeypatch, tmp_path)
    assert profiles.get_default_profile() == profiles.DEFAULT_PROFILE

    profiles.set_default_profile("render-a")
    assert profiles.get_default_profile() == "render-a"
    assert "render-a" in profiles.list_profiles()


@pytest.mark.parametrize("bad", ["../oops", "a/b", " space", "", ".hidden"])
def test_profile_names_reject_path_traversal_and_invalid_names(bad):
    with pytest.raises(ValueError):
        profiles.validate_profile_name(bad)
