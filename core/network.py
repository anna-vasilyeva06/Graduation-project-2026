"""
Сбор информации о сетевых интерфейсах и трафике.
Функции для продвинутых пользователей: ping, проверка порта, DNS.
"""
import platform
import re
import socket
import subprocess
from typing import Any, Dict, List, Tuple

import psutil


def _interface_type(name: str) -> str:
    """Определяет тип подключения по имени интерфейса."""
    ln = name.lower()
    if "wi-fi" in ln or "wireless" in ln or "wlan" in ln:
        return "Wi-Fi"
    if "ethernet" in ln or "eth" in ln:
        return "Ethernet"
    if "bluetooth" in ln:
        return "Bluetooth"
    if "loopback" in ln or "lo" == ln:
        return "Loopback"
    return "Сеть"


def get_network() -> Dict[str, List[str]]:
    """IPv4-адреса по интерфейсам (для обратной совместимости)."""
    net = {}
    for name, addrs in psutil.net_if_addrs().items():
        ips = [a.address for a in addrs if a.family == socket.AF_INET]
        if ips:
            net[name] = ips
    return net


def get_network_info() -> List[Dict[str, Any]]:
    """
    Расширенная информация по каждому активному интерфейсу:
    - name, type (Wi-Fi/Ethernet/...), isup
    - ipv4, ipv6, mac
    - speed (Мбит/с), mtu
    - bytes_sent, bytes_recv (общий трафик с загрузки системы)
    """
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    try:
        counters = psutil.net_io_counters(pernic=True) or {}
    except Exception:
        counters = {}

    result: List[Dict[str, Any]] = []

    for name, addr_list in addrs.items():
        stat = stats.get(name)
        if not stat or not stat.isup:
            continue

        ipv4_list: List[str] = []
        ipv6_list: List[str] = []
        mac: str = ""

        for a in addr_list:
            if hasattr(a.family, "name"):
                fam = a.family.name
            else:
                fam = str(a.family)
            if fam == "AF_INET":
                ipv4_list.append(a.address)
            elif fam == "AF_INET6" and not (a.address or "").startswith("::1"):
                ipv6_list.append(a.address)
            elif fam == "AF_PACKET" or "PACKET" in fam:
                mac = a.address or ""

        # Пропускаем loopback без IPv4 (чтобы не дублировать)
        if _interface_type(name) == "Loopback" and not ipv4_list:
            continue

        io = counters.get(name)
        bytes_sent = io.bytes_sent if io else 0
        bytes_recv = io.bytes_recv if io else 0

        speed_mbps = getattr(stat, "speed", None) or 0
        if speed_mbps and speed_mbps > 0:
            speed_str = f"{speed_mbps} Мбит/с"
        else:
            speed_str = "—"

        result.append({
            "name": name,
            "type": _interface_type(name),
            "isup": True,
            "ipv4": ipv4_list,
            "ipv6": ipv6_list,
            "mac": mac,
            "speed": speed_str,
            "speed_raw": speed_mbps,
            "mtu": getattr(stat, "mtu", None) or "—",
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
        })

    # Сортируем: сначала Wi-Fi и Ethernet, потом остальные
    order = {"Wi-Fi": 0, "Ethernet": 1, "Сеть": 2, "Bluetooth": 3, "Loopback": 4}
    result.sort(key=lambda x: (order.get(x["type"], 5), x["name"]))

    return result


def get_traffic_delta(interval_sec: float = 1.0) -> Dict[str, Dict[str, int]]:
    """
    Возвращает прирост трафика за interval_sec по каждому интерфейсу.
    Вызов дважды с паузой даёт скорость (bytes/sec).
    """
    try:
        before = psutil.net_io_counters(pernic=True) or {}
    except Exception:
        return {}

    import time
    time.sleep(max(0.1, interval_sec))

    try:
        after = psutil.net_io_counters(pernic=True) or {}
    except Exception:
        return {}

    out = {}
    for name in set(before) | set(after):
        b = before.get(name)
        a = after.get(name)
        if b and a:
            out[name] = {
                "bytes_sent": max(0, a.bytes_sent - b.bytes_sent),
                "bytes_recv": max(0, a.bytes_recv - b.bytes_recv),
            }
    return out


# --- Продвинутые функции для проверки сети ---

def resolve_host(hostname: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """
    DNS-резолвинг: преобразует имя хоста в IP.
    Возвращает (успех, IP или сообщение об ошибке).
    """
    if not hostname or not hostname.strip():
        return False, "Укажите хост"
    hostname = hostname.strip()
    try:
        socket.setdefaulttimeout(timeout)
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror as e:
        return False, f"Не удалось разрешить: {e}"
    except Exception as e:
        return False, str(e)


def ping_host(hostname: str, count: int = 1, timeout_sec: int = 5) -> Tuple[bool, str]:
    """
    Проверка доступности хоста через ping.
    Возвращает (успех, сообщение с IP, временем отклика или ошибкой).
    """
    if not hostname or not hostname.strip():
        return False, "Укажите хост"
    hostname = hostname.strip()
    # Сначала резолвим — покажем IP в результате
    ip_info = ""
    try:
        ip = socket.gethostbyname(hostname)
        ip_info = f" ({hostname} → {ip})" if ip != hostname else ""
    except Exception:
        pass
    is_win = platform.system().lower() == "windows"
    cmd = ["ping", "-n" if is_win else "-c", str(count), "-w" if is_win else "-W", str(timeout_sec * 1000 if is_win else timeout_sec), hostname]
    try:
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec + 2,
            encoding="utf-8",
            errors="replace",
        )
        txt = (out.stdout or "") + (out.stderr or "")
        if out.returncode == 0:
            m = re.search(r"(?:time|время)\s*=\s*(\d+(?:\.\d+)?)\s*(?:ms|мс)?", txt, re.I)
            if m:
                return True, f"Доступен{ip_info}, время отклика: {m.group(1)} мс"
            return True, f"Доступен{ip_info}"
        return False, f"Недоступен (код {out.returncode})"
    except subprocess.TimeoutExpired:
        return False, "Таймаут"
    except FileNotFoundError:
        return False, "Команда ping не найдена"
    except Exception as e:
        return False, str(e)


def check_port(hostname: str, port: int, timeout: float = 5.0) -> Tuple[bool, str]:
    """
    Проверка доступности порта на хосте (TCP-подключение).
    Использует socket.create_connection — поддерживает IPv4/IPv6 и резолвинг.
    """
    if not hostname or not hostname.strip():
        return False, "Укажите хост"
    if not (1 <= port <= 65535):
        return False, "Порт должен быть 1–65535"
    hostname = hostname.strip()
    try:
        sock = socket.create_connection((hostname, port), timeout=timeout)
        sock.close()
        return True, f"Порт {port} открыт"
    except socket.timeout:
        return False, f"Таймаут (порт {port})"
    except OSError as e:
        err = e.errno if hasattr(e, "errno") else None
        if err == 10061:  # WSAECONNREFUSED (Windows)
            return False, f"Порт {port} закрыт (соединение отклонено)"
        if err == 10060:  # WSAETIMEDOUT (Windows)
            return False, f"Таймаут (порт {port})"
        if err == 111:  # ECONNREFUSED (Linux)
            return False, f"Порт {port} закрыт (соединение отклонено)"
        return False, f"Порт {port}: {e}"
    except Exception as e:
        return False, str(e)


