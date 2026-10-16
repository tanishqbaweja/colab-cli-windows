# Native Windows Port

This repository contains a native Windows port of Google's Colab CLI.

## Goals

- Runs directly on Windows 10/11.
- Does not require WSL, Docker, MSYS, or a Linux VM.
- Uses native Windows OpenSSH for SSH and file-transfer related operations.
- Keeps the upstream CLI command surface and behavior wherever possible.

## Requirements

- Windows 10 or Windows 11
- `uv`
- Windows OpenSSH Client (`ssh.exe`, `scp.exe`, and `ssh-keygen.exe`)

The included installer checks these dependencies.

## Install

Extract or clone this repository anywhere, then open PowerShell in that folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

The install location can be on any local drive and under any Windows user profile. The installer resolves its own directory at runtime and does not depend on a fixed checkout path.

The portable release ZIP includes a prebuilt wheel. During installation that wheel is copied to `%LOCALAPPDATA%\ColabCLIWindows\packages`, so the extracted ZIP does not need to remain on disk after installation. A Git checkout can still be installed directly when no bundled wheel is present.

If `uv` is not installed, the installer bootstraps it for the current user. Windows OpenSSH Client must be available; it is a standard optional Windows feature on supported Windows 10/11 systems.

Then open a fresh terminal and verify:

```powershell
colab --help
colab ssh --help
```

To explicitly authenticate, switch Google accounts, or log out:

```powershell
colab login
colab login --force
colab logout
```

`colab login --force` clears the locally cached OAuth token before starting a fresh consent flow, making it the simplest way to switch accounts. ADC credentials remain externally managed and are not deleted by `colab logout`.

## Windows compatibility changes

The port keeps upstream behavior and adds Windows-specific handling for:

- OpenSSH `ProxyCommand` quoting using Windows command-line rules.
- `NUL` instead of `/dev/null`.
- Windows console signals including `SIGBREAK`, while avoiding unavailable `SIGHUP`.
- Remote file editing without keeping a temporary file locked open.
- REPL operation in both normal Windows terminals and redirected/non-console environments.
- Native self-update support through the existing pip/uv updater.

## Portability

- No fixed drive letter is used.
- No fixed Windows username or profile directory is used.
- The installer resolves the `uv` tool binary directory dynamically.
- Portable installs keep their package in `%LOCALAPPDATA%` rather than depending on the extraction folder.
- Local-source self-update metadata uses the actual installed package path rather than a hardcoded checkout path.

## Tests

Validated on Windows:

- Full pytest suite: 354 passed, 3 skipped.
- Ruff: all checks passed.

The skipped cases are platform/test-runner-specific terminal tests rather than disabled CLI features.

## Notes

Authentication and Colab resource allocation still use Google's normal Colab services and policies. The Windows port changes only the local client behavior.

The CLI itself is lightweight. A running Colab workload executes remotely; this port does not start WSL or a local Linux VM.
