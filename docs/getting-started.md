# Getting Started

## Prerequisites

- macOS with iTerm2
- Python 3.10+
- A supported coding CLI ([geno-tools](https://github.com/42euge/geno-tools))

## Install

```bash
geno-tools install geno-term
```

Or from within an agent session:

```
/geno-tools install geno-term
```

## First use

Discover sessions under a project directory:

```bash
geno-term discover "/path/to/project"
```

Restart them as iTerm tabs and panes:

```bash
geno-term restart "/path/to/project"
```

## How it works

Session transcripts are stored at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. `geno-term` walks that tree, filters sessions whose encoded cwd matches the target directory or any descendant, and generates an AppleScript that opens iTerm tabs with panes grouped by working directory.
