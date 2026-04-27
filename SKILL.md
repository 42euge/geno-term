---
name: geno-term
description: >-
  Terminal automation for coding agent session recovery. Discover and restart
  crashed sessions as iTerm2 tabs and panes grouped by working directory.
  Use when the user says their window server crashed, sessions vanished,
  or asks to restart or find lost sessions in a project.
allowed-tools: "Bash(geno-term *) Bash(osascript *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-term — Session Recovery

Discover and restart crashed coding agent sessions as iTerm2 tabs and panes, grouped by working directory.

## Available commands

| Command | Description |
|---------|-------------|
| `/geno-term-sessions-restart` | Restart sessions under a project tree as iTerm tabs+panes |

## When to use

- User reports a window server / display crash and wants prior work back.
- User asks what sessions were running in a project before a reboot.
- User says "restart all my sessions in <project>".
