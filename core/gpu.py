import subprocess
def get_gpu():
    gpus = []
    out = subprocess.check_output(
        "wmic path win32_VideoController get name", shell=True
    ).decode(errors="ignore").splitlines()
    for line in out:
        if line.strip() and "Name" not in line:
            gpus.append({"Name": line.strip()})
    return gpus
