"""
Lightweight next-word prediction (autocomplete) for Badini.

A simple, fast n-gram language model trained on the clean corpus. Given the
last 1-2 words the user typed, it suggests the most likely next words.

Why n-gram (not neural): it is instant, needs no GPU, trains in seconds on the
1.4M-word corpus, and is more than good enough for autocomplete suggestions.
A neural LM would be heavier for little practical gain here.

Build the model:
    python -m badini_gec.autocomplete build data/clean/badini_corpus_merged.txt data/ngram.json

Try it:
    python -m badini_gec.autocomplete suggest data/ngram.json "ئەز دێ"
"""

import json
import sys
from collections import Counter, defaultdict

# reuse the project normalizer so suggestions match corrected text
try:
    from badini_gec.normalize import normalize
except Exception:
    def normalize(s):  # fallback if run standalone
        return s


# High-frequency Badini function words (particles/prepositions/conjunctions).
# These are statistically common but useless as autocomplete *suggestions*,
# so we filter them out of the candidate list.
STOPWORDS = {
    "و", "ل", "ب", "د", "ژ", "بۆ", "دا", "کو", "یا", "ژی", "دێ", "وێ",
    "یێ", "یێن", "وی", "وان", "مە", "هەر", "ئەو", "ئەڤ", "ئەز", "تو",
    "ئەم", "نە", "نا", "بێ", "ها", "هاتیە", "–", "-", "،", ".",
}


class Autocomplete:
    """Back-off trigram/bigram/unigram next-word model."""

    def __init__(self, tri=None, bi=None, uni=None):
        self.tri = tri or {}   # "w1 w2" -> {w3: count}
        self.bi = bi or {}     # "w1"    -> {w2: count}
        self.uni = uni or {}   # w       -> count

    # ---- training ----
    @classmethod
    def train(cls, corpus_path):
        tri = defaultdict(Counter)
        bi = defaultdict(Counter)
        uni = Counter()
        for line in open(corpus_path, encoding="utf-8"):
            words = normalize(line.strip()).split()
            if not words:
                continue
            for w in words:
                uni[w] += 1
            for i in range(len(words) - 1):
                bi[words[i]][words[i + 1]] += 1
            for i in range(len(words) - 2):
                key = words[i] + " " + words[i + 1]
                tri[key][words[i + 2]] += 1
        # keep only the top few continuations per context to stay small
        def top(counter_dict, k=8):
            return {ctx: dict(c.most_common(k)) for ctx, c in counter_dict.items()}
        return cls(top(tri), top(bi), dict(uni.most_common(5000)))

    def save(self, path):
        json.dump({"tri": self.tri, "bi": self.bi, "uni": self.uni},
                  open(path, "w", encoding="utf-8"), ensure_ascii=False)

    @classmethod
    def load(cls, path):
        d = json.load(open(path, encoding="utf-8"))
        return cls(d["tri"], d["bi"], d["uni"])

    # ---- prediction ----
    def suggest(self, text, k=3):
        """Return up to k *meaningful* next-word suggestions.

        Filters out high-frequency function words and only offers predictions
        when there is real trigram/bigram context, so it stays quiet rather
        than showing generic particles after every word.
        """
        words = normalize(text.strip()).split()
        if not words:
            return []

        cands = Counter()
        # 1) trigram context (last two words) — strongest signal
        if len(words) >= 2:
            key = words[-2] + " " + words[-1]
            if key in self.tri:
                cands.update(self.tri[key])
        # 2) back off to bigram (last word)
        if not cands and words[-1] in self.bi:
            cands.update(self.bi[words[-1]])
        # NOTE: we deliberately do NOT back off to global unigrams — that only
        # produces generic particles, which look like nonsense suggestions.

        # remove stopwords and the just-typed word; keep content words
        filtered = [(w, c) for w, c in cands.most_common()
                    if w not in STOPWORDS and w != words[-1] and len(w) > 1]

        return [w for w, _ in filtered[:k]]


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "build":
        src, out = sys.argv[2], sys.argv[3]
        m = Autocomplete.train(src)
        m.save(out)
        print(f"Built autocomplete model -> {out}")
        print(f"  trigram contexts: {len(m.tri):,}")
        print(f"  bigram contexts : {len(m.bi):,}")
        print(f"  vocabulary      : {len(m.uni):,}")
    elif cmd == "suggest":
        model_path, text = sys.argv[2], sys.argv[3]
        m = Autocomplete.load(model_path)
        print("Suggestions:", m.suggest(text, k=5))
    else:
        print("commands: build <corpus> <out.json> | suggest <model.json> \"text\"")


if __name__ == "__main__":
    main()