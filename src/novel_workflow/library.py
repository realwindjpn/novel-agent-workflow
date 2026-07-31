from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional


_RUN_OF_DOTS = re.compile(r"\.{2,}")
_WINDOWS_BAD = re.compile(r'[<>:"/\\|?*]')
_RUN_OF_UNDERSCORES = re.compile(r"_+")
_RESERVED = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)

TRASH_DIRECTORY = ".trash"
TRASH_INFO_FILE = ".trash-info.json"


def safe_component(value: str) -> str:
    """Sanitize an arbitrary string into a legal Windows file-system component.

    Rules (deliberately conservative for cross-platform safety):
    - Runs of two or more ASCII dots are collapsed into a single Chinese period
      "。" (so "..." becomes "。").
    - Windows-forbidden characters ``< > : " / \\ | ? *`` are replaced with ``_``;
      adjacent replacements are then collapsed to a single ``_`` so the output
      never carries a run of underscores that came purely from sanitization.
    - Leading/trailing whitespace and trailing dots are removed.
    - Windows reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) are
      prefixed with an underscore.
    """
    if not isinstance(value, str):
        raise TypeError("safe_component requires a str")
    s = _RUN_OF_DOTS.sub("\u3002", value)
    s = _WINDOWS_BAD.sub("_", s)
    s = _RUN_OF_UNDERSCORES.sub("_", s)
    s = s.strip().rstrip(".")
    if s.upper() in _RESERVED:
        s = "_" + s
    return s


def next_book_directory(library: Path, title: str, on_date: Optional[date] = None) -> Path:
    """Return a non-colliding immediate-child directory under ``library``.

    The base name is ``<safe(title)>_<YYYYMMDD>``. If that path exists, the
    suffix ``(N)`` (starting at 1) is appended and incremented until a free
    name is found. ``library`` itself is created if missing so callers do not
    need to pre-create it. The returned path is **not** created on disk; the
    caller decides when to make it.
    """
    if on_date is None:
        on_date = date.today()
    library = Path(library)
    library.mkdir(parents=True, exist_ok=True)
    base = f"{safe_component(title)}_{on_date:%Y%m%d}"
    candidate = library / base
    if not candidate.exists():
        return candidate
    counter = 1
    while True:
        candidate = library / f"{base}({counter})"
        if not candidate.exists():
            return candidate
        counter += 1


@dataclass(frozen=True)
class ProjectEntry:
    directory: str
    title: str
    stage: Optional[str]
    updated_at: Optional[str]
    chapter_count: int
    valid: bool
    error: Optional[str] = None


@dataclass(frozen=True)
class TrashEntry:
    trash_id: str
    original_directory: Optional[str]
    title: Optional[str]
    trashed_at: Optional[str]
    valid: bool
    error: Optional[str] = None


def _safe_resolve(child: Path, library: Path) -> Optional[Path]:
    """Resolve ``child`` against ``library``; reject if it escapes the library."""
    try:
        # Use the child as-is; we never want to follow symlinks that leave the
        # library because the catalog must remain bounded.
        resolved = child.resolve()
    except OSError:
        return None
    try:
        resolved.relative_to(library.resolve())
    except ValueError:
        return None
    return resolved


def next_trash_directory(
    library: Path,
    original_directory: str,
    now: Optional[datetime] = None,
) -> Path:
    library = Path(library)
    trash_root = library / TRASH_DIRECTORY
    if trash_root.is_symlink():
        raise ValueError("symlinked trash directory is not supported")
    trash_root.mkdir(parents=True, exist_ok=True)
    if _safe_resolve(trash_root, library) is None:
        raise ValueError("trash directory escapes the library")
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    instant = instant.astimezone(timezone.utc)
    stamp = instant.strftime("%Y%m%dT%H%M%S%fZ")
    base = f"{stamp}__{safe_component(original_directory)}"
    candidate = trash_root / base
    counter = 1
    while candidate.exists():
        candidate = trash_root / f"{base}({counter})"
        counter += 1
    return candidate


def next_restore_directory(library: Path, original_directory: str) -> Path:
    library = Path(library)
    base = safe_component(original_directory)
    candidate = library / base
    counter = 1
    while candidate.exists():
        candidate = library / f"{base}（恢复{counter}）"
        counter += 1
    return candidate


