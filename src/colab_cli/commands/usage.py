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

import os

import typer
from typing_extensions import Annotated

from colab_cli.auth import AuthProvider
from colab_cli.consumption import format_consumption_status
from colab_cli.profiles import list_profiles
from colab_cli.t4_usage import T4UsageTracker, format_duration


def usage():
    """Show account compute-unit usage rate and balance"""
    from colab_cli.common import state

    try:
        result = state.client.get_consumption_user_info()
    except Exception as e:
        typer.echo(
            f"[colab] Warning: failed to fetch compute-unit info: {e}",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(format_consumption_status(result))


def _print_t4_snapshot(profile: str, snapshot: dict):
    typer.echo(f"Profile: {profile}")
    typer.echo(f"Tracking day: {snapshot['date']} (local time)")
    typer.echo(f"Daily T4 allowance: {format_duration(snapshot['allowance_seconds'])}")
    typer.echo(f"Tracked T4 time used: {format_duration(snapshot['used_seconds'])}")
    typer.echo(f"Tracked T4 time remaining: {format_duration(snapshot['remaining_seconds'])}")
    typer.echo(f"Active tracked T4 sessions: {snapshot['active_t4_sessions']}")


def t4_usage(
    all_profiles: Annotated[
        bool,
        typer.Option("--all", help="Show the local T4 tracker for every profile."),
    ] = False,
):
    """Show locally tracked T4 allocation time against the 4h30m daily budget."""
    from colab_cli.common import state

    if not all_profiles:
        can_reconcile = (
            state.auth_provider != AuthProvider.OAUTH2
            or os.path.exists(state.token_path)
        )
        if can_reconcile:
            try:
                assignments = state.client.list_assignments()
                state.t4_usage.reconcile(assignments)
            except Exception:
                # The local tracker remains useful offline; do not turn a display
                # command into an authentication/error path solely for reconciliation.
                pass
        _print_t4_snapshot(state.profile, state.t4_usage.snapshot())
        return

    profiles = list_profiles()
    for index, profile in enumerate(profiles):
        if index:
            typer.echo("")
        _print_t4_snapshot(profile, T4UsageTracker(profile).snapshot())


def register(app: typer.Typer):
    app.command()(usage)
    app.command(name="t4-usage")(t4_usage)
