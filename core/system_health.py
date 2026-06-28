import os
import shutil
from typing import Any, Dict, List, Optional

import psutil

CPU_OK = 80
CPU_BAD = 95
RAM_OK = 80
RAM_BAD = 95
DISK_OK = 85
DISK_BAD = 95
BATTERY_LOW = 25
BATTERY_CRITICAL = 10
GPU_OK = 80
GPU_BAD = 95

def _safe_disk_percent(mount: str) -> Optional[float]:
    drive, _ = os.path.splitdrive(mount)
    if not drive:
        return None
    path = drive.upper().rstrip(":\\") + ":\\"
    try:
        u = shutil.disk_usage(path)
        total = float(u.total)
        used = float(u.used)
        if total <= 0:
            return None
        return (used / total) * 100.0
    except (OSError, SystemError, TypeError, ValueError):
        return None

def get_system_health() -> Dict[str, Any]:
    details: List[Dict[str, Any]] = []
    worst = "ok"
    try:
        cpu_pct = psutil.cpu_percent(interval=0.1)
    except Exception:
        cpu_pct = None
    if cpu_pct is not None:
        if cpu_pct >= CPU_BAD:
            details.append({
                "component": "CPU",
                "status": "error",
                "value": f"{cpu_pct:.0f}%",
                "reason": "Очень высокая загрузка процессора - возможны подвисания.",
            })
            worst = "error"
        elif cpu_pct >= CPU_OK:
            details.append({
                "component": "CPU",
                "status": "warning",
                "value": f"{cpu_pct:.0f}%",
                "reason": "Повышенная загрузка CPU.",
            })
            if worst == "ok":
                worst = "warning"
        else:
            details.append({
                "component": "CPU",
                "status": "ok",
                "value": f"{cpu_pct:.0f}%",
                "reason": None,
            })
    else:
        details.append({"component": "CPU", "status": "warning", "value": "-", "reason": "Нет данных."})
        if worst == "ok":
            worst = "warning"

    try:
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
    except Exception:
        ram_pct = None
    if ram_pct is not None:
        if ram_pct >= RAM_BAD:
            details.append({
                "component": "Память (ОЗУ)",
                "status": "error",
                "value": f"{ram_pct:.0f}%",
                "reason": "Критически мало свободной памяти - возможны сбои и тормоза.",
            })
            worst = "error"
        elif ram_pct >= RAM_OK:
            details.append({
                "component": "Память (ОЗУ)",
                "status": "warning",
                "value": f"{ram_pct:.0f}%",
                "reason": "Высокая загрузка ОЗУ.",
            })
            if worst == "ok":
                worst = "warning"
        else:
            details.append({
                "component": "Память (ОЗУ)",
                "status": "ok",
                "value": f"{ram_pct:.0f}%",
                "reason": None,
            })
    else:
        details.append({"component": "Память", "status": "warning", "value": "-", "reason": "Нет данных."})
        if worst == "ok":
            worst = "warning"

    disk_issues: List[str] = []
    _seen_disk_labels = set()
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount:
            continue
        pct = _safe_disk_percent(mount)
        if pct is None:
            continue
        drive, _ = os.path.splitdrive(mount)
        label = (drive.upper().rstrip(":\\") + ":") if drive else mount
        _seen_disk_labels.add(label)
        if pct >= DISK_BAD:
            disk_issues.append(f"{label} {pct:.0f}%")
            details.append({
                "component": f"Диск {label}",
                "status": "error",
                "value": f"{pct:.0f}%",
                "reason": "Критически мало свободного места - возможны ошибки обновлений и установки.",
            })
            worst = "error"
        elif pct >= DISK_OK:
            details.append({
                "component": f"Диск {label}",
                "status": "warning",
                "value": f"{pct:.0f}%",
                "reason": "Мало свободного места. Рекомендуется очистка.",
            })
            if worst == "ok":
                worst = "warning"
        else:
            details.append({
                "component": f"Диск {label}",
                "status": "ok",
                "value": f"{pct:.0f}%",
                "reason": None,
            })

    if not _seen_disk_labels:
        try:
            sys_drive = (os.environ.get("SystemDrive") or "C:").upper().rstrip(":\\") + ":"
            u = shutil.disk_usage(sys_drive + "\\")
            pct = (float(u.used) / float(u.total)) * 100.0 if u.total else 0.0
            label = sys_drive

            if pct >= DISK_BAD:
                details.append({
                    "component": f"Диск {label}",
                    "status": "error",
                    "value": f"{pct:.0f}%",
                    "reason": "Критически мало свободного места - возможны ошибки обновлений и установки.",
                })
                worst = "error"
            elif pct >= DISK_OK:
                details.append({
                    "component": f"Диск {label}",
                    "status": "warning",
                    "value": f"{pct:.0f}%",
                    "reason": "Мало свободного места. Рекомендуется очистка.",
                })
                if worst == "ok":
                    worst = "warning"
            else:
                details.append({
                    "component": f"Диск {label}",
                    "status": "ok",
                    "value": f"{pct:.0f}%",
                    "reason": None,
                })
        except Exception:
            pass

    try:
        bat = psutil.sensors_battery()
    except Exception:
        bat = None
    if bat is not None:
        pct = bat.percent
        if pct <= BATTERY_CRITICAL and not bat.power_plugged:
            details.append({
                "component": "Батарея",
                "status": "error",
                "value": f"{pct:.0f}%",
                "reason": "Критически низкий заряд. Рекомендуется подключить питание.",
            })
            worst = "error"
        elif pct <= BATTERY_LOW and not bat.power_plugged:
            details.append({
                "component": "Батарея",
                "status": "warning",
                "value": f"{pct:.0f}%",
                "reason": "Низкий заряд. Рекомендуется подключить зарядку.",
            })
            if worst == "ok":
                worst = "warning"
        else:
            plugged = " (зарядка)" if bat.power_plugged else ""
            details.append({
                "component": "Батарея",
                "status": "ok",
                "value": f"{pct:.0f}%{plugged}",
                "reason": None,
            })


    online = None
    try:
        from .network import has_internet

        online = bool(has_internet(timeout=1.5))
    except Exception:
        online = None

    if online is False:
        details.append({
            "component": "Сеть",
            "status": "warning",
            "value": "Нет",
            "reason": "Нет подключения к Интернету.",
        })
        if worst == "ok":
            worst = "warning"
    elif online is True:
        details.append({
            "component": "Сеть",
            "status": "ok",
            "value": "Есть",
            "reason": None,
        })
    else:
        details.append({
            "component": "Сеть",
            "status": "warning",
            "value": "—",
            "reason": "Не удалось проверить подключение к Интернету.",
        })
        if worst == "ok":
            worst = "warning"

    gpu_summary_extra = ""
    try:
        from .ml_health import get_gpu_health_snapshot

        snap = get_gpu_health_snapshot()
    except Exception:
        snap = {"util_fraction": None, "source": None, "names": []}
    util_frac = snap.get("util_fraction")
    names = snap.get("names") or []
    primary_name = (names[0] or "").strip() if names else ""

    def _gpu_value_str(pct: float) -> str:
        if primary_name:
            short = primary_name if len(primary_name) <= 40 else primary_name[:37] + "…"
            return f"{pct:.0f}% · {short}"
        return f"{pct:.0f}%"

    if util_frac is not None:
        pct = util_frac * 100.0
        value_str = _gpu_value_str(pct)
        if pct >= GPU_BAD:
            details.append({
                "component": "GPU",
                "status": "error",
                "value": value_str,
                "reason": "Очень высокая загрузка видеокарты - возможны подтормаживания и перегрев.",
            })
            worst = "error"
            gpu_summary_extra = (
                "Видеокарта сильно загружена - закройте тяжёлые игры и рендер, снизьте настройки графики, проверьте охлаждение."
            )
        elif pct >= GPU_OK:
            details.append({
                "component": "GPU",
                "status": "warning",
                "value": value_str,
                "reason": "Повышенная загрузка GPU.",
            })
            if worst == "ok":
                worst = "warning"
            gpu_summary_extra = (
                "Загрузка GPU повышена - при необходимости закройте приложения с 3D и снизьте качество изображения."
            )
        else:
            details.append({
                "component": "GPU",
                "status": "ok",
                "value": value_str,
                "reason": None,
            })
    elif primary_name:
        short = primary_name if len(primary_name) <= 48 else primary_name[:45] + "…"
        details.append({
            "component": "GPU",
            "status": "ok",
            "value": short,
            "reason": "Текущая загрузка недоступна; подробности - в разделе «GPU».",
        })
    else:
        details.append({
            "component": "GPU",
            "status": "warning",
            "value": "—",
            "reason": "Не удалось определить видеокарту или снять загрузку.",
        })
        if worst == "ok":
            worst = "warning"

    if worst == "error":
        message = "Критическое состояние: обнаружены критические проблемы."
        summary = "Рекомендуется снизить нагрузку (закрыть программы), освободить место на дисках или подключить питание."
    elif worst == "warning":
        message = "Система в целом работоспособна, но есть замечания."
        summary = "Обратите внимание на компоненты со статусом предупреждение и при необходимости освободите ресурсы или место."
    else:
        message = "Система исправна: все ключевые компоненты в норме."
        summary = "Продолжайте работу. Рекомендуется периодически проверять состояние дисков и памяти."
    if gpu_summary_extra:
        summary = (summary.rstrip() + " " + gpu_summary_extra).strip()

    ml_info: Optional[Dict[str, Any]] = None
    try:
        from .ml_health import predict_only
        ml_info = predict_only()
    except Exception:
        pass

    return {
        "status": worst,
        "message": message,
        "details": details,
        "summary": summary,
        "ml": ml_info,
    }
