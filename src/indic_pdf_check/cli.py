"""Command line: indic-pdf-check file1.pdf [file2.pdf ...] [--json]"""
import collections, json, sys
from . import __version__, check


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__ + "\nVerdicts: NO_TEXT (no text layer, usually a scan), INSUFFICIENT_TEXT (too little text to judge), UNSUPPORTED_SCRIPT, BROKEN (garbled text layer), OK (no problem detected; not a full accessibility check)."); return 0
    if argv[0] == "--version":
        print(__version__); return 0
    as_json = "--json" in argv
    rows = []
    for f in (a for a in argv if a != "--json"):
        try:
            rows.append(check(f))
        except Exception as e:
            rows.append({"file": f, "verdict": "ERROR", "error": repr(e)[:120]})
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            if r["verdict"] == "ERROR":
                print(f"{r['file']}: ERROR {r['error']}"); continue
            print(f"{r['file']}: {r['verdict']:18s} script={r['script']} letters={r['letters']} broken={r['broken_share']:.1%} "
                  f"tagged={r['tagged']} creator={r['creator'][:30]!r}"
                  + (f" suspicious_pages={len(r['suspicious_pages'])}" if r.get("suspicious_pages") else ""))
        c = collections.Counter(r["verdict"] for r in rows)
        print(f"-- {len(rows)} PDFs: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    return 1 if any(r["verdict"] in ("BROKEN", "NO_TEXT") for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
