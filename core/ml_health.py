import json
import math
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import psutil

_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_DIR, "ml_health_model.json")

N_FEATURES = 6
FEATURE_COLS = ["cpu", "ram", "disk", "battery_ok", "network_ok", "gpu", "peak_load"]
LABEL_ORDER = ["OK", "Warn", "Error"]

def _features_with_peak_load(features: List[float]) -> List[float]:
    x = normalize_raw_features(features)
    peak = max(x[0], x[1], x[2], x[5] if len(x) > 5 else 0.0)
    return x + [float(peak)]

def _latent_cutpoints_from_raw(raw_t0: float, raw_t1: float) -> Tuple[float, float]:
    t0 = float(raw_t0)
    t1 = t0 + float(math.exp(raw_t1))
    return t0, t1

def _statsmodels_param_vector(sm_params: Dict[str, Any], feature_cols: List[str]) -> List[float]:
    cut_keys = [k for k in sm_params.keys() if k not in set(feature_cols)]
    if len(cut_keys) < 2:
        raise ValueError("Missing cutpoint params")
    return [float(sm_params[c]) for c in feature_cols] + [float(sm_params[cut_keys[0]]), float(sm_params[cut_keys[1]])]

CPU_OK = 80
CPU_BAD = 95
RAM_OK = 80
RAM_BAD = 95
DISK_OK = 85
DISK_BAD = 95
BATTERY_LOW = 25
BATTERY_CRITICAL = 10
GPU_OK = 80
GPU_BAD = 95

_CPU_OK = CPU_OK / 100.0
_CPU_BAD = CPU_BAD / 100.0
_RAM_OK = RAM_OK / 100.0
_RAM_BAD = RAM_BAD / 100.0
_DISK_OK = DISK_OK / 100.0
_DISK_BAD = DISK_BAD / 100.0
_GPU_OK = GPU_OK / 100.0
_GPU_BAD = GPU_BAD / 100.0
_GPU_FALLBACK = 0.85

def normalize_raw_features(features: List[float]) -> List[float]:
    x = [float(v) for v in features]
    if len(x) == N_FEATURES - 1:
        x = x + [_GPU_FALLBACK]
    if len(x) < N_FEATURES:
        x = x + [_GPU_FALLBACK] * (N_FEATURES - len(x))
    return x[:N_FEATURES]

def _gpu_is_unknown(gpu: float) -> bool:
    return abs(float(gpu) - _GPU_FALLBACK) < 1e-6

def _safe_disk_max_percent() -> float:
    out = 0.0
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount:
            continue
        drive, _ = os.path.splitdrive(mount)
        if not drive:
            continue
        path = drive.upper().rstrip(":\\") + ":\\"
        try:
            u = shutil.disk_usage(path)
            pct = (float(u.used) / float(u.total)) * 100.0 if u.total else 0.0
            out = max(out, pct)
        except Exception:
            pass
    return out

def _safe_system_disk_percent() -> float:
    try:
        drive = (os.environ.get("SystemDrive") or "C:").upper().rstrip(":\\") + ":\\"
        u = shutil.disk_usage(drive)
        return (float(u.used) / float(u.total)) * 100.0 if u.total else 0.0
    except Exception:
        return float(_safe_disk_max_percent())

def _subprocess_no_window_flags() -> int:
    return subprocess.CREATE_NO_WINDOW

def _windows_gpu_util_fraction() -> Optional[float]:
    ps = (
        "$max=0.0; $any=$false; "
        "try { "
        "$samples = (Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction Stop).CounterSamples; "
        "foreach ($s in $samples) { $any=$true; $v=[double]$s.CookedValue; if ($v -gt $max) { $max=$v } } "
        "} catch { exit 2 }; "
        "if (-not $any) { exit 2 }; "
        "[Console]::Out.WriteLine($max.ToString([System.Globalization.CultureInfo]::InvariantCulture))"
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_subprocess_no_window_flags(),
        )
        if r.returncode != 0 or not (r.stdout or "").strip():
            return None
        v = float((r.stdout or "").strip().splitlines()[-1].strip())
        return min(1.0, max(0.0, v / 100.0))
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return None

def _nvidia_gpu_util_fraction() -> Optional[float]:
    try:
        r = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_subprocess_no_window_flags(),
        )
        if r.returncode != 0 or not (r.stdout or "").strip():
            return None
        mx = 0.0
        for line in r.stdout.strip().splitlines():
            try:
                mx = max(mx, float(line.strip()))
            except ValueError:
                continue
        return min(1.0, max(0.0, mx / 100.0))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

def _gpu_feature() -> float:
    u = _windows_gpu_util_fraction()
    if u is None:
        u = _nvidia_gpu_util_fraction()
    if u is not None:
        return u
    try:
        from core.gpu import get_gpu

        if not get_gpu():
            return 0.85
    except Exception:
        return 0.85
    return 0.0

