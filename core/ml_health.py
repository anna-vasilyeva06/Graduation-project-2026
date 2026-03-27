"""
Учебный ML-модуль: простая модель машинного обучения для прогноза состояния системы.

Идея:
  - Собираем «признаки» (CPU %, RAM %, диск %, батарея, сеть) и «метку» (норма / предупреждение / проблема)
    по правилам (пороги). Это наши данные для обучения.
  - Обучаем модель (ординарная логистическая регрессия) предсказывать метку по признакам.
  - Модель учится на накопленных данных; со временем прогноз может учитывать ваши привычные нагрузки.

Математика (упрощённо):
  - Признаки x = [cpu, ram, disk, battery_ok, network_ok] (числа 0–1).
  - Классы упорядочены: 0 < 1 < 2.
  - Используем cumulative logit:
      P(y <= k) = sigmoid(theta[k] - w^T x), k=0..1.
  - Из кумулятивных вероятностей получаем вероятности классов:
      p0 = P(y <= 0), p1 = P(y <= 1) - P(y <= 0), p2 = 1 - P(y <= 1).
  - Обучение: градиентный спуск по бинарной кросс-энтропии для двух порогов.
"""
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Tuple

import psutil

# Пути к файлам данных и модели
_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_DIR, "ml_health_data.jsonl")
MODEL_PATH = os.path.join(_DIR, "ml_health_model.json")

N_FEATURES = 5   # cpu, ram, disk, battery_ok, network_ok
N_CLASSES = 3    # 0=норма, 1=предупреждение, 2=проблема
N_THRESHOLDS = N_CLASSES - 1
MIN_SAMPLES_TO_TRAIN = 25
EPOCHS = 50
LEARNING_RATE = 0.1


def _safe_disk_max_percent() -> float:
    """Максимальный процент заполнения среди дисков (0–100)."""
    out = 0.0
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount:
            continue
        drive, _ = os.path.splitdrive(mount)
        if not drive:
            continue
        path = (drive.upper().rstrip(":\\") + ":\\") if os.name == "nt" else os.path.normpath(mount)
        try:
            u = psutil.disk_usage(path)
            out = max(out, u.percent)
        except Exception:
            pass
    return out


def collect_features() -> List[float]:
    """
    Собирает вектор признаков из текущего состояния системы.
    Все значения в диапазоне 0–1 (проценты делим на 100).
    """
    # CPU: 0–1
    try:
        cpu = min(100, max(0, psutil.cpu_percent(interval=0.1))) / 100.0
    except Exception:
        cpu = 0.0

    # RAM: 0–1
    try:
        mem = psutil.virtual_memory()
        ram = min(100, max(0, mem.percent)) / 100.0
    except Exception:
        ram = 0.0

    # Диск: максимум по всем дискам, 0–1
    disk = min(100, max(0, _safe_disk_max_percent())) / 100.0

    # Батарея: 1 = ок (есть заряд или зарядка), 0 = критично
    try:
        bat = psutil.sensors_battery()
        if bat is None:
            battery_ok = 1.0  # нет батареи — считаем ок
        elif bat.power_plugged:
            battery_ok = 1.0
        elif bat.percent >= 20:
            battery_ok = 1.0
        elif bat.percent >= 10:
            battery_ok = 0.5
        else:
            battery_ok = 0.0
    except Exception:
        battery_ok = 1.0

    # Сеть: 1 = есть активный интерфейс, 0 = нет
    try:
        stats = psutil.net_if_stats()
        network_ok = 1.0 if any(s.isup for s in stats.values()) else 0.0
    except Exception:
        network_ok = 0.0

    return [cpu, ram, disk, battery_ok, network_ok]


def get_rule_label(features: List[float]) -> int:
    """
    По правилам (пороги) определяет метку класса по признакам.
    0 = норма, 1 = предупреждение, 2 = проблема.
    Эти метки используются как «учитель» для обучения модели.
    """
    cpu, ram, disk, battery_ok, network_ok = features[0], features[1], features[2], features[3], features[4]
    worst = 0  # 0 ok, 1 warning, 2 error

    if cpu >= 0.95 or ram >= 0.95 or disk >= 0.95:
        worst = 2
    elif battery_ok == 0.0:
        worst = 2
    elif cpu >= 0.85 or ram >= 0.85 or disk >= 0.90:
        worst = max(worst, 1)
    elif battery_ok <= 0.5:
        worst = max(worst, 1)
    if network_ok == 0.0:
        worst = max(worst, 1)

    return worst


