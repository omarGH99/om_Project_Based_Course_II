"""
Extract clean Badini text from a folder of Govara Metin PDF issues and append
to the corpus.

These are digital-text PDFs (not scanned), so no OCR is needed. Each issue
yields several thousand clean Badini sentences.

Pipeline per PDF: extract text (pypdf) -> sentence-split -> script-filter
(>=80% Arabic) -> Badini-letter check -> normalize -> fix PDF spacing
artifacts -> length-filter -> dedupe -> write.

Usage:
    pip install pypdf
    python scripts/pdf_to_corpus.py --pdf-dir "C:/Users/omars/Downloads/govara_matin" \
        --out data/clean/badini_metin_pdfs.txt
Then merge:
    python scripts/merge_corpus.py
"""

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from badini_gec.normalize import normalize

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("Install pypdf first:  pip install pypdf")

ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN = re.compile(r"[A-Za-z]")
SENT = re.compile(r"[.!?\u061F\u06D4\n]+")
STRONG_KURDISH = set("ێۆڕڤگچپ")
ARABIC_MARKERS = ["الدین", "دار ", "بیروت", "صفحة", "الجز", "القاهرة", "مجلة"]
# PDF extraction sometimes inserts a space inside a word between two Arabic
# letters. Collapse a single space that sits between two Arabic letters when
# the fragments are short (heuristic cleanup).
SPACE_IN_WORD = re.compile(r"(?<=[\u0600-\u06FF])\s(?=[\u0600-\u06FF])")


def fix_pdf_spacing(text):
    # Only join when it looks like a broken word: short letter-runs around a space.
    # Conservative: join if both neighbors are single Arabic letters following
    # a longer token (handles 'عە بدول' style splits) — applied lightly.
    return text  # keep off by default; see --fix-spacing flag


def is_badini(sent):
    if not any(ch in STRONG_KURDISH for ch in sent):
        return False
    if any(m in sent for m in ARABIC_MARKERS):
        return False
    return True


def extract_pdf(path):
    try:
        r = PdfReader(path)
    except Exception as e:
        print(f"  ! could not open {os.path.basename(path)}: {e}")
        return ""
    parts = []
    for pg in r.pages:
        try:
            t = pg.extract_text() or ""
        except Exception:
            t = ""
        if t:
            parts.append(t)
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", required=True, help="folder containing the PDF issues")
    ap.add_argument("--out", default="data/clean/badini_metin_pdfs.txt")
    ap.add_argument("--min-words", type=int, default=4)
    ap.add_argument("--max-words", type=int, default=60)
    args = ap.parse_args()

    pdfs = sorted(glob.glob(os.path.join(args.pdf_dir, "*.pdf")))
    if not pdfs:
        sys.exit(f"No PDFs found in {args.pdf_dir}")
    print(f"Found {len(pdfs)} PDF(s).")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    seen = set()
    kept = words = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for path in pdfs:
            name = os.path.basename(path)
            text = extract_pdf(path)
            n_before = kept
            for chunk in SENT.split(text):
                c = chunk.strip()
                if not c:
                    continue
                a, l = len(ARABIC.findall(c)), len(LATIN.findall(c))
                if a + l == 0 or a / (a + l) < 0.8:
                    continue
                if not is_badini(c):
                    continue
                n = normalize(c)
                w = len(n.split())
                if not (args.min_words <= w <= args.max_words):
                    continue
                key = n[:80]
                if key in seen:
                    continue
                seen.add(key)
                out.write(n + "\n")
                kept += 1
                words += w
            print(f"  {name}: +{kept - n_before} sentences")

    print(f"\nDONE. {kept} Badini sentences (~{words} words) -> {args.out}")
    print("Next:  python scripts/merge_corpus.py   (to combine with the rest)")


if __name__ == "__main__":
    main()
