import argparse
import json
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np


FEATURE_NAMES = ["CPU", "RAM", "Disk", "Battery", "Network", "GPU"]
CLASS_NAMES = ["ok", "warning", "error"]


def sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-x))


def softplus(x: float) -> float:
    x = float(np.clip(x, -60.0, 60.0))
    return np.log1p(np.exp(x))


def load_dataset(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    xs: List[List[float]] = []
    ys: List[int] = []

    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(f"[skip] broken json at line {line_no}")
                continue

            label = row.get("label")
            features = row.get("features")
            if label is None or not isinstance(features, list):
                continue
            if label not in (0, 1, 2):
                continue

            vals = [float(v) for v in features[: len(FEATURE_NAMES)]]
            while len(vals) < len(FEATURE_NAMES):
                vals.append(0.0)

            xs.append(vals)
            ys.append(int(label))

    if not xs:
        raise ValueError(f"no labeled rows found in {path}")

    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=int)


def unpack_params(params: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    w = params[: len(FEATURE_NAMES)]
    t0_raw = params[len(FEATURE_NAMES)]
    gap_raw = params[len(FEATURE_NAMES) + 1]
    theta0 = t0_raw
    theta1 = theta0 + softplus(gap_raw)
    return w, np.asarray([theta0, theta1], dtype=float)


def ordinal_probs(x: np.ndarray, w: np.ndarray, theta: np.ndarray) -> np.ndarray:
    score = x @ w
    c0 = sigmoid(theta[0] - score)
    c1 = sigmoid(theta[1] - score)
    c1 = np.maximum(c1, c0)

    p0 = np.clip(c0, 1e-9, 1.0)
    p1 = np.clip(c1 - c0, 1e-9, 1.0)
    p2 = np.clip(1.0 - c1, 1e-9, 1.0)

    probs = np.column_stack([p0, p1, p2])
    probs /= probs.sum(axis=1, keepdims=True)
    return probs


def loss_fn(params: np.ndarray, x: np.ndarray, y: np.ndarray, reg: float) -> float:
    w, theta = unpack_params(params)
    probs = ordinal_probs(x, w, theta)
    nll = -np.log(probs[np.arange(len(y)), y]).mean()
    return float(nll + reg * np.sum(w * w))


def numeric_grad(params: np.ndarray, x: np.ndarray, y: np.ndarray, reg: float, eps: float = 1e-4) -> np.ndarray:
    grad = np.zeros_like(params)
    for i in range(len(params)):
        step = np.zeros_like(params)
        step[i] = eps
        grad[i] = (
            loss_fn(params + step, x, y, reg) - loss_fn(params - step, x, y, reg)
        ) / (2.0 * eps)
    return grad


def evaluate(params: np.ndarray, x: np.ndarray, y: np.ndarray, reg: float) -> Tuple[float, float]:
    w, theta = unpack_params(params)
    probs = ordinal_probs(x, w, theta)
    pred = probs.argmax(axis=1)
    return loss_fn(params, x, y, reg), accuracy(y, pred)


def fit_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    reg: float,
    epochs: int,
    lr: float,
) -> Tuple[dict, dict]:
    params = np.zeros(len(FEATURE_NAMES) + 2, dtype=float)
    params[len(FEATURE_NAMES)] = 0.5
    params[len(FEATURE_NAMES) + 1] = 0.5

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_params = params.copy()
    best_val_loss = float("inf")

    for _ in range(epochs):
        grad = numeric_grad(params, x_train, y_train, reg)
        params -= lr * grad

        train_loss, train_acc = evaluate(params, x_train, y_train, reg)
        val_loss, val_acc = evaluate(params, x_val, y_val, reg)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_params = params.copy()

    w, theta = unpack_params(best_params)
    model = {
        "model_type": "ordinal_logit",
        "w": [float(v) for v in w],
        "theta": [float(theta[0]), float(theta[1])],
        "train_loss": float(history["train_loss"][-1]),
        "val_loss": float(history["val_loss"][-1]),
    }
    return model, history


def predict(x: np.ndarray, model: dict) -> Tuple[np.ndarray, np.ndarray]:
    w = np.asarray(model["w"], dtype=float)
    theta = np.asarray(model["theta"], dtype=float)
    probs = ordinal_probs(x, w, theta)
    pred = probs.argmax(axis=1)
    return pred, probs


def train_test_split(x: np.ndarray, y: np.ndarray, test_size: float, seed: int) -> Tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    indices = np.arange(len(y))
    rng.shuffle(indices)

    test_count = max(1, int(round(len(indices) * test_size)))
    if test_count >= len(indices):
        test_count = len(indices) - 1

    test_idx = indices[:test_count]
    train_idx = indices[test_count:]
    return x[train_idx], x[test_idx], y[train_idx], y[test_idx]


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float((y_true == y_pred).mean()) if len(y_true) else 0.0


def build_confusion(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    matrix = np.zeros((3, 3), dtype=int)
    for yt, yp in zip(y_true, y_pred):
        matrix[int(yt), int(yp)] += 1
    return matrix


def plot_report(history: dict) -> None:
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(epochs, history["train_acc"], label="train accuracy")
    axes[0].plot(epochs, history["val_acc"], label="val accuracy")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Value")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(epochs, history["train_loss"], label="train loss")
    axes[1].plot(epochs, history["val_loss"], label="val loss")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Value")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    plt.show()


def print_metrics(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    acc = accuracy(y_true, y_pred)
    print(f"{name} accuracy: {acc:.4f} ({int((y_true == y_pred).sum())}/{len(y_true)})")


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Simple trainer for core/ml_health_model.json")
    parser.add_argument("--data", type=Path, default=root / "core" / "ml_health_data.jsonl")
    parser.add_argument("--model", type=Path, default=root / "core" / "ml_health_model.json")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reg", type=float, default=0.01)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = args.data
    model_path = args.model

    x, y = load_dataset(data_path)
    x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=args.test_size, seed=args.seed)

    model, history = fit_model(
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        reg=args.reg,
        epochs=args.epochs,
        lr=args.lr,
    )
    train_pred, _ = predict(x_train, model)
    val_pred, _ = predict(x_val, model)
    full_pred, _ = predict(x, model)

    with model_path.open("w", encoding="utf-8") as fh:
        json.dump(model, fh, ensure_ascii=False, indent=2)

    print(f"[ok] rows: {len(y)}")
    print(f"[ok] train/val: {len(y_train)}/{len(y_val)}")
    print(f"[ok] model saved: {model_path}")
    print(f"[ok] theta: {model['theta']}")
    print(f"[ok] weights: {[round(v, 4) for v in model['w']]}")
    print(f"[ok] final train loss: {history['train_loss'][-1]:.4f}")
    print(f"[ok] final val loss:   {history['val_loss'][-1]:.4f}")
    print_metrics("train", y_train, train_pred)
    print_metrics("val  ", y_val, val_pred)
    print_metrics("full ", y, full_pred)

    plot_report(history, x=x, y=y, model=model)


if __name__ == "__main__":
    main()
