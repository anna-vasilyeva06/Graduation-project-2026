import datetime
import platform
import socket
import psutil
import uuid
import os

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
    }
