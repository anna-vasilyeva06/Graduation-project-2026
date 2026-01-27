import psutil

def get_battery():
    b = psutil.sensors_battery()
    if not b: return None
    return {
        "Percent": b.percent,
        "Plugged": b.power_plugged,
        "Time left min": None if b.secsleft<0 else int(b.secsleft/60)
    }
