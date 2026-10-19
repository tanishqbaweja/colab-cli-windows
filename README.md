# Colab CLI for Windows

A native Windows port of Google's official [Colab CLI](https://github.com/googlecolab/google-colab-cli).

It runs directly on Windows 10/11 without WSL, Docker, MSYS, or a Linux VM. The goal is to preserve the upstream command surface while adding the Windows-specific process, path, terminal, SSH, file-editing, and installer behavior required for the CLI to work natively.

> [!IMPORTANT]
> This is an unofficial community Windows port. Google Colab, the Colab service, and the upstream Colab CLI are products/projects of Google. This repository is not an official Google release.

## What works

The port keeps the upstream CLI features, including:

- OAuth sign-in and persisted credentials
- CPU, GPU, and TPU runtime provisioning
- Session listing, status, restart, and stop
- Local Python/script execution on Colab runtimes
- Interactive console and REPL workflows
- File upload and download
- Remote file editing
- SSH and SCP workflows through native Windows OpenSSH
- Google Drive / cloud-oriented upstream workflows
- Runtime usage reporting
- Self-update/install behavior for the Windows build

Windows-specific fixes include:

- Windows OpenSSH `ProxyCommand` quoting
- `NUL` instead of `/dev/null`
- Windows signal handling, including `SIGBREAK`
- Temporary-file handling that does not keep files locked while an editor reopens them
- Prompt-toolkit behavior for real Windows terminals and redirected output
- Location-independent installation and portable release packaging
- Self-update logic that preserves the installed Windows package source

## Install

### Portable release

Download the latest portable ZIP from the repository's **Releases** page, extract it anywhere, then run:

```powershell
.\install-windows.ps1
```

or double-click:

```text
install-windows.cmd
```

The installer:

1. verifies that native Windows OpenSSH is available;
2. bootstraps `uv` for the current user if needed;
3. provisions Python 3.12 through `uv`;
4. copies the bundled wheel to `%LOCALAPPDATA%\ColabCLIWindows\packages`;
5. installs the `colab` command with `uv tool install`.

The extracted release folder can be deleted after installation.

### Install from a Git checkout

Clone this repository anywhere and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install-windows.ps1
```

No drive letter, Windows username, or checkout location is assumed.

## Requirements

- Windows 10 or Windows 11
- Native Windows OpenSSH Client
  - `ssh.exe`
  - `scp.exe`
  - `ssh-keygen.exe`
- Internet access for Colab authentication and runtime operations

`uv` and Python 3.12 can be provisioned automatically by the installer.

## Quick start

Authenticate and list sessions:

```powershell
colab login
colab sessions
```

On first use, the CLI prints a Google authorization URL. Complete the consent flow and paste the returned authorization code into the terminal.

Switch to a different Google account in one step:

```powershell
colab login --force
```

Log out of the locally managed OAuth account:

```powershell
colab logout
```

`colab logout` removes only the Colab CLI's local OAuth token. It does not sign the account out of your browser or modify Application Default Credentials managed by Google Cloud tooling.

To invalidate the cached OAuth grant at Google as well as remove it locally:

```powershell
colab logout --revoke
```

If server-side revocation fails, the local credentials are kept so you can retry instead of losing the only token that can be revoked.

## Multiple account profiles

Named profiles keep OAuth credentials, session state, history, and local T4
tracking separate. The existing installation remains the `default` profile.

Authenticate several accounts:

```powershell
colab login --profile account1
colab login --profile account2
colab login --profile account3
```

List profiles and choose the default used when `--profile` is omitted:

```powershell
colab profiles
colab profile use account2
colab profile current
```

Every normal command can target one profile explicitly with the global option:

```powershell
colab --profile account1 new -s render-a --gpu T4
colab --profile account2 new -s render-b --gpu T4
colab --profile account1 exec -s render-a -f .\part1.py
colab --profile account2 exec -s render-b -f .\part2.py
```

The command-local `--profile` option is also accepted by `login` and `logout`,
so account management reads naturally even though global options normally come
before the subcommand.

### Parallel manifest

`colab parallel` runs independent, explicitly-profiled CLI jobs concurrently.
It does not automatically select or rotate accounts. Example `jobs.json`:

```json
{
  "jobs": [
    {
      "name": "part-1",
      "profile": "account1",
      "args": ["run", "--gpu", "T4", "part1.py"]
    },
    {
      "name": "part-2",
      "profile": "account2",
      "args": ["run", "--gpu", "T4", "part2.py"]
    }
  ]
}
```

Run it with:

```powershell
colab parallel .\jobs.json
```

Each job's `args` are the same arguments you would normally place after
`colab`. Nested `parallel` jobs are rejected.

## Local T4 daily tracker

The CLI maintains a per-profile local T4 allocation-time counter with a fixed
display budget of **4 hours 30 minutes per local calendar day**. This is local
accounting for planning work; it is not Google's authoritative quota or billing
counter.

```powershell
colab --profile account1 t4-usage
colab t4-usage --all
```

The tracker starts when this CLI allocates a T4 session and accrues continuously
while the session is tracked as active. Session listing/status operations also
reconcile the tracker against current server assignments. Time is split at local
midnight so the displayed allowance resets daily.

Create a T4 GPU runtime:

```powershell
colab new -s gpu-test --gpu T4
```

Check it:

```powershell
colab status -s gpu-test
```

Run a local Python file remotely:

```powershell
colab exec -s gpu-test -f .\workload.py
```

Upload and download files:

```powershell
colab upload -s gpu-test .\input.dat /content/input.dat
colab download -s gpu-test /content/result.json .\result.json
```

Check usage:

```powershell
colab usage
```

Stop the runtime:

```powershell
colab stop -s gpu-test
```

## GPU example

A simple CUDA check:

```python
import torch

print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

a = torch.randn((4096, 4096), device="cuda")
b = torch.randn((4096, 4096), device="cuda")
c = a @ b

print(float(c.sum()))
```

Run it with:

```powershell
colab exec -s gpu-test -f .\gpu_test.py
```

## Verified on Windows

The port has been exercised end-to-end with the native Windows CLI:

- OAuth authorization and token persistence
- authenticated `colab sessions` and `colab usage`
- T4 GPU allocation
- CUDA/PyTorch execution on the remote GPU
- remote artifact creation and download back to Windows
- FFmpeg H.264 NVENC export on a T4 runtime
- session termination and cleanup
- isolated named-account profiles and parallel explicit-profile jobs
- per-profile local T4 daily usage accounting

Repository validation at the time of the Windows port:

- **377 tests passed**
- **3 tests skipped** for platform/test-runner-specific terminal behavior
- **Ruff passed**

## Build the portable release

From a Windows Git checkout:

```powershell
.\build-windows-release.ps1
```

The generated archive is placed under:

```text
release\google-colab-cli-windows-portable.zip
```

The portable release contains a prebuilt wheel plus the installer scripts. It does not need the source repository or `.git` directory at install time.

## Privacy and local data

This repository does not include user OAuth tokens, refresh tokens, local Colab session state, or machine-specific installation paths.

The upstream installed-app OAuth client configuration is included because it is required for the official Colab OAuth flow. User credentials are created locally at runtime and are not part of the repository.

## Updating

For a portable/local Windows installation:

```powershell
colab update --install
```

The Windows port detects the actual installed package source rather than relying on a fixed path.

## Upstream

This project is based on:

- [googlecolab/google-colab-cli](https://github.com/googlecolab/google-colab-cli)

The upstream project remains the source of the core Colab CLI implementation. This repository focuses on native Windows compatibility and packaging.

## License

Apache License 2.0. See [LICENSE](LICENSE).