def generate_synthetic_samples(n: int, seed: Optional[int] = 42) -> List[Dict[str, Any]]:
    """
    Генерирует n синтетических примеров для предобучения модели (без доступа к системе).
    Признаки: cpu, ram, disk — равномерно 0–1; battery_ok — 0 / 0.5 / 1; network_ok — 0 / 1.
    Метка вычисляется по тем же правилам, что и get_rule_label.
    Часть примеров — у границ порогов (0.85, 0.90, 0.95), чтобы модель лучше усвоила границы.
    """
    if seed is not None:
        random.seed(seed)
    out: List[Dict[str, Any]] = []
    # Пороги, важные для правил
    thresholds = [0.0, 0.5, 0.85, 0.90, 0.95, 1.0]

    for i in range(n):
        if i < n // 2:
            # Случайные примеры
            cpu = random.uniform(0, 1)
            ram = random.uniform(0, 1)
            disk = random.uniform(0, 1)
        else:
            # Примеры у границ (с небольшим шумом)
            t = random.choice(thresholds)
            noise = random.uniform(-0.05, 0.05)
            cpu = random.choice([t + noise, random.uniform(0, 1)])
            ram = random.choice([t + noise, random.uniform(0, 1)])
            disk = random.choice([t + noise, random.uniform(0, 1)])
            cpu = max(0, min(1, cpu))
            ram = max(0, min(1, ram))
            disk = max(0, min(1, disk))

        battery_ok = random.choice([0.0, 0.5, 1.0])
        network_ok = float(random.choice([0, 1]))
        features = [cpu, ram, disk, battery_ok, network_ok]
        label = get_rule_label(features)
        out.append({"features": features, "label": label})
    return out


def _sigmoid(z: float) -> float:
    """Численно устойчивый сигмоид."""
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _ordinal_forward(w: List[float], theta: List[float], x: List[float]) -> List[float]:
    """
    Прямой проход для ordinal logit.
    Возвращает вероятности классов [p0, p1, p2].
    """
    score = sum(w[j] * x[j] for j in range(len(x)))
    c0 = _sigmoid(theta[0] - score)  # P(y <= 0)
    c1 = _sigmoid(theta[1] - score)  # P(y <= 1)

    # Гарантируем монотонность CDF, иначе могут появляться отрицательные вероятности
    if c1 < c0:
        c1 = c0

    p0 = max(0.0, min(1.0, c0))
    p1 = max(0.0, min(1.0, c1 - c0))
    p2 = max(0.0, min(1.0, 1.0 - c1))
    s = p0 + p1 + p2
    if s <= 0:
        return [1 / 3, 1 / 3, 1 / 3]
    return [p0 / s, p1 / s, p2 / s]


def predict_with_model(features: List[float], model: Dict[str, Any]) -> Tuple[int, List[float]]:
    """
    Предсказание модели: класс (0/1/2) и вероятности по классам.
    Поддерживает:
      - новый формат (ordinal): {"model_type":"ordinal_logit","w":[...],"theta":[...]}
      - старый формат (softmax): {"W":[[...],...],"b":[...]}
    """
    # Новый формат
    if "w" in model and "theta" in model:
        probs = _ordinal_forward(model["w"], model["theta"], features)
        return int(probs.index(max(probs))), probs

    # Legacy-формат для обратной совместимости
    W = model.get("W")
    b = model.get("b")
    if W is None or b is None:
        return 0, [1 / 3, 1 / 3, 1 / 3]
    scores = [b[k] + sum(W[k][j] * features[j] for j in range(len(features))) for k in range(N_CLASSES)]
    m = max(scores)
    exp = [math.exp(s - m) for s in scores]
    s = sum(exp)
    probs = [e / s for e in exp]
    return int(probs.index(max(probs))), probs


