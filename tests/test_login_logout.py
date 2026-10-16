# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from unittest.mock import MagicMock, patch

import pytest

from colab_cli.auth import AuthProvider
from colab_cli.cli import main


def _run(argv):
    with patch.object(sys, "argv", argv):
        with pytest.raises(SystemExit) as error:
            main()
    return error.value.code


def test_logout_removes_cached_oauth_token(mock_common_state, tmp_path, capsys):
    token_path = tmp_path / "token.json"
    token_path.write_text("{}", encoding="utf-8")
    mock_common_state.auth_provider = AuthProvider.OAUTH2

    with patch("colab_cli.auth.TOKEN_CONFIG_PATH", str(token_path)):
        assert _run(["colab", "logout"]) == 0

    assert not token_path.exists()
    assert "Logged out" in capsys.readouterr().out


def test_logout_is_idempotent(mock_common_state, tmp_path, capsys):
    token_path = tmp_path / "missing-token.json"
    mock_common_state.auth_provider = AuthProvider.OAUTH2

    with patch("colab_cli.auth.TOKEN_CONFIG_PATH", str(token_path)):
        assert _run(["colab", "logout"]) == 0

    assert "Already logged out" in capsys.readouterr().out


def test_login_force_clears_oauth_token_before_auth(mock_common_state, tmp_path, capsys):
    token_path = tmp_path / "token.json"
    token_path.write_text("cached", encoding="utf-8")
    mock_common_state.auth_provider = AuthProvider.OAUTH2
    session = MagicMock()

    with patch("colab_cli.auth.TOKEN_CONFIG_PATH", str(token_path)):
        with patch("colab_cli.auth.get_credentials", return_value=session) as get_creds:
            assert _run(["colab", "login", "--force"]) == 0

    assert not token_path.exists()
    get_creds.assert_called_once()
    assert "Logged in with OAuth2" in capsys.readouterr().out


def test_logout_refuses_to_modify_adc(mock_common_state, capsys):
    mock_common_state.auth_provider = AuthProvider.ADC

    assert _run(["colab", "--auth=adc", "logout"]) == 1
    captured = capsys.readouterr()
    assert "managed outside colab-cli" in (captured.out + captured.err)