# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Optional presentation layer for alternate command frontends.

The default CLI is unchanged.  A frontend may opt in with environment
variables to provide its own executable name, label, prefix, and isolated
configuration directory while reusing the same command implementation.
"""

from __future__ import annotations

import os
import re
import sys
from typing import TextIO


_PROTECTED = re.compile(
    r"(https?://\S+|(?:[A-Za-z0-9-]+\.)+(?:googleapis\.com|google\.com|googleusercontent\.com)\S*)"
)


def _transform_plain(text: str, name: str, label: str, prefix: str) -> str:
    home = os.path.expanduser("~")
    for value in {home, home.replace("\\", "/")}:
        if value:
            text = text.replace(value, "%USERPROFILE%")

    # Update messages are special: the backend may recommend reinstalling from
    # a local source path whose directory happens to contain the backend's
    # package name. Blind brand substitution inside that path would produce a
    # command that does not exist. Present a neutral, valid frontend command
    # instead and describe the version as the runtime engine version.
    text = text.replace(
        "[colab] A new version of Colab CLI is available:",
        f"[{prefix}] A runtime engine update is available:",
    )
    text = re.sub(
        r"\[colab\] Run '[^'\r\n]+' to update\.",
        f"[{prefix}] Run '{name} update --install' to update.",
        text,
    )

    text = text.replace("[colab]", f"[{prefix}]")
    text = text.replace("Google Colab", "Runtime Service")
    text = text.replace("Google Drive", "cloud drive")
    text = text.replace("Google account", "provider account")
    text = text.replace("Google consent flow", "provider consent flow")
    text = text.replace("X-Colab-Ssh-Pubkey", "X-Runtime-Ssh-Pubkey")
    text = text.replace("Colab CLI", label)
    text = text.replace("google-colab-cli", name)
    text = text.replace("colab-cli", name)
    text = text.replace(".colab-cli-oauth-config.json", f".{name}-oauth-config.json")
    text = text.replace(".config/colab-cli", f".config/{name}")
    text = text.replace(".config\\colab-cli", f".config\\{name}")

    text = re.sub(r"(?<![/.A-Za-z0-9_-])Colab(?![.A-Za-z0-9_-])", "Runtime", text)
    text = re.sub(
        r"(?<![/.A-Za-z0-9_-])colab(?![.A-Za-z0-9_-])", name, text
    )
    return text


def transform_text(text: str, name: str, label: str, prefix: str) -> str:
    """Transform user-facing text while leaving provider URLs/domains intact."""
    parts = _PROTECTED.split(text)
    for index in range(0, len(parts), 2):
        parts[index] = _transform_plain(parts[index], name, label, prefix)
    result = "".join(parts)
    # Functional commands such as ``url`` must emit the real provider URL so
    # it remains usable. Help text, however, can present a neutral placeholder
    # without changing the actual default passed to the command.
    if os.environ.get("COLAB_CLI_FRONTEND_HIDE_PROVIDER_URLS") == "1":
        result = result.replace(
            "https://colab.research.google.com", "https://<runtime-service>"
        )
    return result


class _FrontendStream:
    def __init__(self, stream: TextIO, name: str, label: str, prefix: str):
        self._stream = stream
        self._name = name
        self._label = label
        self._prefix = prefix

    def write(self, value):
        if isinstance(value, str):
            value = transform_text(value, self._name, self._label, self._prefix)
        return self._stream.write(value)

    def flush(self):
        return self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


def configure_from_environment() -> None:
    """Activate alternate user-facing branding when a frontend requests it."""
    name = os.environ.get("COLAB_CLI_FRONTEND_NAME")
    if not name:
        return
    label = os.environ.get("COLAB_CLI_FRONTEND_LABEL", name)
    prefix = os.environ.get("COLAB_CLI_FRONTEND_PREFIX", name)

    sys.argv[0] = name
    sys.stdout = _FrontendStream(sys.stdout, name, label, prefix)
    sys.stderr = _FrontendStream(sys.stderr, name, label, prefix)
