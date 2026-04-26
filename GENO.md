# geno-term — terminal automation for session recovery

Discover and restart crashed coding agent sessions as iTerm2 tabs and panes, grouped by working directory. macOS + iTerm2 only.

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-term | — | — (umbrella) |
| geno-term-sessions-restart | sessions | /geno-term-sessions-restart |

## Repo structure

```
geno-term/
├── GENO.md              # agent instructions (this file)
├── SKILL.md             # umbrella skill manifest
├── genotools.yaml       # geno-tools manifest
├── skills/              # skill definitions
│   ├── geno-term/       #   umbrella
│   └── geno-term-sessions-restart/  #   restart sessions
├── geno_term/           # Python package
│   ├── cli.py           #   Click CLI entry point
│   ├── discovery.py     #   session discovery from ~/.claude/projects/
│   └── iterm.py         #   AppleScript renderer for iTerm2
├── docs/                # MkDocs Material site
└── pyproject.toml       # Python package config
```

## How it works

Session transcripts are stored at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. `geno-term` walks that tree, filters sessions whose encoded cwd matches a target directory or any descendant, extracts the real cwd from each JSONL, and generates an AppleScript that:

1. Opens one iTerm2 tab per distinct cwd.
2. Splits the tab into panes (layout depends on session count: single, vertical strip, 2x2, or 3x2 grid).
3. Runs `cd <cwd> && claude --resume <session-id>` in each pane with a topic-derived name.

## CLI commands

```bash
# List sessions under a directory
geno-term discover "/path/to/project"

# Restart sessions as iTerm tabs+panes
geno-term restart "/path/to/project"
```

Options: `--within-hours N` (time window filter), `--close <name>` (close old tabs first), `--print-only` (inspect AppleScript).

## Conventions

- Skills live under `skills/` with a `SKILL.md` in each directory.
- The Python package is `geno_term` with entry point `geno_term.cli:main`.
- macOS + iTerm2 is the only supported platform. Extending to tmux would mean swapping the renderer in `geno_term/iterm.py`.
