"""
Топ процессов по загрузке CPU и RAM.
"""
import time
from typing import Any, Dict, List

import psutil


def get_top_processes(sort_by: str = "cpu", n: int = 10) -> List[Dict[str, Any]]:
    """
    Возвращает топ-n процессов по CPU или RAM.
    sort_by: "cpu" | "memory"
    """
    result: List[Dict[str, Any]] = []

    try:
        procs = list(psutil.process_iter())
    except Exception:
        return []

    if sort_by == "cpu":
        for p in procs:
            try:
                p.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(0.2)
        for p in procs:
            try:
                cpu = p.cpu_percent()
                mem = p.memory_percent()
                name = p.name() or "—"
                result.append({"pid": p.pid, "name": name, "cpu": cpu, "memory": mem})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        result.sort(key=lambda x: x["cpu"], reverse=True)
    else:
        for p in procs:
            try:
                cpu = p.cpu_percent()
                mem = p.memory_percent()
                name = p.name() or "—"
                result.append({"pid": p.pid, "name": name, "cpu": cpu, "memory": mem})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        result.sort(key=lambda x: x["memory"], reverse=True)

    return result[:n]
