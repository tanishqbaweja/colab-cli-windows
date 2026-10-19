# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Named local account profiles for colab-cli."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import filelock

DEFAULT_PROFILE = "default"
_CONFIG_ROOT = Path(
    os.path.expanduser(os.environ.get("COLAB_CLI_CONFIG_ROOT", "~/.config/colab-cli"))
)
_PROFILES_ROOT = _CONFIG_ROOT / "profiles"
_SELECTION_PATH = _CONFIG_ROOT / "profile.json"
_PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def config_root() -> str:
    return str(_CONFIG_ROOT)


def validate_profile_name(name: str) -> str:
    if name != name.strip():
        raise ValueError("Profile names cannot have leading or trailing whitespace.")
    if name == DEFAULT_PROFILE:
        return name
    if not _PROFILE_RE.fullmatch(name):
        raise ValueError(
            "Profile names must start with a letter or digit and contain only "
            "letters, digits, '.', '_' or '-' (max 64 characters)."
        )
    return name


def profile_dir(name: str) -> Path:
    name = validate_profile_name(name)
    if name == DEFAULT_PROFILE:
        return _CONFIG_ROOT
    return _PROFILES_ROOT / name


def token_path(name: str) -> str:
    return str(profile_dir(name) / "token.json")


def sessions_path(name: str) -> str:
    return str(profile_dir(name) / "sessions.json")


def history_dir(name: str) -> str:
    if validate_profile_name(name) == DEFAULT_PROFILE:
        return str(_CONFIG_ROOT / "history")
    return str(profile_dir(name) / "history")


def t4_usage_path(name: str) -> str:
    if validate_profile_name(name) == DEFAULT_PROFILE:
        return str(_CONFIG_ROOT / "t4-usage.json")
    return str(profile_dir(name) / "t4-usage.json")


def ensure_profile(name: str) -> str:
    name = validate_profile_name(name)
    profile_dir(name).mkdir(parents=True, exist_ok=True)
    return name


def _selection_lock() -> filelock.FileLock:
    _CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    return filelock.FileLock(str(_SELECTION_PATH) + ".lock")


def get_default_profile() -> str:
    with _selection_lock():
        if not _SELECTION_PATH.exists():
            return DEFAULT_PROFILE
        try:
            data = json.loads(_SELECTION_PATH.read_text(encoding="utf-8"))
            return validate_profile_name(data.get("default_profile", DEFAULT_PROFILE))
        except Exception:
            return DEFAULT_PROFILE


def set_default_profile(name: str) -> None:
    name = ensure_profile(name)
    with _selection_lock():
        _SELECTION_PATH.write_text(
            json.dumps({"default_profile": name}, indent=2), encoding="utf-8"
        )


def list_profiles() -> list[str]:
    names = {DEFAULT_PROFILE}
    if _PROFILES_ROOT.exists():
        for entry in _PROFILES_ROOT.iterdir():
            if entry.is_dir():
                try:
                    names.add(validate_profile_name(entry.name))
                except ValueError:
                    continue
    return sorted(names, key=lambda item: (item != DEFAULT_PROFILE, item.lower()))


def remove_profile(name: str) -> bool:
    name = validate_profile_name(name)
    if name == DEFAULT_PROFILE:
        raise ValueError("The legacy/default profile cannot be removed.")
    path = profile_dir(name)
    if not path.exists():
        return False
    shutil.rmtree(path)
    if get_default_profile() == name:
        set_default_profile(DEFAULT_PROFILE)
    return True
