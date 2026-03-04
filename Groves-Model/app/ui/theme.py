"""Lakeshore Management — Design tokens and global CSS injection.

Import and call inject_theme() once at the top of every page to apply
the institutional real-estate dashboard look.

Usage:
    from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT
    inject_theme()
"""

import streamlit as st

# ── Design Tokens ─────────────────────────────────────────────────

COLORS = {
    "primary":    "#0B1F3B",   # Navy
    "accent":     "#2F8F9D",   # Lake teal
    "bg":         "#F6F8FB",   # Page background
    "surface":    "#FFFFFF",   # Card / container
    "text":       "#1F2937",   # Body text
    "muted":      "#6B7280",   # Secondary text
    "border":     "#E5E7EB",   # Dividers / borders
    "success":    "#16A34A",
    "warn":       "#F59E0B",
    "error":      "#DC2626",
    "row_alt":    "#F9FAFB",   # Alternating table row
    "kpi_bg":     "#F0FDFA",   # Teal-tinted KPI highlight
    "subtotal":   "#E8EAED",   # Subtotal row background
    "note_bg":    "#E0F2FE",   # Accent-tinted highlight row
    "grid":       "#F3F4F6",   # Chart gridlines
}

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}
RADIUS = {"card": 12, "input": 10, "pill": 999}

# Plotly defaults — merge into any fig.update_layout() call
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, system-ui, sans-serif", color=COLORS["text"], size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=36, b=0),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        font=dict(size=11, color=COLORS["muted"]),
    ),
    xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["border"]),
    yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["border"]),
)

PLOTLY_COLORS = [
    COLORS["primary"], COLORS["accent"], COLORS["success"],
    "#6366F1", COLORS["warn"], COLORS["error"], "#8B5CF6", "#EC4899",
]

# Heatmap / continuous colorscale — teal-to-navy gradient
HEATMAP_COLORSCALE = [
    [0.0, COLORS["kpi_bg"]],
    [0.25, "#99F6E4"],
    [0.5, "#2DD4BF"],
    [0.75, COLORS["accent"]],
    [1.0, COLORS["primary"]],
]


# ── Formatting helpers ────────────────────────────────────────────

def fmt_currency(v, decimals=0):
    if v < 0:
        return f"(${abs(v):,.{decimals}f})"
    return f"${v:,.{decimals}f}"


def fmt_pct(v, decimals=1):
    return f"{v * 100:,.{decimals}f}%"


def fmt_multiple(v):
    return f"{v:.2f}x"


# ── CSS Injection ─────────────────────────────────────────────────

_CSS = """
<style>
/* ── Import Inter font ──────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Root variables ─────────────────────────────────────────── */
:root {
    --c-primary:  %(primary)s;
    --c-accent:   %(accent)s;
    --c-bg:       %(bg)s;
    --c-surface:  %(surface)s;
    --c-text:     %(text)s;
    --c-muted:    %(muted)s;
    --c-border:   %(border)s;
    --c-success:  %(success)s;
    --c-warn:     %(warn)s;
    --c-error:    %(error)s;
    --radius:     12px;
    --radius-sm:  10px;
    --shadow-sm:  0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md:  0 4px 12px rgba(0,0,0,.06);
}

/* ── Global typography ──────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* ── Main area ──────────────────────────────────────────────── */
.stApp > header { background: transparent !important; }
section[data-testid="stSidebar"] > div:first-child {
    background: var(--c-primary);
    padding-top: 2rem;
}

/* Sidebar text → white */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] span {
    color: rgba(255,255,255,.85) !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a {
    color: rgba(255,255,255,.95) !important;
}

/* Nav links in sidebar */
section[data-testid="stSidebar"] nav a {
    color: rgba(255,255,255,.7) !important;
    border-radius: 8px;
    transition: background .15s;
}
section[data-testid="stSidebar"] nav a:hover {
    background: rgba(255,255,255,.08) !important;
    color: #fff !important;
}
section[data-testid="stSidebar"] nav a[aria-current="page"] {
    background: rgba(47,143,157,.25) !important;
    color: #fff !important;
    font-weight: 600;
}

/* ── KPI Metric cards ───────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow-sm);
}
[data-testid="stMetric"] label {
    color: var(--c-muted) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--c-text) !important;
    font-weight: 700 !important;
    font-size: 1.5rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

/* ── Buttons ────────────────────────────────────────────────── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
    transition: all .15s ease;
    border: 1px solid var(--c-border) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: var(--c-accent) !important;
    color: white !important;
    border-color: var(--c-accent) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    background: #267a86 !important;
    border-color: #267a86 !important;
}

/* ── Inputs ─────────────────────────────────────────────────── */
.stNumberInput > div > div > input,
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--c-border) !important;
}
.stNumberInput label,
.stTextInput label,
.stSelectbox label,
.stMultiSelect label {
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: var(--c-muted) !important;
}

/* ── Tabs ───────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    border-bottom: 2px solid var(--c-border);
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 24px;
    font-weight: 500;
    font-size: 0.85rem;
    color: var(--c-muted);
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
}
.stTabs [aria-selected="true"] {
    color: var(--c-accent) !important;
    border-bottom-color: var(--c-accent) !important;
    font-weight: 600 !important;
}

/* ── Expander ───────────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: var(--c-text) !important;
    border-radius: var(--radius) !important;
}

/* ── Dividers ───────────────────────────────────────────────── */
hr {
    border-color: var(--c-border) !important;
    opacity: 0.5;
}

/* ── Page Links (Navigation cards) ────────────────────────────── */
[data-testid="stPageLink-NavLink"] {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: var(--radius) !important;
    padding: 14px 20px !important;
    box-shadow: var(--shadow-sm);
    transition: all .15s ease;
}
[data-testid="stPageLink-NavLink"]:hover {
    border-color: var(--c-accent) !important;
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}
[data-testid="stPageLink-NavLink"] p {
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    color: var(--c-text) !important;
}

/* ── Download Button ──────────────────────────────────────────── */
.stDownloadButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
    transition: all .15s ease;
    border: 1px solid var(--c-accent) !important;
    color: var(--c-accent) !important;
}
.stDownloadButton > button:hover {
    background: var(--c-accent) !important;
    color: white !important;
}

/* ── Alerts ──────────────────────────────────────────────────── */
.stAlert > div {
    border-radius: var(--radius-sm) !important;
    font-size: 0.85rem !important;
}

/* ── Captions ────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {
    font-size: 0.75rem !important;
    color: var(--c-muted) !important;
}

/* ── File Uploader ───────────────────────────────────────────── */
[data-testid="stFileUploader"] section {
    border-radius: var(--radius) !important;
    border: 1px dashed var(--c-border) !important;
    padding: 16px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--c-accent) !important;
}

/* ── Hide Streamlit branding ────────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""" % COLORS


def inject_theme():
    """Call once at the top of each page to inject the global CSS."""
    if not st.session_state.get("_theme_injected_this_run"):
        st.markdown(_CSS, unsafe_allow_html=True)
        st.session_state["_theme_injected_this_run"] = True
    else:
        st.markdown(_CSS, unsafe_allow_html=True)
