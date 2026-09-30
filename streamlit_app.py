"""
VisionGuard - Streamlit demo (redesigned UI).

Talks to the FastAPI service (main.py) which must already be running.

Run with:
  streamlit run streamlit_app.py
"""

import base64
import html

from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="VisionGuard", page_icon="🦺", layout="wide")

# ---------------------------------------------------------------
# Design: site-safety signage. Hi-vis yellow on concrete-dark,
# one hazard-tape strip in the header (the single bold moment),
# everything else quiet. Red / green are reserved for the verdict.
# ---------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap');

:root {
    --hazard: #FFC800;
    --ink: #14161A;
    --concrete: #1D2024;
    --steel: #2A2E34;
    --line: #3A3F47;
    --text: #ECEAE4;
    --muted: #9BA1A8;
    --danger: #FF5A4D;
    --ok: #3DDC84;
}

@keyframes stripeMove {
    from { background-position: 0 0; }
    to   { background-position: 160px 160px; }
}
@keyframes floatUp {
    0%   { transform: translateY(10vh) rotate(0deg); opacity: 0; }
    8%   { opacity: 0.45; }
    92%  { opacity: 0.45; }
    100% { transform: translateY(-110vh) rotate(25deg); opacity: 0; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseWarning {
    0%   { box-shadow: 0 0 0 0 rgba(255, 90, 77, 0.6); }
    70%  { box-shadow: 0 0 0 18px rgba(255, 90, 77, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 90, 77, 0); }
}
@keyframes glowSuccess {
    0%, 100% { box-shadow: 0 0 6px rgba(61, 220, 132, 0.25); }
    50%      { box-shadow: 0 0 20px rgba(61, 220, 132, 0.55); }
}
@keyframes tapeSlide {
    from { background-position: 0 0; }
    to   { background-position: 45px 0; }
}

html, body {
    background-color: var(--ink);
    background-image: repeating-linear-gradient(
        45deg,
        rgba(255, 200, 0, 0.05) 0 22px,
        transparent 22px 44px
    );
    animation: stripeMove 14s linear infinite;
    color: var(--text);
    font-family: 'Barlow', system-ui, sans-serif;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: transparent !important;
    color: var(--text);
}
[data-testid="stAppViewContainer"] > .main { position: relative; z-index: 1; }

.bg-float-layer {
    position: fixed;
    inset: 0;
    z-index: 0;
    overflow: hidden;
    pointer-events: none;
}
.float-icon {
    position: absolute;
    bottom: 0;
    font-size: 2rem;
    opacity: 0;
    animation-name: floatUp;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    filter: drop-shadow(0 0 4px rgba(0,0,0,0.4));
}
[data-testid="stSidebar"] { background: var(--concrete) !important; border-right: 1px solid var(--line); }
.block-container { padding-top: 1.5rem; max-width: 1200px; }

/* ---------- header ---------- */
.tape {
    height: 12px;
    border-radius: 2px;
    background: repeating-linear-gradient(-45deg, var(--hazard) 0 16px, var(--ink) 16px 32px);
    margin-bottom: 18px;
    animation: tapeSlide 1.6s linear infinite;
}
.brand { animation: fadeInUp 0.5s ease-out; display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
.brand-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 3rem!important;
    letter-spacing: 0.01em;
    line-height: 1;
    margin: 0;
}
.brand-sub { color: var(--muted); font-size: 1.05rem; margin: 0; }
.rule { border: 0; border-top: 1px solid var(--line); margin: 18px 0 22px; }

/* ---------- verdict ---------- */
.verdict {
    border-radius: 6px;
    padding: 18px 22px;
    border: 1px solid var(--line);
    border-left-width: 8px;
    background: var(--concrete);
    margin: 6px 0 18px;
    animation: fadeInUp 0.4s ease-out;
}
.verdict-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    line-height: 1.05;
    margin: 0;
}
.verdict-text { color: var(--muted); margin: 6px 0 0; font-size: 1rem; }
.verdict.bad { border-left-color: var(--danger); background: rgba(255, 90, 77, 0.08);
    animation: fadeInUp 0.4s ease-out, pulseWarning 1.8s ease-out infinite; }
.verdict.bad .verdict-title { color: var(--danger); }
.verdict.good { border-left-color: var(--ok); background: rgba(61, 220, 132, 0.07);
    animation: fadeInUp 0.4s ease-out, glowSuccess 2.4s ease-in-out infinite; }
.verdict.good .verdict-title { color: var(--ok); }

/* ---------- stats ---------- */
.stat {
    background: var(--concrete);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 14px 16px;
    height: 100%;
    animation: fadeInUp 0.5s ease-out;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.stat:hover { transform: translateY(-3px); border-color: #5a606a; }
.stat-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 2.3rem;
    line-height: 1;
}
.stat-label { color: var(--muted); font-size: 0.92rem; margin-top: 4px; }
.stat.alert .stat-value { color: var(--danger); }

/* ---------- chips ---------- */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 4px; }
.chip {
    border: 1px solid var(--danger);
    color: var(--danger);
    background: rgba(255, 90, 77, 0.08);
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 0.92rem;
    font-weight: 500;
    animation: fadeInUp 0.4s ease-out;
}

/* ---------- rate bar (video) ---------- */
.rate { margin: 4px 0 18px; }
.rate-head { display: flex; justify-content: space-between; color: var(--muted); font-size: 0.92rem; margin-bottom: 6px; }
.rate-track { height: 10px; border-radius: 6px; background: var(--steel); overflow: hidden; }
.rate-fill { height: 100%; background: var(--danger); }

/* ---------- misc ---------- */
.frame-caption { font-size: 0.9rem; color: var(--muted); margin: 4px 0 14px; }
.panel-label { font-weight: 600; margin-bottom: 6px; }
[data-testid="stImage"] img { border-radius: 6px; border: 1px solid var(--line); animation: fadeInUp 0.4s ease-out; }
.stButton > button[kind="primary"], .stDownloadButton > button {
    font-weight: 600;
    border-radius: 6px;
}
.stButton > button[kind="primary"] {
    background: var(--hazard);
    color: var(--ink);
    border: 0;
}
.stButton > button[kind="primary"]:hover { background: #ffd83a; color: var(--ink); }
button:focus-visible, [role="slider"]:focus-visible { outline: 3px solid var(--hazard) !important; outline-offset: 2px; }

/* ---------- uploader ---------- */
[data-testid="stFileUploader"] label p {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    letter-spacing: 0.01em;
    color: var(--text);
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--concrete) !important;
    border: 2px dashed rgba(255, 200, 0, 0.55) !important;
    border-radius: 10px !important;
    padding: 1.4rem 1.6rem !important;
    transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--hazard) !important;
    background: rgba(255, 200, 0, 0.05) !important;
    box-shadow: 0 0 22px rgba(255, 200, 0, 0.18);
}
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] button {
    background: transparent !important;
    color: var(--hazard) !important;
    border: 1.5px solid var(--hazard) !important;
    border-radius: 6px !important;
    font-weight: 600;
    transition: background 0.15s ease, color 0.15s ease;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--hazard) !important;
    color: var(--ink) !important;
}
[data-testid="stFileUploaderFile"] {
    background: var(--concrete);
    border: 1px solid var(--line);
    border-left: 4px solid var(--hazard);
    border-radius: 8px;
    padding: 6px 10px;
    margin-top: 8px;
    animation: fadeInUp 0.35s ease-out;
}


