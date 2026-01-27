import platform, subprocess

def get_gpu():
    gpus = []

    if platform.system() == "Windows":
        out = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode(errors="ignore").splitlines()
        for line in out:
            if line.strip() and "Name" not in line:
                gpus.append({"Name": line.strip()})
    else:
        out = subprocess.check_output("lspci | grep -i vga", shell=True).decode().splitlines()
        for line in out:
            gpus.append({"Name": line})

    return gpus
