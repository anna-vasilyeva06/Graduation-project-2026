import argparse
import json
import math
import os
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize


FEATURE_NAMES = ["cpu", "ram", "disk", "battery_ok", "network_ok", "gpu"]
N_FEATURES = 6
GPU_FALLBACK = 0.85  # mirrors core/ml_health.py for "unknown GPU"


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def _softplus(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x, dtype=float)
    m = x > 20
    out[m] = x[m]
    out[~m] = np.log1p(np.exp(x[~m]))
    return out


def _softplus_grad(x: np.ndarray) -> np.ndarray:
    return _sigmoid(x)


def _ordinal_probs(X: np.ndarray, w: np.ndarray, theta: np.ndarray) -> np.ndarray:
    score = X @ w
    c0 = _sigmoid(theta[0] - score)
    c1 = _sigmoid(theta[1] - score)
    p0 = np.clip(c0, 0.0, 1.0)
    p1 = np.clip(c1 - c0, 0.0, 1.0)
    p2 = np.clip(1.0 - c1, 0.0, 1.0)
    P = np.stack([p0, p1, p2], axis=1)
    s = P.sum(axis=1, keepdims=True)
    s = np.where(s <= 0.0, 1.0, s)
    return P / s


def _predict_classes(X: np.ndarray, w: np.ndarray, theta: np.ndarray) -> np.ndarray:
    return _ordinal_probs(X, w, theta).argmax(axis=1)


def _accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size == 0:
        return 0.0
    return float(np.mean((y_true == y_pred).astype(float)))


def _confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int = 3) -> np.ndarray:
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[int(t), int(p)] += 1
    return cm


def _macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int = 3) -> float:
    eps = 1e-12
    f1s: List[float] = []
    for c in range(n_classes):
        tp = float(np.sum((y_true == c) & (y_pred == c)))
        fp = float(np.sum((y_true != c) & (y_pred == c)))
        fn = float(np.sum((y_true == c) & (y_pred != c)))
        prec = tp / (tp + fp + eps)
        rec = tp / (tp + fn + eps)
        f1s.append(float((2.0 * prec * rec) / (prec + rec + eps)))
    return float(np.mean(f1s)) if f1s else 0.0


def _per_class_pr(y_true: np.ndarray, y_pred: np.ndarray, c: int) -> Tuple[float, float]:
    tp = float(np.sum((y_true == c) & (y_pred == c)))
    fp = float(np.sum((y_true != c) & (y_pred == c)))
    fn = float(np.sum((y_true == c) & (y_pred != c)))
    prec = tp / (tp + fp + 1e-12)
    rec = tp / (tp + fn + 1e-12)
    return float(prec), float(rec)


def _nll_loss(X: np.ndarray, y: np.ndarray, w: np.ndarray, theta: np.ndarray, sample_w: np.ndarray | None) -> float:
    P = _ordinal_probs(X, w, theta)
    py = np.clip(P[np.arange(P.shape[0]), y], 1e-12, 1.0)
    if sample_w is None:
        return float(-np.mean(np.log(py)))
    sw = np.asarray(sample_w, dtype=float)
    sw = sw / float(np.mean(sw))
    return float(-np.mean(sw * np.log(py)))


def _fit_scaler(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd < 1e-6, 1.0, sd)
    return mu, sd


