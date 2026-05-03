import datetime
import os
import platform
import socket
import uuid

import psutil


def _total_disk_gb_wmi() -> int:
    """Запасной подсчёт на Windows, если psutil не дал ни одного успешного тома."""
    try:
        import wmi

        c = wmi.WMI()
        total = 0
        for d in c.Win32_LogicalDisk():
            try:
                if d.Size is None:
                    continue
                dt = int(d.DriveType or 0)
                if dt not in (2, 3):
                    continue
                total += int(d.Size)
            except (TypeError, ValueError):
                continue
        return total
    except Exception:
        return 0


def get_total_disk_gb():
    """
    Суммарный объём локальных томов (фиксированные + съёмные), без сетевых и CD.
    Возвращает число ГБ или None, если данных нет.
    """
    total_bytes = 0
    for p in psutil.disk_partitions(all=True):
        mp = p.mountpoint
        if not mp:
            continue
        opts = (p.opts or "").lower()
        if "cdrom" in opts or "remote" in opts or "network" in opts:
            continue
        try:
            if not os.path.exists(mp):
                continue
            u = psutil.disk_usage(mp)
            total_bytes += u.total
        except (OSError, PermissionError, FileNotFoundError, SystemError):
            continue

    if total_bytes <= 0:
        total_bytes = _total_disk_gb_wmi()

    if total_bytes <= 0:
        return None
    return round(total_bytes / 1e9, 2)

def get_system_info():
    boot_ts = psutil.boot_time()
    boot_dt = datetime.datetime.fromtimestamp(boot_ts)
    uptime = datetime.datetime.now() - boot_dt

    mem = psutil.virtual_memory()

    return {
        "os": platform.platform(),
        "pc_name": socket.gethostname(),
        "user": socket.getfqdn(),
        "cpu": platform.processor(),
        "architecture": platform.machine(),
        "ram_gb": round(mem.total / 1e9, 2),
        "ram_used_gb": round(mem.used / 1e9, 2),
        "ram_usage_percent": mem.percent,
        "total_disk_gb": get_total_disk_gb(),
        "mac": hex(uuid.getnode()),
        "boot_time": boot_dt.strftime("%d.%m.%Y %H:%M"),
        "uptime": str(uptime).split(".")[0],
        "battery_percent": psutil.sensors_battery().percent if psutil.sensors_battery() else None,
    }
