# geno-term

Terminal automation for Claude Code session recovery.

When the macOS window server crashes (or you close iTerm without meaning to), Claude Code sessions on disk survive — but the running processes don't. `geno-term` discovers those sessions and restarts them as iTerm2 tabs and panes, grouped by working directory.

## Install

```bash
pip install -e .
```

Adds a `geno-term` CLI.

## Use

```bash
# List sessions under a directory and its children
geno-term discover "/path/to/project"

# Restart every session found, grouped into iTerm tabs + panes by cwd
geno-term restart "/path/to/project"
```

## How it works

Claude Code stores session transcripts at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. `geno-term` walks that tree, filters to sessions whose encoded cwd matches the target directory or any descendant, extracts the real cwd from each JSONL, then emits an AppleScript that:

1. Opens one iTerm2 tab per distinct cwd.
2. Splits the tab into panes — one per session sharing that cwd (3×2 grid for 6, vertical strip for 2–3, single pane for 1).
3. Runs `cd <cwd> && claude --resume <session-id>` in each pane, with the tab/pane named after a short topic extracted from the session's first user message.

## Scope

macOS + iTerm2 only. Extending to tmux or other terminals is straightforward — swap the renderer in `geno_term/iterm.py`.