def train_model(samples: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Обучает ordinal logistic regression (cumulative logit) по примерам.
    Возвращает словарь модели:
      {"model_type":"ordinal_logit","w":[...],"theta":[...]}
    """
    if len(samples) < MIN_SAMPLES_TO_TRAIN:
        return None

    # Инициализация: общий вектор весов и два порога theta0 < theta1
    random.seed(42)
    w = [random.uniform(-0.1, 0.1) for _ in range(N_FEATURES)]
    theta = [-0.5, 0.5]

    for _ in range(EPOCHS):
        order = list(range(len(samples)))
        random.shuffle(order)
        for i in order:
            s = samples[i]
            x = s["features"]
            label = s["label"]

            score = sum(w[j] * x[j] for j in range(N_FEATURES))

            # Для каждого порога k учим бинарную цель I(y <= k)
            for k in range(N_THRESHOLDS):
                t = 1.0 if label <= k else 0.0
                z = theta[k] - score
                p = _sigmoid(z)
                # dL/dz = p - t (BCE), z = theta - w*x
                dz = p - t

                # Градиенты и шаг
                theta[k] -= LEARNING_RATE * dz
                for j in range(N_FEATURES):
                    w[j] -= LEARNING_RATE * (-dz * x[j])

            # Поддерживаем порядок порогов theta0 < theta1
            if theta[0] >= theta[1]:
                mid = (theta[0] + theta[1]) / 2.0
                theta[0] = mid - 1e-3
                theta[1] = mid + 1e-3

    return {
        "model_type": "ordinal_logit",
        "w": w,
        "theta": theta,
    }


def load_data() -> List[Dict[str, Any]]:
    """Загружает накопленные примеры из JSONL."""
    if not os.path.exists(DATA_PATH):
        return []
    out = []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if "features" in obj and "label" in obj:
                    out.append(obj)
    except Exception:
        pass
    return out


def save_data(samples: List[Dict[str, Any]]) -> None:
    """Сохраняет примеры в JSONL (последние 500)."""
    samples = samples[-500:]
    try:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_model() -> Optional[Dict[str, Any]]:
    """Загружает сохранённую модель из JSON."""
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        with open(MODEL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_model(model: Dict[str, Any]) -> None:
    """Сохраняет модель в JSON."""
    try:
        with open(MODEL_PATH, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=0)
    except Exception:
        pass


def _get_advice(features: List[float], pred_class: int) -> List[str]:
    """
    Генерирует полезные рекомендации на основе признаков и прогноза модели.
    pred_class: 0=норма, 1=предупреждение, 2=проблема.
    """
    advice: List[str] = []
    cpu, ram, disk, battery_ok, network_ok = features[0], features[1], features[2], features[3], features[4]

    if pred_class == 0:
        advice.append("Система в норме. Продолжайте работу.")
        if disk >= 0.8:
            advice.append("Место на диске заканчивается — при необходимости почистите кэш и ненужные файлы.")
        return advice

    if cpu >= 0.95:
        advice.append("Очень высокая загрузка CPU — закройте тяжёлые программы или подождите завершения задач.")
    elif cpu >= 0.85:
        advice.append("Повышенная загрузка процессора — закройте ненужные приложения для ускорения работы.")

    if ram >= 0.95:
        advice.append("Критически мало свободной памяти — закройте программы или перезагрузите компьютер.")
    elif ram >= 0.85:
        advice.append("Высокая загрузка ОЗУ — закройте вкладки браузера или программы, которые не используете.")

    if disk >= 0.95:
        advice.append("Критически мало места на диске — удалите ненужные файлы, очистите корзину и кэш.")
    elif disk >= 0.90:
        advice.append("Мало свободного места на диске — освободите место для обновлений и стабильной работы.")

    if battery_ok == 0.0:
        advice.append("Батарея почти разряжена — подключите зарядное устройство.")
    elif battery_ok <= 0.5:
        advice.append("Низкий заряд батареи — рекомендуется подключить зарядку.")

    if network_ok == 0.0:
        advice.append("Нет активного сетевого подключения — проверьте Wi‑Fi или кабель.")

    if not advice:
        advice.append("Обратите внимание на компоненты системы и при необходимости освободите ресурсы.")

    return advice


def predict_only() -> Dict[str, Any]:
    """
    Оценка состояния системы только по готовой модели (без записи данных и переобучения).
    Используется в приложении: модель поставляется предобученной.
    Возвращает статус, вероятности и список рекомендаций для пользователя.
    """
    features = collect_features()
    status_names = ["ok", "warning", "error"]
    rule_status = status_names[get_rule_label(features)]

    model = load_model()
    if model is not None:
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

    # Модель не загружена — рекомендации по правилам
    rule_label = get_rule_label(features)
    advice = _get_advice(features, rule_label)
    return {
        "rule_status": rule_status,
        "ml_status": None,
        "ml_probs": None,
        "advice": advice,
        "model_trained": False,
    }


def record_and_predict() -> Dict[str, Any]:
    """
    Устаревший вариант: записывает примеры и при достаточном количестве переобучает модель.
    В приложении используется predict_only().
    """
    features = collect_features()
    label = get_rule_label(features)
    status_names = ["ok", "warning", "error"]
    rule_status = status_names[label]

    samples = load_data()
    samples.append({"features": features, "label": label})
    save_data(samples)
    n_samples = len(samples)

    if n_samples >= MIN_SAMPLES_TO_TRAIN:
        model = train_model(samples)
        if model is not None:
            save_model(model)

    model = load_model()
    if model is not None:
        pred_class, probs = predict_with_model(features, model)
        ml_status = status_names[pred_class]
        return {
            "rule_status": rule_status,
            "ml_status": ml_status,
            "ml_probs": probs,
            "n_samples": n_samples,
            "model_trained": True,
        }

    return {
        "rule_status": rule_status,
        "ml_status": None,
        "ml_probs": None,
        "n_samples": n_samples,
        "model_trained": False,
    }
