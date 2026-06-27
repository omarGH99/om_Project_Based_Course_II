"""
Baseline corrector: frequency lexicon + edit distance (SymSpell if
installed, else a small built-in fallback). This is model (1) in the
proposal's comparison; ByT5 is model (2).

Build the lexicon from the normalized clean corpus:
    python -m badini_gec.baseline build data/clean/badini.txt data/lexicon.tsv
Correct a file (one sentence per line):
    python -m badini_gec.baseline correct data/lexicon.tsv input.txt output.txt
"""

import argparse
from collections import Counter

try:
    from symspellpy import SymSpell, Verbosity
    HAS_SYMSPELL = True
except ImportError:
    HAS_SYMSPELL = False


def build_lexicon(corpus_path, out_path, min_count=2):
    counts = Counter()
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            counts.update(line.split())
    with open(out_path, "w", encoding="utf-8") as out:
        for w, c in counts.most_common():
            if c >= min_count:
                out.write(f"{w}\t{c}\n")
    print(f"Lexicon: {sum(1 for c in counts.values() if c >= min_count)} words")


class Baseline:
    def __init__(self, lexicon_path, max_edit=2):
        self.freq = {}
        with open(lexicon_path, encoding="utf-8") as f:
            for line in f:
                w, c = line.rstrip("\n").split("\t")
                self.freq[w] = int(c)
        self.max_edit = max_edit
        if HAS_SYMSPELL:
            self.ss = SymSpell(max_dictionary_edit_distance=max_edit)
            for w, c in self.freq.items():
                self.ss.create_dictionary_entry(w, c)

    def correct_word(self, word):
        if word in self.freq or not word:
            return word
        if HAS_SYMSPELL:
            sugg = self.ss.lookup(word, Verbosity.TOP,
                                  max_edit_distance=self.max_edit,
                                  include_unknown=True)
            return sugg[0].term if sugg else word
        return self._fallback(word)

    def _fallback(self, word):
        # brute-force edit-distance-1 candidates (slow; for testing only)
        import itertools
        alphabet = set("".join(list(self.freq)[:2000]))
        cands = set()
        for i in range(len(word) + 1):
            for ch in alphabet:
                cands.add(word[:i] + ch + word[i:])      # insert
            if i < len(word):
                cands.add(word[:i] + word[i + 1:])        # delete
                for ch in alphabet:
                    cands.add(word[:i] + ch + word[i + 1:])  # substitute
        best = max((c for c in cands if c in self.freq),
                   key=lambda c: self.freq[c], default=None)
        return best or word

    def correct(self, sentence):
        return " ".join(self.correct_word(w) for w in sentence.split())


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("corpus"); b.add_argument("out")
    c = sub.add_parser("correct")
    c.add_argument("lexicon"); c.add_argument("infile"); c.add_argument("outfile")
    args = p.parse_args()

    if args.cmd == "build":
        build_lexicon(args.corpus, args.out)
    else:
        model = Baseline(args.lexicon)
        with open(args.infile, encoding="utf-8") as f, \
             open(args.outfile, "w", encoding="utf-8") as out:
            for line in f:
                out.write(model.correct(line.strip()) + "\n")
        print("Done.", "" if HAS_SYMSPELL else "(install symspellpy for speed)")


if __name__ == "__main__":
    main()
