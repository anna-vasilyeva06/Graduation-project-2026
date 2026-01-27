import subprocess

def get_devices():
    out = subprocess.check_output(
        'wmic path Win32_PnPEntity where "PNPClass=\'Mouse\' or PNPClass=\'Keyboard\' or PNPClass=\'Image\' or PNPClass=\'Bluetooth\' or PNPClass=\'USB\' or PNPClass=\'Sound\'" get Name,PNPClass',
        shell=True
    ).decode("cp866", errors="ignore")

    devices = []
    for line in out.splitlines():
        if "PNPClass" in line or not line.strip():
            continue
        parts = [p for p in line.split("  ") if p.strip()]
        if len(parts) >= 2:
            devices.append({"type": parts[-1].strip(), "name": parts[0].strip()})
    return devices
