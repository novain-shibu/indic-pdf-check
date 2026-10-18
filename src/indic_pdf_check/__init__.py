"""indic-pdf-check: can a screen reader, search engine or AI read the text of this PDF?

Many PDFs in Indian and other South/Southeast Asian scripts look correct on screen but carry a broken text layer (for
example Microsoft Word's "Save as PDF"), or carry no text at all (scans). This tool reads the PDF's own text layer - the
text that copy-paste, search, screen readers and AI pipelines get - and reports one verdict per PDF:

  NO_TEXT             almost no text at all: usually a scan/image (needs OCR)
  INSUFFICIENT_TEXT   some text in a supported script, but too little to judge (under 200 letters)
  UNSUPPORTED_SCRIPT  plenty of text, but none in a supported script, so this tool cannot judge it
  BROKEN              the main script, or any other supported script with 200+ letters, has more than 5% impossible
                      spellings (e.g. a vowel sign or virama with no consonant before it)
  OK                  no problem detected by these checks (this does not mean "accessible": reading order, headings,
                      tables and alternative text are not checked)
Pages whose own text has a high share of impossible spellings are listed as "suspicious_pages" (for information).

Supported scripts: Devanagari, Bengali/Assamese, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Sinhala,
Thai, Lao, Khmer, Myanmar, Thaana. It cannot prove text is *correct* (a garbled text can still be spelled legally); it
catches the impossible spellings that broken PDF text layers produce. Nothing is uploaded; files are only read.
"""
from pathlib import Path
import unicodedata

from .rules import BASE, OTHER, scan_text

__version__ = "0.2.0"
SCRIPTS = list(BASE) + list(OTHER)
NAMES = {"Deva": "Devanagari", "Beng": "Bengali", "Guru": "Gurmukhi", "Gujr": "Gujarati", "Orya": "Odia", "Taml": "Tamil",
         "Telu": "Telugu", "Knda": "Kannada", "Mlym": "Malayalam", "Sinh": "Sinhala", "Thai": "Thai", "Laoo": "Lao",
         "Khmr": "Khmer", "Mymr": "Myanmar", "Thaa": "Thaana"}


def _block(script):
    if script in BASE:
        return BASE[script], BASE[script] + 0x7F
    return OTHER[script][0]


MIN_LETTERS = 200   # below this the text is too short to judge
NO_TEXT_CHARS = 20  # fewer non-space characters than this in total: treat as no text layer
PAGE_WORDS = 30     # pages need at least this many words in a script to be listed as suspicious


def _letters(text, script):
    lo, hi = _block(script)
    return sum(1 for c in text if lo <= ord(c) <= hi and unicodedata.category(c)[0] in "LM")


def _script_stats(text):
    """[(script, letters, words, bad)] for every supported script present, most letters first."""
    out = []
    for s in SCRIPTS:
        n = _letters(text, s)
        if n:
            w, b = scan_text(text, s)
            out.append((s, n, w, b))
    return sorted(out, key=lambda t: -t[1])


def check_text(text):
    """Verdict for a text string (the text layer of a PDF)."""
    stats = _script_stats(text)
    script, letters, words, bad = stats[0] if stats else (None, 0, 0, 0)
    share = bad / words if words else 0.0
    others = [(s, b / w) for s, n, w, b in stats[1:] if n >= MIN_LETTERS and w and b / w > 0.05]
    if letters >= MIN_LETTERS:
        verdict = "BROKEN" if share > 0.05 or others else "OK"
    elif letters > 0:
        verdict = "INSUFFICIENT_TEXT"
    elif sum(1 for c in text if not c.isspace()) < NO_TEXT_CHARS:
        verdict = "NO_TEXT"
    else:
        verdict = "UNSUPPORTED_SCRIPT"
    return {"verdict": verdict, "script": NAMES[script] if script else None, "letters": letters, "words": words,
            "broken_share": round(share, 4),
            "other_broken_scripts": [{"script": NAMES[s], "broken_share": round(x, 4)} for s, x in others]}


def check(path):
    """Verdict for a PDF file: dict with verdict, script, letters, words, broken_share, pages, tagged, producer, creator."""
    import pymupdf
    pymupdf.TOOLS.mupdf_display_errors(False)
    doc = pymupdf.open(path)
    pages = [page.get_text() for page in doc]
    r = check_text("".join(pages))
    sus = []
    for i, t in enumerate(pages, 1):
        for s, n, w, b in _script_stats(t):
            if w >= PAGE_WORDS and b / w > 0.05:
                sus.append({"page": i, "script": NAMES[s], "broken_share": round(b / w, 4)})
    r["suspicious_pages"] = sus
    md = doc.metadata or {}
    cat = doc.pdf_catalog()
    r.update({"file": Path(path).name, "pages": len(doc), "tagged": bool(cat and "StructTreeRoot" in doc.xref_object(cat)),
              "producer": md.get("producer", ""), "creator": md.get("creator", "")})
    return r
