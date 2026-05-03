import time
from typing import Any
import psutil
def get_top_processes(sort_by: str = "cpu", n: int = 10) -> list[dict[str, Any]]:
    try:
        procs = list(psutil.process_iter())
    except Exception:
        return []
    key = "cpu" if sort_by == "cpu" else "memory"
    if key == "cpu":
        for p in procs:
            try:
                p.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(0.2)
    out: list[dict[str, Any]] = []
    for p in procs:
        try:
            out.append(
                {
                    "pid": p.pid,
                    "name": p.name() or "-",
                    "cpu": p.cpu_percent(),
                    "memory": p.memory_percent(),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    out.sort(key=lambda x: x.get(key) or 0.0, reverse=True)
    return out[:n]
