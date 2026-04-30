"""Launch fresh command sessions as iTerm2 tabs and panes.

Sibling to ``restart`` but for new work rather than crash recovery: given a list
of tasks (cwd + command + optional prompt), opens iTerm tabs grouped by cwd with
one pane per task, running the command in each.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent

from .iterm import (
    MAX_PANES_PER_TAB,
    _quote_as,
    _sh_quote,
    build_fill_tab_script,
    build_layout_script,
)


def current_iterm_session_uid() -> str | None:
    """Unique-id of the iTerm session running this process, or None if not set.

    iTerm exports ``$ITERM_SESSION_ID`` shaped as ``w<n>t<n>p<n>:<UUID>``. We return
    the UUID portion so AppleScript's ``unique id of session`` can match against it.
    """
    raw = os.environ.get("ITERM_SESSION_ID", "")
    if ":" in raw:
        return raw.split(":", 1)[1]
    return None


@dataclass
class LaunchTask:
    """One session to spawn.

    ``command`` is the executable or shell alias to run (e.g. ``"clauded"``).
    ``prompt``, if non-empty, is passed as a single quoted argv to ``command`` —
    useful for seeding a Claude Code session with starting context. ``name`` is
    the pane/tab name; defaults to the basename of ``cwd``.
    """

    cwd: str
    command: str = "clauded"
    prompt: str = ""
    name: str = ""
    extra_args: list[str] = field(default_factory=list)

    def shell_command(self) -> str:
        parts = [f"cd {_sh_quote(self.cwd)} &&", self.command]
        parts.extend(_sh_quote(a) for a in self.extra_args)
        if self.prompt:
            parts.append(_sh_quote(self.prompt))
        return " ".join(parts)

    def pane_name(self) -> str:
        return self.name or Path(self.cwd).name


def tasks_from_spec(path: str | Path) -> list[LaunchTask]:
    """Read a JSON spec file. Top-level array of objects matching LaunchTask fields."""
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        raise ValueError("spec must be a JSON array of tasks")
    return [LaunchTask(**d) for d in data]


def build_launch_script(tasks: list[LaunchTask]) -> str:
    """Render AppleScript: one tab per distinct cwd, panes laid out by task count."""
    if not tasks:
        raise ValueError("no tasks to launch")

    groups: dict[str, list[LaunchTask]] = defaultdict(list)
    for t in tasks:
        groups[t.cwd].append(t)

    body_chunks = []
    for cwd, group in groups.items():
        named = [(t.shell_command(), t.pane_name()) for t in group]
        for i in range(0, len(named), MAX_PANES_PER_TAB):
            body_chunks.append(build_layout_script(named[i : i + MAX_PANES_PER_TAB]))

    body = "\n\n".join(body_chunks)
    return dedent(
        f"""
        tell application "iTerm"
            tell current window
                {body}
            end tell
        end tell
        """
    ).strip()


def build_fill_script(tasks: list[LaunchTask], self_session_uid: str, include_self: bool = False) -> str:
    """Render AppleScript that writes tasks into the caller's tab's existing panes.

    Unlike ``build_launch_script`` this creates no tabs — it targets whatever panes
    are already laid out in the tab containing the pane identified by
    ``self_session_uid`` (the UUID portion of ``$ITERM_SESSION_ID``). One task per
    pane, in iTerm's session order. The caller's own pane is skipped unless
    ``include_self`` is true.
    """
    if not tasks:
        raise ValueError("no tasks to launch")
    named = [(t.shell_command(), t.pane_name()) for t in tasks]
    body = build_fill_tab_script(named, self_session_uid=self_session_uid, include_self=include_self)
    return dedent(
        f"""
        tell application "iTerm"
            {body}
        end tell
        """
    ).strip()
