import os
from collections import defaultdict
from typing import Dict, List

import psutil


def get_memory() -> Dict[str, float]:
    m = psutil.virtual_memory()
    return {
        "Total GB": round(m.total / 1e9, 2),
        "Used GB": round(m.used / 1e9, 2),
        "Free GB": round(m.available / 1e9, 2),
        "Usage %": m.percent,
    }


def get_largest_paths(limit_dirs: int = 5, limit_files: int = 5) -> Dict[str, object]:

    drives = []
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount or not os.path.isdir(mount):
            continue

        drive, _ = os.path.splitdrive(mount)
        if drive and mount.rstrip("\\/") == drive.rstrip("\\/"):
            drives.append(mount)

    if not drives:
        home = os.path.expanduser("~")
        if os.path.isdir(home):
            drives = [home]

    MAX_FILES_PER_DRIVE = 6000
    result_drives: List[Dict[str, object]] = []

    for root in drives:
        size_by_dir = defaultdict(int)
        size_by_file: Dict[str, int] = {}
        files_seen = 0

        try:
            for dirpath, dirnames, filenames in os.walk(root):
                for name in filenames:
                    if files_seen >= MAX_FILES_PER_DRIVE:
                        break

                    fp = os.path.join(dirpath, name)
                    try:
                        s = os.path.getsize(fp)
                    except OSError:
                        continue

                    files_seen += 1
                    size_by_file[fp] = s

                    path = dirpath
                    while True:
                        size_by_dir[path] += s
                        if path == root:
                            break
                        parent = os.path.dirname(path)
                        if not parent or len(parent) < len(root):
                            break
                        path = parent

                if files_seen >= MAX_FILES_PER_DRIVE:
                    break
        except Exception:
            pass

        dirs_sorted = sorted(size_by_dir.items(), key=lambda x: x[1], reverse=True)
        files_sorted = sorted(size_by_file.items(), key=lambda x: x[1], reverse=True)

        dirs_out: List[Dict[str, object]] = [
            {"path": p, "size_gb": round(sz / 1e9, 2)}
            for p, sz in dirs_sorted[:limit_dirs]
        ]
        files_out: List[Dict[str, object]] = [
            {"path": p, "size_gb": round(sz / 1e9, 2)}
            for p, sz in files_sorted[:limit_files]
        ]

        result_drives.append(
            {
                "root": root,
                "scanned_files": files_seen,
                "dirs": dirs_out,
                "files": files_out,
            }
        )

    if result_drives:
        first = result_drives[0]
        return {
            "root": first["root"],
            "scanned_files": first["scanned_files"],
            "dirs": first["dirs"],
            "files": first["files"],
            "drives": result_drives,
        }

    return {"root": "", "scanned_files": 0, "dirs": [], "files": [], "drives": []}

