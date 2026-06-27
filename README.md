# Badini Kurdish Writing Assistant — GEC + Benchmark

Grammatical Error Correction (GEC) and the first public GEC benchmark for
**Badini** (the Arabic-script variety of Kurmanji Kurdish spoken in the Duhok
region). MSc AI Project-Based Course II.

**Author:** Omar Safar Younis (A25100074)

## What this project does

Takes incorrect Badini text and returns corrected text, using a fine-tuned
byte-level neural model (ByT5), compared against a dictionary/edit-distance
baseline. It also releases a real-error benchmark and a synthetic training set.

```
clean Badini text  ->  inject realistic errors  ->  train corrector
                                                          |
                          evaluate on REAL errors  <------+
```

## Repository structure

```
badini-gec/
├── badini_gec/
│   ├── normalize.py        Arabic-script normalization (kaf/yeh/heh, ZWNJ)
│   ├── error_inject.py     synthetic error generator (one injector per taxonomy code)
│   └── baseline.py         dictionary + edit-distance corrector (SymSpell)
├── scripts/
│   ├── check_corpus.py     script-detection + cleaning for a raw corpus
│   ├── build_badini_base.py  build clean corpus from ScriptNormalization data
│   └── clean_badini.py     remove Arabic-language + Sorani contamination
├── eval/
│   └── evaluate.py         precision / recall / F0.5 / GLEU
├── notebooks/
│   └── byt5_pilot.ipynb    ByT5 fine-tuning pilot (Colab)
├── app/
│   └── app.py              Streamlit writing-assistant (3 modes)
├── data/
│   ├── clean/badini_clean.txt   14,826 clean Badini sentences (~310k words)
│   ├── benchmark/               GEC benchmark (real errors) + template
│   └── lexicon.tsv              frequency lexicon for the baseline
├── docs/
│   └── error_taxonomy_v0.1.md
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone <your-repo-url>
cd badini-gec
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproduce the results

**1. Run the normalizer tests**
```bash
python tests/test_normalize.py          # expect 11/11 passed
```

**2. Build the clean Badini corpus** (from Ahmadi & Anastasopoulos ScriptNormalization, ACL 2023; Apache-2.0)
```bash
git clone --depth 1 https://github.com/sinaahmadi/ScriptNormalization.git
python scripts/build_badini_base.py --src ScriptNormalization/data/corpus/kmr-arab_corpus.txt --out data/clean/badini_kmr.txt
python scripts/clean_badini.py --in data/clean/badini_kmr.txt --out data/clean/badini_clean.txt
```

**3. Build the baseline lexicon and run the baseline**
```bash
python -m badini_gec.baseline build data/clean/badini_clean.txt data/lexicon.tsv
python -m badini_gec.error_inject data/clean/badini_clean.txt data/test_synth.tsv --pairs 300 --seed 999
python -m badini_gec.baseline correct data/lexicon.tsv <(cut -f1 data/test_synth.tsv) hyp.txt
python -m eval.evaluate <(cut -f1 data/test_synth.tsv) hyp.txt <(cut -f2 data/test_synth.tsv)
```

**4. Train ByT5** — open `notebooks/byt5_pilot.ipynb` in Google Colab (GPU runtime), set your repo URL, run all cells.

**5. Run the app**
```bash
streamlit run app/app.py
# optional: set BYT5_DIR=/path/to/model to use the trained corrector
```

## Current results (Week 2)

Baseline (SymSpell dictionary) on 300 held-out synthetic Badini errors:

| Metric | Score |
|--------|-------|
| Precision | 0.243 |
| Recall | 0.352 |
| F0.5 | 0.259 |
| GLEU | 0.794 |
| Exact match | 0.160 |

This is the floor the neural model (ByT5) is expected to beat, especially on
word-boundary and grammatical errors the dictionary cannot handle.

## Data & licenses

- **Clean text:** Kurmanji Arabic-script corpus from Ahmadi & Anastasopoulos,
  *ScriptNormalization* (ACL 2023), Apache-2.0.
- **Error taxonomy grounding:** AsoSoft Central Kurdish Spelling datasets; KUTED.
- **Self-built:** real-error sample, GEC benchmark, synthetic error set (this repo).

## AI-tool usage

AI assistants (e.g. Claude) were used as productivity aids for code scaffolding,
debugging, and drafting, in line with the course policy. All code is understood
and maintained by the author.

## Citation

If you use this work, please cite the project and:
Ahmadi & Anastasopoulos, "Script Normalization for Unconventional Writing of
Under-Resourced Languages in Bilingual Communities," ACL 2023.
