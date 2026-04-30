"""geno-term CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .discovery import discover, group_by_cwd
from .iterm import build_script, run_script
from .launch import (
    build_fill_script,
    build_launch_script,
    current_iterm_session_uid,
    tasks_from_spec,
)


@click.group()
def main() -> None:
    """Terminal automation for coding agent session recovery."""


@main.command("discover")
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--within-hours", type=float, default=None, help="Only sessions within N hours of the newest — isolates the cluster active at crash time.")
def cmd_discover(target_dir: str, within_hours: float | None) -> None:
    """List coding agent sessions whose cwd is under TARGET_DIR."""
    sessions = discover(target_dir, within_hours=within_hours)
    if not sessions:
        click.echo(f"No sessions found under {target_dir}", err=True)
        sys.exit(0)
    groups = group_by_cwd(sessions)
    for cwd, group in groups.items():
        click.echo(f"\n{cwd}  ({len(group)})")
        for s in group:
            click.echo(f"  {s.session_id}  {s.short_topic}")


@main.command("restart")
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--within-hours", type=float, default=1.0, help="Only restart sessions within N hours of the newest (default 1.0 — the crash cluster).")
@click.option("--close", "close_names", multiple=True, help="Tab name to close before opening (repeatable).")
@click.option("--print-only", is_flag=True, help="Print the AppleScript instead of running it.")
def cmd_restart(target_dir: str, within_hours: float, close_names: tuple[str, ...], print_only: bool) -> None:
    """Restart every session under TARGET_DIR as iTerm tabs+panes grouped by cwd."""
    sessions = discover(target_dir, within_hours=within_hours)
    if not sessions:
        click.echo(f"No sessions found under {target_dir}", err=True)
        sys.exit(1)
    script = build_script(sessions, close_names=list(close_names) or None)
    if print_only:
        click.echo(script)
        return
    run_script(script)
    click.echo(f"Opened {len(sessions)} session(s) across {len(group_by_cwd(sessions))} tab(s).")


@main.command("launch")
@click.option(
    "--spec",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    required=True,
    help="JSON spec file — array of tasks with cwd, command, prompt, name.",
)
@click.option(
    "--in-current-tab",
    "in_current_tab",
    is_flag=True,
    help="Write tasks into existing panes of the current iTerm tab instead of creating new tabs. Skips the pane running geno-term. One task per pane, in iTerm's session order.",
)
@click.option(
    "--include-current-pane",
    is_flag=True,
    help="With --in-current-tab, also target the pane running geno-term. Off by default to avoid self-nuking.",
)
@click.option("--print-only", is_flag=True, help="Print the AppleScript instead of running it.")
def cmd_launch(spec: str, in_current_tab: bool, include_current_pane: bool, print_only: bool) -> None:
    """Launch fresh command sessions in iTerm.

    The spec file is a JSON array. Each entry:

      { "cwd": "/abs/path", "command": "clauded", "prompt": "...", "name": "..." }

    ``command`` defaults to "clauded"; ``prompt`` (if present) is passed as one
    quoted argv to the command — handy for seeding a Claude Code session with
    starting context.

    Default behavior: one new tab per distinct ``cwd``, panes laid out by task
    count. With ``--in-current-tab``: writes tasks into the panes of the current
    tab in iTerm's session order, skipping the pane running geno-term (override
    with ``--include-current-pane``).
    """
    tasks = tasks_from_spec(spec)
    if not tasks:
        click.echo(f"No tasks in {spec}", err=True)
        sys.exit(1)

    if in_current_tab:
        self_uid = current_iterm_session_uid()
        if not self_uid:
            click.echo(
                "error: --in-current-tab needs $ITERM_SESSION_ID — run geno-term from an iTerm pane.",
                err=True,
            )
            sys.exit(2)
        script = build_fill_script(tasks, self_session_uid=self_uid, include_self=include_current_pane)
    else:
        script = build_launch_script(tasks)

    if print_only:
        click.echo(script)
        return
    run_script(script)

    if in_current_tab:
        click.echo(f"Filled {len(tasks)} pane(s) in current tab.")
    else:
        distinct_cwds = len({t.cwd for t in tasks})
        click.echo(f"Launched {len(tasks)} session(s) across {distinct_cwds} tab(s).")


if __name__ == "__main__":
    main()
