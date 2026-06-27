"""
Build the clean Badini base corpus from Sina Ahmadi's ScriptNormalization
data (ACL 2023), which contains a Kurmanji Arabic-script corpus crawled from
rojnameyaevro.com, gavtv.net, and badinan.org. Apache-licensed.

This replaces KurCorpus (which turned out to be all Sorani) as the clean-text
source. Cite:
  Ahmadi & Anastasopoulos, "Script Normalization for Unconventional Writing
  of Under-Resourced Languages in Bilingual Communities", ACL 2023.

Usage:
    # one-time: clone the repo somewhere
    git clone --depth 1 https://github.com/sinaahmadi/ScriptNormalization.git
    python scripts/build_badini_base.py \
        --src ScriptNormalization/data/corpus/kmr-arab_corpus.txt \
        --out data/clean/badini_kmr.txt
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from badini_gec.normalize import normalize

ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN = re.compile(r"[A-Za-z]")
SENT = re.compile(r"[.!?\u061F\u06D4\n]+")
# drop lines that are mostly a leading number/fragment or a citation
LEADING_JUNK = re.compile(r"^[\d\\/%]+")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="kmr-arab_corpus.txt path")
    p.add_argument("--out", default="data/clean/badini_kmr.txt")
    p.add_argument("--min-words", type=int, default=4)
    p.add_argument("--max-words", type=int, default=60)
    p.add_argument("--drop-leading-digits", action="store_true",
                   help="skip sentences that start with a number/fragment")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    sents = kept = words = 0
    seen = set()

    with open(args.src, encoding="utf-8", errors="replace") as f, \
         open(args.out, "w", encoding="utf-8") as out:
        for line in f:
            for chunk in SENT.split(line):
                c = chunk.strip()
                if not c:
                    continue
                sents += 1
                a, l = len(ARABIC.findall(c)), len(LATIN.findall(c))
                if a + l == 0 or a / (a + l) < 0.8:
                    continue
                if args.drop_leading_digits and LEADING_JUNK.match(c):
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

    print(f"Sentences seen : {sents:,}")
    print(f"KEPT           : {kept:,} sentences, {words:,} words -> {args.out}")
    if words < 1_000_000:
        print("\nThis is a modest base. Supplement with badinan.org / gavtv.net "
              "scraping or Badini books to grow it before full training.")


if __name__ == "__main__":
    main()
