# geno-term

Terminal automation for coding agent session recovery.

When the macOS window server crashes (or you close iTerm without meaning to), coding agent sessions on disk survive — but the running processes don't. `geno-term` discovers those sessions and restarts them as iTerm2 tabs and panes, grouped by working directory.

## Install

```bash
geno-tools install geno-term
```

Or from within an agent session:

```
/geno-tools install geno-term
```

## Use

```bash
# List sessions under a directory and its children
geno-term discover "/path/to/project"

# Restart every session found, grouped into iTerm tabs + panes by cwd
geno-term restart "/path/to/project"

# Launch fresh command sessions (one per task) from a JSON spec
geno-term launch --spec tasks.json
```

### `launch` spec format

```json
[
  {
    "cwd": "/abs/path/to/repo-a",
    "command": "clauded",
    "prompt": "Work on issue #2 — start with `gh issue view 2 ...`",
    "name": "i2"
  },
  {
    "cwd": "/abs/path/to/repo-b",
    "command": "clauded",
    "prompt": "Scaffold the new product — start by reading issue #4",
    "name": "i4"
  }
]
```

`command` defaults to `clauded`. `prompt`, if set, is passed as one quoted
argv to the command — handy for seeding a Claude Code session with starting
context. Tasks are grouped into tabs by `cwd`, same layout rules as `restart`.

#### Filling the current tab instead of creating new ones

```bash
# Write one task per existing pane in the current iTerm tab.
# The pane running geno-term is skipped so you don't nuke yourself.
geno-term launch --spec tasks.json --in-current-tab
```

Use this when you've already split a tab into the layout you want and just
need commands written into the panes. Panes are targeted in iTerm's session
order. Pass `--include-current-pane` to also target the running pane.

## How it works

Session transcripts are stored at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. `geno-term` walks that tree, filters to sessions whose encoded cwd matches the target directory or any descendant, extracts the real cwd from each JSONL, then emits an AppleScript that:

1. Opens one iTerm2 tab per distinct cwd.
2. Splits the tab into panes — one per session sharing that cwd (3x2 grid for 6, vertical strip for 2-3, single pane for 1).
3. Runs `cd <cwd> && claude --resume <session-id>` in each pane, with the tab/pane named after a short topic extracted from the session's first user message.

## Scope

macOS + iTerm2 only. Extending to tmux or other terminals is straightforward — swap the renderer in `geno_term/iterm.py`.
