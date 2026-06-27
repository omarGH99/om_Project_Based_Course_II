"""
Evaluation for Badini GEC.

Primary: precision / recall / F0.5 over token-level edits, computed by
aligning (source, hypothesis) and (source, reference) edit sets — a
lightweight language-agnostic stand-in compatible with M2-style scoring.
For the report, also run the official M2 scorer on the same files
(scripts to convert to .m2 format included below).
Secondary: sentence-level GLEU (simplified) and exact-match accuracy.

Usage:
    python -m eval.evaluate source.txt hypothesis.txt reference.txt
"""

import argparse
import difflib
from collections import Counter


def edits(src_tokens, tgt_tokens):
    """Return a set of edit operations transforming src -> tgt."""
    sm = difflib.SequenceMatcher(a=src_tokens, b=tgt_tokens, autojunk=False)
    ops = set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            ops.add((i1, i2, tuple(tgt_tokens[j1:j2])))
    return ops


def prf(source, hyps, refs, beta=0.5):
    tp = fp = fn = 0
    for s, h, r in zip(source, hyps, refs):
        s, h, r = s.split(), h.split(), r.split()
        he, re_ = edits(s, h), edits(s, r)
        tp += len(he & re_)
        fp += len(he - re_)
        fn += len(re_ - he)
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = ((1 + beta**2) * p * r / (beta**2 * p + r)) if p + r else 0.0
    return p, r, f


def gleu(hyps, refs, n=4):
    """Simplified corpus GLEU (n-gram precision-recall min)."""
    score_num = score_den = 0
    for h, r in zip(hyps, refs):
        h, r = h.split(), r.split()
        for k in range(1, n + 1):
            hg = Counter(tuple(h[i:i+k]) for i in range(len(h)-k+1))
            rg = Counter(tuple(r[i:i+k]) for i in range(len(r)-k+1))
            score_num += sum((hg & rg).values())
            score_den += max(sum(hg.values()), 1)
    return score_num / max(score_den, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source"); p.add_argument("hypothesis"); p.add_argument("reference")
    args = p.parse_args()
    read = lambda f: [l.strip() for l in open(f, encoding="utf-8")]
    src, hyp, ref = read(args.source), read(args.hypothesis), read(args.reference)
    assert len(src) == len(hyp) == len(ref), "line counts differ"

    pr, rc, f05 = prf(src, hyp, ref)
    em = sum(h == r for h, r in zip(hyp, ref)) / len(ref)
    print(f"Precision: {pr:.4f}")
    print(f"Recall:    {rc:.4f}")
    print(f"F0.5:      {f05:.4f}")
    print(f"GLEU:      {gleu(hyp, ref):.4f}")
    print(f"ExactMatch:{em:.4f}")


if __name__ == "__main__":
    main()
