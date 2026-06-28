import json
import os
from datetime import datetime
from typing import Dict, List, Sequence, Tuple

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

from core.ml_health import N_FEATURES, normalize_raw_features

DATA_PATH = os.path.join("core", "ml_health_data.jsonl")
OUT_PATH = os.path.join("core", "ml_health_model.json")

EPOCHS = 500
VAL_RATIO = 0.2
RANDOM_STATE = 42
SHOW_PLOTS = True

OVERSAMPLE_WARN = 3
OVERSAMPLE_ERROR = 4

MIN_OK_RECALL = 0.80

LABEL_ORDER = ["OK", "Warn", "Error"]
BASE_FEATURE_COLS = ["cpu", "ram", "disk", "battery_ok", "network_ok", "gpu"]
FEATURE_COLS = BASE_FEATURE_COLS + ["peak_load"]

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
        X_list.append(normalize_raw_features(x))
        y_list.append(yy)
    return np.asarray(X_list, dtype=float), np.asarray(y_list, dtype=int)

def _oversample_indices(y: np.ndarray) -> np.ndarray:
    idx: List[int] = []
    for i in range(int(y.size)):
        idx.append(i)
        if y[i] == 1:
            for _ in range(OVERSAMPLE_WARN - 1):
                idx.append(i)
        elif y[i] == 2:
            for _ in range(OVERSAMPLE_ERROR - 1):
                idx.append(i)
    return np.asarray(idx, dtype=int)

def _add_peak_load(X: np.ndarray) -> np.ndarray:
    peak = np.max(X[:, [0, 1, 2, 5]], axis=1, keepdims=True)
    return np.hstack([X, peak])

def _make_df(X: np.ndarray, y: np.ndarray):
    import pandas as pd
    Xe = _add_peak_load(X)
    df = pd.DataFrame(Xe, columns=FEATURE_COLS)
    df["label"] = pd.Categorical([LABEL_ORDER[int(v)] for v in y.tolist()], categories=LABEL_ORDER, ordered=True)
    return df

def _cutpoint_names(params_index) -> List[str]:
    names = [str(k) for k in params_index]
    return [n for n in names if n not in FEATURE_COLS]

def _params_vector(params: Dict[str, float], cut_names: List[str]) -> np.ndarray:
    coef = [float(params[c]) for c in FEATURE_COLS]
    cuts = [float(params[cut_names[0]]), float(params[cut_names[1]])]
    return np.asarray(coef + cuts, dtype=float)

def _latent_cutpoints(raw_t0: float, raw_t1: float) -> Tuple[float, float]:
    t0 = float(raw_t0)
    t1 = t0 + float(np.exp(raw_t1))
    return t0, t1


def _ordinal_probs_score(s: np.ndarray, theta0: float, theta1: float) -> np.ndarray:
    s = np.asarray(s, dtype=float).reshape(-1)
    z0 = theta0 - s
    z1 = theta1 - s
    c0 = _sigmoid(z0)
    c1 = _sigmoid(z1)
    p0 = np.clip(c0, 0.0, 1.0)
    p1 = np.clip(c1 - c0, 0.0, 1.0)
    p2 = np.clip(1.0 - c1, 0.0, 1.0)
    P = np.stack([p0, p1, p2], axis=1)
    tot = P.sum(axis=1, keepdims=True)
    tot = np.where(tot <= 0.0, 1.0, tot)
    return P / tot

def _predict_with_params(results, df_exog, params) -> np.ndarray:
    if isinstance(params, dict):
        cut_names = _cutpoint_names(results.params.index)
        pvec = _params_vector(params, cut_names)
    else:
        pvec = np.asarray(params, dtype=float)
    probs = results.model.predict(pvec, exog=df_exog[FEATURE_COLS])
    arr = np.asarray(probs, dtype=float)
    if arr.ndim == 1:
        return arr.astype(int)
    return arr.argmax(axis=1).astype(int)

def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[int, int, float, List[float]]:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    correct = int(np.sum(y_true == y_pred))
    wrong = int(y_true.size - correct)
    acc = (correct / y_true.size) if y_true.size else 0.0
    recall: List[float] = []
    for c in range(3):
        mask = y_true == c
        n = int(mask.sum())
        recall.append(float(np.sum(y_pred[mask] == c) / n) if n else 0.0)
    return correct, wrong, acc, recall

