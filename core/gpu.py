import platform
import subprocess
from typing import Any, Dict, List, Optional


def get_gpu() -> List[Dict[str, Any]]:
    """Список видеокарт (минимальная информация по имени)."""
    gpus: List[Dict[str, Any]] = []

    if platform.system() == "Windows":
        out = subprocess.check_output(
            "wmic path win32_VideoController get name",
            shell=True,
        ).decode(errors="ignore").splitlines()
        for line in out:
            if line.strip() and "Name" not in line:
                gpus.append({"Name": line.strip()})
    else:
        out = subprocess.check_output(
            "lspci | grep -i vga",
            shell=True,
        ).decode(errors="ignore").splitlines()
        for line in out:
            gpus.append({"Name": line})

    return gpus


def get_gpu_stats() -> Optional[Dict[str, Any]]:
    """
    Температура и загрузка памяти видеокарты (если доступно).
    Для NVIDIA пытаемся использовать nvidia-smi.
    Возвращает словарь вида:
      {"temperature": float, "mem_used_mb": float, "mem_total_mb": float}
    или None, если данные недоступны.
    """
    try:
        if platform.system().lower() != "windows":
            return None
        # nvidia-smi установлен только для NVIDIA
        cmd = [
            "nvidia-smi",
            "--query-gpu=temperature.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode(
            "utf-8", errors="ignore"
        )
        line = out.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            return None
        temp = float(parts[0])
        mem_used = float(parts[1])
        mem_total = float(parts[2])
        return {
            "temperature": temp,
            "mem_used_mb": mem_used,
            "mem_total_mb": mem_total,
        }
    except Exception:
        return None
