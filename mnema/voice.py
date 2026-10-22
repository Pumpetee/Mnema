"""Voice command: the owner speaks, Mnema recognises the words on this computer and sends them as a message.

Only the microphone is recorded (not the computer's sound, unlike the meeting scribe), into a temporary file that is
deleted right after recognition. The same faster-whisper model as the scribe, already loaded if it was used.
"""

from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path

from . import scribe
from .vault import Vault

_rec: dict = {}


def start(vault: Vault) -> dict:
    if _rec.get("status") == "recording":
        return status()
    ok, why = scribe.available()
    if not ok:
        raise ValueError(why)
    import soundcard as sc

    try:
        mic = sc.default_microphone()
    except Exception:
        raise ValueError(scribe.MIC_HELP) from None
    path = Path(tempfile.gettempdir()) / f"mnema-voice-{int(time.time() * 1000)}.wav"
    stop_evt, errors = threading.Event(), []
    t = threading.Thread(target=scribe._capture, args=(mic, path, stop_evt, errors), daemon=True)
    t.start()
    _rec.clear()
    _rec.update(
        status="recording", path=path, stop=stop_evt, thread=t, errors=errors, started=time.time(), mic=mic.name
    )
    return status()


def status() -> dict:
    out = {"status": _rec.get("status", "idle")}
    if out["status"] == "recording":
        out["elapsed"] = round(time.time() - _rec["started"], 1)
    return out


def cancel() -> dict:
    if _rec.get("status") == "recording":
        _rec["stop"].set()
        _rec["thread"].join(timeout=3)
        Path(_rec["path"]).unlink(missing_ok=True)
    _rec.clear()
    return {"status": "idle"}


def stop(vault: Vault, language: str = "") -> dict:
    """Stop and recognise. language: the interface language code, a hint for the recogniser ("" — detect)."""
    if _rec.get("status") != "recording":
        raise ValueError("запись не идёт")
    _rec["stop"].set()
    _rec["thread"].join(timeout=5)
    path = Path(_rec["path"])
    _rec["status"] = "recognising"
    try:
        if _rec["errors"]:
            raise ValueError("микрофон недоступен: " + _rec["errors"][0])
        from . import tuning

        model = scribe._whisper(scribe.model_name(vault), tuning.get(vault)["threads"])
        if not path.exists() or path.stat().st_size < 8000:
            return {"text": "", "seconds": 0}
        segments, info = model.transcribe(
            str(path), language=language or None, vad_filter=True, vad_parameters={"min_silence_duration_ms": 500}
        )
        parts = [s.text.strip() for s in segments if s.text.strip() and getattr(s, "no_speech_prob", 0) <= 0.6]
        text = " ".join(parts).strip()
        if text:
            from . import achievements

            achievements.event(vault, "voice")
        return {"text": text, "seconds": round(info.duration or 0, 1)}
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(scribe.human_error(e)) from None
    finally:
        path.unlink(missing_ok=True)
        _rec.clear()
