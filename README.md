# indic-pdf-check

**Can a screen reader, a search engine or an AI read the text of this PDF?**

Many PDFs in Indian and other South/Southeast Asian scripts look perfect on screen but carry a broken text layer: copy-paste,
search, screen readers and AI pipelines get garbled words. Microsoft Word's "Save as PDF" is a common cause (see the
[research report](https://github.com/novain-shibu/finepdfs-audit)). Others are scans with no text at all. This tool reads a
PDF's own text layer and tells you which case you have, in a second, on your own computer.

```bash
pip install git+https://github.com/novain-shibu/indic-pdf-check
indic-pdf-check circular.pdf notice.pdf
```

```
circular.pdf: BROKEN             script=Malayalam letters=1994 broken=29.4% tagged=True creator='Microsoft® Word for Microsoft '
notice.pdf:   NO_TEXT            script=None letters=0 broken=0.0% tagged=False creator='Canon '
-- 2 PDFs: BROKEN 1, NO_TEXT 1
```

| verdict | meaning | what to do |
|---|---|---|
| `NO_TEXT` | almost no text at all: usually a scan or an image | run OCR (e.g. OCRmyPDF with Tesseract language packs) before publishing |
| `INSUFFICIENT_TEXT` | some text in a supported script, but under 200 letters: too little to judge | check by hand (e.g. a short notice) |
| `UNSUPPORTED_SCRIPT` | plenty of text, but none in a supported script (e.g. English only) | this tool cannot judge it |
| `BROKEN` | the main script, or any other supported script with 200+ letters, has more than 5% impossible spellings (e.g. a vowel sign or virama with no consonant before it) | re-export with another tool and check again; or recover the text with [Unshape](https://github.com/novain-shibu/unshape) (needs the document's original font) |
| `OK` | no problem detected by these checks | - (this is not a full accessibility check: reading order, headings, tables and alternative text are not checked) |

Pages whose own text has a high share of impossible spellings are listed as `suspicious_pages` (with `--json`), so damage
confined to some pages or to a second script is visible.

Also reported: the script, the share of broken words, whether the PDF is tagged for accessibility, and the program that
made it. `--json` gives machine-readable output; the exit code is 1 if any file is `NO_TEXT` or `BROKEN` (useful in CI).

**Scripts:** Devanagari (Hindi, Marathi, Nepali...), Bengali/Assamese, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada,
Malayalam, Sinhala, Thai, Lao, Khmer, Myanmar, Thaana (Divehi).

**Python:**
```python
from indic_pdf_check import check, check_text
check("notice.pdf")["verdict"]          # 'BROKEN' | 'OK' | 'NO_TEXT' | 'INSUFFICIENT_TEXT' | 'UNSUPPORTED_SCRIPT'
```

## How well it works (tested before release)
- Word for Microsoft 365 PDFs with known-broken text in 14 scripts: 12 flagged `BROKEN`; Kannada was passed as `OK`
  (only 4% impossible spellings although many words are wrong - see limits).
- Clean source text in the same 14 scripts: 0 false alarms.
- Microsoft Edge PDFs of the same text are flagged in 3 of 4 scripts: they really do contain doubled vowel signs, which a
  screen reader also reads.

## Limits
- It finds *impossible* spellings. Garbled text can still be spelled legally (e.g. a wrong consonant), so `OK` means "no
  sign of breakage", not "verified correct".
- Scripts not listed (Arabic, Hebrew, Latin, Chinese...) come out as `UNSUPPORTED_SCRIPT` (version 0.1.0 said `NO_TEXT`).
- Version 0.2.0 kept every verdict of the release tests above unchanged; it only splits the old `NO_TEXT` into three
  clearer cases and adds per-script and per-page checks.
- It reads only the text layer; it does not look at how the page renders.

Apache-2.0 · Novain Shibu · [github.com/novain-shibu](https://github.com/novain-shibu)