def _read_trash_entry(child: Path) -> TrashEntry:
    tag = child / TRASH_INFO_FILE
    if not tag.is_file():
        return TrashEntry(child.name, None, None, None, False, "trash tag missing")
    try:
        data = json.loads(tag.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return TrashEntry(child.name, None, None, None, False, f"trash tag unreadable: {exc}")
    original = data.get("original_directory")
    title = data.get("title")
    trashed_at = data.get("trashed_at")
    if (
        data.get("schema_version") != 1
        or not isinstance(original, str) or not original
        or original in {".", "..", TRASH_DIRECTORY}
        or "/" in original or "\\" in original
        or not isinstance(title, str) or not title
        or not isinstance(trashed_at, str) or not trashed_at
    ):
        return TrashEntry(child.name, None, None, None, False, "trash tag invalid")
    return TrashEntry(child.name, original, title, trashed_at, True, None)


def discover_trash(library: Path) -> list[TrashEntry]:
    library = Path(library)
    trash_root = library / TRASH_DIRECTORY
    if not trash_root.is_dir() or trash_root.is_symlink():
        return []
    entries: list[TrashEntry] = []
    for child in sorted(trash_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.is_symlink():
            continue
        if _safe_resolve(child, trash_root) is None:
            continue
        entries.append(_read_trash_entry(child))
    entries.sort(key=lambda e: (e.trashed_at or "", e.trash_id), reverse=True)
    return entries


def _read_project(child: Path) -> ProjectEntry:
    wf = child / "workflow.json"
    directory = child.name
    if not wf.is_file():
        return ProjectEntry(
            directory=directory,
            title=directory,
            stage=None,
            updated_at=None,
            chapter_count=0,
            valid=False,
            error="workflow.json missing",
        )
    try:
        data = json.loads(wf.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ProjectEntry(
            directory=directory,
            title=directory,
            stage=None,
            updated_at=None,
            chapter_count=0,
            valid=False,
            error=f"workflow.json unreadable: {exc}",
        )
    title = data.get("title") or directory
    stage = data.get("stage")
    updated_at = data.get("updated_at")
    chapters = data.get("chapters") or {}
    if isinstance(chapters, dict):
        chapter_count = sum(1 for k in chapters.keys() if str(k).isdigit())
    else:
        chapter_count = 0
    return ProjectEntry(
        directory=directory,
        title=title,
        stage=stage,
        updated_at=updated_at,
        chapter_count=chapter_count,
        valid=True,
        error=None,
    )


def discover_projects(library: Path) -> list[ProjectEntry]:
    """List immediate-child projects of ``library`` as ``ProjectEntry`` records.

    Sub-directories without a readable ``workflow.json`` are returned as
    invalid entries (so the UI can show "broken" projects), and they sort
    last. Valid entries are sorted by ``updated_at`` descending, ties broken
    by ``directory`` descending. The catalog is intentionally non-recursive
    and never follows symlinks whose resolution leaves the library.
    """
    library = Path(library)
    if not library.is_dir():
        return []
    entries: list[ProjectEntry] = []
    for child in sorted(library.iterdir(), key=lambda p: p.name):
        if child.name == TRASH_DIRECTORY:
            continue
        if not child.is_dir() or child.is_symlink():
            # Reject symlinks at the top level outright: a symlink whose
            # target is outside the library could escape the catalog.
            continue
        if _safe_resolve(child, library) is None:
            continue
        entries.append(_read_project(child))

    valid = [e for e in entries if e.valid]
    invalid = [e for e in entries if not e.valid]
    valid.sort(key=lambda e: (e.updated_at or "", e.directory), reverse=True)
    invalid.sort(key=lambda e: e.directory, reverse=True)
    return valid + invalid


def same_title(entries: list[ProjectEntry], title: str) -> list[ProjectEntry]:
    """Return entries whose title matches ``title`` after casefold + strip."""
    needle = title.strip().casefold()
    return [e for e in entries if (e.title or "").strip().casefold() == needle]


def chapter_artifact_dir(chapter: int, on_date: Optional[date] = None) -> Path:
    """Return the relative artifact directory used for ``chapter``'s workspace.

    Layout: ``chapters/第NNN章_YYYYMMDD`` relative to the project root. The
    ``chapter`` argument must be a positive integer; zero and negative values
    raise ``ValueError`` so callers never silently create a bogus directory.
    """
    if not isinstance(chapter, int) or isinstance(chapter, bool):
        raise TypeError("chapter must be an int")
    if chapter < 1:
        raise ValueError("chapter must be >= 1")
    if on_date is None:
        on_date = date.today()
    return Path(f"chapters/\u7b2c{chapter:03d}\u7ae0_{on_date:%Y%m%d}")
