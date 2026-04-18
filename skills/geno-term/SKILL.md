---
name: geno-term
description: >-
  Recover crashed Claude Code sessions in a project tree. Discovers every
  session whose cwd is under a target directory, then restarts them as
  iTerm2 tabs with panes grouped by cwd. Use when the user says their
  window server crashed, sessions vanished, or asks to "restart all my
  sessions" / "find my lost sessions" in a project.
allowed-tools: "Bash(geno-term *) Bash(osascript *)"
argument-hint: "[discover|restart] <target_dir>"
---

# geno-term — Claude Code Session Recovery

When a macOS window server crash or accidental quit kills iTerm, Claude Code session transcripts on disk survive. This skill finds them and puts them back.

## Commands

### `/geno-term discover <dir>`
Scan `~/.claude/projects/` for sessions whose cwd is `<dir>` or any descendant. Shows session IDs and topics grouped by cwd. Read-only.

```bash
geno-term discover "$TARGET"
```

### `/geno-term restart <dir>`
Discover sessions under `<dir>`, then open iTerm tabs — one per distinct cwd — and split each tab into panes, one per session sharing that cwd. Each pane runs `claude --resume <id>`.

```bash
geno-term restart "$TARGET"
```

Add `--close <name>` (repeatable) if a previous flat-tab run left old tabs around that should be closed first. Use `--print-only` to inspect the generated AppleScript.

## When to use

- User reports a window server / display crash and wants prior Claude Code work back.
- User asks what sessions were running in a project before a reboot.
- User says "restart all my sessions in <project>".

## Layout rules

One tab per distinct cwd. Pane count determines grid:

- 1 session → single pane
- 2–3 sessions → vertical strip
- 4 sessions → 2×2
- 5–6 sessions → 3×2

More than 6 sessions sharing a cwd means multiple tabs for that cwd — the CLI handles this by splitting into chunks (future work).

## Caveats

- macOS + iTerm2 only.
- Sessions that hit a rate limit before the crash may still be limited on resume.
- If a session already resumed earlier in the day, `claude --resume` continues the same JSONL — no fork.
