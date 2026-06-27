"""
Badini Kurdish Writing Assistant — stylized bilingual interface.
Streamlit + heavy custom CSS (glassmorphism, starry atmosphere, animations).

Wired to the real ByT5 corrector + autocomplete + normalizer, with a
normalization-only fallback so the UI is always interactive.

Run:
    $env:BYT5_DIR="badini_gec/models/byt5-badini-100k"
    python -m streamlit run app/app.py
"""

# ============================================================
#  CONFIG
# ============================================================
import os, re, sys, difflib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from badini_gec.normalize import normalize

MODEL_DIR = os.environ.get("BYT5_DIR", "badini_gec/models/byt5-badini-100k")
NGRAM = os.environ.get("NGRAM", "data/ngram.json")

MODES = {
    "Giştî · General / گشتی": "Everyday writing — fix clear errors, keep style natural.",
    "Fermî · Formal / فەرمی": "Official documents — strict spelling and grammar.",
    "Akademî · Academic / ئەکادیمی": "Academic writing — strict and consistent.",
}
MODE_ICONS = {0: "\u270F\ufe0f", 1: "\U0001FAB6", 2: "\U0001F393"}  # pencil, feather, cap

st.set_page_config(page_title="Badini Writing Assistant", page_icon="\u2600\ufe0f",
                   layout="wide")

# ============================================================
#  CSS INJECTION  (atmosphere, glassmorphism, animations, RTL)
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;700&family=Amiri:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');

:root{
    --gold:#E8B85C; --terra:#C0392B; --terra2:#D35400;
    --field:#0E7C6B; --canvas:#1A2E3B; --parch:#FFFDF9;
}

