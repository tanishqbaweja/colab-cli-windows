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