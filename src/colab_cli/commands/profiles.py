# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from __future__ import annotations

import os

import typer
from typing_extensions import Annotated

from colab_cli.profiles import (
    DEFAULT_PROFILE,
    get_default_profile,
    list_profiles,
    remove_profile,
    set_default_profile,
    token_path,
    validate_profile_name,
)

profile_app = typer.Typer(help="Manage named account profiles.", no_args_is_help=True)


def profiles_command():
    """List locally configured account profiles."""
    default = get_default_profile()
    for name in list_profiles():
        marker = "*" if name == default else " "
        auth = "authenticated" if os.path.exists(token_path(name)) else "not logged in"
        typer.echo(f"{marker} {name} | {auth}")


@profile_app.command("use")
def use_profile(name: Annotated[str, typer.Argument(help="Profile name")]):
    """Set the default profile used when --profile is omitted."""
    try:
        name = validate_profile_name(name)
        set_default_profile(name)
    except ValueError as e:
        typer.echo(f"[colab] {e}", err=True)
        raise typer.Exit(2)
    typer.echo(f"[colab] Default profile set to '{name}'.")


@profile_app.command("current")
def current_profile():
    """Print the current default profile."""
    typer.echo(get_default_profile())


@profile_app.command("remove")
def remove_profile_command(
    name: Annotated[str, typer.Argument(help="Profile name")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Remove local profile data without confirmation."),
    ] = False,
):
    """Remove a named profile's local credentials, sessions, history, and usage data."""
    try:
        name = validate_profile_name(name)
    except ValueError as e:
        typer.echo(f"[colab] {e}", err=True)
        raise typer.Exit(2)
    if name == DEFAULT_PROFILE:
        typer.echo("[colab] The default profile cannot be removed.", err=True)
        raise typer.Exit(1)
    if not yes and not typer.confirm(f"Remove local profile '{name}'?"):
        raise typer.Abort()
    try:
        removed = remove_profile(name)
    except ValueError as e:
        typer.echo(f"[colab] {e}", err=True)
        raise typer.Exit(1)
    typer.echo(
        f"[colab] Profile '{name}' removed." if removed
        else f"[colab] Profile '{name}' does not exist."
    )


def register(app: typer.Typer):
    app.command(name="profiles")(profiles_command)
    app.add_typer(profile_app, name="profile")
