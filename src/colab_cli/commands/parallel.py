# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from colab_cli.profiles import validate_profile_name


def _run_job(index: int, job: dict, timeout: Optional[float]) -> dict:
    name = str(job.get("name") or f"job-{index + 1}")
    profile = validate_profile_name(str(job["profile"]))
    args = job.get("args")
    if not isinstance(args, list) or not args or not all(isinstance(x, str) for x in args):
        raise ValueError(f"{name}: 'args' must be a non-empty list of strings")
    if args[0] == "parallel":
        raise ValueError(f"{name}: nested parallel jobs are not allowed")
    cmd = [sys.executable, "-m", "colab_cli.cli", "--profile", profile, *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        errors="replace",
    )
    return {
        "index": index,
        "name": name,
        "profile": profile,
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def parallel(
    manifest: Annotated[
        str,
        typer.Argument(
            help=(
                "JSON manifest with a jobs array. Each job must explicitly specify "
                "{name, profile, args}."
            )
        ),
    ],
    max_workers: Annotated[
        Optional[int],
        typer.Option("--max-workers", help="Maximum concurrent jobs (default: number of jobs)."),
    ] = None,
    timeout: Annotated[
        Optional[float],
        typer.Option("--timeout", help="Optional per-job timeout in seconds."),
    ] = None,
):
    """Run explicitly profiled CLI jobs concurrently."""
    path = Path(manifest)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        typer.echo(f"[colab] Could not read parallel manifest: {e}", err=True)
        raise typer.Exit(2)
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list) or not jobs:
        typer.echo("[colab] Manifest must contain a non-empty 'jobs' array.", err=True)
        raise typer.Exit(2)

    workers = max_workers or len(jobs)
    workers = max(1, min(workers, len(jobs)))
    results = []
    failed = False

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_job, i, job, timeout): i for i, job in enumerate(jobs)}
        for future in as_completed(futures):
            index = futures[future]
            try:
                result = future.result()
            except Exception as e:
                failed = True
                result = {
                    "index": index,
                    "name": str(jobs[index].get("name") or f"job-{index + 1}"),
                    "profile": jobs[index].get("profile", "?"),
                    "returncode": 1,
                    "stdout": "",
                    "stderr": str(e),
                }
            if result["returncode"] != 0:
                failed = True
            results.append(result)

    for result in sorted(results, key=lambda item: item["index"]):
        typer.echo(
            f"=== {result['name']} | profile={result['profile']} | "
            f"exit={result['returncode']} ==="
        )
        if result.get("stdout"):
            typer.echo(result["stdout"].rstrip())
        if result.get("stderr"):
            typer.echo(result["stderr"].rstrip(), err=True)

    if failed:
        raise typer.Exit(1)


def register(app: typer.Typer):
    app.command(name="parallel")(parallel)
