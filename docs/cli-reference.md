# CLI Reference

## `geno-term discover <target_dir>`

Scan `~/.claude/projects/` for sessions whose working directory is `<target_dir>` or any descendant. Shows session IDs and topics grouped by cwd. Read-only.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--within-hours N` | None | Only sessions within N hours of the newest |

## `geno-term restart <target_dir>`

Discover sessions under `<target_dir>`, then open iTerm tabs (one per distinct cwd) and split each tab into panes (one per session). Each pane runs `claude --resume <id>`.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--within-hours N` | 1.0 | Only restart sessions within N hours of the newest |
| `--close <name>` | — | Tab name to close before opening (repeatable) |
| `--print-only` | false | Print the AppleScript instead of running it |

## Layout rules

One tab per distinct working directory. Pane count determines grid layout:

| Sessions | Layout |
|----------|--------|
| 1 | Single pane |
| 2-3 | Vertical strip |
| 4 | 2x2 grid |
| 5-6 | 3x2 grid |

More than 6 sessions sharing a cwd produces multiple tabs for that cwd.
