import re
import socket
import subprocess
from typing import Any

import psutil

_IFACE_ORDER = {"Wi-Fi": 0, "Ethernet": 1, "Сеть": 2, "Bluetooth": 3, "Loopback": 4}
_AF_LINK = getattr(psutil, "AF_LINK", None)
_AF_PACKET = getattr(socket, "AF_PACKET", None)


def _interface_type(name: str) -> str:
    ln = name.lower()
    if "wi-fi" in ln or "wireless" in ln or "wlan" in ln:
        return "Wi-Fi"
    if "ethernet" in ln or "eth" in ln:
        return "Ethernet"
    if "bluetooth" in ln:
        return "Bluetooth"
    if "loopback" in ln or ln == "lo":
        return "Loopback"
    return "Сеть"


def _collect_addresses(addr_list: list) -> tuple[list[str], list[str], str]:
    ipv4: list[str] = []
    ipv6: list[str] = []
    mac = ""
    for a in addr_list:
        fam = a.family
        if fam == socket.AF_INET:
            ipv4.append(a.address)
        elif fam == socket.AF_INET6 and not (a.address or "").startswith("::1"):
            ipv6.append(a.address)
        elif _AF_PACKET is not None and fam == _AF_PACKET:
            mac = a.address or mac
        elif _AF_LINK is not None and fam == _AF_LINK:
            mac = a.address or mac
    return ipv4, ipv6, mac


def get_network_info() -> list[dict[str, Any]]:
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    out: list[dict[str, Any]] = []
    for name, addr_list in addrs.items():
        stat = stats.get(name)
        if not stat or not stat.isup:
            continue
        ipv4, ipv6, mac = _collect_addresses(addr_list)
        itype = _interface_type(name)
        if itype == "Loopback" and not ipv4:
            continue
        speed_mbps = getattr(stat, "speed", None) or 0
        out.append({
            "name": name,
            "type": itype,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "mac": mac,
            "speed": f"{speed_mbps} Мбит/с" if speed_mbps > 0 else "—",
            "mtu": getattr(stat, "mtu", None) or "—",
        })
    out.sort(key=lambda x: (_IFACE_ORDER.get(x["type"], 5), x["name"]))
    return out


def _host_ping_hint(hostname: str) -> str:
    try:
        ip = socket.gethostbyname(hostname.strip())
        h = hostname.strip()
        return f" ({h} → {ip})" if ip != h else ""
    except OSError:
        return ""


def ping_host(hostname: str, count: int = 1, timeout_sec: int = 5) -> tuple[bool, str]:
    if not hostname or not hostname.strip():
        return False, "Укажите хост"
    hostname = hostname.strip()
    hint = _host_ping_hint(hostname)
    cmd = ["ping", "-n", str(count), "-w", str(timeout_sec * 1000), hostname]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec + 2,
            encoding="utf-8",
            errors="replace",
        )
        txt = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0:
            return False, f"Недоступен (код {r.returncode})"
        m = re.search(r"(?:time|время)\s*=\s*(\d+(?:\.\d+)?)\s*(?:ms|мс)?", txt, re.I)
        if m:
            return True, f"Доступен{hint}, время отклика: {m.group(1)} мс"
        return True, f"Доступен{hint}"
    except subprocess.TimeoutExpired:
        return False, "Таймаут"
    except FileNotFoundError:
        return False, "Команда ping не найдена"
    except OSError as e:
        return False, str(e)


def check_port(hostname: str, port: int, timeout: float = 5.0) -> tuple[bool, str]:
    if not hostname or not hostname.strip():
        return False, "Укажите хост"
    if not (1 <= port <= 65535):
        return False, "Порт должен быть 1-65535"
    hostname = hostname.strip()
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            pass
        return True, f"Порт {port} открыт"
    except TimeoutError:
        return False, f"Таймаут (порт {port})"
    except ConnectionRefusedError:
        return False, f"Порт {port} закрыт (соединение отклонено)"
    except OSError as e:
        return False, f"Порт {port}: {e}"
