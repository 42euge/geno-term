# Restart Claude Code sessions

Recover Claude Code sessions in a project tree after a crash by restarting them as iTerm2 tabs+panes grouped by cwd.

## Input

`$ARGUMENTS` — the target directory. Defaults to the current working directory if empty.

## Steps

1. Resolve `$ARGUMENTS` (or `pwd`) to an absolute path.
2. Run `geno-term discover "<path>"` and show the user the grouped list.
3. Ask before restarting if more than 8 sessions would open.
4. Run `geno-term restart "<path>"`.
5. Report the number of tabs and panes opened.
