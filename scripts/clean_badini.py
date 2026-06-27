"""
Clean the Kurmanji/Badini corpus by removing two kinds of contamination
confirmed by a native speaker:

  1. Arabic-LANGUAGE lines (book citations, quotes) that are in the Arabic
     script but are not Kurdish. Detected by absence of Kurdish-specific
     letters and/or high density of Arabic-only function words.

  2. Sorani (Central Kurdish) lines mixed into the Kurmanji corpus. Detected
     by Sorani-marker tokens/morphology that Badini does not use.

This is deliberately conservative on Badini: when unsure, we KEEP the line,
because the bigger risk is throwing away good Badini. Tune the thresholds
after eyeballing the rejects file.

Usage:
    python scripts/clean_badini.py \
        --in data/clean/badini_kmr.txt \
        --out data/clean/badini_clean.txt \
        --rejects data/clean/badini_rejects.txt
"""

import argparse
import re

# Letters that exist in Kurdish Arabic-script orthography but NOT in standard
# Arabic. A real Kurdish sentence almost always contains some of these.
KURDISH_LETTERS = set("ێۆڕڤژگچپڵڤەهـ")  # ێ ۆ ڕ ڤ ژ گ چ پ ڵ ە
# (note ه/ە handled loosely; ە is the strong Kurdish signal)
STRONG_KURDISH = set("ێۆڕڤگچپ")  # these are essentially never in Arabic text

# Arabic-language giveaway tokens common in citations/quotes (not Kurdish).
ARABIC_MARKERS = [
    "الدین", "دار ", "بیروت", "الجز", "صفحە", "مکتبە", "التاریخ",
    "المرکز", "العربی", "ص1", "ص2", "ص3", "ج1", "ج2", "ج3",
    "الله", "بتاریخ", "انباو", "المقدسی", "الدمشقی",
]

# Sorani-marker tokens / morphemes that Badini does NOT use the same way.
# Badini uses دێ/ دە- differently, ێت endings, ب-/ ژ-/ ل- prepositions, etc.
# These are high-precision Sorani signals.
SORANI_MARKERS = [
    "ەکانی", "ەکان ", "ییەوە", "بەخشینەوە", "یەکێتی", "هەبێت",
    "دەکەن ", "دەکات", "ئەوەی ", "بۆیە", "ئێستا", "کردووە",
    "هەیە ", "نییە ", "چییە", "بەرەو", "لەسەر", "ئەمەی",
    "هەبووە", "دەبێت ", "کراوە", "ناوی ", "خۆیان",
]
# NOTE: some of these can rarely appear in Badini; this filter errs toward
# removing suspected Sorani. Inspect the rejects file and prune markers that
# catch good Badini.


def kurdish_score(text: str) -> int:
    return sum(1 for ch in text if ch in STRONG_KURDISH)


def is_arabic_language(text: str) -> bool:
    # No strong-Kurdish letters at all -> very likely Arabic-language line
    if kurdish_score(text) == 0:
        return True
    # Or contains explicit Arabic citation markers
    return any(m in text for m in ARABIC_MARKERS)


def is_sorani(text: str) -> bool:
    hits = sum(1 for m in SORANI_MARKERS if m in text)
    return hits >= 2  # need 2+ signals to call it Sorani (precision over recall)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/clean/badini_kmr.txt")
    ap.add_argument("--out", default="data/clean/badini_clean.txt")
    ap.add_argument("--rejects", default="data/clean/badini_rejects.txt")
    args = ap.parse_args()

    kept = arab = sor = 0
    with open(args.inp, encoding="utf-8") as f, \
         open(args.out, "w", encoding="utf-8") as out, \
         open(args.rejects, "w", encoding="utf-8") as rej:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if is_arabic_language(s):
                arab += 1
                rej.write("ARABIC\t" + s + "\n")
                continue
            if is_sorani(s):
                sor += 1
                rej.write("SORANI\t" + s + "\n")
                continue
            out.write(s + "\n")
            kept += 1

    total = kept + arab + sor
    print(f"Input lines      : {total:,}")
    print(f"  removed Arabic : {arab:,}")
    print(f"  removed Sorani : {sor:,}")
    print(f"  KEPT (Badini)  : {kept:,}  -> {args.out}")
    print(f"\nRejects written to {args.rejects} — eyeball it to confirm the "
          f"filter isn't dropping good Badini.")


if __name__ == "__main__":
    main()
