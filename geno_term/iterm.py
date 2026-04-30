"""Render and execute AppleScript that opens sessions as iTerm2 tabs/panes."""

from __future__ import annotations

import subprocess
from textwrap import dedent

from .discovery import Session, group_by_cwd


def _quote_as(s: str) -> str:
    """AppleScript string literal — escape backslashes and double quotes."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _sh_quote(s: str) -> str:
    """Single-quote a string for use inside an AppleScript-embedded shell command."""
    return "'" + s.replace("'", "'\\''") + "'"


MAX_PANES_PER_TAB = 6


def _pane_layout(n: int) -> str:
    """Pick a grid shape given pane count."""
    if n <= 1:
        return "single"
    if n <= 3:
        return "vstrip"  # vertical splits, one row
    if n <= 4:
        return "2x2"
    return "3x2"  # up to 6


def build_layout_script(named_commands: list[tuple[str, str]]) -> str:
    """AppleScript for a new iTerm tab split into panes running given commands.

    ``named_commands`` is a list of ``(shell_command, pane_name)`` pairs. One tab
    is created, panes are laid out in a grid sized to the list length, and each
    pane runs its command and takes its name. Callers wrap this in the outer
    ``tell application "iTerm"`` / ``tell current window`` block.
    """
    n = len(named_commands)
    if n == 0:
        raise ValueError("need at least one command")
    if n > MAX_PANES_PER_TAB:
        raise ValueError(f"at most {MAX_PANES_PER_TAB} panes per tab")
    layout = _pane_layout(n)
    cmds = [c for c, _ in named_commands]
    names = [n for _, n in named_commands]

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


def build_fill_tab_script(
    named_commands: list[tuple[str, str]],
    self_session_uid: str,
    include_self: bool = False,
) -> str:
    """AppleScript body that writes commands into panes of the tab containing the caller.

    Locates the target tab by searching every iTerm window for a session whose
    ``unique id`` matches ``self_session_uid`` (the UUID portion of
    ``$ITERM_SESSION_ID``). This is intentional: AppleScript's ``current tab`` is
    the *focused* tab at execution time, which is often not the tab the script
    was launched from — see geno-term#2.

    One command per pane, in iTerm's session order for the tab. The caller's own
    pane is skipped unless ``include_self`` is true. Errors (via AppleScript
    ``error``) if the target tab can't be found or has fewer panes than commands.
    Wrap the return value in ``tell application "iTerm"`` only — this body walks
    windows itself, so a ``tell current window`` wrapper would be wrong.
    """
    n = len(named_commands)
    if n == 0:
        raise ValueError("need at least one command")
    if not self_session_uid:
        raise ValueError("self_session_uid is required to locate the caller's tab")

    lines = [
        f"set myId to {_quote_as(self_session_uid)}",
        "set targetTab to missing value",
        "repeat with w in windows",
        "\trepeat with t in tabs of w",
        "\t\trepeat with s in sessions of t",
        "\t\t\tif unique id of s is myId then",
        "\t\t\t\tset targetTab to t",
        "\t\t\t\texit repeat",
        "\t\t\tend if",
        "\t\tend repeat",
        "\t\tif targetTab is not missing value then exit repeat",
        "\tend repeat",
        "\tif targetTab is not missing value then exit repeat",
        "end repeat",
        "if targetTab is missing value then",
        '\terror "could not locate tab containing the caller; is $ITERM_SESSION_ID set?"',
        "end if",
        "set allSessions to sessions of targetTab",
    ]

    if include_self:
        lines.append("set paneList to allSessions")
    else:
        lines.append("set paneList to {}")
        lines.append("repeat with i from 1 to count of allSessions")
        lines.append("\tset s to item i of allSessions")
        lines.append("\tif unique id of s is not myId then")
        lines.append("\t\tset end of paneList to s")
        lines.append("\tend if")
        lines.append("end repeat")

    lines.append(f"if (count of paneList) < {n} then")
    lines.append(f'\terror "target tab has fewer than {n} available pane(s)"')
    lines.append("end if")

    for i, (cmd, name) in enumerate(named_commands, start=1):
        lines.append(f"tell item {i} of paneList")
        lines.append(f"\twrite text {_quote_as(cmd)}")
        lines.append(f"\tset name to {_quote_as(name)}")
        lines.append("end tell")

    return "\n".join(lines)


def _build_tab_script(cwd: str, sessions: list[Session]) -> str:
    named = [
        (f"cd {_sh_quote(cwd)} && claude --resume {s.session_id}", s.short_topic)
        for s in sessions
    ]
    return build_layout_script(named)


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
