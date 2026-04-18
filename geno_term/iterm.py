"""Render and execute AppleScript that opens sessions as iTerm2 tabs/panes."""

from __future__ import annotations

import subprocess
from textwrap import dedent

from .discovery import Session, group_by_cwd


def _quote_as(s: str) -> str:
    """AppleScript string literal — escape backslashes and double quotes."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _pane_layout(n: int) -> str:
    """Pick a grid shape given pane count."""
    if n <= 1:
        return "single"
    if n <= 3:
        return "vstrip"  # vertical splits, one row
    if n <= 4:
        return "2x2"
    return "3x2"  # up to 6


def _build_tab_script(cwd: str, sessions: list[Session]) -> str:
    n = len(sessions)
    layout = _pane_layout(n)
    cmds = [f"cd {_sh_quote(cwd)} && claude --resume {s.session_id}" for s in sessions]
    names = [s.short_topic for s in sessions]

    lines = ["set newTab to (create tab with default profile)"]
    lines.append("set s1 to current session of newTab")

    if layout == "single":
        pane_vars = ["s1"]
    elif layout == "vstrip":
        pane_vars = ["s1"]
        for i in range(2, n + 1):
            prev = pane_vars[-1]
            lines.append(f"tell {prev}")
            lines.append(f"\tset s{i} to (split vertically with default profile)")
            lines.append("end tell")
            pane_vars.append(f"s{i}")
    elif layout == "2x2":
        # s1 | s2 (top row), s3 | s4 (bottom row)
        lines.append("tell s1")
        lines.append("\tset s2 to (split vertically with default profile)")
        lines.append("end tell")
        lines.append("tell s1")
        lines.append("\tset s3 to (split horizontally with default profile)")
        lines.append("end tell")
        lines.append("tell s2")
        lines.append("\tset s4 to (split horizontally with default profile)")
        lines.append("end tell")
        pane_vars = ["s1", "s2", "s3", "s4"][:n]
    else:  # 3x2
        lines.append("tell s1")
        lines.append("\tset s2 to (split vertically with default profile)")
        lines.append("end tell")
        lines.append("tell s2")
        lines.append("\tset s3 to (split vertically with default profile)")
        lines.append("end tell")
        lines.append("tell s1")
        lines.append("\tset s4 to (split horizontally with default profile)")
        lines.append("end tell")
        lines.append("tell s2")
        lines.append("\tset s5 to (split horizontally with default profile)")
        lines.append("end tell")
        lines.append("tell s3")
        lines.append("\tset s6 to (split horizontally with default profile)")
        lines.append("end tell")
        pane_vars = ["s1", "s2", "s3", "s4", "s5", "s6"][:n]

    for var, cmd, name in zip(pane_vars, cmds, names):
        lines.append(f"tell {var}")
        lines.append(f"\twrite text {_quote_as(cmd)}")
        lines.append(f"\tset name to {_quote_as(name)}")
        lines.append("end tell")

    return "\n".join(lines)


def _sh_quote(s: str) -> str:
    """Single-quote a string for use inside an AppleScript-embedded shell command."""
    return "'" + s.replace("'", "'\\''") + "'"


MAX_PANES_PER_TAB = 6


def build_script(sessions: list[Session], close_names: list[str] | None = None) -> str:
    groups = group_by_cwd(sessions)
    body_chunks = []
    for cwd, group in groups.items():
        for i in range(0, len(group), MAX_PANES_PER_TAB):
            body_chunks.append(_build_tab_script(cwd, group[i : i + MAX_PANES_PER_TAB]))

    close_block = ""
    if close_names:
        as_names = ", ".join(_quote_as(n) for n in close_names)
        close_block = dedent(
            f"""
            set oldNames to {{{as_names}}}
            set toClose to {{}}
            repeat with t in tabs
                try
                    set tname to name of current session of t
                    if oldNames contains tname then
                        set end of toClose to t
                    end if
                end try
            end repeat
            repeat with t in toClose
                close t
            end repeat
            """
        ).strip()

    body = "\n\n".join(body_chunks)
    return dedent(
        f"""
        tell application "iTerm"
            tell current window
                {close_block}

                {body}
            end tell
        end tell
        """
    ).strip()


def run_script(script: str) -> None:
    subprocess.run(["osascript", "-e", script], check=True)
