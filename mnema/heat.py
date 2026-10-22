"""How hard the local model works this computer — the «нагрев» indicator. Cloud AIs don't load the computer, so it is
about local agents only.

Every 2 seconds, while the local model is running or the window asks, it samples:
- the whole processor load (GetSystemTimes),
- the share of it taken by the local model (llama-server, GetProcessTimes),
- memory in use (GlobalMemoryStatusEx),
- the temperature, if Windows gives it without admin rights (ACPI thermal zone; often it doesn't — then it is not shown).

Over the last 20 seconds:
- hot  — temperature ≥ 90 °C, or memory ≥ 92 % (Windows starts swapping to disk), or the processor ≥ 90 % with the model
         taking ≥ 40 % of it;
- warm — temperature ≥ 80 °C, or memory ≥ 85 %, or the processor ≥ 70 % with the model taking ≥ 25 %;
- cool — otherwise; idle — the local model is not running.
Hot for a minute while the model works → Mnema itself lowers the model's priority (windows and the browser stay responsive)
and says so. Fewer cores or stopping the model is the owner's call: buttons in the indicator.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import threading
import time

from . import localllm

WINDOW_S = 20
STEP_S = 2.0
_state = {
    "samples": [],
    "last_poll": 0.0,
    "thread": None,
    "temp": None,
    "temp_at": 0.0,
    "temp_ok": True,
    "hot_since": 0.0,
    "cooled": False,
    "prev_sys": None,
    "prev_proc": None,
}
_lock = threading.Lock()


class _FT(ctypes.Structure):
    _fields_ = [("lo", ctypes.c_uint32), ("hi", ctypes.c_uint32)]


def _ft(f: _FT) -> int:
    return (f.hi << 32) | f.lo


def _psutil():
    try:
        import psutil

        return psutil
    except Exception:
        return None


def _sys_times() -> tuple[float, float] | None:
    if sys.platform != "win32":  # macOS, Linux: seconds summed over all cores, same as the model's own below
        ps = _psutil()
        if not ps:
            return None
        t = ps.cpu_times()
        idle = t.idle + getattr(t, "iowait", 0.0)
        return idle, sum(t)
    idle, kern, user = _FT(), _FT(), _FT()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
        return None
    return _ft(idle), _ft(kern) + _ft(user)  # kernel time includes idle


def _proc_time(pid: int) -> float | None:
    if not pid:
        return None
    if sys.platform != "win32":
        ps = _psutil()
        try:
            t = ps.Process(pid).cpu_times() if ps else None
            return t.user + t.system if t else None
        except Exception:
            return None
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return None
    try:
        c, e, k, u = _FT(), _FT(), _FT(), _FT()
        if not ctypes.windll.kernel32.GetProcessTimes(
            h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)
        ):
            return None
        return _ft(k) + _ft(u)
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def _ram_load() -> int:
    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("a", ctypes.c_ulonglong * 7)]

    if sys.platform != "win32":
        ps = _psutil()
        return int(ps.virtual_memory().percent) if ps else 0
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    return int(m.dwMemoryLoad) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else 0


def _temperature() -> float | None:
    """ACPI thermal zone, °C. Without admin rights Windows often refuses — then None, and we stop asking."""
    now = time.time()
    if not _state["temp_ok"] or now - _state["temp_at"] < 30:
        return _state["temp"]
    _state["temp_at"] = now
    if sys.platform != "win32":  # Linux gives the sensors to everyone; macOS doesn't without admin rights
        ps = _psutil()
        try:
            temps = [x.current for v in (ps.sensors_temperatures() or {}).values() for x in v if x.current]
            _state["temp"] = round(max(temps), 1) if temps else None
        except Exception:
            _state["temp"] = None
        _state["temp_ok"] = _state["temp"] is not None
        return _state["temp"]
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop |"
                " Measure-Object -Property CurrentTemperature -Maximum).Maximum",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        v = float((r.stdout or "").strip().replace(",", "."))
        _state["temp"] = round(v / 10 - 273.15, 1) if v > 0 else None
    except Exception:
        _state["temp"], _state["temp_ok"] = None, False
    return _state["temp"]


def _pid() -> int:
    p = localllm._srv.get("proc")
    return p.pid if p and p.poll() is None else 0


def sample() -> dict:
    st = _sys_times()
    pid = _pid()
    pt = _proc_time(pid)
    cpu = model = 0.0
    if st and _state["prev_sys"]:
        di, dt_ = st[0] - _state["prev_sys"][0], st[1] - _state["prev_sys"][1]
        if dt_ > 0:
            cpu = max(0.0, min(100.0, (1 - di / dt_) * 100))
            if pt is not None and _state["prev_proc"] and _state["prev_proc"][0] == pid:
                model = max(0.0, min(100.0, (pt - _state["prev_proc"][1]) / dt_ * 100))
    _state["prev_sys"], _state["prev_proc"] = st, (pid, pt) if pt is not None else None
    return {"t": time.time(), "cpu": round(cpu, 1), "model": round(model, 1), "ram": _ram_load(), "running": bool(pid)}


def _loop() -> None:
    while time.time() - _state["last_poll"] < 60 or _pid():
        s = sample()
        with _lock:
            _state["samples"] = [x for x in _state["samples"] if s["t"] - x["t"] <= WINDOW_S] + [s]
        if s["running"]:
            _temperature()
        _guard()
        time.sleep(STEP_S)
    _state["thread"] = None


def _ensure_thread() -> None:
    if not _state["thread"]:
        t = threading.Thread(target=_loop, daemon=True, name="mnema-heat")
        _state["thread"] = t
        t.start()


def level(samples: list[dict], temp: float | None, running: bool) -> tuple[str, str]:
    if not running:
        return "idle", "локальная модель не запущена"
    if not samples:
        return "cool", "замеряю"
    cpu = sum(x["cpu"] for x in samples) / len(samples)
    model = sum(x["model"] for x in samples) / len(samples)
    ram = samples[-1]["ram"]
    if temp is not None and temp >= 90:
        return "hot", f"температура {temp:.0f} °C"
    if ram >= 92:
        return "hot", f"память занята на {ram}% — Windows начинает сбрасывать её на диск"
    if cpu >= 90 and model >= 40:
        return "hot", f"процессор занят на {cpu:.0f}%, из них модель — {model:.0f}%"
    if temp is not None and temp >= 80:
        return "warm", f"температура {temp:.0f} °C"
    if ram >= 85:
        return "warm", f"память занята на {ram}%"
    if cpu >= 70 and model >= 25:
        return "warm", f"процессор занят на {cpu:.0f}%, из них модель — {model:.0f}%"
    return "cool", "компьютер справляется спокойно"


def _set_low_priority(pid: int) -> bool:
    if sys.platform != "win32":
        try:
            os.setpriority(os.PRIO_PROCESS, pid, 10)
            return True
        except OSError:
            return False
    h = ctypes.windll.kernel32.OpenProcess(0x0200 | 0x1000, False, pid)  # SET_INFORMATION | QUERY_LIMITED
    if not h:
        return False
    try:
        return bool(ctypes.windll.kernel32.SetPriorityClass(h, 0x4000))  # BELOW_NORMAL_PRIORITY_CLASS
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def _guard() -> None:
    """Hot for a minute while the model works → lower its priority once (reversible, nothing else changes)."""
    with _lock:
        samples = list(_state["samples"])
    lv, _ = level(samples, _state["temp"], bool(_pid()))
    now = time.time()
    if lv != "hot":
        _state["hot_since"] = 0.0
        return
    _state["hot_since"] = _state["hot_since"] or now
    if now - _state["hot_since"] >= 60 and not _state["cooled"] and _pid():
        _state["cooled"] = _set_low_priority(_pid())


def status() -> dict:
    _state["last_poll"] = time.time()
    _ensure_thread()
    with _lock:
        samples = list(_state["samples"])
    running = bool(_pid())
    lv, why = level(samples, _state["temp"], running)
    last = samples[-1] if samples else {"cpu": 0, "model": 0, "ram": _ram_load()}
    return {
        "level": lv,
        "why": why,
        "running": running,
        "model": localllm._srv.get("model", "") if running else "",
        "cpu": round(sum(x["cpu"] for x in samples) / len(samples)) if samples else round(last["cpu"]),
        "model_cpu": round(sum(x["model"] for x in samples) / len(samples)) if samples else 0,
        "ram": last["ram"],
        "temp": _state["temp"],
        "auto_cooled": _state["cooled"],
    }


def cool_down(vault) -> dict:
    """«Снизить нагрузку»: half the cores and low priority; the model restarts with them on the next message."""
    from . import tuning

    e = tuning.get(vault)
    tuning.save(vault, {"threads": max(1, e["threads"] // 2), "low": True})
    if _pid():
        _set_low_priority(_pid())
    return status()


def stop_model() -> dict:
    localllm.stop_server()
    _state.update(cooled=False, hot_since=0.0)
    return status()
