from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def extract_pdf(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception as e:
        raise RuntimeError(f"cannot open pdf: {e}") from e
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    return "\n\n".join(parts)


def write_pdf(text: str, output_path: Path) -> Path:
    """
    Write a simple multi-page PDF with the translated text.
    Uses built-in CID fonts so CJK / common scripts render.
    Original layout is not preserved (extraction already lost it).
    """
    # Prefer CID fonts that cover CJK + Latin
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))  # CJK-friendly
        font_name = "STSong-Light"
    except Exception:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
            font_name = "HeiseiMin-W3"
        except Exception:
            font_name = "Helvetica"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "BodyTranslated",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=16,
        wordWrap="CJK",
    )
    story = []
    # Escape for reportlab Paragraph (minimal)
    def _esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    for para in text.split("\n"):
        if not para.strip():
            story.append(Spacer(1, 6))
            continue
        story.append(Paragraph(_esc(para), body))
        story.append(Spacer(1, 4))

    if not story:
        story.append(Paragraph("(empty)", body))

    doc.build(story)
    return output_path