def _print_metrics(title: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    correct, wrong, acc, recall = _metrics(y_true, y_pred)
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    print(f"\n=== {title} ===")
    print(f"Всего примеров : {y_true.size}")
    print(f"Правильно      : {correct}")
    print(f"Неправильно    : {wrong}")
    print(f"Accuracy       : {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Macro-F1       : {f1_score(y_true, y_pred, average='macro'):.4f}")
    print("\nПо классам (истинный класс -> верно / неверно):")
    for i, name in enumerate(LABEL_ORDER):
        mask = y_true == i
        n = int(mask.sum())
        if n == 0:
            print(f"  {name:5s}: нет примеров")
            continue
        ok = int(np.sum(y_pred[mask] == i))
        bad = n - ok
        print(f"  {name:5s}: {ok} верно, {bad} неверно (из {n}) | recall={recall[i]:.3f}")
    cm = np.zeros((3, 3), dtype=int)
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        cm[int(t), int(p)] += 1
    print("\nМатрица ошибок (строка=истина, столбец=предсказание):")
    print("        OK   Warn Error")
    for i, name in enumerate(LABEL_ORDER):
        print(f"  {name:5s} " + " ".join(f"{cm[i, j]:5d}" for j in range(3)))

def _tune_cutpoints(results, df_val, y_val: np.ndarray, cut_names: List[str]) -> Tuple[float, float, float, List[float]]:
    best_d0, best_d1 = 0.0, 0.0
    best_score = -1.0
    best_recall = [0.0, 0.0, 0.0]
    base = results.params.copy()
    for d0 in np.arange(-1.5, 1.55, 0.05):
        for d1 in np.arange(-1.5, 1.55, 0.05):
            p = base.copy()
            p[cut_names[0]] = float(p[cut_names[0]]) + float(d0)
            p[cut_names[1]] = float(p[cut_names[1]]) + float(d1)
            y_pred = _predict_with_params(results, df_val[FEATURE_COLS], p)
            _, _, _, recall = _metrics(y_val, y_pred)
            if recall[0] < MIN_OK_RECALL:
                continue
            score = 0.15 * recall[0] + 0.425 * recall[1] + 0.425 * recall[2]
            if score > best_score:
                best_score = score
                best_d0, best_d1 = float(d0), float(d1)
                best_recall = recall
    if best_score < 0:
        for d0 in np.arange(-1.2, 1.25, 0.1):
            for d1 in np.arange(-1.2, 1.25, 0.1):
                p = base.copy()
                p[cut_names[0]] = float(p[cut_names[0]]) + float(d0)
                p[cut_names[1]] = float(p[cut_names[1]]) + float(d1)
                y_pred = _predict_with_params(results, df_val[FEATURE_COLS], p)
                mf1 = float(f1_score(y_val, y_pred, average="macro"))
                if mf1 > best_score:
                    best_score = mf1
                    best_d0, best_d1 = float(d0), float(d1)
                    _, _, _, best_recall = _metrics(y_val, y_pred)
    return best_d0, best_d1, best_score, best_recall

def _apply_cut_offsets(params_dict: Dict[str, float], cut_names: List[str], d0: float, d1: float) -> Dict[str, float]:
    out = dict(params_dict)
    out[cut_names[0]] = float(out[cut_names[0]]) + float(d0)
    out[cut_names[1]] = float(out[cut_names[1]]) + float(d1)
    return out

def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out

def plot_ordinal_diag(
    df_exog,
    y_true: np.ndarray,
    params: Dict[str, float],
    cut_names: List[str],
    *,
    seed: int = RANDOM_STATE,
) -> None:
    beta = np.asarray([float(params[c]) for c in FEATURE_COLS], dtype=float)
    X = np.asarray(df_exog[FEATURE_COLS], dtype=float)
    s = (X @ beta).astype(float)
    raw_t0 = float(params[cut_names[0]])
    raw_t1 = float(params[cut_names[1]])
    theta0, theta1 = _latent_cutpoints(raw_t0, raw_t1)
    P = _ordinal_probs_score(s, theta0, theta1)
    y_pred = P.argmax(axis=1).astype(int)
    y_true = np.asarray(y_true, dtype=int)
    correct = y_pred == y_true
    rng = np.random.default_rng(int(seed) ^ 0xA5A5A5A5)
    jitter = rng.normal(0.0, 0.08, size=s.shape[0])
    y_band = y_true.astype(float) + jitter
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.2, 7.6))
    face = np.where(correct, "#2ca02c", "#d62728")
    edge = np.where(correct, "#1b6b1b", "#7f1d1d")
    alpha = np.where(correct, 0.85, 0.95)
    ax1.scatter(s, y_band, c=face, edgecolors=edge, s=58, alpha=alpha)
    ax1.scatter([], [], c="#2ca02c", edgecolors="#1b6b1b", s=58, label="верно")
    ax1.scatter([], [], c="#d62728", edgecolors="#7f1d1d", s=58, label="неверно")
    ax1.axvline(theta0, color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.axvline(theta1, color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.8)
    ax1.text(theta0, 2.45, r"$\theta_1$", ha="center", va="bottom")
    ax1.text(theta1, 2.45, r"$\theta_2$", ha="center", va="bottom")
    ax1.axvspan(theta0, theta1, color="#ffeeaa", alpha=0.12, label="зона Warn")
    ax1.set_title(r"Верно / неверно: $s = X\beta$, класс = argmax $P(Y|s,\theta)$")
    ax1.set_xlabel(r"score $s = X\beta$")
    ax1.set_yticks([0, 1, 2])
    ax1.set_yticklabels(LABEL_ORDER)
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
    c0 = _sigmoid(theta0 - xs)
    c1 = _sigmoid(theta1 - xs)
    ax2.plot(xs, c0, color="#1f77b4", linewidth=2.5, label=r"$\sigma(\theta_1 - s)$")
    ax2.plot(xs, c1, color="#2ca02c", linewidth=2.5, label=r"$\sigma(\theta_2 - s)$")
    ax2.axvline(theta0, color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.9)
    ax2.axvline(theta1, color="#4c4c4c", linestyle="--", linewidth=1.2, alpha=0.9)
    ax2.set_title("Кумулятивные функции связи (пороги)")
    ax2.set_xlabel(r"score $s$")
    ax2.set_ylabel("value")
    ax2.set_ylim(-0.02, 1.02)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper right")
    fig.tight_layout()

def main() -> int:
    from statsmodels.miscmodels.ordinal_model import OrderedModel

    rows = _read_jsonl(DATA_PATH)
    X, y = _prepare_xy(rows)
    if X.shape[0] < 10:
        raise SystemExit(f"Too few samples in {DATA_PATH}: {X.shape[0]}")
    formula = "label ~ 0 + " + " + ".join(FEATURE_COLS)

    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=VAL_RATIO, stratify=y, random_state=RANDOM_STATE
    )
    idx_os = _oversample_indices(y_tr)
    df_tr = _make_df(X_tr[idx_os], y_tr[idx_os])
    df_val = _make_df(X_val, y_val)

    model_val = OrderedModel.from_formula(formula, df_tr, distr="logit")
    results_val = model_val.fit(method="bfgs", disp=False, maxiter=int(EPOCHS))
    cut_names = _cutpoint_names(results_val.params.index)
    if len(cut_names) < 2:
        raise SystemExit(f"Expected 2 cutpoints, got: {cut_names}")

    d0, d1, val_score, val_recall = _tune_cutpoints(results_val, df_val, y_val, cut_names)
    print(
        f"\nПодбор порогов на валидации ({int(100 * VAL_RATIO)}%): "
        f"d_OK/Warn={d0:+.2f}, d_Warn/Error={d1:+.2f}, score={val_score:.4f}, "
        f"recall OK/Warn/Error={[round(r, 3) for r in val_recall]}"
    )

    y_val_base = _predict_with_params(results_val, df_val[FEATURE_COLS], results_val.params)
    _print_metrics("До настройки (валидация)", y_val, y_val_base)

    p_val = results_val.params.copy()
    p_val[cut_names[0]] += d0
    p_val[cut_names[1]] += d1
    y_val_tuned = _predict_with_params(results_val, df_val[FEATURE_COLS], p_val)
    _print_metrics("После настройки порогов (валидация)", y_val, y_val_tuned)
    idx_full = _oversample_indices(y)
    df_full = _make_df(X[idx_full], y[idx_full])
    model = OrderedModel.from_formula(formula, df_full, distr="logit")
    results = model.fit(method="bfgs", disp=False, maxiter=int(EPOCHS))
    base_params: Dict[str, float] = {str(k): float(v) for k, v in results.params.to_dict().items()}
    tuned_params = _apply_cut_offsets(base_params, cut_names, d0, d1)
    df_eval = _make_df(X, y)
    import pandas as pd
    p_series = pd.Series(tuned_params)
    y_pred = _predict_with_params(results, df_eval[FEATURE_COLS], p_series)
    correct, wrong, acc, _rec = _metrics(y, y_pred)
    _print_metrics("Финальная модель (все данные, с настройкой порогов)", y, y_pred)
    if SHOW_PLOTS:
        try:
            t0, t1 = _latent_cutpoints(tuned_params[cut_names[0]], tuned_params[cut_names[1]])
            print(f"\nПороги на шкале score: theta1={t0:.4f}, theta2={t1:.4f}")
            print(f"  (в JSON raw: {cut_names[0]}={tuned_params[cut_names[0]]:.4f}, "
                  f"{cut_names[1]}={tuned_params[cut_names[1]]:.4f} — второй это log-шаг, не theta2)")
            plot_ordinal_diag(
                df_eval,
                y,
                tuned_params,
                cut_names,
                seed=RANDOM_STATE,
            )
            plt.show()
        except Exception as e:
            print(f"Графики пропущены: {e}")
        finally:
            plt.close("all")
    out = {
        "model_type": "statsmodels_ordered_logit",
        "meta": {
            "trainer": "statsmodels.OrderedModel",
            "trained_at": datetime.now().isoformat(timespec="seconds"),
            "formula": formula,
            "label_order": LABEL_ORDER,
            "features": FEATURE_COLS,
            "n_samples": int(X.shape[0]),
            "oversample_warn": OVERSAMPLE_WARN,
            "oversample_error": OVERSAMPLE_ERROR,
            "cutpoint_offsets": {cut_names[0]: d0, cut_names[1]: d1},
            "val_tune_score": float(val_score),
            "val_recall": [float(r) for r in val_recall],
            "statsmodels_params": tuned_params,
            "cut_names": cut_names,
            "theta": list(_latent_cutpoints(tuned_params[cut_names[0]], tuned_params[cut_names[1]])),
            "coef": {c: float(tuned_params[c]) for c in FEATURE_COLS},
            "train_correct": correct,
            "train_wrong": wrong,
            "train_accuracy": float(acc),
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nsaved model: {OUT_PATH}")
    try:
        print(results.summary())
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