def get_gpu_health_snapshot() -> Dict[str, Any]:
    util = _windows_gpu_util_fraction()
    source: Optional[str] = "windows" if util is not None else None
    if util is None:
        util = _nvidia_gpu_util_fraction()
        source = "nvidia" if util is not None else None
    names: List[str] = []
    try:
        from core.gpu import get_gpu

        for g in get_gpu() or []:
            n = (g.get("Name") or "").strip()
            if n:
                names.append(n)
    except Exception:
        pass
    return {"util_fraction": util, "source": source, "names": names}

_gpu_chart_last_t: float = -1e9
_gpu_chart_last_frac: Optional[float] = None

def sample_gpu_util_fraction(min_interval_s: float = 1.0) -> Optional[float]:
    global _gpu_chart_last_t, _gpu_chart_last_frac
    import time

    now = time.monotonic()
    if (now - _gpu_chart_last_t) < min_interval_s:
        return _gpu_chart_last_frac
    u = _windows_gpu_util_fraction()
    if u is None:
        u = _nvidia_gpu_util_fraction()
    _gpu_chart_last_t = now
    _gpu_chart_last_frac = u
    return u

def collect_features() -> List[float]:
    try:
        cpu = min(100, max(0, psutil.cpu_percent(interval=0.1))) / 100.0
    except Exception:
        cpu = 0.0
    try:
        mem = psutil.virtual_memory()
        ram = min(100, max(0, mem.percent)) / 100.0
    except Exception:
        ram = 0.0
    disk = min(100, max(0, _safe_system_disk_percent())) / 100.0
    try:
        bat = psutil.sensors_battery()
        if bat is None:
            battery_ok = 1.0
        elif bat.power_plugged:
            battery_ok = 1.0
        elif bat.percent >= BATTERY_LOW:
            battery_ok = 1.0
        elif bat.percent >= BATTERY_CRITICAL:
            battery_ok = 0.5
        else:
            battery_ok = 0.0
    except Exception:
        battery_ok = 1.0
    try:
        from core.network import has_internet

        network_ok = 1.0 if has_internet(timeout=1.5) else 0.0
    except Exception:
        network_ok = 0.0
    gpu = _gpu_feature()
    return [cpu, ram, disk, battery_ok, network_ok, gpu]

def get_rule_label(features: List[float]) -> int:
    cpu, ram, disk, battery_ok, network_ok, gpu = (
        features[0],
        features[1],
        features[2],
        features[3],
        features[4],
        features[5] if len(features) > 5 else 0.0,
    )
    worst = 0
    gpu_known = not _gpu_is_unknown(gpu)
    if (
        cpu >= (CPU_BAD / 100.0)
        or ram >= (RAM_BAD / 100.0)
        or disk >= (DISK_BAD / 100.0)
        or (gpu_known and gpu >= (GPU_BAD / 100.0))
    ):
        worst = 2
    elif battery_ok == 0.0:
        worst = 2
    elif (
        cpu >= (CPU_OK / 100.0)
        or ram >= (RAM_OK / 100.0)
        or disk >= (DISK_OK / 100.0)
        or (gpu_known and gpu >= (GPU_OK / 100.0))
    ):
        worst = max(worst, 1)
    elif battery_ok <= 0.5:
        worst = max(worst, 1)
    if network_ok == 0.0:
        worst = max(worst, 1)

    return worst

def _ordinal_model_valid(model: Dict[str, Any]) -> bool:
    meta = model.get("meta")
    sm_params = (meta or {}).get("statsmodels_params") if isinstance(meta, dict) else None
    if isinstance(sm_params, dict) and all(isinstance(k, str) for k in sm_params.keys()):
        feat_keys = list((meta or {}).get("features") or FEATURE_COLS)
        if not all(k in sm_params for k in feat_keys):
            return False
        cut_keys = [k for k in sm_params.keys() if k not in set(feat_keys)]
        if len(cut_keys) < 2:
            return False
        try:
            for k in feat_keys:
                float(sm_params[k])
            float(sm_params[cut_keys[0]])
            float(sm_params[cut_keys[1]])
        except (TypeError, ValueError):
            return False
        return True
    return False

