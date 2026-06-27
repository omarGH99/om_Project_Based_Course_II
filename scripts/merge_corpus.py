"""
Merge all clean Badini corpus sources into one deduplicated file.

Combines:
  - data/clean/badini_clean.txt        (ScriptNormalization, cleaned)
  - data/clean/badini_govarametin.txt  (scraped magazine, if present)
  - any other data/clean/badini_*.txt you add later

Output: data/clean/badini_corpus_merged.txt  (use THIS for training/lexicon)

Usage:
    python scripts/merge_corpus.py
"""

import glob
import os

OUT = "data/clean/badini_corpus_merged.txt"
SOURCES = sorted(glob.glob("data/clean/badini_*.txt"))
SOURCES = [s for s in SOURCES if os.path.basename(s) != os.path.basename(OUT)]

seen = set()
total = kept = words = 0
with open(OUT, "w", encoding="utf-8") as out:
    for src in SOURCES:
        n_src = 0
        for line in open(src, encoding="utf-8"):
            s = line.strip()
            if not s:
                continue
            total += 1
            key = s[:80]
            if key in seen:
                continue
            seen.add(key)
            out.write(s + "\n")
            kept += 1
            words += len(s.split())
            n_src += 1
        print(f"  {src}: contributed {n_src} new unique lines")

print(f"\nMerged {len(SOURCES)} sources: {kept} unique sentences "
      f"(~{words} words) from {total} total -> {OUT}")
