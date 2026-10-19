from types import SimpleNamespace
from unittest.mock import patch

from colab_cli.commands.files import _launch_editor


def test_windows_configured_editor_uses_native_shell(monkeypatch):
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", r"C:\tools\editor.cmd")

    with (
        patch("colab_cli.commands.files.os.name", "nt"),
        patch(
            "colab_cli.commands.files.subprocess.run",
            return_value=SimpleNamespace(returncode=0),
        ) as run,
    ):
        _launch_editor(r"C:\Temp Folder\edit.txt")

    command = run.call_args.args[0]
    assert command.startswith(r"C:\tools\editor.cmd ")
    assert r'"C:\Temp Folder\edit.txt"' in command
    assert run.call_args.kwargs["shell"] is True
