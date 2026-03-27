"""
ML-модуль оценки состояния системы: рассматривает CPU, GPU, память, батарею,
диски и сеть как элементы одной системы и выносит общий вердикт — исправна или нет.
"""
import datetime
import json
import os
from typing import Any, Dict, List, Optional

import psutil

# Пороги (в процентах или флагах)
CPU_OK = 85
CPU_BAD = 95
RAM_OK = 85
RAM_BAD = 95
DISK_OK = 90
DISK_BAD = 95
BATTERY_LOW = 20
BATTERY_CRITICAL = 10

_HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "health_history.jsonl")


def get_health_history_path() -> str:
    """Полный путь к файлу журнала проверок здоровья системы."""
    return _HISTORY_PATH


def append_health_history(status: str) -> None:
    """Добавляет запись о проверке здоровья системы в историю (jsonl-файл)."""
    rec = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "status": status,
    }
    try:
        with open(_HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        # История — вспомогательная функция, не должна ломать основную логику
        pass


def _safe_disk_percent(mount: str) -> Optional[float]:
    """Безопасно возвращает процент заполнения диска."""
    drive, _ = os.path.splitdrive(mount)
    if not drive:
        return None
    if os.name == "nt":
        path = drive.upper().rstrip(":\\") + ":\\"
    else:
        path = os.path.normpath(mount)
    try:
        u = psutil.disk_usage(path)
        return u.percent
    except (OSError, SystemError, TypeError, ValueError):
        return None


def get_system_health() -> Dict[str, Any]:
    """
    Собирает метрики по всем подсистемам (CPU, память, диски, батарея, сеть, GPU),
    оценивает каждую по порогам и выносит общий прогноз по системе.

    Возвращает:
    - status: "ok" | "warning" | "error"
    - message: краткий вердикт
    - details: список {"component", "status", "value", "reason"}
    - summary: рекомендация (что сделать)
    """
    details: List[Dict[str, Any]] = []
    worst = "ok"  # ok < warning < error

    # --- CPU ---
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
                "reason": "Очень высокая загрузка процессора — возможны подвисания.",
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
        details.append({"component": "CPU", "status": "warning", "value": "—", "reason": "Нет данных."})
        if worst == "ok":
            worst = "warning"

    # --- Память (ОЗУ) ---
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
                "reason": "Критически мало свободной памяти — возможны сбои и тормоза.",
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
        details.append({"component": "Память", "status": "warning", "value": "—", "reason": "Нет данных."})
        if worst == "ok":
            worst = "warning"

    # --- Диски ---
    disk_issues: List[str] = []
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount:
            continue
        pct = _safe_disk_percent(mount)
        if pct is None:
            continue
        drive, _ = os.path.splitdrive(mount)
        label = (drive.upper().rstrip(":\\") + ":") if drive else mount
        if pct >= DISK_BAD:
            disk_issues.append(f"{label} {pct:.0f}%")
            details.append({
                "component": f"Диск {label}",
                "status": "error",
                "value": f"{pct:.0f}%",
                "reason": "Критически мало свободного места — возможны ошибки обновлений и установки.",
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

    # --- Батарея ---
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
    # Если батареи нет — не добавляем в список (стационарный ПК)

    # --- Сеть ---
    try:
        stats = psutil.net_if_stats()
        up_count = sum(1 for s in stats.values() if s.isup)
    except Exception:
        up_count = 0
    if up_count > 0:
        details.append({
            "component": "Сеть",
            "status": "ok",
            "value": f"Активных интерфейсов: {up_count}",
            "reason": None,
        })
    else:
        details.append({
            "component": "Сеть",
            "status": "warning",
            "value": "0",
            "reason": "Нет активных подключений (возможно, вы offline).",
        })
        if worst == "ok":
            worst = "warning"

    # --- GPU ---
    try:
        from .gpu import get_gpu
        gpus = get_gpu()
        has_gpu = len(gpus) > 0
    except Exception:
        has_gpu = False
    if has_gpu:
        details.append({
            "component": "GPU",
            "status": "ok",
            "value": "Обнаружен",
            "reason": None,
        })
    else:
        details.append({
            "component": "GPU",
            "status": "warning",
            "value": "—",
            "reason": "Не удалось определить видеокарту.",
        })
        if worst == "ok":
            worst = "warning"

    # --- Итог и рекомендация ---
    if worst == "error":
        message = "Система неисправна: обнаружены критические проблемы."
        summary = "Рекомендуется снизить нагрузку (закрыть программы), освободить место на дисках или подключить питание (ноутбук)."
    elif worst == "warning":
        message = "Система в целом работоспособна, но есть замечания."
        summary = "Обратите внимание на компоненты со статусом «предупреждение» и при необходимости освободите ресурсы или место."
    else:
        message = "Система исправна: все ключевые компоненты в норме."
        summary = "Продолжайте работу. Рекомендуется периодически проверять состояние дисков и памяти."

    # Записываем факт проверки в историю (по итоговому статусу правил)
    try:
        append_health_history(worst)
    except Exception:
        pass

    # Оценка по предобученной модели (без записи и переобучения)
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
