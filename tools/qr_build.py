"""The QR code to the repository for the README (shown on a screen at a conference): rounded dots, the three corner
squares in the brand violet (square: rounded ones are missed by some readers), the Mnemai mark in the middle
(error correction H keeps it readable).

    python tools/qr_build.py   →  docs/img/brand/qr.svg   (needs segno: pip install segno)
"""

from __future__ import annotations

import sys
from pathlib import Path

import segno

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/Pumpetee/Mnemai"
OUT = ROOT / "docs" / "img" / "brand" / "qr.svg"


def build(
    url: str = URL, gap: int = 1, rounded: int = 3, hole_part: float = 0.22, ink: str = "url(#g)", eye_round: int = 0
) -> str:
    qr = segno.make(url, error="h", micro=False)
    m = [list(row) for row in qr.matrix]
    n = len(m)
    q = 4  # quiet zone, in modules (the standard four: some readers miss the code with less)
    s = 10  # one module, in px
    size = (n + 2 * q) * s

    def finder(r: int, c: int) -> bool:
        return (r < 7 and c < 7) or (r < 7 and c >= n - 7) or (r >= n - 7 and c < 7)

    # the middle keeps a clear square for the mark: about 16% of the side, well inside what level H restores
    hole = int(n * hole_part) | 1 if hole_part else 0
    h0 = (n - hole) // 2
    dots = []
    for r in range(n):
        for c in range(n):
            if not m[r][c] or finder(r, c):
                continue
            if h0 <= r < h0 + hole and h0 <= c < h0 + hole:
                continue
            x, y = (c + q) * s, (r + q) * s
            dots.append(
                f'<rect x="{x + gap}" y="{y + gap}" width="{s - 2 * gap}" height="{s - 2 * gap}" rx="{rounded}"/>'
            )

    def eye(r: int, c: int) -> str:
        x, y = (c + q) * s, (r + q) * s
        return (
            f'<rect x="{x + 5}" y="{y + 5}" width="{6 * s}" height="{6 * s}" rx="{eye_round}" fill="none" stroke="{ink}" stroke-width="{s}"/>'
            f'<rect x="{x + 2 * s}" y="{y + 2 * s}" width="{3 * s}" height="{3 * s}" rx="{eye_round // 2}" fill="{ink}"/>'
        )

    eyes = eye(0, 0) + eye(0, n - 7) + eye(n - 7, 0)
    mid = size / 2
    logo = max(hole * s - 2 * s, 0)
    lx = mid - logo / 2
    k = logo / 24  # the mark is drawn in a 24-unit box, as in the app
    mark = (
        f'<rect x="{lx}" y="{lx}" width="{logo}" height="{logo}" rx="{logo * 0.28}" fill="url(#g)"/>'
        f'<g transform="translate({lx + logo * 0.19} {lx + logo * 0.19}) scale({k * 0.62})">'
        '<path d="M5 19.5V9.6M5.6 6.8L12 14.2l6.4-7.4M19 9.6v9.9" fill="none" stroke="#fff" stroke-width="2.7" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="5" cy="6.6" r="2.5" fill="#fff"/><circle cx="19" cy="6.6" r="2.5" fill="#fff"/></g>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#a855f7"/></linearGradient></defs>'
        f'<rect width="{size}" height="{size}" rx="28" fill="#ffffff"/>'
        f'<g fill="#1e1b4b">{"".join(dots)}</g>{eyes}{mark}</svg>\n'
    )


if __name__ == "__main__":
    OUT.write_text(build(sys.argv[1] if len(sys.argv) > 1 else URL), encoding="utf-8")
    print(OUT)
