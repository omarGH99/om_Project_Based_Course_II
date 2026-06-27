"""
Extract clean Arabic-script Kurmanji/Badini text from Kurmanji Wikipedia.

Why this script exists
----------------------
KurCorpus 2B turned out to be effectively all Sorani, so it cannot serve as
the clean-Badini source. Kurmanji Wikipedia (language code `ku`) IS genuine
Kurmanji, but most of it is Latin script (Turkey style). The Arabic-script
subset of it is Badini-compatible — that is what we keep here.

Source
------
Primary: the pre-cleaned `wikimedia/wikipedia` dataset on Hugging Face,
config `20231101.ku` (Kurmanji). It is already plain article text, so we
avoid parsing raw MediaWiki markup.

Output
------
- data/clean/badini_wiki.txt : normalized, Arabic-script, length-filtered
                               sentences ready for error injection / LM training
- prints a coverage report (how much Arabic-script Kurmanji actually exists)

Usage
-----
    pip install datasets
    python scripts/extract_wiki_badini.py
    # options:
    python scripts/extract_wiki_badini.py --min-words 4 --max-words 60 \
        --out data/clean/badini_wiki.txt
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from badini_gec.normalize import normalize

ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN = re.compile(r"[A-Za-z\u00C0-\u024F]")
# Sentence-ish splitter: break on ., !, ?, Arabic full stop, newlines
SENT_SPLIT = re.compile(r"[.!?\u061F\u06D4\n]+")
PLACEHOLDERS = ("[URL]", "[EMAIL]")


def script_of(text: str) -> str:
    a, l = len(ARABIC.findall(text)), len(LATIN.findall(text))
    if a + l == 0:
        return "other"
    if a / (a + l) >= 0.8:
        return "arabic"
    if l / (a + l) >= 0.8:
        return "latin"
    return "mixed"


def iter_sentences(article_text: str):
    for chunk in SENT_SPLIT.split(article_text):
        chunk = chunk.strip()
        if chunk:
            yield chunk


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="20231101.ku",
                   help="HF wikimedia/wikipedia config (Kurmanji = 20231101.ku)")
    p.add_argument("--out", default="data/clean/badini_wiki.txt")
    p.add_argument("--min-words", type=int, default=4)
    p.add_argument("--max-words", type=int, default=60)
    p.add_argument("--max-articles", type=int, default=0,
                   help="0 = all; set a number for a quick test run")
    args = p.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("Please install the datasets library:  pip install datasets")

    print(f"Loading wikimedia/wikipedia [{args.config}] (streaming)...")
    ds = load_dataset("wikimedia/wikipedia", args.config,
                      split="train", streaming=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    stats = {"arabic": 0, "latin": 0, "mixed": 0, "other": 0}
    articles = 0
    kept = 0
    kept_words = 0
    seen = set()  # crude dedup

    with open(args.out, "w", encoding="utf-8") as out:
        for ex in ds:
            articles += 1
            for sent in iter_sentences(ex.get("text", "")):
                sc = script_of(sent)
                stats[sc] += 1
                if sc != "arabic":
                    continue
                norm = normalize(sent)
                if any(ph in norm for ph in PLACEHOLDERS):
                    # keep sentence but it's fine; placeholders are harmless.
                    pass
                n = len(norm.split())
                if not (args.min_words <= n <= args.max_words):
                    continue
                key = norm[:80]
                if key in seen:
                    continue
                seen.add(key)
                out.write(norm + "\n")
                kept += 1
                kept_words += n
            if args.max_articles and articles >= args.max_articles:
                break

    total_sent = sum(stats.values())
    print(f"\nArticles scanned : {articles:,}")
    print(f"Sentences seen   : {total_sent:,}")
    for k in ("arabic", "latin", "mixed", "other"):
        v = stats[k]
        print(f"  {k:>7}: {v:>10,}  ({100*v/max(total_sent,1):.1f}%)")
    print(f"\nKEPT (Arabic-script, {args.min_words}-{args.max_words} words, "
          f"deduped): {kept:,} sentences, {kept_words:,} words")
    print(f"-> {args.out}")
    if kept_words < 200_000:
        print("\nNote: this is a small corpus. Plan to supplement with Badini "
              "news/social scraping to reach a comfortable size.")


if __name__ == "__main__":
    main()
