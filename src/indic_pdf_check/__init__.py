"""indic-pdf-check: can a screen reader, search engine or AI read the text of this PDF?

Many PDFs in Indian and other South/Southeast Asian scripts look correct on screen but carry a broken text layer (for
example Microsoft Word's "Save as PDF"), or carry no text at all (scans). This tool reads the PDF's own text layer - the
text that copy-paste, search, screen readers and AI pipelines get - and reports one verdict per PDF:

  NO_TEXT  fewer than 200 letters in a supported script: a scan/image, or text without real Unicode (needs OCR)
  BROKEN   more than 5% of words are impossible spellings (e.g. a vowel sign or virama with no consonant before it)
  OK       the text layer looks readable

Supported scripts: Devanagari, Bengali/Assamese, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Sinhala,
Thai, Lao, Khmer, Myanmar, Thaana. It cannot prove text is *correct* (a garbled text can still be spelled legally); it
catches the impossible spellings that broken PDF text layers produce. Nothing is uploaded; files are only read.
"""
from pathlib import Path
import unicodedata

from .rules import BASE, OTHER, scan_text

__version__ = "0.1.0"
SCRIPTS = list(BASE) + list(OTHER)
NAMES = {"Deva": "Devanagari", "Beng": "Bengali", "Guru": "Gurmukhi", "Gujr": "Gujarati", "Orya": "Odia", "Taml": "Tamil",
         "Telu": "Telugu", "Knda": "Kannada", "Mlym": "Malayalam", "Sinh": "Sinhala", "Thai": "Thai", "Laoo": "Lao",
         "Khmr": "Khmer", "Mymr": "Myanmar", "Thaa": "Thaana"}


def _block(script):
    if script in BASE:
        return BASE[script], BASE[script] + 0x7F
    return OTHER[script][0]


def check_text(text):
    """Verdict for a text string (the text layer of a PDF)."""
    best = None
    for s in SCRIPTS:
        lo, hi = _block(s)
        letters = sum(1 for c in text if lo <= ord(c) <= hi and unicodedata.category(c)[0] in "LM")
        if best is None or letters > best[1]:
            best = (s, letters)
    script, letters = best
    words, bad = scan_text(text, script) if letters else (0, 0)
    share = bad / words if words else 0.0
    verdict = "NO_TEXT" if letters < 200 else ("BROKEN" if share > 0.05 else "OK")
    return {"verdict": verdict, "script": NAMES[script] if letters else None, "letters": letters, "words": words,
            "broken_share": round(share, 4)}


def check(path):
    """Verdict for a PDF file: dict with verdict, script, letters, words, broken_share, pages, tagged, producer, creator."""
    import pymupdf
    pymupdf.TOOLS.mupdf_display_errors(False)
    doc = pymupdf.open(path)
    r = check_text("".join(page.get_text() for page in doc))
    md = doc.metadata or {}
    cat = doc.pdf_catalog()
    r.update({"file": Path(path).name, "pages": len(doc), "tagged": bool(cat and "StructTreeRoot" in doc.xref_object(cat)),
              "producer": md.get("producer", ""), "creator": md.get("creator", "")})
    return r
