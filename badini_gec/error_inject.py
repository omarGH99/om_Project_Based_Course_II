"""
Synthetic error injection for Badini Kurdish GEC training data.

Each injector corresponds to a code in docs/error_taxonomy_v0.1.md.
Frequencies (CONFIG weights) are placeholders — they MUST be re-fitted to
the real Badini error sample in Week 2 (proposal Section 6).

Usage:
    python -m badini_gec.error_inject clean.txt pairs.tsv --pairs 50000
Output TSV columns: incorrect <TAB> correct <TAB> error_codes
"""

import argparse
import random
import re

# ---------------------------------------------------------------------------
# Error injectors. Each takes a correct sentence and returns
# (corrupted_sentence, code) or None if not applicable.
# ---------------------------------------------------------------------------

# SCR: reverse-normalization confusions (canonical -> common wrong form)
SCR_CONFUSIONS = [
    ("SCR-KAF", "ک", "ك"),
    ("SCR-YEH", "ی", "ي"),
    ("SCR-HEH", "ە", "ه"),
    ("SCR-DIA", "ڕ", "ر"),
    ("SCR-DIA", "ۆ", "و"),
    ("SCR-DIA", "ێ", "ی"),
    ("SCR-DIA", "ڤ", "ف"),
]

# Approximate Kurdish (Arabic-script) keyboard adjacency for TYP-SUB.
# TODO Week 2: replace with the actual KRG-standard layout map.
KEY_ADJ = {
    "ب": "لیت", "ی": "بسن", "س": "یشو", "ت": "بن", "ن": "تم",
    "ا": "ەل", "ە": "او", "و": "ەر", "ر": "ود", "د": "رژ",
    "ل": "اک", "ک": "لگ", "م": "نء", "ژ": "دز", "ز": "ژخ",
}

CLITICS = ["ژی", "دا", "ڤە", "یە"]  # SPC-CLT candidates (Badini)


def _rand_word_idx(words, min_len=2):
    cands = [i for i, w in enumerate(words) if len(w) >= min_len]
    return random.choice(cands) if cands else None


def inj_scr(sent):
    code, good, bad = random.choice(SCR_CONFUSIONS)
    if good not in sent:
        return None
    # replace one random occurrence
    idxs = [m.start() for m in re.finditer(re.escape(good), sent)]
    i = random.choice(idxs)
    return sent[:i] + bad + sent[i + len(good):], code


def inj_typ_sub(sent):
    chars = [i for i, c in enumerate(sent) if c in KEY_ADJ]
    if not chars:
        return None
    i = random.choice(chars)
    return sent[:i] + random.choice(KEY_ADJ[sent[i]]) + sent[i + 1:], "TYP-SUB"


def inj_typ_del(sent):
    words = sent.split()
    wi = _rand_word_idx(words, 3)
    if wi is None:
        return None
    w = words[wi]
    ci = random.randrange(len(w))
    words[wi] = w[:ci] + w[ci + 1:]
    return " ".join(words), "TYP-DEL"


def inj_typ_tra(sent):
    words = sent.split()
    wi = _rand_word_idx(words, 4)
    if wi is None:
        return None
    w = words[wi]
    ci = random.randrange(len(w) - 1)
    words[wi] = w[:ci] + w[ci + 1] + w[ci] + w[ci + 2:]
    return " ".join(words), "TYP-TRA"


def inj_typ_dbl(sent):
    # remove one letter of a doubled vowel (وو -> و, یی -> ی)
    for pat, rep in [("وو", "و"), ("یی", "ی")]:
        if pat in sent and random.random() < 0.7:
            return sent.replace(pat, rep, 1), "TYP-DBL"
    return None


def inj_spc_mrg(sent):
    words = sent.split()
    if len(words) < 3:
        return None
    i = random.randrange(len(words) - 1)
    merged = words[:i] + [words[i] + words[i + 1]] + words[i + 2:]
    return " ".join(merged), "SPC-MRG"


