"""Find coding agent sessions on disk for a given target directory."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"


@dataclass
class Session:
    session_id: str
    cwd: str
    jsonl_path: Path
    mtime: float
    topic: str

    @property
    def short_topic(self) -> str:
        return _slugify(self.topic)[:32] or self.session_id[:8]


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _extract_topic(first_user_text: str | None) -> str:
    if not first_user_text:
        return ""
    # First meaningful line, trimmed
    for line in first_user_text.splitlines():
        line = line.strip()
        if line and not line.startswith("<") and not line.startswith("["):
            return line[:80]
    return ""


def _read_session(jsonl_path: Path) -> Session | None:
    cwd = None
    first_user_text = None
    try:
        with jsonl_path.open() as fp:
            for line in fp:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if cwd is None and d.get("cwd"):
                    cwd = d["cwd"]
                if first_user_text is None and d.get("type") == "user" and not d.get("isMeta") and not d.get("isSidechain"):
                    msg = d.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        text = " ".join(
                            c.get("text", "")
                            for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        )
                    else:
                        text = ""
                    if text and not text.startswith("<") and not text.startswith("[Request"):
                        first_user_text = text
                if cwd and first_user_text:
                    break
    except OSError:
        return None
    if not cwd:
        return None
    sid = jsonl_path.stem
    return Session(
        session_id=sid,
        cwd=cwd,
        jsonl_path=jsonl_path,
        mtime=jsonl_path.stat().st_mtime,
        topic=_extract_topic(first_user_text),
    )


def discover(target_dir: str | Path, within_hours: float | None = None) -> list[Session]:
    """Find sessions whose cwd is target_dir or a descendant of it.

    If within_hours is set, only include sessions whose JSONL mtime is within
    that many hours of the most recent session found — useful for isolating
    the cluster that was active when a crash hit.
    """
    import time

    target = str(Path(target_dir).resolve())
    out: list[Session] = []
    if not PROJECTS_DIR.is_dir():
        return out
    for proj_dir in PROJECTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        for jsonl in proj_dir.glob("*.jsonl"):
            s = _read_session(jsonl)
            if s is None:
                continue
            cwd = s.cwd
            if cwd == target or cwd.startswith(target + os.sep):
                out.append(s)
    if within_hours is not None and out:
        newest = max(s.mtime for s in out)
        cutoff = newest - within_hours * 3600
        out = [s for s in out if s.mtime >= cutoff]
    out.sort(key=lambda s: (s.cwd, -s.mtime))
    return out


def group_by_cwd(sessions: list[Session]) -> dict[str, list[Session]]:
    groups: dict[str, list[Session]] = {}
    for s in sessions:
        groups.setdefault(s.cwd, []).append(s)
    return groups
