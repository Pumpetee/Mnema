"""Text from scans and pictures, recognised on this computer, free, for any model.

RapidOCR (PaddleOCR's models on onnxruntime, Apache-2.0): a detector finds the lines, a recogniser reads them. The
recogniser follows the interface language: Cyrillic (Russian, Ukrainian, Belarusian, Bulgarian, Serbian — and
English) for ru, Latin with accents for the European languages, the default Chinese-English one for zh and ja.
PDF pages are drawn by PDFium (pypdfium2) and read the same way.

Nothing leaves the computer. Without the libraries (the console helper, an old system) every function returns ""
and callers fall back to what they did before.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

MAX_PAGES = 40  # a longer scan: the first 40 pages, and the text says so
SCALE = 2.5  # PDF points → pixels: about 180 dpi, enough for print, fast on a laptop
REC = {"cyrillic": "cyrillic_PP-OCRv5_rec_mobile.onnx", "latin": "latin_PP-OCRv5_rec_mobile.onnx"}
LATIN_LANGS = {"de", "fr", "es", "pt", "it", "nl", "pl", "cs", "tr"}

_lock = threading.Lock()
_engines: dict[str, object] = {}


def models_dir() -> Path:
    """Where the recognisers are: next to the program when installed, vendor/ocr in the source tree."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "ocr"
    return Path(__file__).resolve().parents[1] / "vendor" / "ocr"


def _rec_path(script: str) -> Path | None:
    name = REC.get(script)
    if not name:
        return None
    for d in (models_dir(),):
        if (d / name).exists():
            return d / name
    try:  # a development copy: RapidOCR keeps what it downloaded in its own folder
        import rapidocr

        p = Path(rapidocr.__file__).parent / "models" / name
        return p if p.exists() else None
    except Exception:
        return None


def script_for(lang: str) -> str:
    lang = (lang or "ru").lower()[:2]
    if lang in ("zh", "ja"):
        return "default"
    if lang in LATIN_LANGS:
        return "latin"
    return "cyrillic"  # ru and the rest; it reads English too


def ready() -> bool:
    try:
        import onnxruntime  # noqa: F401
        import rapidocr  # noqa: F401

        return True
    except Exception:
        return False


def _engine(script: str):
    with _lock:
        if script in _engines:
            return _engines[script]
        from rapidocr import RapidOCR

        params = {"Global.log_level": "error"}
        rec = _rec_path(script)
        if rec is not None:
            params["Rec.model_path"] = str(rec)
        elif script != "default":
            return _engine_default_locked()
        eng = RapidOCR(params=params)
        _engines[script] = eng
        return eng


def _engine_default_locked():
    from rapidocr import RapidOCR

    if "default" not in _engines:
        _engines["default"] = RapidOCR(params={"Global.log_level": "error"})
    return _engines["default"]


def _lines(result) -> str:
    """Boxes → lines in reading order: boxes whose middles are at one height make one line."""
    boxes, txts = getattr(result, "boxes", None), getattr(result, "txts", None)
    if boxes is None or not txts:
        return ""
    items = []
    for b, t in zip(boxes, txts):
        ys = [float(p[1]) for p in b]
        xs = [float(p[0]) for p in b]
        items.append(((min(ys) + max(ys)) / 2, max(ys) - min(ys), min(xs), str(t)))
    items.sort(key=lambda x: (x[0], x[2]))
    lines: list[list[tuple]] = []
    for it in items:
        if lines and abs(it[0] - lines[-1][0][0]) < max(6.0, 0.5 * min(it[1], lines[-1][0][1])):
            lines[-1].append(it)
        else:
            lines.append([it])
    return "\n".join(" ".join(t for *_, t in sorted(ln, key=lambda x: x[2])) for ln in lines).strip()


def image_text(img, lang: str = "ru") -> str:
    """Text on a picture (a path, bytes or a PIL image). "" if nothing is readable or OCR is not available."""
    if not ready():
        return ""
    try:
        import numpy as np
        from PIL import Image

        if isinstance(img, (str, Path)):
            img = Image.open(img)
        elif isinstance(img, (bytes, bytearray)):
            import io

            img = Image.open(io.BytesIO(img))
        img = img.convert("RGB")
        arr = np.array(img)[:, :, ::-1]  # RGB → BGR, as OpenCV expects
        return _lines(_engine(script_for(lang))(arr))
    except Exception:
        return ""


def pdf_text(path: Path, lang: str = "ru", max_pages: int = MAX_PAGES) -> tuple[str, int]:
    """(text with [стр. N] marks, pages read). Each page is drawn and read; empty pages are skipped."""
    if not ready():
        return "", 0
    try:
        import pypdfium2 as pdfium
    except Exception:
        return "", 0
    out, n = [], 0
    try:
        doc = pdfium.PdfDocument(str(path))
    except Exception:
        return "", 0
    try:
        total = len(doc)
        for i in range(min(total, max_pages)):
            page = doc[i]
            try:
                pil = page.render(scale=SCALE).to_pil()
            finally:
                page.close()
            t = image_text(pil, lang)
            n += 1
            if t:
                out.append(f"[стр. {i + 1}]\n{t}")
        if total > max_pages:
            out.append(f"[дальше {total - max_pages} стр. не распознаны: длинный скан, прочитаны первые {max_pages}]")
    finally:
        doc.close()
    return "\n\n".join(out), n


def selftest() -> str:
    """What recognition reads from a picture it draws itself — the built program's check that OCR is packed whole."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 200), "white")
    try:
        font = ImageFont.load_default(size=56)
    except TypeError:
        font = ImageFont.load_default()
    ImageDraw.Draw(img).text((40, 60), "Invoice 1427 paid", fill="black", font=font)
    return image_text(img, "en")