def inj_spc_spl(sent):
    words = sent.split()
    wi = _rand_word_idx(words, 5)
    if wi is None:
        return None
    w = words[wi]
    ci = random.randrange(2, len(w) - 1)
    words[wi] = w[:ci] + " " + w[ci:]
    return " ".join(words), "SPC-SPL"


def inj_spc_clt(sent):
    # detach a clitic that is attached, or attach one that is separate
    words = sent.split()
    for i, w in enumerate(words):
        for cl in CLITICS:
            if w.endswith(cl) and len(w) > len(cl) + 2 and random.random() < 0.5:
                words[i] = w[: -len(cl)] + " " + cl
                return " ".join(words), "SPC-CLT"
    for i in range(len(words) - 1):
        if words[i + 1] in CLITICS:
            merged = words[:i] + [words[i] + words[i + 1]] + words[i + 2:]
            return " ".join(merged), "SPC-CLT"
    return None


# GRM-FNW: function-word confusions. TODO Week 2: replace placeholder pairs
# with confusion sets confirmed from the real Badini sample.
FNW_PAIRS = [("ژ", "ل"), ("ب", "د"), ("بۆ", "ژبۆ")]

def inj_grm_fnw(sent):
    words = sent.split()
    for a, b in random.sample(FNW_PAIRS, len(FNW_PAIRS)):
        for i, w in enumerate(words):
            if w == a:
                words[i] = b
                return " ".join(words), "GRM-FNW"
    return None


INJECTORS = {
    "SCR": inj_scr,
    "TYP-SUB": inj_typ_sub,
    "TYP-DEL": inj_typ_del,
    "TYP-TRA": inj_typ_tra,
    "TYP-DBL": inj_typ_dbl,
    "SPC-MRG": inj_spc_mrg,
    "SPC-SPL": inj_spc_spl,
    "SPC-CLT": inj_spc_clt,
    "GRM-FNW": inj_grm_fnw,
}

# PLACEHOLDER weights — refit to real-error sample in Week 2.
CONFIG = {
    "SCR": 0.30, "TYP-SUB": 0.10, "TYP-DEL": 0.08, "TYP-TRA": 0.05,
    "TYP-DBL": 0.07, "SPC-MRG": 0.12, "SPC-SPL": 0.08, "SPC-CLT": 0.12,
    "GRM-FNW": 0.08,
}

ERRORS_PER_SENT = [(1, 0.6), (2, 0.3), (3, 0.1)]  # how many errors to inject


def corrupt(sent, rng=random):
    """Return (incorrect, codes) for one clean sentence, or None."""
    n = rng.choices([k for k, _ in ERRORS_PER_SENT],
                    [w for _, w in ERRORS_PER_SENT])[0]
    cur, codes = sent, []
    names = list(CONFIG)
    weights = list(CONFIG.values())
    for _ in range(n * 3):  # allow retries for inapplicable injectors
        if len(codes) >= n:
            break
        inj = INJECTORS[rng.choices(names, weights)[0]]
        res = inj(cur)
        if res and res[0] != cur:
            cur, code = res
            codes.append(code)
    if not codes:
        return None
    return cur, codes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("clean", help="normalized clean text, one sentence per line")
    p.add_argument("out", help="output TSV: incorrect\\tcorrect\\tcodes")
    p.add_argument("--pairs", type=int, default=50000)
    p.add_argument("--seed", type=int, default=13)
    args = p.parse_args()
    random.seed(args.seed)

    written = 0
    with open(args.clean, encoding="utf-8") as f, \
         open(args.out, "w", encoding="utf-8") as out:
        sents = [l.strip() for l in f if l.strip()]
        while written < args.pairs and sents:
            sent = random.choice(sents)
            res = corrupt(sent)
            if res:
                bad, codes = res
                out.write(f"{bad}\t{sent}\t{','.join(codes)}\n")
                written += 1
    print(f"Wrote {written} pairs -> {args.out}")


if __name__ == "__main__":
    main()
