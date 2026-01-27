import cpuinfo, psutil

def get_cpu():
    info = cpuinfo.get_cpu_info()
    return {
        "Model": info["brand_raw"],
        "Cores": psutil.cpu_count(logical=False),
        "Threads": psutil.cpu_count(),
        "Frequency MHz": psutil.cpu_freq().current,
        "Load %": psutil.cpu_percent(interval=1)
    }
