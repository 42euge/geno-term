---
name: geno-term-sessions-restart
description: >-
  Restart coding agent sessions in a project tree after a crash by opening them
  as iTerm2 tabs and panes grouped by working directory.
allowed-tools: "Bash(geno-term *) Bash(osascript *)"
argument-hint: "<target_dir>"
metadata:
  author: 42euge
  version: "0.1.0"
---

# Restart sessions

Recover coding agent sessions in a project tree after a crash by restarting them as iTerm2 tabs+panes grouped by cwd.

## Input

`$ARGUMENTS` — the target directory. Defaults to the current working directory if empty.

## Steps

1. Resolve `$ARGUMENTS` (or `pwd`) to an absolute path.
2. Run `geno-term discover "<path>"` and show the user the grouped list.
3. Ask before restarting if more than 8 sessions would open.
4. Run `geno-term restart "<path>"`.
5. Report the number of tabs and panes opened.
