"""
Improved synthetic error injection for Badini GEC training.

Generates (wrong, correct, error_codes) pairs from clean Badini sentences.
Improvements over the basic version:
  - error TYPES are weighted toward the ones that actually occur most in Badini
    (script/diacritic confusion dominates; typos are rarer)
  - realistic error DENSITY: most sentences get 1-2 errors, some 0, few 3+
  - richer script/diacritic confusion set (the real Badini pain points)
  - spacing merges/splits and keyboard-adjacent typos

Usage:
    python error_inject_v2.py <clean_sentences.txt> <out_pairs.tsv> --pairs 200000 --seed 1
"""

import argparse
import random
import re

WORD = re.compile(r"[\u0600-\u06FF]+")

# --- the confusions that actually happen in Badini (typed plain vs correct) ---
# each maps a CORRECT char to a list of plausible WRONG substitutions
SCRIPT_CONFUSIONS = {
    "ک": ["ك"],            # Arabic kaf vs Persian/Kurdish
    "ی": ["ي", "ى"],       # Arabic ya vs Kurdish
    "ۆ": ["و", "و"],       # o -> plain waw (very common)
    "ێ": ["ی", "ي"],       # e-circumflex -> plain ya (very common)
    "ە": ["ه"],            # e -> plain ha (very common)
    "ڤ": ["ف", "و"],       # v -> f
    "ڕ": ["ر"],            # strong r -> plain r
    "ڵ": ["ل"],            # strong l -> plain l
    "چ": ["ج"],
    "پ": ["ب"],
    "گ": ["ك", "ک"],
    "ژ": ["ز"],
}

# keyboard-adjacent-ish typo neighbours (rough, for TYP)
TYPO_NEIGHBORS = {
    "ا": "لأ", "ب": "ني", "ت": "بن", "د": "ذر", "ر": "ذد",
    "س": "شص", "ع": "غخ", "ف": "قغ", "ل": "اك", "م": "ن",
    "ن": "مب", "ه": "ةع", "و": "ؤ", "ی": "ىي",
}


def _apply_script(word):
    """Swap one correct special char for a plain/wrong one."""
    idxs = [i for i, c in enumerate(word) if c in SCRIPT_CONFUSIONS]
    if not idxs:
        return None
    i = random.choice(idxs)
    wrong = random.choice(SCRIPT_CONFUSIONS[word[i]])
    return word[:i] + wrong + word[i+1:]


def _apply_typo(word):
    if len(word) < 2:
        return None
    kind = random.choice(["sub", "del", "ins", "swap"])
    i = random.randrange(len(word))
    if kind == "sub":
        c = word[i]
        repl = TYPO_NEIGHBORS.get(c)
        if not repl:
            return None
        return word[:i] + random.choice(repl) + word[i+1:]
    if kind == "del":
        return word[:i] + word[i+1:]
    if kind == "ins":
        return word[:i] + random.choice("اویهن") + word[i:]
    if kind == "swap" and i < len(word) - 1:
        return word[:i] + word[i+1] + word[i] + word[i+2:]
    return None


def corrupt_sentence(sentence):
    """Return (wrong_sentence, codes). Realistic density: mostly 1-2 errors."""
    words = sentence.split()
    if not words:
        return sentence, []
    # how many errors: weighted toward 1-2
    n_err = random.choices([0, 1, 2, 3], weights=[8, 45, 35, 12])[0]
    n_err = min(n_err, len(words))
    if n_err == 0:
        return sentence, []          # some clean sentences (teaches precision)

    codes = []
    targets = random.sample(range(len(words)), n_err)
    for ti in targets:
        w = words[ti]
        # weight error TYPE: script/diacritic dominates in real Badini
        etype = random.choices(
            ["SCR", "SPC", "TYP"], weights=[62, 20, 18])[0]
        if etype == "SCR":
            new = _apply_script(w)
            if new:
                words[ti] = new; codes.append("SCR"); continue
            etype = "TYP"  # fall through if no special char
        if etype == "SPC":
            # merge with a neighbour, or split this word
            if random.random() < 0.5 and ti < len(words) - 1:
                words[ti] = w + words[ti+1]
                words[ti+1] = ""
                codes.append("SPC"); continue
            elif len(w) > 3:
                cut = random.randrange(1, len(w))
                words[ti] = w[:cut] + " " + w[cut:]
                codes.append("SPC"); continue
            etype = "TYP"
        if etype == "TYP":
            new = _apply_typo(w)
            if new:
                words[ti] = new; codes.append("TYP")
    wrong = " ".join(x for x in words if x != "").strip()
    wrong = re.sub(r"\s+", " ", wrong)
    return wrong, codes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--pairs", type=int, default=150000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    random.seed(args.seed)

    lines = [l.strip() for l in open(args.src, encoding="utf-8")
             if l.strip() and 3 <= len(l.split()) <= 40]
    print(f"source sentences: {len(lines):,}")

    n = 0
    with open(args.out, "w", encoding="utf-8") as g:
        while n < args.pairs:
            s = random.choice(lines)
            wrong, codes = corrupt_sentence(s)
            if wrong == s and not codes:
                # keep ~10% clean pairs for precision, skip the rest
                if random.random() > 0.10:
                    continue
            g.write(f"{wrong}\t{s}\t{','.join(codes)}\n")
            n += 1
            if n % 20000 == 0:
                print(f"  wrote {n:,}")
    print(f"DONE. wrote {n:,} pairs -> {args.out}")


if __name__ == "__main__":
    main()