def _apply_scaler(X: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return (X - mu) / sd


def _to_raw_params(w_z: np.ndarray, theta_z: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    w_raw = w_z / sd
    bias = float(np.sum(w_z * (mu / sd)))
    theta_raw = theta_z + bias
    return w_raw, theta_raw


def _tune_thresholds_for_metric(
    X: np.ndarray,
    y: np.ndarray,
    w: np.ndarray,
    theta_init: np.ndarray,
    metric: str,
    n_grid: int = 140,
) -> np.ndarray:
    if X.size == 0:
        return np.asarray(theta_init, dtype=float)
    s = (X @ w).astype(float)
    lo = float(np.percentile(s, 2))
    hi = float(np.percentile(s, 98))
    if not (math.isfinite(lo) and math.isfinite(hi)) or hi <= lo:
        return np.asarray(theta_init, dtype=float)
    grid = np.linspace(lo, hi, int(max(40, n_grid)))

    def score(theta: np.ndarray) -> float:
        yh = _predict_classes(X, w, theta)
        if metric == "acc":
            return _accuracy(y, yh)
        if metric == "recall_error":
            return _per_class_pr(y, yh, 2)[1]
        if metric == "f2_error":
            prec, rec = _per_class_pr(y, yh, 2)
            beta2 = 4.0
            f2 = float((1.0 + beta2) * prec * rec / (beta2 * prec + rec + 1e-12))
            if prec < 0.55 or _accuracy(y, yh) < 0.55:
                return 0.0
            return f2
        return _macro_f1(y, yh, n_classes=3)

    best = np.asarray(theta_init, dtype=float).copy()
    best_s = score(best)
    for i in range(len(grid) - 1):
        t1 = float(grid[i])
        for j in range(i + 1, len(grid)):
            th = np.array([t1, float(grid[j])], dtype=float)
            sc = score(th)
            if sc > best_s:
                best_s = sc
                best = th
    return best


@dataclass
class TrainResult:
    w: np.ndarray
    theta: np.ndarray
    train_loss: float
    val_loss: float
    train_losses: List[float]
    val_losses: List[float]
    train_accs: List[float]
    val_accs: List[float]


def _read_jsonl(path: str) -> List[dict]:
    rows: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _prepare_xy(rows: Sequence[dict]) -> Tuple[np.ndarray, np.ndarray]:
    X_list: List[List[float]] = []
    y_list: List[int] = []
    for r in rows:
        feats = r.get("features")
        lab = r.get("label")
        if not isinstance(feats, list):
            continue
        try:
            x = [float(v) for v in feats]
            yy = int(lab)
        except Exception:
            continue
        if yy not in (0, 1, 2):
            continue
        if len(x) == N_FEATURES - 1:
            x = x + [GPU_FALLBACK]
        if len(x) < N_FEATURES:
            x = x + [GPU_FALLBACK] * (N_FEATURES - len(x))
        if len(x) > N_FEATURES:
            x = x[:N_FEATURES]
        X_list.append(x)
        y_list.append(yy)
    return np.asarray(X_list, dtype=float), np.asarray(y_list, dtype=int)


def _stratified_split(X: np.ndarray, y: np.ndarray, val_ratio: float, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    idx0 = np.where(y == 0)[0]
    idx1 = np.where(y == 1)[0]
    idx2 = np.where(y == 2)[0]
    rng.shuffle(idx0)
    rng.shuffle(idx1)
    rng.shuffle(idx2)

    def take(idx: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n = int(idx.shape[0])
        n_val = int(round(n * val_ratio))
        n_val = min(max(1, n_val), max(1, n - 1)) if n >= 2 else 0
        return idx[:n_val], idx[n_val:]

    v0, t0 = take(idx0)
    v1, t1 = take(idx1)
    v2, t2 = take(idx2)
    val_idx = np.concatenate([v0, v1, v2])
    tr_idx = np.concatenate([t0, t1, t2])
    rng.shuffle(val_idx)
    rng.shuffle(tr_idx)
    return X[tr_idx], y[tr_idx], X[val_idx], y[val_idx]


def train_mle(
    Xtr: np.ndarray,
    ytr: np.ndarray,
    Xva: np.ndarray,
    yva: np.ndarray,
    maxiter: int,
    l2: float,
    seed: int,
    class_weights: np.ndarray,
    threshold_metric: str,
) -> TrainResult:
    mu, sd = _fit_scaler(Xtr)
    Xtrz = _apply_scaler(Xtr, mu, sd)
    Xvaz = _apply_scaler(Xva, mu, sd)

    w_cls = np.asarray(class_weights, dtype=float).reshape(3)
    w_cls = np.where(w_cls <= 0, 1.0, w_cls)
    sample_w = w_cls[ytr]
    sample_w = sample_w / float(np.mean(sample_w))

    rng = np.random.default_rng(seed)
    w0 = rng.normal(0.0, 0.2, size=(N_FEATURES,)).astype(float)
    a0 = 0.0
    b0 = 1.0

    def unpack(p: np.ndarray) -> Tuple[np.ndarray, float, float]:
        ww = p[:N_FEATURES]
        a = float(p[N_FEATURES])
        b = float(p[N_FEATURES + 1])
        return ww, a, b

    def obj_and_grad(p: np.ndarray) -> Tuple[float, np.ndarray]:
        ww, a, b = unpack(p)
        sp = float(_softplus(np.array([b]))[0])
        gsp = float(_softplus_grad(np.array([b]))[0])
        theta = np.array([a, a + sp], dtype=float)

        score = Xtrz @ ww
        a0v = theta[0] - score
        a1v = theta[1] - score
        s0 = _sigmoid(a0v)
        s1 = _sigmoid(a1v)
        ds0 = s0 * (1.0 - s0)
        ds1 = s1 * (1.0 - s1)

        p0 = np.clip(s0, 1e-12, 1.0)
        p1 = np.clip(s1 - s0, 1e-12, 1.0)
        p2 = np.clip(1.0 - s1, 1e-12, 1.0)
        py = np.where(ytr == 0, p0, np.where(ytr == 1, p1, p2))

        loss = float(-np.mean(sample_w * np.log(py)) + 0.5 * l2 * float(np.sum(ww * ww)))

        dL_ds0 = np.zeros_like(score)
        dL_ds1 = np.zeros_like(score)
        m0 = ytr == 0
        m1 = ytr == 1
        m2 = ytr == 2
        dL_ds0[m0] = -1.0 / p0[m0]
        dL_ds0[m1] = +1.0 / p1[m1]
        dL_ds1[m1] = -1.0 / p1[m1]
        dL_ds1[m2] = +1.0 / p2[m2]
        dL_ds0 *= sample_w
        dL_ds1 *= sample_w

        dL_da0 = dL_ds0 * ds0
        dL_da1 = dL_ds1 * ds1
        g_theta0 = float(np.mean(dL_da0 + dL_da1))
        g_theta1 = float(np.mean(dL_da1))

        dL_dscore = -(dL_da0 + dL_da1)
        g_w = (Xtrz.T @ dL_dscore) / Xtrz.shape[0]
        g_w = g_w + l2 * ww

        g_a = g_theta0 + g_theta1
        g_b = g_theta1 * gsp

        grad = np.zeros(N_FEATURES + 2, dtype=float)
        grad[:N_FEATURES] = g_w
        grad[N_FEATURES] = g_a
        grad[N_FEATURES + 1] = g_b
        return loss, grad

    x0 = np.concatenate([w0, np.array([a0, b0], dtype=float)])

    hist_tr_loss: List[float] = []
    hist_va_loss: List[float] = []
    hist_tr_acc: List[float] = []
    hist_va_acc: List[float] = []

    def callback(p: np.ndarray) -> None:
        ww, a, b = unpack(p)
        sp = float(_softplus(np.array([b]))[0])
        theta = np.array([a, a + sp], dtype=float)
        hist_tr_loss.append(_nll_loss(Xtrz, ytr, ww, theta, sample_w=sample_w))
        hist_va_loss.append(_nll_loss(Xvaz, yva, ww, theta, sample_w=None))
        hist_tr_acc.append(_accuracy(ytr, _predict_classes(Xtrz, ww, theta)))
        hist_va_acc.append(_accuracy(yva, _predict_classes(Xvaz, ww, theta)))

    opt = minimize(
        fun=lambda p: obj_and_grad(p)[0],
        x0=x0,
        jac=lambda p: obj_and_grad(p)[1],
        method="L-BFGS-B",
        options={"maxiter": int(max(50, maxiter)), "ftol": 1e-10},
        callback=callback,
    )

    p_opt = np.asarray(opt.x, dtype=float)
    ww, a, b = unpack(p_opt)
    sp = float(_softplus(np.array([b]))[0])
    theta_z = np.array([a, a + sp], dtype=float)

    w_raw, theta_raw = _to_raw_params(ww, theta_z, mu, sd)
    theta_raw = _tune_thresholds_for_metric(Xva, yva, w_raw, theta_raw, metric=str(threshold_metric))

    tr_loss = _nll_loss(Xtr, ytr, w_raw, theta_raw, sample_w=w_cls[ytr])
    va_loss = _nll_loss(Xva, yva, w_raw, theta_raw, sample_w=None)

    if not hist_tr_loss:
        hist_tr_loss = [float(tr_loss)]
        hist_va_loss = [float(va_loss)]
        hist_tr_acc = [_accuracy(ytr, _predict_classes(Xtr, w_raw, theta_raw))]
        hist_va_acc = [_accuracy(yva, _predict_classes(Xva, w_raw, theta_raw))]

    return TrainResult(
        w=w_raw,
        theta=theta_raw,
        train_loss=float(tr_loss),
        val_loss=float(va_loss),
        train_losses=hist_tr_loss,
        val_losses=hist_va_loss,
        train_accs=hist_tr_acc,
        val_accs=hist_va_acc,
    )


def save_model_json(path: str, result: TrainResult) -> None:
    model = {
        "model_type": "ordinal_logit",
        "w": [float(v) for v in result.w.tolist()],
        "theta": [float(v) for v in result.theta.tolist()],
        "train_loss": float(result.train_loss),
        "val_loss": float(result.val_loss),
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)


def plot_accuracy_loss(res: TrainResult) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))
    it = list(range(1, len(res.train_losses) + 1))
    ax1.plot(it, res.train_accs, label="Train Accuracy")
    ax1.plot(it, res.val_accs, label="Val Accuracy")
    ax1.set_title("Training and Validation Accuracy")
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Accuracy")
    ax1.set_ylim(0.0, 1.0)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax2.plot(it, res.train_losses, label="Train Loss")
    ax2.plot(it, res.val_losses, label="Val Loss")
    ax2.set_title("Training and Validation Loss")
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Loss (NLL)")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    fig.suptitle("Training / Validation — train / val split")
    fig.tight_layout(rect=(0, 0, 1, 0.92))


def plot_ordinal_diag(Xva: np.ndarray, yva: np.ndarray, w: np.ndarray, theta: np.ndarray, seed: int) -> None:
    s = (Xva @ w).astype(float)
    y_pred = _predict_classes(Xva, w, theta)
    correct = (y_pred == yva)
    rng = np.random.default_rng(seed ^ 0xA5A5A5A5)
    jitter = rng.normal(0.0, 0.08, size=s.shape[0])
    y_band = yva.astype(float) + jitter
    face = np.where(correct, "#2ca02c", "#d62728")
    edge = np.where(correct, "#1b6b1b", "#7f1d1d")
    alpha = np.where(correct, 0.85, 0.95)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.2, 7.6))
    ax1.scatter(s, y_band, c=face, edgecolors=edge, s=58, alpha=alpha)
    ax1.scatter([], [], c="#2ca02c", edgecolors="#1b6b1b", s=58, label="correct")
    ax1.scatter([], [], c="#d62728", edgecolors="#7f1d1d", s=58, label="wrong")
    ax1.axvline(theta[0], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.axvline(theta[1], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.text(theta[0], 2.45, r"$\theta_1$", ha="center", va="bottom")
    ax1.text(theta[1], 2.45, r"$\theta_2$", ha="center", va="bottom")
    ax1.set_title(r"Prediction correctness on projection $s = w^\top x$")
    ax1.set_xlabel(r"score $s = w^\top x$")
    ax1.set_yticks([0, 1, 2])
    ax1.set_yticklabels(["class 0", "class 1", "class 2"])
    ax1.set_ylim(-0.5, 2.6)
    ax1.grid(True, axis="x", alpha=0.35)
    ax1.legend(loc="upper left", frameon=True)
    xmin = float(np.percentile(s, 1))
    xmax = float(np.percentile(s, 99))
    span = xmax - xmin
    if not np.isfinite(span) or span <= 0:
        span = 1.0
    xmin -= 0.2 * span
    xmax += 0.2 * span
    xs = np.linspace(xmin, xmax, 500)
    c0 = _sigmoid(theta[0] - xs)
    c1 = _sigmoid(theta[1] - xs)
    ax2.plot(xs, c0, color="#1f77b4", linewidth=2.5, label=r"$\sigma(\theta_1 - s)$")
    ax2.plot(xs, c1, color="#2ca02c", linewidth=2.5, label=r"$\sigma(\theta_2 - s)$")
    ax2.axvline(theta[0], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.9)
    ax2.axvline(theta[1], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.9)
    ax2.set_title("Cumulative link functions")
    ax2.set_xlabel(r"score $s$")
    ax2.set_ylabel("value")
    ax2.set_ylim(-0.02, 1.02)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper right")
    fig.tight_layout()


def main() -> int:
    p = argparse.ArgumentParser(description="Train ml_health ordinal model (MLE) + plots.")
    p.add_argument("--data", default=os.path.join("core", "ml_health_data.jsonl"))
    p.add_argument("--out", default=os.path.join("core", "ml_health_model.json"))
    p.add_argument("--no-show", action="store_true")
    p.add_argument("--epochs", type=int, default=250)
    p.add_argument("--l2", type=float, default=0.01)
    p.add_argument("--val-ratio", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument(
        "--select-metric",
        default="macro_f1",
        choices=["macro_f1", "acc", "recall_error", "f2_error"],
    )
    p.add_argument(
        "--class-weights",
        type=float,
        nargs=3,
        default=[1.0, 1.0, 1.0],
        metavar=("W_OK", "W_WARN", "W_ERR"),
    )
    args = p.parse_args()

    X, y = _prepare_xy(_read_jsonl(args.data))
    if X.shape[0] < 10:
        raise SystemExit(f"Too few samples in {args.data}: {X.shape[0]}")

    runs = int(max(1, args.runs))
    base_seed = int(args.seed) if args.seed is not None else (int.from_bytes(os.urandom(8), "little") & 0x7FFFFFFF)

    best: TrainResult | None = None
    best_seed: int | None = None
    best_split: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None
    best_score = -1e9

    for k in range(runs):
        seed = (base_seed + 1000003 * k) & 0x7FFFFFFF
        rng = np.random.default_rng(seed)
        Xtr, ytr, Xva, yva = _stratified_split(X, y, float(args.val_ratio), rng=rng)

        res = train_mle(
            Xtr=Xtr,
            ytr=ytr,
            Xva=Xva,
            yva=yva,
            maxiter=int(args.epochs),
            l2=float(args.l2),
            seed=int(seed),
            class_weights=np.asarray(args.class_weights, dtype=float),
            threshold_metric=str(args.select_metric),
        )
        yhat = _predict_classes(Xva, res.w, res.theta)
        acc = _accuracy(yva, yhat)
        mf1 = _macro_f1(yva, yhat, n_classes=3)
        prec_e, rec_e = _per_class_pr(yva, yhat, 2)
        score = mf1 + 0.15 * acc + 0.10 * rec_e + 0.03 * prec_e
        if score > best_score:
            best_score = score
            best = res
            best_seed = int(seed)
            best_split = (Xtr, ytr, Xva, yva)

    if best is None or best_split is None:
        raise SystemExit("Training failed.")

    Xtr, ytr, Xva, yva = best_split
    save_model_json(args.out, best)

    yhat = _predict_classes(Xva, best.w, best.theta)
    cm = _confusion_matrix(yva, yhat, n_classes=3)
    acc = _accuracy(yva, yhat)
    mf1 = _macro_f1(yva, yhat, n_classes=3)
    prec_e, rec_e = _per_class_pr(yva, yhat, 2)

    print(f"seed      : {best_seed}")
    print(f"saved model: {args.out}")
    print("confusion (rows=true, cols=pred):")
    for i in range(3):
        print("  " + " ".join(f"{int(v):4d}" for v in cm[i, :].tolist()))
    print(f"val acc: {acc:.4f} | macro_f1: {mf1:.4f} | error recall: {rec_e:.4f} | error precision: {prec_e:.4f}")

    plot_accuracy_loss(best)
    plot_ordinal_diag(Xva, yva, best.w, best.theta, seed=int(best_seed or base_seed))

    if not bool(args.no_show):
        plt.show()
    plt.close("all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

import mord


FEATURE_NAMES = ["cpu", "ram", "disk", "battery_ok", "network_ok", "gpu"]
N_FEATURES = 6
GPU_FALLBACK = 0.85  # как в core/ml_health.py, когда GPU не определён


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def ordinal_probs(X: np.ndarray, w: np.ndarray, theta: np.ndarray) -> np.ndarray:
    score = X @ w
    c0 = sigmoid(theta[0] - score)
    c1 = sigmoid(theta[1] - score)
    p0 = np.clip(c0, 0.0, 1.0)
    p1 = np.clip(c1 - c0, 0.0, 1.0)
    p2 = np.clip(1.0 - c1, 0.0, 1.0)
    P = np.stack([p0, p1, p2], axis=1)
    s = P.sum(axis=1, keepdims=True)
    s = np.where(s <= 0.0, 1.0, s)
    return P / s


def nll_loss(X: np.ndarray, y: np.ndarray, w: np.ndarray, theta: np.ndarray) -> float:
    P = ordinal_probs(X, w, theta)
    py = P[np.arange(P.shape[0]), y]
    py = np.clip(py, 1e-12, 1.0)
    return float(-np.mean(np.log(py)))


def fit_scaler(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd < 1e-6, 1.0, sd)
    return mu, sd


def apply_scaler(X: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return (X - mu) / sd


def to_raw_params(w_z: np.ndarray, theta_z: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert parameters learned on z-scored features back to raw feature space
    compatible with core/ml_health.py.
    score_z = w_z^T ((x-mu)/sd) = (w_z/sd)^T x - sum(w_z*mu/sd)
    Model uses sigmoid(theta - score), so theta_raw = theta_z + bias.
    """
    w_raw = w_z / sd
    bias = float(np.sum(w_z * (mu / sd)))
    theta_raw = theta_z + bias
    return w_raw, theta_raw


def eval_metrics(X: np.ndarray, y: np.ndarray, w: np.ndarray, theta: np.ndarray) -> dict:
    yhat = ordinal_probs(X, w, theta).argmax(axis=1)
    cm = confusion_matrix(y, yhat, labels=[0, 1, 2])
    acc = float(accuracy_score(y, yhat))
    # error (class 2) precision/recall
    tp = float(((y == 2) & (yhat == 2)).sum())
    fp = float(((y != 2) & (yhat == 2)).sum())
    fn = float(((y == 2) & (yhat != 2)).sum())
    prec = tp / (tp + fp + 1e-12)
    rec = tp / (tp + fn + 1e-12)
    return {"acc": acc, "cm": cm, "prec_err": float(prec), "recall_err": float(rec)}


def read_jsonl(path: str) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def prepare_xy(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    X: list[list[float]] = []
    y: list[int] = []
    for r in rows:
        feats = r.get("features")
        lab = r.get("label")
        if not isinstance(feats, list):
            continue
        try:
            x = [float(v) for v in feats]
            yy = int(lab)
        except Exception:
            continue
        if yy not in (0, 1, 2):
            continue

        if len(x) == 5:
            x = x + [GPU_FALLBACK]
        if len(x) < N_FEATURES:
            x = x + [GPU_FALLBACK] * (N_FEATURES - len(x))
        if len(x) > N_FEATURES:
            x = x[:N_FEATURES]

        X.append(x)
        y.append(yy)
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def save_model_json(path: str, w: np.ndarray, theta: np.ndarray) -> None:
    model = {
        "model_type": "ordinal_logit",
        "w": [float(v) for v in w.tolist()],
        "theta": [float(v) for v in theta.tolist()],
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)


def plot_accuracy_loss_curves(
    Xtr: np.ndarray,
    ytr: np.ndarray,
    Xva: np.ndarray,
    yva: np.ndarray,
    alpha: float,
    seed: int,
    points: int = 25,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """
    mord doesn't expose per-epoch history, so we build a learning-curve style history:
    train on increasing subset sizes and evaluate accuracy + NLL on train/val.
    """
    rng = np.random.default_rng(seed)
    n = int(Xtr.shape[0])
    order = np.arange(n, dtype=int)
    rng.shuffle(order)

    sizes = np.linspace(max(30, n // 10), n, int(max(6, points))).astype(int)
    sizes = np.unique(sizes)

    train_acc: list[float] = []
    val_acc: list[float] = []
    train_loss: list[float] = []
    val_loss: list[float] = []

    for m in sizes.tolist():
        idx = order[:m]
        mu, sd = fit_scaler(Xtr[idx])
        Xtrz = apply_scaler(Xtr[idx], mu, sd)
        Xvaz = apply_scaler(Xva, mu, sd)
        model = mord.LogisticAT(alpha=float(alpha))
        model.fit(Xtrz, ytr[idx])
        w_z = np.asarray(model.coef_, dtype=float).reshape(-1)
        theta_z = np.asarray(model.theta_, dtype=float).reshape(-1)[:2]
        w, theta = to_raw_params(w_z, theta_z, mu, sd)

        yhat_tr = ordinal_probs(Xtr[idx], w, theta).argmax(axis=1)
        yhat_va = ordinal_probs(Xva, w, theta).argmax(axis=1)
        train_acc.append(float(accuracy_score(ytr[idx], yhat_tr)))
        val_acc.append(float(accuracy_score(yva, yhat_va)))
        train_loss.append(nll_loss(Xtr[idx], ytr[idx], w, theta))
        val_loss.append(nll_loss(Xva, yva, w, theta))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))
    it = list(range(1, len(train_acc) + 1))

    ax1.plot(it, train_acc, label="Train Accuracy")
    ax1.plot(it, val_acc, label="Val Accuracy")
    ax1.set_title("Training and Validation Accuracy")
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Accuracy")
    ax1.set_ylim(0.0, 1.0)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.plot(it, train_loss, label="Train Loss")
    ax2.plot(it, val_loss, label="Val Loss")
    ax2.set_title("Training and Validation Loss")
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Loss (NLL)")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    fig.suptitle("Training / Validation — train / val split")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return train_acc, val_acc, train_loss, val_loss


def plot_ordinal_diagnostics(
    Xva: np.ndarray,
    yva: np.ndarray,
    w: np.ndarray,
    theta: np.ndarray,
    seed: int,
) -> None:
    s = (Xva @ w).astype(float)
    y_pred = ordinal_probs(Xva, w, theta).argmax(axis=1)
    correct = (y_pred == yva)

    rng = np.random.default_rng(seed ^ 0xA5A5A5A5)
    jitter = rng.normal(0.0, 0.08, size=s.shape[0])
    y_band = yva.astype(float) + jitter

    face = np.where(correct, "#2ca02c", "#d62728")
    edge = np.where(correct, "#1b6b1b", "#7f1d1d")
    alpha = np.where(correct, 0.85, 0.95)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.2, 7.6))

    ax1.scatter(s, y_band, c=face, edgecolors=edge, s=58, alpha=alpha)
    ax1.scatter([], [], c="#2ca02c", edgecolors="#1b6b1b", s=58, label="correct")
    ax1.scatter([], [], c="#d62728", edgecolors="#7f1d1d", s=58, label="wrong")
    ax1.axvline(theta[0], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.axvline(theta[1], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.text(theta[0], 2.45, r"$\theta_1$", ha="center", va="bottom")
    ax1.text(theta[1], 2.45, r"$\theta_2$", ha="center", va="bottom")
    ax1.set_title(r"Prediction correctness on projection $s = w^\top x$")
    ax1.set_xlabel(r"score $s = w^\top x$")
    ax1.set_yticks([0, 1, 2])
    ax1.set_yticklabels(["class 0", "class 1", "class 2"])
    ax1.set_ylim(-0.5, 2.6)
    ax1.grid(True, axis="x", alpha=0.35)
    ax1.legend(loc="upper left", frameon=True)

    xmin = float(np.percentile(s, 1))
    xmax = float(np.percentile(s, 99))
    span = xmax - xmin
    if not np.isfinite(span) or span <= 0:
        span = 1.0
    xmin -= 0.2 * span
    xmax += 0.2 * span
    xs = np.linspace(xmin, xmax, 500)
    c0 = sigmoid(theta[0] - xs)
    c1 = sigmoid(theta[1] - xs)
    ax2.plot(xs, c0, color="#1f77b4", linewidth=2.5, label=r"$\sigma(\theta_1 - s)$")
    ax2.plot(xs, c1, color="#2ca02c", linewidth=2.5, label=r"$\sigma(\theta_2 - s)$")
    ax2.axvline(theta[0], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.9)
    ax2.axvline(theta[1], color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.9)
    ax2.set_title("Cumulative link functions")
    ax2.set_xlabel(r"score $s$")
    ax2.set_ylabel("value")
    ax2.set_ylim(-0.02, 1.02)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper right")

    fig.tight_layout()


def main() -> int:
    p = argparse.ArgumentParser(description="Train ml_health ordinal model (mord) + plots.")
    p.add_argument("--data", default=os.path.join("core", "ml_health_data.jsonl"))
    p.add_argument("--out", default=os.path.join("core", "ml_health_model.json"))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--alpha", type=float, default=1.0, help="L2 regularization strength for mord (used if --search-alpha is off).")
    # IMPORTANT: core/ml_health.py implements cumulative-link ordinal logit.
    # mord.LogisticAT matches this (coef_ + theta_ can be exported as w/theta).
    # mord.LogisticIT uses a different formulation and is NOT compatible with our runtime predictor.
    p.add_argument(
        "--select-metric",
        default="acc",
        choices=["acc", "balanced"],
        help="How to choose best model/alpha during search. acc = best overall accuracy.",
    )
    p.add_argument(
        "--search-alpha",
        action="store_true",
        help="Grid-search alpha on validation split to improve accuracy.",
    )
    p.add_argument(
        "--alpha-grid",
        type=float,
        nargs="*",
        default=[0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0],
        help="Alpha candidates for --search-alpha.",
    )
    p.add_argument("--curve-points", type=int, default=25, help="Number of points for accuracy/loss curves.")
    p.add_argument("--no-show", action="store_true", help="Do not show plots window.")
    args = p.parse_args()

    X, y = prepare_xy(read_jsonl(args.data))
    if X.shape[0] < 10:
        raise SystemExit(f"Too few samples in {args.data}: {X.shape[0]}")

    Xtr, Xva, ytr, yva = train_test_split(
        X, y, test_size=0.2, random_state=int(args.seed), stratify=y
    )

    # scale features for mord, then convert params back to raw space
    mu, sd = fit_scaler(Xtr)
    Xtrz = apply_scaler(Xtr, mu, sd)
    Xvaz = apply_scaler(Xva, mu, sd)

    def make_model(alpha: float):
        return mord.LogisticAT(alpha=float(alpha))

    best_alpha = float(args.alpha)
    best_model_name = "AT"
    if bool(args.search_alpha):
        best_score = -1e9
        for a in [float(v) for v in (args.alpha_grid or [])]:
            m = make_model(a)
            m.fit(Xtrz, ytr)
            yhat = m.predict(Xvaz)
            cm = confusion_matrix(yva, yhat, labels=[0, 1, 2])
            acc = float(accuracy_score(yva, yhat))
            tp = float(cm[2, 2])
            fp = float(cm[0, 2] + cm[1, 2])
            fn = float(cm[2, 0] + cm[2, 1])
            prec_e = tp / (tp + fp + 1e-12)
            rec_e = tp / (tp + fn + 1e-12)
            score = acc if str(args.select_metric) == "acc" else (acc + 0.06 * rec_e + 0.02 * prec_e)
            if score > best_score:
                best_score = score
                best_alpha = float(a)

    model = make_model(best_alpha)
    model.fit(Xtrz, ytr)

    w_z = np.asarray(model.coef_, dtype=float).reshape(-1)
    theta_z = np.asarray(model.theta_, dtype=float).reshape(-1)[:2]
    w, theta = to_raw_params(w_z, theta_z, mu, sd)
    met = eval_metrics(Xva, yva, w, theta)
    acc = float(met["acc"])
    cm = met["cm"]

    save_model_json(args.out, w=w, theta=theta)

    print(f"saved model: {args.out}")
    if bool(args.search_alpha):
        print(f"best: model={best_model_name} alpha={best_alpha}")
    print(f"val acc: {acc:.4f}")
    print("confusion (rows=true, cols=pred):")
    for i in range(3):
        print("  " + " ".join(f"{int(v):4d}" for v in cm[i, :].tolist()))
    print(f"error recall: {met['recall_err']:.4f} | error precision: {met['prec_err']:.4f}")

    # Plots like previous version:
    # 1) Training/Validation Accuracy + Loss
    plot_accuracy_loss_curves(
        Xtr=Xtr,
        ytr=ytr,
        Xva=Xva,
        yva=yva,
        alpha=float(best_alpha),
        seed=int(args.seed),
        points=int(args.curve_points),
    )
    # 2) Ordinal diagnostics (correct / wrong on projection + sigmoid curves)
    plot_ordinal_diagnostics(Xva=Xva, yva=yva, w=w, theta=theta, seed=int(args.seed))
    # 3) Confusion matrix (text + optional visual is already printed; keep a small plot too)
    fig_cm = plt.figure(figsize=(5.8, 4.8))
    ax = fig_cm.add_subplot(1, 1, 1)
    ax.set_title("Confusion matrix (val)")
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xlabel("pred")
    ax.set_ylabel("true")
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    for i in range(3):
        for j in range(3):
            ax.text(j, i, str(int(cm[i, j])), ha="center", va="center", color="black")
    fig_cm.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig_cm.tight_layout()

    if not bool(args.no_show):
        plt.show()
    plt.close("all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