/* ---- atmospheric night-sky background (CSS-generated) ---- */
.stApp{
    background:
      radial-gradient(2px 2px at 20% 30%, #fff 50%, transparent),
      radial-gradient(1px 1px at 60% 20%, #fff 50%, transparent),
      radial-gradient(1.5px 1.5px at 80% 40%, #ffe9b0 50%, transparent),
      radial-gradient(1px 1px at 35% 60%, #fff 50%, transparent),
      radial-gradient(2px 2px at 75% 75%, #fff 50%, transparent),
      radial-gradient(1px 1px at 50% 85%, #ffe9b0 50%, transparent),
      radial-gradient(900px 500px at 50% -10%, #2a4a52 0%, transparent 70%),
      linear-gradient(180deg, #0d1f29 0%, #14323a 45%, #1d2b24 100%);
    background-attachment: fixed;
}
/* faint floating calligraphy glyphs */
.stApp::before{
    content:"ﻙ ﻭ ﺭ ﺩ ﯼ  ﺏ ﺍ ﺩ ﯼ ﻥ ﯼ"; position:fixed; inset:0;
    font-family:'Amiri',serif; font-size:120px; color:rgba(232,184,92,0.05);
    line-height:2.4; white-space:pre-wrap; text-align:center; pointer-events:none;
    animation: drift 40s ease-in-out infinite alternate; z-index:0;
}
@keyframes drift{ from{transform:translateY(0)} to{transform:translateY(-30px)} }
@keyframes floaty{ 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
@keyframes inkglow{
    0%{ box-shadow:0 0 0 rgba(232,184,92,0); }
    40%{ box-shadow:0 0 40px rgba(232,184,92,0.55); }
    100%{ box-shadow:0 8px 32px rgba(0,0,0,0.37); }
}

.block-container{ max-width:1200px; padding-top:1.4rem; position:relative; z-index:1; }
#MainMenu, footer, header{ visibility:hidden; }

/* ---- glass wrapper feel on key cards ---- */
.glass{
    background:rgba(255,255,255,0.12); border-radius:20px;
    backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
    border:1px solid rgba(255,255,255,0.2);
    box-shadow:0 8px 32px 0 rgba(0,0,0,0.37);
    padding:18px 20px; animation: floaty 7s ease-in-out infinite;
}

/* ---- header (light text on dark) ---- */
h1.title{ font-family:'Inter',sans-serif; font-weight:700; font-size:30px;
    color:#FBF7F0; margin:0; }
.title .ar{ font-family:'Vazirmatn'; color:var(--gold); }
.sub{ font-family:'Inter'; color:#cfe0e0; font-size:13.5px; margin:6px 0 16px; }
.sub .ar{ font-family:'Vazirmatn'; color:#e9d4a6; direction:rtl; }

.colhead{ font-family:'Inter'; font-weight:700; font-size:15px;
    color:#FBF7F0; margin:4px 0 10px; }
.colhead .ar{ font-family:'Vazirmatn'; color:var(--gold); }

/* ---- RTL everywhere Kurdish text appears ---- */
.rtl, .stTextArea textarea{ direction:rtl !important; text-align:right !important;
    font-family:'Vazirmatn','Segoe UI',Tahoma,Geneva,sans-serif !important; }

/* LEFT: parchment input */
.stTextArea textarea{ font-size:19px !important; background:var(--parch) !important;
    border:1px solid #e7dcc4 !important; border-radius:14px !important;
    padding:14px !important; color:#23201a !important; line-height:1.95 !important;
    box-shadow:inset 0 1px 4px rgba(0,0,0,0.06) !important; }
.stTextArea textarea:focus{ border-color:var(--gold) !important;
    box-shadow:0 0 0 3px rgba(232,184,92,0.25) !important; }

/* RIGHT: dark canvas with glowing gold text */
.outcard{ background:var(--canvas); border-radius:16px; padding:20px 22px;
    min-height:200px; font-family:'Vazirmatn'; font-size:22px; line-height:2.05;
    color:var(--gold); text-shadow:0 0 12px rgba(232,184,92,0.45);
    direction:rtl; text-align:right; border:1px solid rgba(232,184,92,0.25);
    animation: inkglow 1.1s ease-out; }
.outcard.empty{ color:#5d7480; text-shadow:none; animation:none; }

/* suggestion / change pills */
.lbl{ font-family:'Inter'; font-size:11px; color:#cbd9d9;
    text-transform:uppercase; letter-spacing:.08em; margin:14px 0 8px; }
.pill{ display:inline-block; font-family:'Vazirmatn'; font-size:16px;
    background:rgba(255,255,255,0.1); color:#FBF7F0; padding:6px 14px;
    border-radius:999px; margin:0 0 7px 7px; border:1px solid rgba(255,255,255,0.18);
    direction:rtl; backdrop-filter:blur(6px); }
.pill .from{ color:#e89b8c; text-decoration:line-through; opacity:.8; }
.pill .arrow{ color:var(--gold); font-weight:700; padding:0 5px; }
.pill .to{ color:#7fe0c4; font-weight:600; }

/* segmented control — pill hover/scale */
div[data-baseweb="segmented-control"]{ background:rgba(255,255,255,0.08);
    border-radius:999px; }
button[kind="segmented_control"], div[role="radiogroup"] label{
    transition:transform .15s ease, background .2s ease !important; }
button[kind="segmented_control"]:hover{ transform:scale(1.04); }

/* main correct button — full-width terracotta */
.stButton button[kind="primary"]{ width:100%;
    background:linear-gradient(180deg,var(--terra2),var(--terra)) !important;
    color:#fff !important; border:none !important; border-radius:14px !important;
    padding:14px !important; font-family:'Inter' !important; font-weight:700 !important;
    font-size:16px !important; letter-spacing:.3px;
    box-shadow:0 6px 20px rgba(192,57,43,0.4) !important;
    transition:transform .15s ease, box-shadow .2s ease !important; }
.stButton button[kind="primary"]:hover{ transform:scale(1.02);
    box-shadow:0 8px 28px rgba(192,57,43,0.55) !important; }
.stButton button:not([kind="primary"]){ width:100%; border-radius:12px !important;
    font-family:'Inter' !important; font-weight:600 !important;
    background:rgba(255,255,255,0.12) !important; color:#FBF7F0 !important;
    border:1px solid rgba(255,255,255,0.2) !important; }
.stCaption, .stMarkdown p{ color:#bccccc; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  STATE
# ============================================================
st.session_state.setdefault("corrected", "")
st.session_state.setdefault("diffs", [])

# ============================================================
#  BACKEND (real model, else normalization mock)
# ============================================================
@st.cache_resource
def load_corrector():
    if MODEL_DIR and os.path.isdir(MODEL_DIR):
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            tok = AutoTokenizer.from_pretrained(MODEL_DIR)
            model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR); model.eval()
            def fn(t):
                ids = tok(t, return_tensors="pt", truncation=True, max_length=256).input_ids
                with torch.no_grad():
                    out = model.generate(ids, max_length=256, num_beams=4)
                return tok.decode(out[0], skip_special_tokens=True)
            return fn, True
        except Exception:
            pass
    return (lambda t: normalize(t)), False


@st.cache_resource
def load_autocomplete():
    if os.path.exists(NGRAM):
        try:
            from badini_gec.autocomplete import Autocomplete
            return Autocomplete.load(NGRAM)
        except Exception:
            return None
    return None


def correct_text(text, corrector):
    normalized = normalize(text)
    parts = re.split(r"([.!?\u061F\u06D4\n]+)", normalized)
    out = []
    for p in parts:
        if p.strip() and not re.match(r"^[.!?\u061F\u06D4\n]+$", p):
            out.append(corrector(p.strip()))
        else:
            out.append(p)
    corrected = "".join(out)
    diffs, a, b = [], text.split(), corrected.split()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        if tag in ("replace", "delete", "insert"):
            frm, to = " ".join(a[i1:i2]) or "\u2014", " ".join(b[j1:j2]) or "\u2014"
            if frm != to:
                diffs.append((frm, to))
    return corrected, diffs

# ============================================================
#  HEADER
# ============================================================
corrector, model_on = load_corrector()
autocomplete = load_autocomplete()

st.markdown(
    "<h1 class='title'>\u2600\ufe0f Badini Writing Assistant "
    "<span class='ar'>• هاریکارێ نڤیسینا بادینی</span></h1>"
    "<p class='sub'>Grammatical error correction &amp; autocomplete for Badini Kurdish "
    "(Arabic script) &nbsp;/&nbsp; <span class='ar'>ڕاستڤەکرنا شاشیێن ڕێزمانی و "
    "تەمامکرنا ئۆتۆماتیکی بۆ کوردییا بادینی</span></p>",
    unsafe_allow_html=True)

# ============================================================
#  MODE SELECTOR
# ============================================================
mode = st.segmented_control("Mode", list(MODES.keys()),
                            default=list(MODES.keys())[0])
if mode:
    st.caption(MODES[mode])
st.write("")

# ============================================================
#  WORKSPACE (side by side)
# ============================================================
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("<div class='colhead'>\U0001F4DD Pênûsa Te \u00b7 Your Text "
                "<span class='ar'>\u067e\u06ce\u0646\u0648\u0633\u0627 \u062a\u06d5</span></div>",
                unsafe_allow_html=True)
    text = st.text_area("input", height=240, label_visibility="collapsed",
                        placeholder="Nivîsa xwe li vir binivîse...")
    if autocomplete and text.strip():
        sugg = autocomplete.suggest(text, k=4)
        if sugg:
            pills = "".join(f"<span class='pill'>{w}</span>" for w in sugg)
            st.markdown("<div class='lbl'>\U0001F4A1 Suggestions \u00b7 \u067e\u06ce\u0634\u0646\u06cc\u0627\u0631</div>"
                        f"<div class='rtl'>{pills}</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='colhead'>\u2728 Derketina Drust \u00b7 Corrected Output "
                "<span class='ar'>\u062f\u06d5\u0631\u0643\u06d5\u062a\u0646</span></div>",
                unsafe_allow_html=True)
    if st.session_state.corrected:
        st.markdown(f"<div class='outcard rtl'>{st.session_state.corrected}</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<div class='outcard rtl empty'>\u2026</div>", unsafe_allow_html=True)
    if st.session_state.diffs:
        st.markdown("<div class='lbl'>\U0001F4A1 Changes \u00b7 \u06af\u06c6\u0695\u0627\u0646\u06a9\u0627\u0631\u06cc</div>",
                    unsafe_allow_html=True)
        pills = ""
        for frm, to in st.session_state.diffs[:12]:
            pills += (f"<span class='pill'><span class='from'>{frm}</span>"
                      f"<span class='arrow'>\u2794</span><span class='to'>{to}</span></span>")
        st.markdown(f"<div class='rtl'>{pills}</div>", unsafe_allow_html=True)

# ============================================================
#  MAIN BUTTON (full width, terracotta)
# ============================================================
st.write("")
if st.button("\U0001F58B\ufe0f Drust BIKIN \u00b7 CORRECT TEXT / \u0695\u0627\u0633\u062a\u06ce\u0628\u06a9\u06d5",
             type="primary"):
    if text.strip():
        st.session_state.corrected, st.session_state.diffs = correct_text(text, corrector)
        st.rerun()
    else:
        st.session_state.corrected, st.session_state.diffs = "", []

if st.session_state.corrected:
    a1, a2 = st.columns(2)
    with a1:
        st.download_button("\u2B07\ufe0f Download \u00b7 \u062f\u0627\u0628\u06d5\u0632\u0627\u0646\u062f\u0646",
                           st.session_state.corrected, file_name="corrected.txt")
    with a2:
        if st.button("\U0001F4CB Copy \u00b7 \u0644\u06ce\u0628\u06af\u0631\u062a\u0646"):
            st.toast("Select the gold text above to copy.")

if not model_on:
    st.caption("Normalization-only mode (mock backend). Set BYT5_DIR for full correction.")