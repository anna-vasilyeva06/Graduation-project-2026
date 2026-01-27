import psutil, socket

def get_network():
    net = {}
    for name, addrs in psutil.net_if_addrs().items():
        ips = [a.address for a in addrs if a.family==socket.AF_INET]
        if ips: net[name] = ips
    return net
