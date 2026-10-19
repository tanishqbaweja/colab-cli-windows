# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from colab_cli.frontend import transform_text


def test_frontend_transforms_cli_branding_and_prefix():

    text = "Usage: colab new\n[colab] Colab CLI created a Colab session\n"
    out = transform_text(text, "runtimectl", "RuntimeCtl", "runtimectl")

    assert "Usage: runtimectl" in out
    assert "[runtimectl]" in out
    assert "RuntimeCtl" in out
    assert "Colab session" not in out


def test_frontend_preserves_provider_urls_and_domains():
    text = (
        "https://colab.research.google.com/example "
        "colab.pa.googleapis.com "
        "https://www.googleapis.com/auth/colaboratory"
    )
    assert transform_text(text, "runtimectl", "RuntimeCtl", "runtimectl") == text


def test_frontend_help_can_hide_provider_url_and_protocol_header(monkeypatch):
    monkeypatch.setenv("COLAB_CLI_FRONTEND_HIDE_PROVIDER_URLS", "1")
    text = (
        "X-Colab-Ssh-Pubkey\n"
        "[default: https://colab.research.google.com]\n"
    )

    out = transform_text(text, "runtimectl", "RuntimeCtl", "runtimectl")

    assert "X-Runtime-Ssh-Pubkey" in out
    assert "https://<runtime-service>" in out
    assert "Colab" not in out


def test_frontend_update_message_does_not_rewrite_local_source_path():
    text = (
        "[colab] A new version of Colab CLI is available: 9.9.9 (current: 1.0.0)\n"
        "[colab] Run 'uv tool install -U \"C:\\portable\\backend-source\"' "
        "to update.\n"
    )

    out = transform_text(text, "runtimectl", "RuntimeCtl", "runtimectl")

    assert "A runtime engine update is available: 9.9.9" in out
    assert "Run 'runtimectl update --install' to update." in out
    assert "backend-source" not in out