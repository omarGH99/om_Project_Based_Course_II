# Badini Kurdish GEC — Draft Error-Type Taxonomy (v0.1)

Status: Week-1 draft. Categories are seeded from the Sorani resources
(AsoSoft spelling datasets, KUTED) plus Badini linguistic knowledge, per the
proposal. Frequencies will be fitted to the real Badini error sample once
collected. Each benchmark sentence pair gets exactly one primary label
(plus optional secondary labels).

## A. Script / orthographic errors (transfer from Sorani resources)

| Code | Name | Description | Example pattern |
|------|------|-------------|-----------------|
| SCR-KAF | Kaf variant | Arabic ك for Kurdish ک | كورد → کورد |
| SCR-YEH | Yeh variant | Arabic ي / ى for Kurdish ی | كوردي → کوردی |
| SCR-HEH | Heh/Ae confusion | ه where ە intended (or vice versa) | ناڤه → ناڤە |
| SCR-DIA | Missing Kurdish diacritic letter | ر for ڕ, و for ۆ, ی for ێ, ل for ڵ (note: ڵ marginal in Badini) | دور → دوور/دۆر context-dependent |
| SCR-ZWNJ | ZWNJ misuse | missing/extra zero-width non-joiner | — |
| SCR-HMZ | Hamza/alef variant | أ/إ/آ inconsistency | — |

## B. Typographic errors

| Code | Name | Description |
|------|------|-------------|
| TYP-SUB | Keyboard substitution | adjacent-key replacement (Kurdish QWERTY layout) |
| TYP-INS / TYP-DEL / TYP-TRA | Insertion / deletion / transposition | classic edit-distance typos |
| TYP-DBL | Doubling/undoubling | missing or extra doubled vowel letter (وو, یی) |

## C. Word-boundary errors

| Code | Name | Description |
|------|------|-------------|
| SPC-MRG | Merged words | missing space between two words |
| SPC-SPL | Split word | space inside a single word |
| SPC-CLT | Clitic attachment | postposition/clitic wrongly attached or detached (e.g. ژی, دا, ڤە) |

## D. Grammatical errors (Badini-specific; real-word errors)

| Code | Name | Description |
|------|------|-------------|
| GRM-IZF | Izafa/ezafe marking | wrong or missing ezafe linker (-ێ/-a/-ên patterns as written in Arabic script) |
| GRM-AGR | Agreement | verb–subject or gender/number agreement |
| GRM-FNW | Function-word confusion | confusable prepositions/particles (ل/لە, ب/بە, ژ/ژە etc. as used in Badini) |
| GRM-VRB | Verb form | wrong tense/aspect affix, wrong copula form |
| GRM-WO | Word order | misplaced constituent (rare; low priority) |

## E. Lexical errors

| Code | Name | Description |
|------|------|-------------|
| LEX-RW | Real-word substitution | valid word but wrong meaning in context |
| LEX-DLT | Dialect interference | Sorani or Arabic form used where Badini form intended |

## Open questions for the real-error analysis (Week 2)
1. Relative frequency of SCR-HEH vs SCR-DIA in social-media text.
2. Whether SPC-CLT should be split per clitic (ژی vs دا/ڤە circumpositions).
3. How writers actually mark ezafe in Arabic-script Badini — this decides
   the GRM-IZF annotation guideline and part of the spelling convention.
4. Whether LEX-DLT is frequent enough to keep as a category.