def _predict_with_statsmodels(features: List[float], model: Dict[str, Any]) -> Optional[List[float]]:
    meta = model.get("meta")
    if not isinstance(meta, dict):
        return None
    sm_params = meta.get("statsmodels_params")
    if not isinstance(sm_params, dict):
        return None
    try:
        import pandas as pd
        from statsmodels.miscmodels.ordinal_model import OrderedModel
        meta_features = meta.get("features")
        cols = list(meta_features) if isinstance(meta_features, list) and meta_features else FEATURE_COLS
        x = _features_with_peak_load(features)
        if len(cols) == len(FEATURE_COLS) - 1:
            cols = FEATURE_COLS
            x = normalize_raw_features(features)
        df_pred = pd.DataFrame([x], columns=cols)
        formula = str(meta.get("formula") or ("label ~ 0 + " + " + ".join(FEATURE_COLS)))

        import math
        n_init = 12
        rows = []
        for i in range(n_init):
            row = {}
            for j, col in enumerate(cols):
                base = float(df_pred.loc[0, col])
                dv = 0.05 * math.sin((i + 1) * (j + 2))
                row[col] = min(1.0, max(0.0, base + dv))
            if "peak_load" in cols:
                row["peak_load"] = max(row.get("cpu", 0), row.get("ram", 0), row.get("disk", 0), row.get("gpu", 0))
            row["label"] = LABEL_ORDER[i % len(LABEL_ORDER)]
            rows.append(row)
        df_init = pd.DataFrame(rows)
        df_init["label"] = pd.Categorical(df_init["label"], categories=LABEL_ORDER, ordered=True)

        mod = OrderedModel.from_formula(formula, data=df_init, distr="logit")
        params = _statsmodels_param_vector(sm_params, cols)
        pred = mod.predict(params, exog=df_pred)
        if hasattr(pred, "to_numpy"):
            arr = pred.to_numpy()
        else:
            arr = pred
        probs = [float(v) for v in arr.reshape(-1).tolist()]
        if len(probs) != 3:
            return None
        s = sum(probs)
        if not (s > 0):
            return None
        return [p / s for p in probs]
    except Exception:
        return None

def predict_with_model(features: List[float], model: Dict[str, Any]) -> Tuple[int, List[float]]:
    if not _ordinal_model_valid(model):
        return 0, [1 / 3, 1 / 3, 1 / 3]

    probs_sm = _predict_with_statsmodels(features, model)
    if probs_sm is None:
        return 0, [1 / 3, 1 / 3, 1 / 3]
    return int(probs_sm.index(max(probs_sm))), probs_sm

def load_model() -> Optional[Dict[str, Any]]:
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        with open(MODEL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_model(model: Dict[str, Any]) -> None:
    try:
        with open(MODEL_PATH, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=0)
    except Exception:
        pass

def _get_advice(features: List[float], pred_class: int) -> List[str]:
    advice: List[str] = []
    cpu, ram, disk, battery_ok, network_ok = features[0], features[1], features[2], features[3], features[4]
    gpu = features[5] if len(features) > 5 else 0.0
    cpu_ok = CPU_OK / 100.0
    cpu_bad = CPU_BAD / 100.0
    ram_ok = RAM_OK / 100.0
    ram_bad = RAM_BAD / 100.0
    disk_ok = DISK_OK / 100.0
    disk_bad = DISK_BAD / 100.0
    gpu_ok = GPU_OK / 100.0
    gpu_bad = GPU_BAD / 100.0

    if pred_class == 0:
        advice.append("Система в норме. Продолжайте работу.")
        if disk >= disk_ok:
            advice.append("Место на диске заканчивается - при необходимости почистите кэш и ненужные файлы.")
        return advice

    if cpu >= cpu_bad:
        advice.append("Очень высокая загрузка CPU - закройте тяжёлые программы или подождите завершения задач.")
    elif cpu >= cpu_ok:
        advice.append("Повышенная загрузка процессора - закройте ненужные приложения для ускорения работы.")

    if ram >= ram_bad:
        advice.append("Критически мало свободной памяти - закройте программы или перезагрузите компьютер.")
    elif ram >= ram_ok:
        advice.append("Высокая загрузка ОЗУ - закройте вкладки браузера или программы, которые не используете.")

    if disk >= disk_bad:
        advice.append("Критически мало места на диске - удалите ненужные файлы, очистите корзину и кэш.")
    elif disk >= disk_ok:
        advice.append("Мало свободного места на диске - освободите место для обновлений и стабильной работы.")

    if battery_ok == 0.0:
        advice.append("Батарея почти разряжена - подключите зарядное устройство.")
    elif battery_ok <= 0.5:
        advice.append("Низкий заряд батареи - рекомендуется подключить зарядку.")

    if network_ok == 0.0:
        advice.append("Нет активного сетевого подключения - проверьте Wi‑Fi или кабель.")

    if pred_class > 0:
        if gpu >= gpu_bad:
            advice.append(
                "Очень высокая загрузка GPU - снизьте нагрузку на видеокарту, проверьте температуру и охлаждение."
            )
        elif gpu >= gpu_ok:
            advice.append(
                "Повышенная загрузка GPU либо видеокарта не определена."
            )

    if not advice:
        advice.append("Обратите внимание на компоненты системы и при необходимости освободите ресурсы.")
    return advice

def predict_only() -> Dict[str, Any]:
    features = collect_features()
    status_names = ["ok", "warning", "error"]
    rule_status = status_names[get_rule_label(features)]
    model = load_model()
    if model is not None and _ordinal_model_valid(model):
        pred_class, probs = predict_with_model(features, model)
        ml_status = status_names[pred_class]
        advice = _get_advice(features, pred_class)
        return {
            "rule_status": rule_status,
            "ml_status": ml_status,
            "ml_probs": probs,
            "advice": advice,
            "model_trained": True,
        }
    rule_label = get_rule_label(features)
    advice = _get_advice(features, rule_label)
    return {
        "rule_status": rule_status,
        "ml_status": None,
        "ml_probs": None,
        "advice": advice,
        "model_trained": False,
    }
