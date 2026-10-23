"""Documents on the computer, for any model: scans and pictures recognised, PDF merged / cut / turned / split, Word and
Excel changed in place — every write in the journal and undoable."""

import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema import docs, ocr  # noqa: E402
from mnema.agent import profile as P  # noqa: E402
from mnema.chat import attach, tools as TL  # noqa: E402
from mnema.journal import events, undo  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402

LINES = ["Счёт № 1427 от 3 ноября 2026 года", "Итого к оплате: 48 300,00 руб.", "Invoice total: $1,250.00"]


def _font(size=30):
    from PIL import ImageFont

    for f in (
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return None


def _scan_image(lines=LINES):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1240, 120 + 110 * len(lines)), "white")
    d = ImageDraw.Draw(img)
    for i, t in enumerate(lines):
        d.text((60, 60 + i * 110), t, fill="black", font=_font())
    return img


def _pdf(path: Path, pages: int) -> Path:
    """A real PDF with text pages «Страница N»."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    w = PdfWriter()
    for n in range(1, pages + 1):
        pg = w.add_blank_page(300, 200)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        pg[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): w._add_object(font)})}
        )
        s = DecodedStreamObject()
        s.set_data(f"BT /F1 18 Tf 40 100 Td (Page {n}) Tj ET".encode())
        pg[NameObject("/Contents")] = w._add_object(s)
    with open(path, "wb") as f:
        w.write(f)
    return path


def _pages(path: Path) -> list[str]:
    from pypdf import PdfReader

    return [(p.extract_text() or "").strip() for p in PdfReader(str(path)).pages]


def _docx(path: Path) -> Path:
    """A Word file where «48 300» is split over runs, one of them bold."""
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"><w:body>'
        "<w:p><w:r><w:t>Итого к оплате: </w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>48 3</w:t></w:r>"
        '<w:r><w:rPr><w:b/></w:rPr><w:t>00 руб.</w:t></w:r></w:p>'
        "<w:p><w:r><w:t>Подпись: директор</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        z.writestr("word/document.xml", doc)
        z.writestr("word/styles.xml", "<styles/>")
    return path


RU = ocr.ready() and ocr._rec_path("cyrillic") is not None and _font() is not None


class Documents(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        self.work = Path(tempfile.mkdtemp())
        P.save(self.v, {"tool_folders": [str(self.work)]})

    def act(self, **call):
        call.setdefault("body", "")
        return TL.run(self.v, call)

    # ---- PDF

    def test_page_list(self):
        self.assertEqual(TL.page_list("1-3, 7", 9), [0, 1, 2, 6])
        self.assertEqual(TL.page_list("", 3), [0, 1, 2])
        self.assertEqual(TL.page_list("3-1", 3), [2, 1, 0])
        self.assertEqual(TL.page_list("8-", 9), [7, 8])
        with self.assertRaises(TL.Refused):
            TL.page_list("12", 9)

    def test_merge_pages_rotate_split(self):
        a, b = _pdf(self.work / "a.pdf", 3), _pdf(self.work / "b.pdf", 2)
        out = self.work / "вместе.pdf"
        self.act(tool="edit_pdf", do="merge", files=f"{a}; {b}", path=str(out))
        self.assertEqual(_pages(out), ["Page 1", "Page 2", "Page 3", "Page 1", "Page 2"])

        cut = self.work / "кусок.pdf"
        self.act(tool="edit_pdf", do="pages", path=str(cut), pages="3, 1", **{"from": str(a)})
        self.assertEqual(_pages(cut), ["Page 3", "Page 1"])

        turned = self.work / "повёрнут.pdf"
        self.act(tool="edit_pdf", do="rotate", path=str(turned), pages="2", angle="90", **{"from": str(a)})
        from pypdf import PdfReader

        self.assertEqual([p.rotation for p in PdfReader(str(turned)).pages], [0, 90, 0])

        res, line, _ = self.act(
            tool="edit_pdf", do="split", path=str(self.work / "части"), pages="1-2; 3", **{"from": str(a)}
        )
        parts = sorted((self.work / "части").glob("*.pdf"))
        self.assertEqual([p.name for p in parts], ["a — стр. 1-2.pdf", "a — стр. 3.pdf"])
        self.assertIn("2 PDF", line)
        self.assertEqual(_pages(a), ["Page 1", "Page 2", "Page 3"], "the source stays as it was")

    def test_pdf_never_overwrites_and_is_undoable(self):
        a = _pdf(self.work / "a.pdf", 2)
        self.act(tool="edit_pdf", do="pages", path=str(a), pages="2", **{"from": str(a)})
        self.assertTrue((self.work / "a (2).pdf").exists())
        self.assertEqual(_pages(a), ["Page 1", "Page 2"])
        ev = [e for e in events(self.v) if "a (2).pdf" in str(e.get("paths"))][-1]
        undo(self.v, ev["id"])
        self.assertFalse((self.work / "a (2).pdf").exists())

    def test_pdf_outside_open_folders_refused(self):
        a = _pdf(self.work / "a.pdf", 1)
        other = Path(tempfile.mkdtemp()) / "x.pdf"
        with self.assertRaises(TL.Refused):
            self.act(tool="edit_pdf", do="pages", path=str(other), pages="1", **{"from": str(a)})

    # ---- Word

    def test_docx_replace_keeps_format_across_runs(self):
        f = _docx(self.work / "счёт.docx")
        res, line, _ = self.act(
            tool="edit_file",
            path=str(f),
            body="<<<\n48 300 руб.\n===\n51 000 руб.\n>>>\n<<<\nдиректор\n===\nгенеральный директор\n>>>",
        )
        self.assertIn("замен: 2", res)
        xml = zipfile.ZipFile(f).read("word/document.xml").decode()
        self.assertIn("<w:b/></w:rPr><w:t xml:space=\"preserve\">51 000 руб.</w:t>", xml)
        self.assertIn('mc:Ignorable="w14"', xml)
        self.assertIn('xmlns:w14=', xml, "unused namespaces stay, or Word calls the file broken")
        self.assertIn("генеральный директор", docs.extract(f)[0])
        self.assertEqual(zipfile.ZipFile(f).read("word/styles.xml"), b"<styles/>")

    def test_docx_missing_text_refused(self):
        f = _docx(self.work / "счёт.docx")
        with self.assertRaises(TL.Refused):
            self.act(tool="edit_file", path=str(f), body="<<<\nнет такого\n===\nx\n>>>")

    # ---- Excel

    def test_xlsx_cells_and_text(self):
        from openpyxl import Workbook, load_workbook

        f = self.work / "бюджет.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Итог"
        ws["A1"], ws["B1"], ws["B2"], ws["B3"] = "Статья", 100, 200, "=SUM(B1:B2)"
        wb.create_sheet("Мой лист")["A1"] = "черновик"
        wb.save(f)
        res, _, _ = self.act(
            tool="edit_file",
            path=str(f),
            body="B2 = 250\n'Мой лист'!A2 = 3,5\nИтог!C1 = =B3*2\n<<<\nчерновик\n===\nчистовик\n>>>",
        )
        self.assertIn("изменено ячеек: 4", res)
        wb = load_workbook(f)
        self.assertEqual(wb["Итог"]["B2"].value, 250)
        self.assertEqual(wb["Итог"]["B3"].value, "=SUM(B1:B2)")
        self.assertEqual(wb["Итог"]["C1"].value, "=B3*2")
        self.assertEqual(wb["Мой лист"]["A2"].value, 3.5)
        self.assertEqual(wb["Мой лист"]["A1"].value, "чистовик")

    def test_xlsx_with_chart_refused(self):
        from openpyxl import Workbook
        from openpyxl.chart import BarChart, Reference

        f = self.work / "график.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.append([1])
        ws.append([2])
        ch = BarChart()
        ch.add_data(Reference(ws, min_col=1, min_row=1, max_row=2))
        ws.add_chart(ch, "C1")
        wb.save(f)
        before = f.read_bytes()
        with self.assertRaises(TL.Refused):
            self.act(tool="edit_file", path=str(f), body="A1 = 5")
        self.assertEqual(f.read_bytes(), before)

    # ---- recognition

    @unittest.skipUnless(
        RU, "OCR libraries, the Cyrillic recogniser (tools/fetch_vendor.py --ocr) or a font are not here"
    )
    def test_scanned_pdf_read_on_the_computer(self):
        f = self.work / "скан.pdf"
        _scan_image().save(f, resolution=150)
        text, info = docs.extract(f, "ru")
        self.assertEqual(info.get("ocr"), 1)
        self.assertIn("[стр. 1]", text)
        self.assertIn("48 300,00", text)
        self.assertIn("Итого к оплате", text)
        # attached: any model gets it as text, not as a file only some can open
        buf = io.BytesIO()
        _scan_image().save(buf, format="PDF", resolution=150)
        import base64

        item = attach.save(self.v, "c1", [{"name": "скан.pdf", "data": base64.b64encode(buf.getvalue()).decode()}])[0]
        self.assertEqual(item["kind"], "text")
        self.assertIn("Итого", attach.inline_text("что тут?", [item]))

    @unittest.skipUnless(
        RU, "OCR libraries, the Cyrillic recogniser (tools/fetch_vendor.py --ocr) or a font are not here"
    )
    def test_picture_text_for_every_model(self):
        import base64

        buf = io.BytesIO()
        _scan_image().save(buf, format="PNG")
        item = attach.save(self.v, "c2", [{"name": "фото.png", "data": base64.b64encode(buf.getvalue()).decode()}])[0]
        self.assertEqual(item["kind"], "image")
        self.assertIn("Счёт № 1427", attach.inline_text("что тут?", [item]))
        p = self.work / "фото.png"
        p.write_bytes(buf.getvalue())
        res, _, _ = self.act(tool="read_file", path=str(p))
        self.assertIn("Invoice total", res)

    @unittest.skipUnless(ocr.ready(), "OCR libraries are not here")
    def test_selftest_of_the_built_program(self):
        self.assertIn("1427", ocr.selftest())

    def test_without_ocr_a_scan_still_goes_as_a_file(self):
        from unittest import mock

        f = self.work / "пусто.pdf"
        from PIL import Image

        Image.new("RGB", (400, 300), "white").save(f)
        with mock.patch.object(ocr, "ready", lambda: False):
            text, info = docs.extract(f, "ru")
        self.assertNotIn("ocr", info)
        self.assertTrue(docs.scanned(text, info["pages"]))


if __name__ == "__main__":
    unittest.main()
