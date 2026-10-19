# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

import json
from types import SimpleNamespace
from unittest.mock import patch

from colab_cli.commands import parallel


def test_run_job_injects_explicit_profile():
    proc = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")
    with patch("subprocess.run", return_value=proc) as run:
        result = parallel._run_job(
            0,
            {"name": "part-a", "profile": "account1", "args": ["status", "-s", "a"]},
            None,
        )

    cmd = run.call_args.args[0]
    assert cmd[1:4] == ["-m", "colab_cli.cli", "--profile"]
    assert cmd[4] == "account1"
    assert cmd[5:] == ["status", "-s", "a"]
    assert result["returncode"] == 0


def test_parallel_manifest_runs_all_jobs(tmp_path):
    manifest = tmp_path / "jobs.json"
    manifest.write_text(
        json.dumps(
            {
                "jobs": [
                    {"name": "a", "profile": "one", "args": ["status"]},
                    {"name": "b", "profile": "two", "args": ["sessions"]},
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_run_job(index, job, timeout):
        return {
            "index": index,
            "name": job["name"],
            "profile": job["profile"],
            "returncode": 0,
            "stdout": job["name"],
            "stderr": "",
        }

    with patch.object(parallel, "_run_job", side_effect=fake_run_job):
        parallel.parallel(str(manifest), max_workers=2, timeout=None)
