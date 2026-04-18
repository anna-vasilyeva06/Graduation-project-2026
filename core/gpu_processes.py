"""
Процессы с использованием GPU: NVIDIA (nvidia-smi), иначе — топ по системной RAM.
"""
import csv
import subprocess
import sys
from typing import Any, Dict, List, Tuple

from core.processes import get_top_processes


def _subprocess_creationflags() -> int:
    if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        return subprocess.CREATE_NO_WINDOW
    return 0


def nvidia_driver_available() -> bool:
    try:
        r = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_subprocess_creationflags(),
        )
        return r.returncode == 0 and bool((r.stdout or "").strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _nvidia_compute_apps() -> List[Dict[str, Any]]:
    try:
        r = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_gpu_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_subprocess_creationflags(),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if r.returncode != 0 or not (r.stdout or "").strip():
        return []
    rows: List[Dict[str, Any]] = []
    for line in r.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parts = next(csv.reader([line]))
            if len(parts) < 3:
                continue
            pid = int(parts[0].strip())
            name = (parts[1] or "").strip() or "—"
            gpu_mem = float(parts[2].strip())
            rows.append({"pid": pid, "name": name, "gpu_mem_mib": gpu_mem})
        except (ValueError, StopIteration):
            continue
    return rows


def get_top_gpu_vram_rows(n: int = 10) -> Tuple[List[Dict[str, Any]], str]:
    """
    Возвращает (строки, режим): режим "nvidia" | "nvidia_empty" | "ram_fallback".
    """
    apps = _nvidia_compute_apps()
    if apps:
        apps.sort(key=lambda x: x["gpu_mem_mib"], reverse=True)
        return apps[:n], "nvidia"
    if nvidia_driver_available():
        return [], "nvidia_empty"
    return get_top_processes(sort_by="memory", n=n), "ram_fallback"
