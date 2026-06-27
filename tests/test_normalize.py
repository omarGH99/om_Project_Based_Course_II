"""Tests for badini_gec.normalize — each test encodes one rule of the
draft Badini spelling convention."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from badini_gec.normalize import normalize, ZWNJ


def test_arabic_kaf_to_keheh():
    assert normalize("كورد") == "کورد"          # ك -> ک

def test_arabic_yeh_to_farsi_yeh():
    assert normalize("كوردي") == "کوردی"        # ي -> ی
    assert normalize("على") == "علی"            # ى -> ی

def test_word_final_heh_to_ae():
    # 'name' written with Arabic heh at the end should become ە
    assert normalize("ناڤه") == "ناڤە"

def test_internal_heh_zwnj_to_ae():
    assert normalize("هه" + ZWNJ + "ر") == "هەر"

def test_heh_as_consonant_kept():
    # word-initial /h/ stays HEH
    assert normalize("هات").startswith("ه")

def test_teh_marbuta():
    assert normalize("مدرسة") == "مدرسە"

def test_hamza_alef_variants():
    assert normalize("أاإ") == "ااا"

def test_tatweel_removed():
    assert normalize("کـورد") == "کورد"

def test_digits():
    assert normalize("٢٠٢٦ و ۱۲") == "2026 و 12"

def test_zwnj_collapse_and_strip():
    assert ZWNJ + ZWNJ not in normalize("a" + ZWNJ + ZWNJ + "b")
    # ZWNJ after non-joining waw is redundant
    assert normalize("و" + ZWNJ + "کورد") == "وکورد"

def test_whitespace():
    assert normalize("  کورد   باش  ") == "کورد باش"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
