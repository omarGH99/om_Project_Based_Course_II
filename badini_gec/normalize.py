"""
Badini Kurdish (Arabic-script) text normalization.

Handles the script inconsistencies described in the proposal:
- Variant Unicode forms of kaf, yeh, and heh
- Arabic vs Kurdish code points
- Zero-width non-joiner (ZWNJ) cleanup
- Tatweel, diacritics, digit unification

This is a first implementation of the normalization layer; it is designed
to be checked against (and eventually combined with) the AsoSoft normaliser
and KLPT. Every rule is documented so it can be folded into the project's
"documented Badini spelling convention" (Week 1 deliverable).
"""

import re
import unicodedata

ZWNJ = "\u200C"
TATWEEL = "\u0640"

# ---------------------------------------------------------------------------
# 1. Character-level mappings (unconditional)
# ---------------------------------------------------------------------------
# Each entry: wrong/variant codepoint -> canonical Kurdish codepoint
CHAR_MAP = {
    # --- kaf ---
    "\u0643": "\u06A9",  # ARABIC KAF (ك) -> KEHEH (ک)
    "\u06AA": "\u06A9",  # SWASH KAF -> KEHEH

    # --- yeh ---
    "\u064A": "\u06CC",  # ARABIC YEH (ي) -> FARSI YEH (ی)
    "\u0649": "\u06CC",  # ALEF MAKSURA (ى) -> FARSI YEH
    "\u06D2": "\u06CC",  # YEH BARREE -> FARSI YEH

    # --- heh family ---
    "\u06BE": "\u0647",  # HEH DOACHASHMEE (ھ) -> HEH (ه); see final-ae rule below
    "\u06C1": "\u0647",  # HEH GOAL -> HEH

    # --- alef / hamza variants ---
    "\u0623": "\u0627",  # ALEF WITH HAMZA ABOVE (أ) -> ALEF (ا)
    "\u0625": "\u0627",  # ALEF WITH HAMZA BELOW (إ) -> ALEF
    "\u0671": "\u0627",  # ALEF WASLA -> ALEF

    # --- misc Arabic letters not in Kurdish orthography (kept conservative) ---
    "\u0629": "\u06D5",  # TEH MARBUTA (ة) -> AE (ە) — common in loanword spellings

    # --- presentation/compat forms occasionally pasted from PDFs ---
    "\uFEFB": "\u0644\u0627",  # LAM-ALEF ligature -> ل + ا
    "\uFEF7": "\u0644\u0627",
    "\uFEF9": "\u0644\u0627",
    "\uFEF5": "\u0644\u0627",
}

# Arabic-Indic and Extended Arabic-Indic digits -> ASCII (configurable)
DIGIT_MAP = {chr(0x0660 + i): str(i) for i in range(10)}
DIGIT_MAP.update({chr(0x06F0 + i): str(i) for i in range(10)})

# Arabic diacritics (harakat) — rarely meaningful in written Kurdish
DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]")

# Kurdish letters that NEVER join to a following letter, after which a ZWNJ
# is redundant: alef, dal-family, reh-family, waw-family, ae
NON_JOINERS = set("اآدذرڕزژوۆۋە")


def map_chars(text: str) -> str:
    """Apply unconditional character mappings."""
    return text.translate(str.maketrans(CHAR_MAP))


def fix_heh_ae(text: str) -> str:
    """
    Distinguish HEH (ه /h/) from AE (ە, the vowel /a/).

    Convention (draft — to be confirmed in the spelling-convention doc):
    - Word-final ه preceded by a letter is almost always the vowel ە in
      Kurdish, so map word-final ه -> ە.
    - Word-internal ه followed by ZWNJ is the vowel ە (writers use ZWNJ to
      force its isolated/final shape): ه + ZWNJ -> ە (and the ZWNJ becomes
      unnecessary because ە never joins forward).
    """
    # internal heh+ZWNJ -> ae
    text = text.replace("\u0647" + ZWNJ, "\u06D5")
    # word-final heh -> ae (word = sequence of Arabic-block letters)
    text = re.sub(r"(?<=[\u0600-\u06FF])\u0647(?![\u0600-\u06FF])", "\u06D5", text)
    return text


def clean_zwnj(text: str) -> str:
    """Collapse repeated ZWNJ; drop ZWNJ after non-joining letters and at
    word edges, where it has no visual effect and only adds noise."""
    text = re.sub(f"{ZWNJ}+", ZWNJ, text)
    # ZWNJ after a non-joining letter is redundant
    text = re.sub(f"(?<=[{''.join(NON_JOINERS)}]){ZWNJ}", "", text)
    # ZWNJ at start/end of word (adjacent to space/punct/edges)
    text = re.sub(f"(^|\\s){ZWNJ}", r"\1", text)
    text = re.sub(f"{ZWNJ}($|\\s)", r"\1", text)
    return text


def normalize(
    text: str,
    *,
    digits_to_ascii: bool = True,
    strip_diacritics: bool = True,
) -> str:
    """Full normalization pipeline for Badini Kurdish text."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace(TATWEEL, "")
    text = map_chars(text)
    text = fix_heh_ae(text)
    text = clean_zwnj(text)
    if strip_diacritics:
        text = DIACRITICS_RE.sub("", text)
    if digits_to_ascii:
        text = text.translate(str.maketrans(DIGIT_MAP))
    # whitespace cleanup
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text


if __name__ == "__main__":
    import sys
    for line in sys.stdin:
        print(normalize(line.rstrip("\n")))
