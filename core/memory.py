import os
from collections import defaultdict
from typing import Any, Dict, List

import psutil

_MAX_FILES_PER_DRIVE = 6000
_EXCLUDED: tuple[tuple[str, ...], ...] = (
    ("windows",),
    ("system volume information",),
    ("$recycle.bin",),
    ("recovery",),
    ("program files", "windowsapps"),
    ("program files", "modifiablewindowsapps"),
    ("program files (x86)", "windowsapps"),
)
_SKIP_ROOT_FILES = frozenset({"pagefile.sys", "hiberfil.sys", "swapfile.sys"})


def _n(p: str) -> str:
    return os.path.normcase(os.path.normpath(p))


def _excluded(full: str, root_n: str) -> bool:
    full_n = _n(full)
    if not full_n.startswith(root_n):
        return False
    rel = os.path.relpath(full_n, root_n)
    if rel in (".", os.curdir):
        return False
    parts = [x.lower() for x in rel.split(os.sep) if x and x != "."]
    return any(
        len(parts) >= len(pref) and parts[: len(pref)] == list(pref) for pref in _EXCLUDED
    )


def _rollup_size(dirpath: str, size: int, root_n: str, size_by_dir: Dict[str, int]) -> None:
    path = dirpath
    while True:
        size_by_dir[path] += size
        if _n(path) == root_n:
            break
        parent = os.path.dirname(path)
        if not parent or len(parent) < len(root_n):
            break
        path = parent


def get_memory() -> Dict[str, float]:
    m = psutil.virtual_memory()
    return {
        "Total GB": round(m.total / 1e9, 2),
        "Used GB": round(m.used / 1e9, 2),
        "Free GB": round(m.available / 1e9, 2),
        "Usage %": m.percent,
    }


def _fixed_drive_roots() -> List[str]:
    roots: List[str] = []
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount or not os.path.isdir(mount):
            continue
        drive, _ = os.path.splitdrive(mount)
        if drive and mount.rstrip("\\/") == drive.rstrip("\\/"):
            roots.append(mount)
    if not roots:
        home = os.path.expanduser("~")
        if os.path.isdir(home):
            roots.append(home)
    return roots


def _scan_drive_for_largest(root: str, limit_dirs: int, limit_files: int) -> Dict[str, Any]:
    root_n = _n(root)
    size_by_dir: Dict[str, int] = defaultdict(int)
    size_by_file: Dict[str, int] = {}
    files_seen = 0
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not _excluded(os.path.join(dirpath, d), root_n)]
            for name in filenames:
                if files_seen >= _MAX_FILES_PER_DRIVE:
                    break
                fp = os.path.join(dirpath, name)
                skip_sys = name.lower() in _SKIP_ROOT_FILES and _n(dirpath) == root_n
                if _excluded(fp, root_n) or skip_sys:
                    continue
                try:
                    s = os.path.getsize(fp)
                except OSError:
                    continue
                files_seen += 1
                size_by_file[fp] = s
                _rollup_size(dirpath, s, root_n, size_by_dir)
            if files_seen >= _MAX_FILES_PER_DRIVE:
                break
    except Exception:
        pass

    dirs_sorted = sorted(size_by_dir.items(), key=lambda x: x[1], reverse=True)
    files_sorted = sorted(size_by_file.items(), key=lambda x: x[1], reverse=True)

    return {
        "root": root,
        "scanned_files": files_seen,
        "dirs": [{"path": p, "size_gb": round(sz / 1e9, 2)} for p, sz in dirs_sorted[:limit_dirs]],
        "files": [{"path": p, "size_gb": round(sz / 1e9, 2)} for p, sz in files_sorted[:limit_files]],
    }


def get_largest_paths(limit_dirs: int = 5, limit_files: int = 5) -> Dict[str, object]:
    return {"drives": [_scan_drive_for_largest(r, limit_dirs, limit_files) for r in _fixed_drive_roots()]}
