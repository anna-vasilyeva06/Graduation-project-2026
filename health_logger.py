import argparse
import datetime as dt
import json
import os
import time
from zoneinfo import ZoneInfo
from typing import Any, Dict, Optional, Tuple


_TZ = ZoneInfo("Asia/Yekaterinburg")
_TS_FORMAT = "%Y-%m-%d %H:%M:%S"


def _now_local() -> dt.datetime:
    return dt.datetime.now(tz=_TZ)


def _fmt_local(ts: dt.datetime) -> str:
    return ts.astimezone(_TZ).strftime(_TS_FORMAT)


def _severity_rank(status: Optional[str]) -> int:
    return {"ok": 0, "warning": 1, "error": 2}.get(status or "ok", 0)


def _max_severity(a: Optional[str], b: Optional[str]) -> str:
    ra = _severity_rank(a)
    rb = _severity_rank(b)
    return (a or "ok") if ra >= rb else (b or "ok")


def _compute_status_final(health: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Returns:
      status_final: max(rule_status, ml_status, rules overall status)
      status_parts: small dict for analysis
    """
    rules_status = (health or {}).get("status") or "ok"
    ml = (health or {}).get("ml") or {}
    rule_status = ml.get("rule_status") or rules_status
    ml_status = ml.get("ml_status")

    status_final = rules_status
    status_final = _max_severity(status_final, rule_status)
    status_final = _max_severity(status_final, ml_status)

    return status_final, {
        "rules": rules_status,
        "rule": rule_status,
        "ml": ml_status,
    }


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _extract_cause(health: Dict[str, Any], status_final: str) -> Optional[str]:
    """
    "cause" for episode: the first component marked warning/error.
    For ok episodes cause is empty (None).
    """
    if status_final == "ok":
        return None
    details = (health or {}).get("details") or []
    for st in ("error", "warning"):
        for d in details:
            if (d or {}).get("status") == st:
                comp = (d or {}).get("component") or ""
                val = (d or {}).get("value") or ""
                if comp and val and val != "—":
                    return f"{comp}: {val}"
                return comp or None
    return None


def _collect_state_episode_fields() -> Tuple[str, Optional[str]]:
    """
    Lightweight poll:
      - state: ok/warning/error (final severity)
      - cause: short text (component/value) for warning/error
    """
    from core.system_health import get_system_health

    health = get_system_health()
    status_final, _ = _compute_status_final(health)
    cause = _extract_cause(health, status_final)
    return status_final, cause


def main() -> int:
    p = argparse.ArgumentParser(description="Simple ITMetric episode logger (JSONL).")
    p.add_argument("--interval-s", type=int, default=60, help="Polling interval in seconds (default: 60).")
    p.add_argument(
        "--out-dir",
        default=os.path.join("logs", "health"),
        help="Output directory for JSONL logs (default: logs/health).",
    )
    p.add_argument(
        "--tag",
        default=None,
        help="Optional tag to separate experiments (e.g. 'without', 'with', 'pc1').",
    )
    p.add_argument("--once", action="store_true", help="Collect one poll and exit (no episode unless state changes).")
    args = p.parse_args()

    interval_s = max(5, int(args.interval_s))
    out_dir = os.path.abspath(args.out_dir)
    _ensure_dir(out_dir)

    tag = (args.tag or "").strip()
    tag_part = f"_{tag}" if tag else ""
    day = dt.datetime.now().strftime("%Y%m%d")

    episodes_path = os.path.join(out_dir, f"6_episodes{tag_part}_{day}.jsonl")

    prev_status: Optional[str] = None
    prev_enter_dt: Optional[dt.datetime] = None
    prev_cause: Optional[str] = None

    def _write_episode(state: str, enter_ts: str, exit_ts: str, duration_s: float, cause: Optional[str]) -> None:
        row = {
            "state": state,
            "enter_time": enter_ts,
            "exit_time": exit_ts,
            "duration_s": float(duration_s),
            "cause": cause,
        }
        with open(episodes_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    try:
        while True:
            now_dt = _now_local()
            ts = _fmt_local(now_dt)
            status, cause = _collect_state_episode_fields()

            if prev_status is None:
                prev_status = status
                prev_enter_dt = now_dt
                prev_cause = cause
            elif status != prev_status:
                # close previous episode
                enter_dt = prev_enter_dt or now_dt
                dur_s = (now_dt - enter_dt).total_seconds()
                _write_episode(prev_status, _fmt_local(enter_dt), ts, float(dur_s), prev_cause)

                prev_status = status
                prev_enter_dt = now_dt
                prev_cause = cause

            if args.once:
                break
            time.sleep(interval_s)
    except KeyboardInterrupt:
        now_dt = _now_local()
        ts = _fmt_local(now_dt)
        # Close the current episode on stop (best-effort)
        if prev_status is not None and prev_enter_dt is not None:
            dur_s = (now_dt - prev_enter_dt).total_seconds()
            _write_episode(prev_status, _fmt_local(prev_enter_dt), ts, float(dur_s), prev_cause)
        return 0
    except Exception as e:
        raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

