import psutil


def _get_capacity_info():
    """
    Расчётная и номинальная ёмкость батареи (Windows / WMI), если доступно.
    Возвращает словарь с полями design_mwh, full_mwh, wear_percent или None.
    """
    try:
        import wmi

        c = wmi.WMI()
        bats = c.Win32_Battery()
        if not bats:
            return None
        b = bats[0]
        design = getattr(b, "DesignCapacity", None)
        full = getattr(b, "FullChargeCapacity", None)
        if not design or not full:
            return None
        wear = max(0.0, 100.0 - (full / design) * 100.0)
        return {
            "design_mwh": float(design),
            "full_mwh": float(full),
            "wear_percent": round(wear, 1),
        }
    except Exception:
        return None


def get_battery():
    b = psutil.sensors_battery()
    if not b:
        return None
    data = {
        "Percent": b.percent,
        "Plugged": b.power_plugged,
        "Time left min": None if b.secsleft < 0 else int(b.secsleft / 60),
    }
    extra = _get_capacity_info()
    if extra:
        data["Design mWh"] = extra["design_mwh"]
        data["Full mWh"] = extra["full_mwh"]
        data["WearPercent"] = extra["wear_percent"]
    return data