/* ---------- viewfinder dropzone (overrides earlier dropzone rules) ---------- */
@keyframes scanLine {
    0%   { top: 8%;  opacity: 0; }
    10%  { opacity: 1; }
    90%  { opacity: 1; }
    100% { top: 92%; opacity: 0; }
}
[data-testid="stFileUploaderDropzone"] {
    position: relative;
    overflow: hidden;
    min-height: 170px;
    justify-content: center;
    border: 1px solid var(--line) !important;
    background:
        linear-gradient(var(--hazard), var(--hazard)) top left / 34px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) top left / 3px 34px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) top right / 34px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) top right / 3px 34px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom left / 34px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom left / 3px 34px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom right / 34px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom right / 3px 34px no-repeat,
        var(--concrete) !important;
}
[data-testid="stFileUploaderDropzone"]::after {
    content: "";
    position: absolute;
    left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--hazard), transparent);
    box-shadow: 0 0 14px 2px rgba(255, 200, 0, 0.45);
    pointer-events: none;
    animation: scanLine 3.2s ease-in-out infinite;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > span:first-child { display: none; }
[data-testid="stFileUploaderDropzoneInstructions"] > div::before {
    content: "Drop your file here to scan it";
    display: block;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 600;
    font-size: 1.6rem;
    letter-spacing: 0.02em;
    text-align: center;
    color: #A9AEB5;
}
[data-testid="stFileUploaderDropzone"] {
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: flex !important;
    justify-content: center;
    width: 100%;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div { margin: 0 !important; padding: 0 !important; text-align: center; }
[data-testid="stFileUploaderDropzoneInstructions"] svg,
[data-testid="stFileUploaderDropzoneInstructions"] small { display: none !important; }

/* ---------- steps ---------- */
.steps { display: flex; gap: 10px; margin: 4px 0 16px; flex-wrap: wrap; }
.step {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 16px 8px 8px;
    border: 1px solid var(--line);
    border-radius: 999px;
    color: var(--muted);
    background: var(--concrete);
    font-weight: 500;
    transition: all 0.2s ease;
}
.step-n {
    width: 26px; height: 26px; border-radius: 50%;
    display: grid; place-items: center;
    background: var(--steel); color: var(--muted);
    font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 1.05rem;
}
.step.active { color: var(--ink); background: var(--hazard); border-color: var(--hazard); }
.step.active .step-n { background: var(--ink); color: var(--hazard); }
.step.done { color: var(--text); border-color: var(--ok); }
.step.done .step-n { background: var(--ok); color: var(--ink); }


/* ---------- run button: flat, compact, light sweep on hover ---------- */
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    position: relative;
    overflow: hidden;
    width: 100%;
    min-height: 3rem;
    padding: 0 1.2rem;
    margin-top: 0;
    border: 0;
    border-radius: 6px;
    background: var(--hazard);
    color: var(--ink);
    box-shadow: none;
    transition: transform 0.12s ease, background 0.15s ease;
}
.stButton > button[kind="primary"]::before,
[data-testid="stBaseButton-primary"]::before {
    content: "";
    position: absolute;
    top: 0; bottom: 0;
    left: -60%;
    width: 40%;
    background: linear-gradient(105deg, transparent, rgba(255, 255, 255, 0.55), transparent);
    transform: skewX(-20deg);
    transition: left 0.55s ease;
    pointer-events: none;
}
.stButton > button[kind="primary"]:hover::before,
[data-testid="stBaseButton-primary"]:hover::before { left: 130%; }
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover { background: #ffd83a; color: var(--ink); transform: translateY(-1px); }
.stButton > button[kind="primary"]:active,
[data-testid="stBaseButton-primary"]:active { transform: scale(0.98); }
.stButton > button[kind="primary"] p,
[data-testid="stBaseButton-primary"] p {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em;
    margin: 0;
    color: var(--ink);
}

/* ---------- sidebar ---------- */
@keyframes dotPulse {
    0%   { box-shadow: 0 0 0 0 rgba(61, 220, 132, 0.6); }
    70%  { box-shadow: 0 0 0 8px rgba(61, 220, 132, 0); }
    100% { box-shadow: 0 0 0 0 rgba(61, 220, 132, 0); }
}
.side-tape {
    height: 8px; border-radius: 2px; margin-bottom: 14px;
    background: repeating-linear-gradient(-45deg, var(--hazard) 0 10px, var(--ink) 10px 20px);
}
.side-title { font-family: 'Barlow Condensed', sans-serif; font-size: 1.9rem; font-weight: 700; margin: 0; line-height: 1.1; }
.side-sub { color: var(--muted); font-size: 0.92rem; margin: 2px 0 6px; }
.side-group {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 600; font-size: 1.2rem; color: var(--hazard);
    margin: 22px 0 8px; padding-bottom: 5px; border-bottom: 1px solid var(--line);
}
[data-testid="stSidebar"] [role="radiogroup"] { gap: 8px; width: 100%; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    flex: 1; justify-content: center; cursor: pointer;
    padding: 9px 10px; border: 1px solid var(--line); border-radius: 6px;
    background: var(--steel);
    transition: background 0.15s ease, border-color 0.15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-of-type:not(:last-of-type) { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label p { margin: 0; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { border-color: var(--hazard); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--hazard); border-color: var(--hazard); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: var(--ink); font-weight: 700; }
[data-testid="stSidebar"] [data-testid="stSlider"] { padding-bottom: 6px; }
.api-pill {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; border-radius: 8px;
    border: 1px solid var(--line); background: var(--steel); font-weight: 500;
}
.api-dot { width: 10px; height: 10px; border-radius: 50%; }
.api-pill.ok .api-dot { background: var(--ok); animation: dotPulse 1.8s ease-out infinite; }
.api-pill.off .api-dot { background: var(--danger); }
.api-pill.off { border-color: var(--danger); color: var(--danger); }
.spec { border: 1px solid var(--line); border-radius: 8px; background: var(--steel); padding: 2px 14px; margin-top: 10px; }
.spec-row { display: flex; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid var(--line); font-size: 0.92rem; }
.spec-row:last-child { border-bottom: 0; }
.spec-row span { color: var(--muted); }

/* ---------- slider labels + help tooltips ---------- */
.slider-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    margin-bottom: -4px;
}

.slider-label-text {
    font-size: 15px;
    font-weight: 500;
    color: var(--text);
}

.help-icon {
    position: relative;
    width: 18px;
    height: 18px;
    border: 1px solid var(--muted);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    cursor: help;
    box-sizing: border-box;
}

.help-icon:hover {
    color: var(--hazard);
    border-color: var(--hazard);
}

.help-tooltip {
    position: absolute;
    right: 0;
    top: 25px;
    width: 220px;
    padding: 9px 11px;
    border-radius: 6px;
    background: #14161A;
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 12.5px;
    line-height: 1.4;
    text-align: left;

    opacity: 0;
    visibility: hidden;
    transform: translateY(-3px);
    transition: opacity 0.15s ease, transform 0.15s ease;

    z-index: 9999;
    pointer-events: none;
}

.help-icon:hover .help-tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
}

/* Make sure the tooltip is not clipped inside the sidebar */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebar"] [data-testid="stElementContainer"] {
    overflow: visible !important;
}
            
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
""", unsafe_allow_html=True)


FLOAT_ICONS = [
    (4, 22, 0, "🦺"), (14, 26, 4, "🚧"), (24, 20, 9, "🔧"), (34, 28, 2, "👷"),
    (46, 24, 12, "🏗️"), (58, 30, 6, "⚠️"), (68, 21, 15, "🔩"), (78, 27, 3, "🦺"),
    (88, 23, 10, "🚧"), (94, 25, 7, "⚠️"),
]
floating_html = "".join(
    f'<span class="float-icon" style="left:{left}%; animation-duration:{dur}s; '
    f'animation-delay:-{delay}s;">{icon}</span>'
    for left, dur, delay, icon in FLOAT_ICONS
)
st.markdown(f'<div class="bg-float-layer">{floating_html}</div>', unsafe_allow_html=True)


# ---------- helpers ----------
def esc(value):
    return html.escape(str(value))


def stat(label, value, alert=False):
    cls = "stat alert" if alert else "stat"
    st.markdown(
        f'<div class="{cls}"><div class="stat-value">{esc(value)}</div>'
        f'<div class="stat-label">{esc(label)}</div></div>',
        unsafe_allow_html=True,
    )


def verdict(is_violation, detail):
    cls = "bad" if is_violation else "good"
    title = "Violation found" if is_violation else "Compliant"
    st.markdown(
        f'<div class="verdict {cls}"><p class="verdict-title">{title}</p>'
        f'<p class="verdict-text">{esc(detail)}</p></div>',
        unsafe_allow_html=True,
    )


def chips(items):
    if items:
        body = "".join(f'<span class="chip">{esc(i)}</span>' for i in items)
        st.markdown(f'<div class="chips">{body}</div>', unsafe_allow_html=True)


def image_ext(data):
    return "png" if data[:4] == b"\x89PNG" else "jpg"


def call_api(endpoint, uploaded_file, params, timeout):
    """POST the file to the API. Returns (json, error_message)."""
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    try:
        response = requests.post(f"{API_URL}{endpoint}", files=files, params=params, timeout=timeout)
    except requests.exceptions.ConnectionError:
        return None, f"Can't reach the API at {API_URL}. Start it with `uvicorn main:app` and try again."
    except requests.exceptions.Timeout:
        return None, "The API took too long to respond. Try a shorter video or a higher frame skip."
    if response.status_code != 200:
        return None, f"The API returned an error ({response.status_code}): {response.text}"
    return response.json(), None


def api_online():
    try:
        requests.get(API_URL, timeout=1.5)
        return True
    except requests.exceptions.RequestException:
        return False


def file_key(f):
    return f"{f.name}:{f.size}"


def upload_row(label, types, key):
    """Uploader on its own row when empty; shrinks with the Run button beside it once a file is set."""
    has_file = st.session_state.get(key) is not None
    spec = [3, 1] if has_file else [1, 0.001]
    try:
        c_up, c_btn = st.columns(spec, vertical_alignment="bottom")
    except TypeError:
        c_up, c_btn = st.columns(spec)
    with c_up:
        uploaded = st.file_uploader(label, type=types, key=key)
    run = False
    if uploaded is not None:
        with c_btn:
            run = st.button("Run detection", type="primary", key=f"run_{key}")
    return uploaded, run


def api_pill(online):
    cls, text = ("ok", "API connected") if online else ("off", "API offline")
    st.markdown(f'<div class="api-pill {cls}"><span class="api-dot"></span>{text}</div>', unsafe_allow_html=True)


def spec_card(rows):
    body = "".join(f'<div class="spec-row"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k, v in rows)
    st.markdown(f'<div class="spec">{body}</div>', unsafe_allow_html=True)


def render_steps(slot, uploaded, result_key):
    if uploaded is None:
        active = 1
    else:
        saved = st.session_state.get(result_key)
        active = 4 if saved and saved[0] == file_key(uploaded) else 2
    labels = ["Upload", "Run detection", "Review results"]
    parts = []
    for i, label in enumerate(labels, start=1):
        cls = "done" if active > i else ("active" if active == i else "")
        mark = "✓" if active > i else i
        parts.append(f'<div class="step {cls}"><span class="step-n">{mark}</span>{label}</div>')
    slot.markdown(f'<div class="steps">{"".join(parts)}</div>', unsafe_allow_html=True)


EMPTY_DROPZONE_CSS = """
<style>
[data-testid="stFileUploaderDropzone"] button { display: none !important; }
[data-testid="stFileUploaderDropzone"] { cursor: pointer; }
[data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) { gap: 0 !important; }
</style>
"""


COMPACT_DROPZONE_CSS = """
<style>
[data-testid="stFileUploaderDropzone"] {
    min-height: 0 !important;
    padding: 12px 16px !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    background:
        linear-gradient(var(--hazard), var(--hazard)) top left / 20px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) top left / 3px 20px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) top right / 20px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) top right / 3px 20px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom left / 20px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom left / 3px 20px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom right / 20px 3px no-repeat,
        linear-gradient(var(--hazard), var(--hazard)) bottom right / 3px 20px no-repeat,
        var(--concrete) !important;
}
[data-testid="stFileUploaderDropzone"]::after { display: none; }
[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
[data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) { gap: 1rem !important; }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] { min-height: 4.1rem; }
</style>
"""


# ---------- custom slider (native <input type="range"> inside a tiny component) ----------
# Streamlit's built-in slider was drawing its handle in the wrong place on some setups,
# so the app ships its own. The component file is written next to this script on first run.

 
# ---------- header ---------- 
st.markdown('<div class="tape"></div>', unsafe_allow_html=True) 
st.markdown( 
    '<div class="brand"><p class="brand-name">🦺 VisionGuard</p>' 
    '<p class="brand-sub">PPE detection for construction site safety</p></div>' 
    '<hr class="rule">', 
    unsafe_allow_html=True, 
) 
 
# ---------- sidebar ----------
if "conf" not in st.session_state:
    st.session_state["conf"] = 0.25

if "frame_skip" not in st.session_state:
    st.session_state["frame_skip"] = 10


@st.fragment
def settings_fragment():

    with st.sidebar:

        st.markdown(
            '<p class="side-title">Settings</p>'
            '<p class="side-sub">Choose what to scan and how strict to be.</p>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p class="side-group">Media</p>',
            unsafe_allow_html=True
        )

        st.radio(
            "Media type",
            ["Image", "Video"],
            horizontal=True,
            label_visibility="collapsed",
            key="media_type"
        )

        st.markdown(
            '<p class="side-group">Detection</p>',
            unsafe_allow_html=True
        )

        st.html(
            """
            <div class="slider-label-row">
                <span class="slider-label-text">Confidence threshold</span>

                <span class="help-icon">
                    ?
                    <span class="help-tooltip">
                        Lower finds more items but may add false alarms.
                        Higher is stricter.
                    </span>
                </span>
            </div>
            """
        )

        st.slider(
            "Confidence threshold",
            min_value=0.05,
            max_value=0.95,
            value=0.25,
            step=0.05,
            key="conf",
            label_visibility="collapsed"
        )
    

        if st.session_state["media_type"] == "Video":

            st.html(
                """
                <div class="slider-label-row">
                    <span class="slider-label-text">Frame skip</span>

                    <span class="help-icon">
                        ?
                        <span class="help-tooltip">
                            Higher is faster but can miss short violations.
                        </span>
                    </span>
                </div>
                """
            )

            st.slider(
                "Frame skip",
                min_value=1,
                max_value=30,
                value=10,
                step=1,
                key="frame_skip",
                label_visibility="collapsed"
            )

        st.markdown(
            '<p class="side-group">System</p>',
            unsafe_allow_html=True
        )

        api_pill(api_online())

        spec_card([
            ("Model", "yolo26s_exp1"),
            ("Input size", "640 px")
        ])


settings_fragment()


# Get the current settings
media_type = st.session_state["media_type"]
conf = st.session_state["conf"]
frame_skip = st.session_state["frame_skip"]

# ============================================================ 
# IMAGE MODE 
# ============================================================ 
if media_type == "Image": 
    step_slot = st.empty() 
    uploaded_file, run_clicked = upload_row("Upload a site photo", ["jpg", "jpeg", "png"], "uploader_image") 
 
    if uploaded_file is not None: 
        st.markdown(COMPACT_DROPZONE_CSS, unsafe_allow_html=True) 
 
    if uploaded_file is None: 
        st.markdown(EMPTY_DROPZONE_CSS, unsafe_allow_html=True) 
    else: 
        key = file_key(uploaded_file) 
        if run_clicked: 
            with st.spinner("Analyzing image..."): 
                data, error = call_api("/predict/image", uploaded_file, {"conf": conf}, timeout=120) 
            if error: 
                st.error(error) 
                st.session_state.pop("image_result", None) 
            else: 
                st.session_state["image_result"] = (key, data) 
 
        saved = st.session_state.get("image_result") 
        if saved and saved[0] == key: 
            result = saved[1] 
            summary = result["compliance"] 
            is_violation = summary["status"] == "VIOLATION" 
            annotated = base64.b64decode(result["annotated_image_base64"]) 
 
            verdict( 
                is_violation, 
                f"{summary['violations_detected']} violation(s) among {summary['persons_detected']} person(s) detected." 
                if is_violation 
                else f"No violations among {summary['persons_detected']} person(s) detected.", 
            ) 
 
            s1, s2, s3, s4 = st.columns(4) 
            with s1: 
                stat("Persons", summary["persons_detected"]) 
            with s2: 
                stat("Compliant items", summary["compliant_detections"]) 
            with s3: 
                stat("Violations", summary["violations_detected"], alert=summary["violations_detected"] > 0) 
            with s4: 
                stat("Processing time (ms)", result["processing_time_ms"]) 
 
            chips(summary["violation_types"]) 
            st.write("") 
 
            tab_detected, tab_original, tab_side = st.tabs(["Detected", "Original", "Side by side"]) 
            with tab_detected: 
                st.image(annotated, use_container_width=True) 
            with tab_original: 
                st.image(uploaded_file, use_container_width=True) 
            with tab_side: 
                c1, c2 = st.columns(2) 
                with c1: 
                    st.markdown('<div class="panel-label">Original</div>', unsafe_allow_html=True) 
                    st.image(uploaded_file, use_container_width=True) 
                with c2: 
                    st.markdown('<div class="panel-label">Detected</div>', unsafe_allow_html=True) 
                    st.image(annotated, use_container_width=True) 
 
            st.download_button( 
                "Download annotated image", 
                data=annotated, 
                file_name=f"visionguard_result.{image_ext(annotated)}", 
                mime=f"image/{'png' if image_ext(annotated) == 'png' else 'jpeg'}", 
            ) 
            st.caption(f"Confidence threshold used: {result['confidence_threshold']}") 
        else: 
            st.image(uploaded_file, use_container_width=True) 
 
    render_steps(step_slot, uploaded_file, "image_result") 
 
# ============================================================ 
# VIDEO MODE 
# ============================================================ 
else: 
    step_slot = st.empty() 
    uploaded_file, run_clicked = upload_row("Upload a short site video", ["mp4", "avi", "mov"], "uploader_video") 
 
    if uploaded_file is not None: 
        st.markdown(COMPACT_DROPZONE_CSS, unsafe_allow_html=True) 
 
    if uploaded_file is None: 
        st.markdown(EMPTY_DROPZONE_CSS, unsafe_allow_html=True) 
    else: 
        key = file_key(uploaded_file) 
        if run_clicked: 
            with st.spinner("Analyzing video. This can take a while..."): 
                data, error = call_api( 
                    "/predict/video", uploaded_file, 
                    {"conf": conf, "frame_skip": frame_skip}, timeout=900, 
                ) 
            if error: 
                st.error(error) 
                st.session_state.pop("video_result", None) 
            else: 
                st.session_state["video_result"] = (key, data) 
 
        saved = st.session_state.get("video_result") 
        if saved and saved[0] == key: 
            result = saved[1] 
            violated = result["frames_with_violation"] 
            total = result["frames_analyzed"] 
            rate = (violated / total * 100) if total else 0 
            violation_frames = result.get("violation_frames", []) 
 
            verdict( 
                violated > 0, 
                f"Violations appear in {violated} of {total} analyzed frames." 
                if violated > 0 
                else f"No violations in {total} analyzed frames.", 
            ) 
 
            s1, s2, s3, s4 = st.columns(4) 
            with s1: 
                stat("Frames analyzed", total) 
            with s2: 
                stat("Frames with violation", violated, alert=violated > 0) 
            with s3: 
                stat("Confidence threshold", result["confidence_threshold"]) 
            with s4: 
                stat("Processing time (ms)", result["processing_time_ms"]) 
 
            st.write("") 
            st.markdown( 
                f'<div class="rate"><div class="rate-head"><span>Share of frames with a violation</span>' 
                f'<span>{rate:.0f}%</span></div>' 
                f'<div class="rate-track"><div class="rate-fill" style="width:{rate:.1f}%"></div></div></div>', 
                unsafe_allow_html=True, 
            ) 
 
            all_types = sorted({t for vf in violation_frames for t in vf["compliance"]["violation_types"]}) 
            chips(all_types) 
 
            if violation_frames: 
                st.subheader(f"Violation frames ({len(violation_frames)})") 
                st.caption("Each image is a frame where a violation was detected.") 
                cols = st.columns(3) 
                for i, vf in enumerate(violation_frames): 
                    with cols[i % 3]: 
                        st.image(base64.b64decode(vf["annotated_image_base64"]), use_container_width=True) 
                        ts = vf["timestamp_sec"] 
                        ts_label = f"{ts}s" if ts is not None else f"Frame {vf['frame_index']}" 
                        types = ", ".join(vf["compliance"]["violation_types"]) 
                        st.markdown( 
                            f'<p class="frame-caption"><b>{esc(ts_label)}</b> · {esc(types)}</p>', 
                            unsafe_allow_html=True, 
                        ) 
            else: 
                st.success("No violation frames found in the analyzed sample.") 
 
            with st.expander("Original video"): 
                st.video(uploaded_file) 
        else: 
            st.video(uploaded_file) 
 
    render_steps(step_slot, uploaded_file, "video_result") 
 
 
