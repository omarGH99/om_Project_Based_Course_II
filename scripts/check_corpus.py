"""
Check a Kurdish corpus file: how much is Arabic script vs Latin script,
basic stats, and produce a cleaned Arabic-script-only file ready for
error injection.

Usage:
    python scripts/check_corpus.py path/to/corpus.txt --out data/clean/badini.txt
Works on .txt (one sentence/paragraph per line). For HF datasets, export
the text column to .txt first (see notebooks/byt5_pilot.ipynb cell 2).
"""

import argparse
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from badini_gec.normalize import normalize

ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN = re.compile(r"[A-Za-z\u00C0-\u024F]")


def classify(line: str) -> str:
    a, l = len(ARABIC.findall(line)), len(LATIN.findall(line))
    if a + l == 0:
        return "other"
    if a / (a + l) >= 0.8:
        return "arabic"
    if l / (a + l) >= 0.8:
        return "latin"
    return "mixed"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("corpus")
    p.add_argument("--out", help="write normalized Arabic-script lines here")
    p.add_argument("--min-words", type=int, default=3)
    p.add_argument("--max-words", type=int, default=60)
    args = p.parse_args()

    counts = {"arabic": 0, "latin": 0, "mixed": 0, "other": 0}
    kept, total_words = 0, 0
    out = open(args.out, "w", encoding="utf-8") if args.out else None

    with open(args.corpus, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = classify(line)
            counts[c] += 1
            if c == "arabic" and out:
                norm = normalize(line)
                n = len(norm.split())
                if args.min_words <= n <= args.max_words:
                    out.write(norm + "\n")
                    kept += 1
                    total_words += n
    if out:
        out.close()

    total = sum(counts.values())
    print(f"Lines: {total}")
    for k, v in counts.items():
        print(f"  {k:>7}: {v:>10}  ({100*v/max(total,1):.1f}%)")
    if args.out:
        print(f"Kept (normalized, {args.min_words}-{args.max_words} words): "
              f"{kept} lines, {total_words} words -> {args.out}")


if __name__ == "__main__":
    main()
