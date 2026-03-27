import cpuinfo
import psutil


def get_cpu():
    info = cpuinfo.get_cpu_info()
    freq = None
    try:
        f = psutil.cpu_freq()
        freq = f.current if f else None
    except Exception:
        freq = None
    return {
        "Model": info.get("brand_raw", ""),
        "Cores": psutil.cpu_count(logical=False),
        "Threads": psutil.cpu_count(),
        "Frequency MHz": freq,
        "Load %": psutil.cpu_percent(interval=0.5),
    }


def get_cpu_temperature():
    """
    Средняя температура CPU по доступным датчикам.
    На некоторых системах может быть недоступна → возвращает None.
    """
    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        return None
    if not temps:
        return None
    values = []
    for entries in temps.values():
        for e in entries:
            cur = getattr(e, "current", None)
            if cur is not None:
                values.append(cur)
    if not values:
        return None
    return round(sum(values) / len(values), 1)
