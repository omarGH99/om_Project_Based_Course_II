# Setup Guide — Badini Writing Assistant

This is the FINAL project folder. Use only this one.

## 1. One-time environment setup

Open this folder in VS Code, open a terminal, then:

```
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Verify the GPU is seen (optional, for training):
```
python -c "import torch; print(torch.cuda.is_available())"
```

## 2. Build the data artifacts (already included, but to rebuild)

```
python -m badini_gec.baseline build data/clean/badini_clean.txt data/lexicon.tsv
python -m badini_gec.autocomplete build data/clean/badini_clean.txt data/ngram.json
```

(If you have the merged 1.4M-word corpus, build from data/clean/badini_corpus_merged.txt instead.)

## 3. Run the app

Download your trained ByT5 model from Google Drive into:  models/byt5-badini-100k/

Then:
```
$env:BYT5_DIR="models/byt5-badini-100k"
python -m streamlit run app/app.py
```

Without the model, the app still runs (normalization + autocomplete only).

## 4. Train (on Colab)

Use notebooks/byt5_train or the comparison notebook on Colab with an L4 GPU.
Remember: use bf16=True (not fp16) for ByT5.

## What's where
- badini_gec/   core modules (normalize, error_inject, baseline, autocomplete)
- scripts/      data tools (corpus building, cleaning, PDF extraction, merging)
- notebooks/    training + comparison notebooks (Colab)
- app/          the Streamlit writing assistant
- data/         corpus, pairs, lexicon, ngram model
- eval/         evaluation metrics
- docs/         error taxonomy
