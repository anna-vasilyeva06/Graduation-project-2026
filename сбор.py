import json
import datetime
import os
import sys
import time

import psutil

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.ml_health import _gpu_feature

DATA_FILE = "data_1.jsonl"
INTERVAL_SECONDS = 60

def collect():
    cpu = psutil.cpu_percent(interval=0.5) / 100.0
    ram = psutil.virtual_memory().percent / 100.0
    system_disk = None
    for part in psutil.disk_partitions():
        if 'C:\\' in part.mountpoint or part.mountpoint == '/':
            system_disk = part.mountpoint
            break

    if system_disk:
        usage = psutil.disk_usage(system_disk)
        disk = usage.percent / 100.0
    else:
        disk = 0.0

    battery = psutil.sensors_battery()
    if battery is None:
        battery_ok = 1.0
    elif battery.power_plugged:
        battery_ok = 1.0
    elif battery.percent >= 20:
        battery_ok = 1.0
    elif battery.percent >= 10:
        battery_ok = 0.5
    else:
        battery_ok = 0.0

    net_stats = psutil.net_if_stats()
    network_ok = 1.0 if any(s.isup for s in net_stats.values()) else 0.0

    # Как в collect_features() в core/ml_health.py: Windows-счётчики → nvidia-smi → эвристика
    gpu = _gpu_feature()

    features = [cpu, ram, disk, battery_ok, network_ok, gpu]

    return features

def save(record):
    with open(DATA_FILE, 'a') as f:
        f.write(json.dumps(record) + '\n')

def main():
    print("Сбор данных для обучения: CPU, RAM, диск, батарея, сеть, GPU (6 признаков, 0–1)")
    print("File: {}".format(DATA_FILE))
    print("Interval: {} seconds".format(INTERVAL_SECONDS))
    print("Press Ctrl+C to stop")
    count = 0
    try:
        while True:
            features = collect()

            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            print("\n[{}] CPU: {:.1f}% RAM: {:.1f}% DISK: {:.1f}% GPU(ML): {:.1f}%".format(
                timestamp,
                features[0] * 100,
                features[1] * 100,
                features[2] * 100,
                features[5] * 100,
            ))

            record = {
                'timestamp': datetime.datetime.now().isoformat(),
                'features': features,
                'label': None
            }

            save(record)
            count += 1
            print("Saved #{}".format(count))

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopped. Saved {} records".format(count))


if __name__ == "__main__":
    main()