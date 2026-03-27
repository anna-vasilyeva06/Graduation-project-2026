import datetime
import platform
import socket
import subprocess
import psutil
import uuid
import os


def _get_bios_version() -> str:
    """Версия BIOS/UEFI (Windows) или '—' при ошибке/неподдерживаемой ОС."""
    try:
        if platform.system().lower() != "windows":
            return "—"
        # wmic часто есть «из коробки», не требует дополнительных зависимостей
        out = subprocess.check_output(
            ["wmic", "bios", "get", "smbiosbiosversion", "/value"],
            shell=False,
            stderr=subprocess.DEVNULL,
        ).decode(errors="ignore")
        for line in out.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip().lower() == "smbiosbiosversion":
                value = value.strip()
                return value or "—"
    except Exception:
        pass
    return "—"


def _get_last_windows_update() -> str:
    """
    Дата последнего установленного обновления Windows.
    Возвращает человекочитаемую строку или '—' при ошибке.
    """
    try:
        if platform.system().lower() != "windows":
            return "—"
        # Берём самое свежее обновление по полю InstalledOn
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-HotFix | Sort-Object InstalledOn | Select-Object -Last 1).InstalledOn | Out-String"
        ]
        raw = subprocess.check_output(cmd, shell=True)
        txt = raw.decode("utf-8", errors="ignore").strip()
        # PowerShell может вернуть пустую строку
        return txt or "—"
    except Exception:
        return "—"

def get_total_disk_gb():
    total = 0
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            total += usage.total
        except:
            pass
    return round(total/1e9,2)

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
        "bios": _get_bios_version(),
        "last_update": _get_last_windows_update(),
    }
