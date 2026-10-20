"""
Ambulance Response Analysis dashboard.

Run from the project folder with:
    streamlit run dashboard/app.py

Data files are created by notebooks/04_prepare_dashboard_data.ipynb.
Illustrations (hero banner and sidebar skyline) are original SVG drawings in dashboard/assets.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from plotly.colors import hex_to_rgb, sample_colorscale

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
ASSET_DIR = APP_DIR / "assets"
GITHUB_URL = ""  # paste your GitHub repository link here to show it in the footer

TARGETS = {"Category 1": 7, "Category 2": 18}  # national mean response targets (minutes)
CATEGORY_HELP = {
    "Category 1": "life-threatening",
    "Category 2": "urgent",
}
FIRST_FULL_MONTH = pd.Timestamp("2018-04-01")  # every trust reports from April 2018 onwards

# Colours
NAVY = "#0b1f4d"
BLUE = "#1f5fcf"
BLUE_LIGHT = "#e8f0fc"
RED = "#d93a3a"
RED_LIGHT = "#fdeeee"
GREEN = "#1e9e3a"
PURPLE = "#8b3fd1"
INK = "#1a2233"
INK_2 = "#55607a"
MUTED = "#8a93a6"
GRID = "#e6eaf1"
BORDER = "#e1e6ef"
FONT = "Inter, 'Segoe UI', sans-serif"

st.set_page_config(page_title="Ambulance Response Analysis", page_icon="🚑", layout="wide")


# ---------------------------------------------------------------------------
# Icons (simple line icons drawn as inline SVG)
# ---------------------------------------------------------------------------
ICON_PATHS = {
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>'
              '<path d="M16 8l5-5M18 3h3v3"/>',
    "trend": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "trophy": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>'
              '<path d="M4 22h16"/><path d="M10 14.7V17c0 .6-.5 1-1 1.2C7.9 18.8 7 20.2 7 22"/>'
              '<path d="M14 14.7V17c0 .6.5 1 1 1.2 1.1.6 2 2 2 3.8"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    "alert": '<path d="M21.7 18l-8-14a2 2 0 0 0-3.5 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3"/>'
             '<path d="M12 9v4"/><path d="M12 17h.01"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "line": '<path d="M3 3v18h18"/><polyline points="7 15 11 10 14 13 20 6"/>',
    "bars": '<path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6"/><rect x="12" y="8" width="3" height="10"/>'
            '<rect x="17" y="5" width="3" height="13"/>',
    "people": '<circle cx="8" cy="7" r="3"/><circle cx="16" cy="7" r="3"/><path d="M2 21v-2a5 5 0 0 1 10 0v2"/>'
              '<path d="M12 21v-2a5 5 0 0 1 10 0v2"/>',
    "network": '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="17" r="2.5"/><circle cx="19" cy="17" r="2.5"/>'
               '<path d="M12 7.5v4M12 11.5L6.5 15M12 11.5l5.5 3.5"/>',
    "tree": '<path d="M12 22v-5"/><path d="M12 2 6 10h3l-4 6h14l-4-6h3z"/>',
    "bulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
            '<path d="M9 18h6"/><path d="M10 22h4"/>',
    "heart": '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2'
             'A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z"/>',
    "hospital": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M12 7v4M10 9h4"/>'
                '<path d="M8 15h2M14 15h2M8 18h2M14 18h2"/>',
    "pointer": '<path d="M9 3v10l2.5-2.5L14 16l2-1-2.5-5H17z"/><path d="M4 7h2M4 3l1.5 1.5M8 1v2"/>',
    "code": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "pulse": '<polyline points="2 12 6 12 9 4 15 20 18 12 22 12"/>',
}


def icon(name, color, size=24, stroke=2, fill="none"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="{fill}" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round" style="flex-shrink:0">{ICON_PATHS[name]}</svg>')


def html(markup):
    """Render HTML. Collapsed onto one line so Streamlit never mistakes indented HTML for a code block."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Dancing+Script:wght@500;600;700&display=swap');
html, body, .stApp, p, li, label, input, textarea, td, th, button {{ font-family: {FONT}; }}
[data-testid="stIconMaterial"], span[class*="material-symbols"] {{ font-family: "Material Symbols Rounded" !important; }}
.stApp {{ background: #f3f6fb; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding: 1.6rem 2rem 1.5rem 2rem; max-width: 1560px; }}
h1, h2, h3 {{ font-family: {FONT}; }}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0a2350 0%, #0c2c63 55%, #0a2350 100%);
  min-width: 290px !important; max-width: 290px !important;
}}
section[data-testid="stSidebar"] > div {{ padding-top: 0.6rem; }}
section[data-testid="stSidebar"] {{ color: #ffffff; }}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .stMarkdown *,
section[data-testid="stSidebar"] button, section[data-testid="stSidebar"] button * {{ color: #ffffff; }}
[data-testid="stSidebarCollapseButton"] * {{ color: #ffffff; }}
section[data-testid="stSidebar"] label p {{ color: #ffffff !important; font-size: 0.92rem; font-weight: 500; }}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] div[data-baseweb="input"],
section[data-testid="stSidebar"] div[data-baseweb="input"] > div {{
  background: #ffffff !important; border-radius: 8px; border: none;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] div[data-baseweb="input"] input {{ font-size: 0.82rem; color: {INK} !important; -webkit-text-fill-color: {INK} !important; opacity: 1 !important; }}
section[data-testid="stSidebar"] div[data-baseweb="select"] svg {{ fill: {INK_2} !important; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.15); margin: 0.8rem 0; }}
.nav-btn button, [class*="st-key-nav_"] button {{
  width: 100%; justify-content: flex-start; background: transparent; border: none;
  padding: 0.65rem 0.9rem; border-radius: 10px; font-size: 0.95rem; text-align: left;
}}
[class*="st-key-nav_"] button p {{ font-size: 0.95rem; text-align: left; line-height: 1.3; }}
[class*="st-key-nav_"] button > div {{ justify-content: flex-start; gap: 0.7rem; width: 100%; }}
[class*="st-key-nav_"] button:hover {{ background: rgba(255,255,255,0.08); color: #fff; }}
[class*="st-key-nav_"] button:focus:not(:active) {{ color: #fff; border: none; }}
[class*="st-key-nav_"] {{ margin-bottom: -0.6rem; }}
.st-key-reset button {{
  width: 100%; background: #e8eef8; color: {NAVY} !important; border: none; border-radius: 8px; font-weight: 500;
}}
.st-key-reset button p, .st-key-reset button span {{ color: {NAVY} !important; }}
.st-key-reset button:hover {{ background: #ffffff; }}
.sb-brand {{ display: flex; gap: 0.7rem; align-items: center; padding: 0.4rem 0.4rem 1rem 0.4rem; }}
.sb-brand .t {{ font-weight: 700; font-size: 1.08rem; line-height: 1.25; }}
.sb-brand .s {{ font-size: 0.85rem; opacity: 0.85; margin-top: 0.15rem; }}
.sb-heading {{ font-size: 0.8rem; font-weight: 700; letter-spacing: 0.06em; margin: 0.2rem 0 0.4rem 0; }}
.sb-target {{
  display: flex; gap: 0.8rem; align-items: center; border: 1px solid rgba(255,255,255,0.25);
  border-radius: 10px; padding: 0.9rem; margin-top: 1rem; background: rgba(255,255,255,0.04);
}}
.sb-target .v {{ font-size: 1.1rem; font-weight: 700; }}
.sb-target .l, .sb-target .h {{ font-size: 0.85rem; }}
.sb-art {{ margin: 1.2rem -1.5rem -1rem -1.5rem; position: relative; }}
.sb-art img {{
  width: 100%; height: 340px; object-fit: cover; object-position: 60% 35%; display: block;
  -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 30%);
  mask-image: linear-gradient(180deg, transparent 0%, #000 30%);
}}
.sb-art .script {{
  position: absolute; left: 1.2rem; bottom: 1.6rem; font-family: 'Dancing Script', 'Segoe Script', 'Brush Script MT', cursive;
  font-weight: 600; font-size: 1.7rem; line-height: 1.1; transform: rotate(-7deg); color: #fff;
  text-shadow: 0 2px 10px rgba(5,15,45,0.8);
}}

/* ---- Hero ---- */
.hero {{ position: relative; min-height: 158px; margin-bottom: 0.9rem; }}
.hero .art {{
  position: absolute; right: -2rem; top: -1.6rem; height: 196px; width: 60%; z-index: 0;
  -webkit-mask-image: linear-gradient(90deg, transparent 0%, #000 28%);
  mask-image: linear-gradient(90deg, transparent 0%, #000 28%);
}}
.hero .art img {{ width: 100%; height: 100%; object-fit: cover; object-position: 78% 62%; }}
.hero .script {{
  position: absolute; right: 27%; top: -1.35rem; z-index: 2; color: #fff; text-align: right;
  font-family: 'Dancing Script', 'Segoe Script', 'Brush Script MT', cursive; font-weight: 600;
  font-size: 1.45rem; line-height: 1.12; letter-spacing: 0.01em; transform: rotate(-5deg);
  text-shadow: 0 2px 10px rgba(5,15,45,0.65);
}}
.hero .text {{ position: relative; z-index: 1; max-width: 58%; }}
.hero .eyebrow {{ font-size: 0.76rem; font-weight: 600; letter-spacing: 0.04em; color: {INK_2}; text-transform: uppercase; }}
.hero h1 {{ font-size: 2.15rem; font-weight: 800; color: {NAVY}; line-height: 1.12; margin: 0.35rem 0 0.5rem 0; padding: 0; }}
.hero p {{ color: {INK_2}; font-size: 1rem; margin: 0; max-width: 600px; }}
.hero p b {{ color: {INK}; }}
@media (max-width: 900px) {{ .hero .art, .hero .script {{ display: none; }} .hero .text {{ max-width: 100%; }} }}

/* ---- Cards ---- */
.kpi {{
  display: flex; gap: 0.9rem; align-items: flex-start; background: #fff; border: 1px solid {BORDER};
  border-radius: 10px; padding: 1rem 1.1rem; height: 100%; min-height: 164px; box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}}
@media (max-width: 900px) {{ .kpi {{ min-height: auto; }} }}
.kpi.red {{ background: {RED_LIGHT}; border-color: #f6d4d4; }}
.kpi .l {{ font-size: 0.88rem; font-weight: 600; color: {INK}; line-height: 1.25; }}
.kpi .n {{ font-size: 1.05rem; font-weight: 700; color: {INK}; margin-top: 0.15rem; }}
.kpi .v {{ font-size: 2rem; font-weight: 800; color: {NAVY}; line-height: 1.15; margin-top: 0.1rem; }}
.kpi .s {{ font-size: 0.86rem; color: {INK_2}; }}
.kpi .s.red {{ color: {RED}; font-weight: 600; }}
div[class*="st-key-card_"] {{
  background: #fff; border: 1px solid {BORDER}; border-radius: 10px; padding: 1rem 1.1rem 0.9rem 1.1rem;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}}
.ctitle {{ font-size: 1.08rem; font-weight: 700; color: {NAVY}; margin: 0; }}
.csub {{ font-size: 0.86rem; color: {INK_2}; margin: 0.1rem 0 0.2rem 0; }}
.hint {{ display: flex; gap: 0.35rem; align-items: flex-start; font-size: 0.74rem; color: {INK_2}; line-height: 1.25; }}

/* Segmented control (trend view) */
[class*="st-key-trend_view"] button {{ min-width: 82px; font-size: 0.82rem; }}
[class*="st-key-trend_view"] button[aria-checked="true"],
[class*="st-key-trend_view"] button[kind="segmented_controlActive"] {{ background: {NAVY} !important; border-color: {NAVY} !important; }}
[class*="st-key-trend_view"] button[aria-checked="true"] *,
[class*="st-key-trend_view"] button[kind="segmented_controlActive"] * {{ color: #fff !important; }}

/* Factors */
.factor-head {{ display: flex; gap: 0.75rem; align-items: flex-start; min-height: 58px; }}
.factor-head .t {{ font-weight: 700; color: {NAVY}; font-size: 0.98rem; }}
.factor-head .d {{ font-size: 0.84rem; color: {INK_2}; line-height: 1.3; }}

/* Findings */
.finding {{ display: flex; gap: 0.8rem; margin: 0.65rem 0 0.95rem 0; }}
.finding .num {{
  flex: 0 0 2rem; height: 2rem; border-radius: 50%; background: #e7eef9; color: {NAVY};
  font-weight: 700; display: flex; align-items: center; justify-content: center;
}}
.finding .t {{ font-weight: 700; color: {BLUE}; font-size: 0.92rem; line-height: 1.25; }}
.finding .b {{ font-size: 0.86rem; color: {INK_2}; line-height: 1.35; }}

/* Why it matters strip */
.why {{ display: flex; gap: 1rem; align-items: stretch; margin-top: 1rem; flex-wrap: wrap; }}
.why .main {{
  flex: 1 1 520px; display: flex; gap: 1.2rem; align-items: center; background: #fff; border: 1px solid {BORDER};
  border-radius: 10px; padding: 0.9rem 1.2rem;
}}
.why .main .t {{ font-size: 1.2rem; font-weight: 800; color: {BLUE}; white-space: nowrap; }}
.why .main .b {{ font-size: 0.88rem; color: {INK_2}; flex: 1; }}
.why .side {{
  flex: 1 1 480px; display: flex; gap: 1.2rem; justify-content: space-around; align-items: center; background: #fff;
  border: 1px solid {BORDER}; border-radius: 10px; padding: 0.9rem 1.2rem;
}}
.why .item {{ display: flex; gap: 0.6rem; align-items: center; font-size: 0.86rem; color: {INK}; line-height: 1.25; }}
.footer {{
  display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; font-size: 0.76rem; color: {INK_2};
  margin-top: 1rem; padding-top: 0.7rem; border-top: 1px solid {BORDER};
}}
.footer a {{ color: {INK}; text-decoration: none; display: inline-flex; gap: 0.35rem; align-items: center; }}
</style>
""")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    monthly = pd.read_csv(DATA_DIR / "monthly_response_times.csv", parse_dates=["date"])
    measures = pd.read_csv(DATA_DIR / "trust_area_measures.csv").set_index("trust")
    with open(DATA_DIR / "ambulance_trusts.geojson") as f:
        geojson = json.load(f)
    return monthly, measures, geojson


@st.cache_data
def image_data_uri(name):
    """Embed an image from dashboard/assets directly in the page."""
    import base64
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "svg": "image/svg+xml"}[name.rsplit(".", 1)[-1]]
    return f"data:{mime};base64," + base64.b64encode((ASSET_DIR / name).read_bytes()).decode()


def cat_cols(category):
    prefix = "c1" if category == "Category 1" else "c2"
    return f"{prefix}_calls", f"{prefix}_total_sec"


def weighted_mean_minutes(df, category):
    """Average response in minutes = total seconds waited / number of calls / 60."""
    calls, total = cat_cols(category)
    return df[total].sum() / df[calls].sum() / 60


def trust_summary(category, start, end):
    """Mean response time for each trust over a date range (weighted by calls)."""
    calls, total = cat_cols(category)
    period = monthly[(monthly["level"] == "Trust") & monthly["date"].between(start, end)]
    out = period.groupby("name")[[calls, total]].sum()
    out["mean_min"] = out[total] / out[calls] / 60
    return out.rename(columns={calls: "calls"})[["calls", "mean_min"]].sort_values("mean_min")


def yearly(category, name=None):
    """Yearly average response (weighted). The latest year may be part of a year."""
    rows = monthly[(monthly["name"] == name) if name else (monthly["level"] == "England")]
    rows = rows[rows["date"] >= FIRST_FULL_MONTH.replace(month=1)]
    rows = rows.assign(year=rows["date"].dt.year)
    out = rows.groupby("year").apply(weighted_mean_minutes, category=category, include_groups=False)
    months = rows.groupby("year")["date"].count()
    return pd.DataFrame({"mean_min": out, "months": months})


def monthly_series(category, name=None):
    calls, total = cat_cols(category)
    rows = monthly[(monthly["name"] == name) if name else (monthly["level"] == "England")]
    rows = rows[rows["date"] >= FIRST_FULL_MONTH]
    return pd.DataFrame({"date": rows["date"], "mean_min": rows[total] / rows[calls] / 60})


monthly, measures, geojson = load_data()
latest = monthly["date"].max()
trust_names = sorted(monthly.loc[monthly["level"] == "Trust", "name"].unique())
SERVICE_ALL = "All services (England)"
DEFAULTS = {
    "service": SERVICE_ALL,
    "category": "Category 2",
    "dates": ((latest - pd.DateOffset(months=11)).date(), (latest + pd.offsets.MonthEnd(0)).date()),
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)
st.session_state.setdefault("page", "overview")
st.session_state.setdefault("nav", "overview")
st.session_state.setdefault("scroll_to", None)


def fmt_month(d):
    return pd.Timestamp(d).strftime("%b %Y")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def go_to(nav):
    st.session_state["nav"] = nav
    st.session_state["page"] = "methodology" if nav == "methodology" else "overview"
    st.session_state["scroll_to"] = {"explains": "explains", "findings": "findings"}.get(nav, "top")


def reset_filters():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def pick_from_map():
    """When someone clicks a service on the map, select it in the sidebar filter."""
    points = st.session_state.get("map_chart", {}).get("selection", {}).get("points", [])
    if points and points[0].get("customdata"):
        st.session_state["service"] = points[0]["customdata"][0]


NAV_ITEMS = [
    ("overview", "Overview", ":material/home:"),
    ("explains", "What explains the differences?", ":material/bar_chart:"),
    ("methodology", "Data & methodology", ":material/description:"),
    ("findings", "Key findings", ":material/lightbulb:"),
]

with st.sidebar:
    html(f"""<div class="sb-brand">{icon('pulse', '#7fb2ff', 34, 2)}
         <div><div class="t">Ambulance<br>Response Analysis</div>
         <div class="s">England | {FIRST_FULL_MONTH.year} – {latest.year}</div></div></div>""")

    active = st.session_state["nav"]
    html(f"""<style>.st-key-nav_{active} button {{ background: #1f5fcf !important; font-weight: 600; }}</style>""")
    for key, label, mat_icon in NAV_ITEMS:
        st.button(label, key=f"nav_{key}", icon=mat_icon, on_click=go_to, args=(key,), width="stretch")

    st.divider()
    html('<div class="sb-heading">FILTERS</div>')
    service = st.selectbox("Ambulance service", [SERVICE_ALL] + trust_names, key="service")
    category = st.selectbox("Call category", list(TARGETS), key="category",
                            format_func=lambda c: f"{c} ({CATEGORY_HELP[c]})")
    dates = st.date_input("Date range", key="dates", format="DD/MM/YYYY",
                          min_value=FIRST_FULL_MONTH.date(), max_value=(latest + pd.offsets.MonthEnd(0)).date())
    st.button("Reset filters", key="reset", icon=":material/refresh:", on_click=reset_filters, width="stretch")

    target = TARGETS[category]
    html(f"""<div class="sb-target">{icon('target', '#ffffff', 34, 1.8)}
         <div><div class="l">{category} target</div><div class="v">{target} minutes</div>
         <div class="h">(mean response time)</div></div></div>""")
    html(f"""<div class="sb-art"><img src="{image_data_uri('sidebar.jpg')}" alt="">
         <div class="script">Faster<br>&nbsp;Care<br>&nbsp;&nbsp;Healthier<br>&nbsp;&nbsp;&nbsp;Communities</div></div>""")

# Whole months covered by the chosen dates (a half-picked range keeps the previous one)
if isinstance(dates, (tuple, list)) and len(dates) == 2:
    start = pd.Timestamp(dates[0]).to_period("M").to_timestamp()
    end = pd.Timestamp(dates[1]).to_period("M").to_timestamp()
else:
    start = pd.Timestamp(DEFAULTS["dates"][0]).to_period("M").to_timestamp()
    end = latest
selected = None if service == SERVICE_ALL else service
period_label = f"{fmt_month(start)} – {fmt_month(end)}"

summary = trust_summary(category, start, end)
england_avg = weighted_mean_minutes(
    monthly[(monthly["level"] == "England") & monthly["date"].between(start, end)], category)
annual = yearly(category)
full_years = annual[annual["months"] == 12]
peak_year, peak_value = full_years["mean_min"].idxmax(), full_years["mean_min"].max()
combined = summary.join(measures, how="inner")
PLOTLY_CONFIG = {"displayModeBar": False}


def base_layout(fig, height, **kwargs):
    kwargs.setdefault("margin", dict(l=8, r=8, t=8, b=8))
    fig.update_layout(
        height=height, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family=FONT, color=INK_2, size=12), showlegend=False,
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=INK), bordercolor=BORDER), **kwargs)
    fig.update_xaxes(gridcolor=GRID, linecolor="#c9d0dc", zeroline=False, tickfont=dict(color=INK_2))
    fig.update_yaxes(gridcolor=GRID, linecolor="#c9d0dc", zeroline=False, tickfont=dict(color=INK_2))
    return fig


def card_header(title, subtitle):
    html(f'<div class="ctitle">{title}</div><div class="csub">{subtitle}</div>')


# ---------------------------------------------------------------------------
# Overview components
# ---------------------------------------------------------------------------
def hero():
    html(f"""<div class="hero" id="top">
      <div class="art"><img src="{image_data_uri('hero.jpg')}" alt=""></div>
      <div class="script">Different places.<br>Different challenges.<br>Same urgent need.</div>
      <div class="text">
        <div class="eyebrow">A data analysis project using NHS England, OHID and ONS data</div>
        <h1>Does where you live affect<br>how fast an ambulance arrives?</h1>
        <p>Exploring ambulance response times across England and the role of <b>deprivation</b>,
        ageing populations and rurality.</p>
      </div></div>""")


def kpi(col, icon_name, icon_color, label, value, sub, name="", value_color=NAVY, red=False, sub_red=False):
    name_html = f'<div class="n">{name}</div>' if name else ""
    with col:
        html(f"""<div class="kpi {'red' if red else ''}">{icon(icon_name, icon_color, 34, 2)}
             <div><div class="l">{label}</div>{name_html}
             <div class="v" style="color:{value_color}">{value}</div>
             <div class="s {'red' if sub_red else ''}">{sub}</div></div></div>""")


def kpi_row():
    fastest, slowest = summary.index[0], summary.index[-1]
    c = st.columns(5, gap="small")
    if selected:
        value = summary.loc[selected, "mean_min"]
        diff = value - england_avg
        kpi(c[0], "clock", RED if value > target else GREEN, f"{selected} average ({category})",
            f"{value:.1f} min", f"{'↑' if diff > 0 else '↓'} {abs(diff):.1f} min vs England ({england_avg:.1f})",
            value_color=RED if value > target else GREEN, red=value > target, sub_red=diff > 0)
    else:
        above = england_avg > target
        kpi(c[0], "clock", RED, f"England average<br>({category})", f"{england_avg:.1f} min",
            f"↑ {england_avg - target:.1f} min above {target} min target" if above else "Meets the target",
            value_color=RED if above else GREEN, red=above, sub_red=above)
    kpi(c[1], "target", BLUE, f"Long-term standard<br>({category})", f"{target} min", "(mean response time)")
    kpi(c[2], "trend", RED, "Peak (England)", f"{peak_value:.1f} min", f"in {peak_year}")
    kpi(c[3], "trophy", GREEN, "Fastest service", f"{summary.loc[fastest, 'mean_min']:.1f} min", period_label,
        name=fastest, value_color=GREEN)
    kpi(c[4], "alert", RED, "Slowest service", f"{summary.loc[slowest, 'mean_min']:.1f} min",
        f"{summary.loc[slowest, 'mean_min'] / summary.loc[fastest, 'mean_min']:.1f}× as long as the fastest",
        name=slowest, value_color=RED, red=True, sub_red=True)


def outer_rings(geometry):
    polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    return [p[0] for p in polys]


KX = math.cos(math.radians(53))  # squash longitude so England isn't stretched sideways


def map_card():
    with st.container(key="card_map"):
        card_header("Response times across England", f"Average {category} response time, {period_label}")
        vals = summary["mean_min"]
        cmin, cmax = math.floor(vals.min() / 5) * 5, math.ceil(vals.max() / 5) * 5
        mid = min(max((england_avg - cmin) / (cmax - cmin), 0.05), 0.95)
        scale = [[0, "rgb(29,79,184)"], [mid / 2, "rgb(122,160,222)"], [mid, "rgb(236,236,244)"],
                 [(1 + mid) / 2, "rgb(232,138,140)"], [1, "rgb(214,54,60)"]]

        fig = go.Figure()
        centroids = {}
        for feat in geojson["features"]:
            trust = feat["properties"]["trust"]
            if trust not in vals:
                continue
            v = vals[trust]
            color = sample_colorscale(scale, [(v - cmin) / (cmax - cmin)])[0]
            xs, ys = [], []
            rings = outer_rings(feat["geometry"])
            for ring in rings:
                xs += [p[0] * KX for p in ring] + [None]
                ys += [p[1] for p in ring] + [None]
            biggest = max(rings, key=len)
            centroids[trust] = (np.mean([p[0] for p in biggest]) * KX, np.mean([p[1] for p in biggest]))
            fig.add_scatter(x=xs, y=ys, fill="toself", fillcolor=color, mode="lines",
                            line=dict(color=NAVY if trust == selected else "white", width=2.5 if trust == selected else 1),
                            hoverinfo="skip")
        # Invisible points at each service's centre: they give the hover box and let people click to filter
        names = list(centroids)
        fig.add_scatter(
            x=[centroids[n][0] for n in names], y=[centroids[n][1] for n in names], mode="markers",
            marker=dict(size=34, opacity=0), customdata=[[n, vals[n], vals[n] - england_avg] for n in names],
            hovertemplate="<b>%{customdata[0]}</b><br>Average: %{customdata[1]:.1f} min"
                          "<br>%{customdata[2]:+.1f} min vs England<br><i>Click to filter</i><extra></extra>",
            selected=dict(marker=dict(opacity=0)), unselected=dict(marker=dict(opacity=0)),
        )
        # Colour key
        fig.add_scatter(x=[None], y=[None], mode="markers", hoverinfo="skip", marker=dict(
            colorscale=scale, cmin=cmin, cmax=cmax, color=[cmin], showscale=True,
            colorbar=dict(thickness=12, len=0.36, x=0.0, xanchor="left", y=0.98, yanchor="top",
                          tickvals=[cmin, (cmin + cmax) / 2, cmax],
                          ticktext=[f"{cmin:g}", f"{(cmin + cmax) / 2:g}", f"{cmax:g}+"],
                          title=dict(text="Average response<br>time (minutes)", side="top", font=dict(size=10)),
                          tickfont=dict(size=10), outlinewidth=0)))

        # Call-out boxes: fastest, slowest, London and the selected service
        fastest, slowest = vals.idxmin(), vals.idxmax()
        callouts = [(fastest, BLUE, "white", "(fastest)"), (slowest, RED, RED_LIGHT, "(slowest)")]
        if "London" not in (fastest, slowest):
            callouts.append(("London", INK, "white", ""))
        if selected and selected not in [c[0] for c in callouts]:
            callouts.append((selected, NAVY, BLUE_LIGHT, "(selected)"))
        box_x = 0.95 * KX  # boxes sit in a column to the right of the map
        used_y = []
        for name, color, bg, note in sorted(callouts, key=lambda c: -centroids[c[0]][1]):
            cx, cy = centroids[name]
            by = cy if not used_y else min(cy, used_y[-1] - 1.15)
            used_y.append(by)
            fig.add_annotation(
                x=cx, y=cy, ax=box_x, ay=by, axref="x", ayref="y", xanchor="left",
                text=f"<b>{name}</b><br><span style='font-size:15px'><b>{vals[name]:.1f} min</b></span>"
                     + (f"<br>{note}" if note else ""),
                align="left", font=dict(color=color, size=11, family=FONT), bgcolor=bg, bordercolor=BORDER,
                borderwidth=1, borderpad=5, showarrow=True, arrowhead=0, arrowwidth=1.2, arrowcolor=color,
                startstandoff=2)
            fig.add_scatter(x=[cx], y=[cy], mode="markers", hoverinfo="skip",
                            marker=dict(size=7, color=color, line=dict(color="white", width=1.5)))

        base_layout(fig, 372, dragmode=False, clickmode="event+select")
        fig.update_xaxes(visible=False, range=[-6.6 * KX, 4.0 * KX])
        fig.update_yaxes(visible=False, range=[49.85, 55.95], scaleanchor="x", scaleratio=1)
        html(f'<div class="hint">{icon("pointer", INK_2, 16, 1.6)}<span>Hover to see details<br>Click to filter</span></div>')
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG, key="map_chart",
                        on_select=pick_from_map, selection_mode="points")


def trend_card():
    with st.container(key="card_trend"):
        card_header("How response times have changed over time",
                    f"{selected or 'England'} average {category} response time")
        view = st.segmented_control("View", ["England", "By service", "Monthly"], default="England",
                                    key="trend_view", label_visibility="collapsed") or "England"
        fig = go.Figure()
        if view == "Monthly":
            eng = monthly_series(category)
            fig.add_vrect(x0=start, x1=end + pd.offsets.MonthEnd(0), fillcolor=BLUE_LIGHT, opacity=0.8,
                          layer="below", line_width=0)
            fig.add_scatter(x=eng["date"], y=eng["mean_min"], mode="lines", name="England",
                            line=dict(color=MUTED if selected else BLUE, width=2),
                            hovertemplate="<b>England</b> %{x|%b %Y}: %{y:.1f} min<extra></extra>")
            if selected:
                s = monthly_series(category, selected)
                fig.add_scatter(x=s["date"], y=s["mean_min"], mode="lines", name=selected,
                                line=dict(color=BLUE, width=2.2),
                                hovertemplate=f"<b>{selected}</b> %{{x|%b %Y}}: %{{y:.1f}} min<extra></extra>")
            peak = eng.loc[eng["mean_min"].idxmax()]
            peak_x, peak_y, peak_text = peak["date"], peak["mean_min"], f"{peak['date']:%b %Y} peak"
        else:
            eng = annual.reset_index()
            label = [f"{y}" if m == 12 else f"{y} (Jan–{latest:%b})" for y, m in zip(eng["year"], eng["months"])]
            if view == "By service":
                for t in trust_names:
                    s = yearly(category, t).reset_index()
                    hi = t == selected
                    fig.add_scatter(x=s["year"], y=s["mean_min"], mode="lines+markers" if hi else "lines",
                                    line=dict(color=BLUE if hi else "#c3cad8", width=2.4 if hi else 1.2),
                                    marker=dict(size=6), name=t,
                                    hovertemplate=f"<b>{t}</b> %{{x}}: %{{y:.1f}} min<extra></extra>")
                fig.add_scatter(x=eng["year"], y=eng["mean_min"], mode="lines", name="England",
                                line=dict(color=NAVY, width=2.2, dash="dot"),
                                hovertemplate="<b>England</b> %{x}: %{y:.1f} min<extra></extra>")
            else:
                name = selected or "England"
                series = yearly(category, selected).reset_index() if selected else eng
                if selected:
                    fig.add_scatter(x=eng["year"], y=eng["mean_min"], mode="lines", name="England",
                                    line=dict(color=MUTED, width=1.6, dash="dot"),
                                    hovertemplate="<b>England</b> %{x}: %{y:.1f} min<extra></extra>")
                fig.add_scatter(x=series["year"], y=series["mean_min"], mode="lines+markers", name=name,
                                line=dict(color=BLUE, width=2.4), marker=dict(size=6, color=BLUE),
                                fill="tozeroy", fillcolor="rgba(31,95,207,0.10)", customdata=label,
                                hovertemplate=f"<b>{name}</b> %{{customdata}}: %{{y:.1f}} min<extra></extra>")
            full = annual[annual["months"] == 12]["mean_min"]
            peak_x, peak_y, peak_text = full.idxmax(), full.max(), f"{full.idxmax()} peak"
            fig.update_xaxes(dtick=1, range=[eng["year"].min() - 0.4, eng["year"].max() + 0.4])

        fig.add_hline(y=target, line=dict(color=RED, dash="dash", width=1.5),
                      annotation_text=f"<b>{target} min target</b>", annotation_position="top right",
                      annotation_font=dict(color=RED, size=11))
        fig.add_annotation(x=peak_x, y=peak_y, text=f"{peak_text}<br><b style='font-size:16px'>{peak_y:.0f} min</b>",
                           font=dict(color=RED, size=11), bgcolor=RED_LIGHT, bordercolor="#f3caca", borderpad=5,
                           showarrow=True, arrowhead=0, arrowcolor=RED, ax=40, ay=-34)
        fig.add_scatter(x=[peak_x], y=[peak_y], mode="markers", hoverinfo="skip",
                        marker=dict(size=9, color=RED, line=dict(color="white", width=2)))
        fig.add_annotation(x=0, y=1.0, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
                           text="Response time<br>(minutes)", showarrow=False, align="left",
                           font=dict(size=11, color=INK_2))
        base_layout(fig, 352, hovermode="closest", margin=dict(l=8, r=8, t=40, b=8))
        fig.update_yaxes(rangemode="tozero", showgrid=False, showline=True)
        fig.update_xaxes(showgrid=False, showline=True)
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def ranking_card():
    with st.container(key="card_rank"):
        card_header("Ambulance services ranked", f"Average {category} response time, {period_label}")
        rank = summary.sort_values("mean_min", ascending=False).reset_index()
        lo, hi = rank["mean_min"].min(), rank["mean_min"].max()
        pale = [[0, "rgb(168,192,232)"], [0.5, "rgb(205,198,226)"], [1, "rgb(236,170,180)"]]
        colors, label_colors = [], []
        for n, v in zip(rank["name"], rank["mean_min"]):
            if v == hi:
                colors.append(RED)
            elif v == lo:
                colors.append(BLUE)
            else:
                colors.append(sample_colorscale(pale, [(v - lo) / (hi - lo)])[0])
            label_colors.append(NAVY if n == selected else INK)
        fig = go.Figure(go.Bar(
            x=rank["mean_min"], y=rank["name"], orientation="h", marker=dict(
                color=colors, line=dict(color=[NAVY if n == selected else "rgba(0,0,0,0)" for n in rank["name"]],
                                        width=2)),
            text=[f"<b>{v:.1f}</b>" if v in (lo, hi) else f"{v:.1f}" for v in rank["mean_min"]],
            textposition="outside", cliponaxis=False, textfont=dict(color=INK, size=11),
            hovertemplate="<b>%{y}</b><br>%{x:.1f} min<extra></extra>"))
        fig.add_vline(x=target, line=dict(color=RED, dash="dash", width=1.4))
        fig.add_annotation(x=target, y=1.0, yref="paper", yanchor="bottom", xanchor="left", showarrow=False,
                           text=f"<b>{target} min target</b>", font=dict(color=RED, size=11))
        base_layout(fig, 402, bargap=0.28, margin=dict(l=8, r=30, t=26, b=8))
        fig.update_yaxes(autorange="reversed", showgrid=False, ticksuffix="  ",
                         tickfont=dict(color=INK, size=11.5))
        if selected:
            fig.update_yaxes(ticktext=[f"<b>{n}</b>" if n == selected else n for n in rank["name"]],
                             tickvals=rank["name"])
        fig.update_xaxes(title=dict(text="Average response time (minutes)", font=dict(size=11.5)),
                         range=[0, hi * 1.12], showgrid=True)
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def factors_card():
    with st.container(key="card_factors"):
        html('<div id="explains"></div>')
        card_header("What explains the differences?",
                    "Each point represents an ambulance service. Explore the relationships below. "
                    "With only 11 services, these are clues, not proof.")
        factors = [
            ("imd_score", "network", PURPLE, "Deprivation", "More deprived areas tend to get faster responses.",
             "Higher deprivation →", False),
            ("pct_65_plus", "people", BLUE, "Older population",
             "Little link between the share of older people and response times.", "% aged 65+ →", False),
            ("pop_weighted_density", "tree", GREEN, "Rurality",
             "Rural areas are slower, particularly for the most urgent calls.", "More rural (fewer people per sq km) →",
             True),
        ]
        cols = st.columns(3, gap="medium")
        for col, (field, icon_name, icon_color, title, desc, xlabel, is_density) in zip(cols, factors):
            d = combined[[field, "mean_min"]].dropna()
            rho = d[field].corr(d["mean_min"], method="spearman")
            with col:
                html(f"""<div class="factor-head">{icon(icon_name, icon_color, 32, 1.8)}
                     <div><div class="t">{title}</div><div class="d">{desc}</div></div></div>""")
                x = np.log10(d[field]) if is_density else d[field]
                fig = go.Figure()
                slope, intercept = np.polyfit(x, d["mean_min"], 1)
                xx = np.linspace(x.min(), x.max(), 20)
                fig.add_scatter(x=10 ** xx if is_density else xx, y=slope * xx + intercept, mode="lines",
                                line=dict(color="#4b6aa8", width=1.4), hoverinfo="skip")
                is_london = d.index == "London"
                for mask, color in [(~is_london, BLUE), (is_london, RED)]:
                    fig.add_scatter(x=d.loc[mask, field], y=d.loc[mask, "mean_min"], mode="markers",
                                    marker=dict(size=9, color=color, line=dict(color="white", width=1)),
                                    text=d.index[mask], customdata=[rho] * mask.sum(),
                                    hovertemplate="<b>%{text}</b><br>%{x:,.1f}<br>%{y:.1f} min<extra></extra>")
                lx = d.loc["London", field]
                fig.add_annotation(x=math.log10(lx) if is_density else lx, y=d.loc["London", "mean_min"],
                                   text="London", showarrow=False, yshift=11, font=dict(color=RED, size=10.5))
                if selected and selected != "London" and selected in d.index:
                    sx = d.loc[selected, field]
                    fig.add_annotation(x=math.log10(sx) if is_density else sx, y=d.loc[selected, "mean_min"],
                                       text=selected, showarrow=False, yshift=11, font=dict(color=NAVY, size=10.5))
                fig.add_annotation(x=0, y=1.0, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
                                   text="Response time<br>(mins)", showarrow=False, align="left",
                                   font=dict(size=10.5, color=INK_2))
                base_layout(fig, 290, margin=dict(l=8, r=8, t=34, b=8))
                fig.update_xaxes(title=dict(text=xlabel, font=dict(size=11.5, color=INK)), showgrid=False,
                                 showline=True)
                fig.update_yaxes(rangemode="tozero", showgrid=False, showline=True)
                if is_density:
                    fig.update_xaxes(type="log", autorange="reversed", tickvals=[500, 1000, 2000, 5000],
                                     ticktext=["500", "1,000", "2,000", "5,000"])
                st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
                html(f'<div class="csub" style="margin-top:-0.6rem">Spearman correlation: {rho:+.2f}</div>')


def findings_card():
    """Key findings, written for the default view: Category 2, latest 12 months."""
    f_start = latest - pd.DateOffset(months=11)
    s = trust_summary("Category 2", f_start, latest)
    eng = weighted_mean_minutes(
        monthly[(monthly["level"] == "England") & monthly["date"].between(f_start, latest)], "Category 2")
    yr = yearly("Category 2")
    yr = yr[yr["months"] == 12]["mean_min"]
    fast, slow = s.index[0], s.index[-1]
    items = [
        ("Response times are well above the target",
         f"Category 2 calls have an 18-minute target, but England averages about {eng:.0f} minutes, "
         f"peaking at {yr.max():.0f} minutes in {yr.idxmax()}."),
        ("There is large regional variation",
         f"The slowest service ({slow}, {s.loc[slow, 'mean_min']:.1f} min) is almost twice as slow as "
         f"the fastest ({fast}, {s.loc[fast, 'mean_min']:.1f} min)."),
        ("More deprived areas get faster responses",
         "Higher deprivation is associated with shorter response times. This partly overlaps with "
         "urban areas being faster."),
        ("Rural areas are slower, but it's not the whole story",
         "Rurality is linked to slower responses, especially for the most urgent calls, yet London is dense "
         "but still slow."),
    ]
    with st.container(key="card_findings"):
        html('<div id="findings"></div>')
        html(f'<div style="display:flex;gap:0.5rem;align-items:center">{icon("bulb", "#f5a524", 24, 2)}'
             f'<span class="ctitle" style="font-size:1.2rem">Key findings</span></div>')
        html("".join(f"""<div class="finding"><div class="num">{i}</div><div>
                 <div class="t">{t}</div><div class="b">{b}</div></div></div>"""
                     for i, (t, b) in enumerate(items, start=1)))
        html(f'<div class="csub" style="margin-bottom:0.6rem">Category 2, {fmt_month(f_start)} – {fmt_month(latest)}</div>')


def why_and_footer():
    html(f"""<div class="why">
      <div class="main">{icon('target', BLUE, 46, 1.8)}<div class="t">Why it matters</div>
        <div class="b">Faster ambulance response times can save lives and reduce long-term health impacts,
        particularly for time-critical conditions like strokes and heart attacks.</div>{icon('arrow', MUTED, 22, 1.6)}</div>
      <div class="side">
        <div class="item">{icon('heart', BLUE, 30, 1.5, fill=BLUE)}<span>Improved survival<br>and outcomes</span></div>
        <div class="item">{icon('people', BLUE, 30, 1.8)}<span>Reduced health<br>inequalities</span></div>
        <div class="item">{icon('hospital', BLUE, 30, 1.8)}<span>More efficient use<br>of NHS resources</span></div>
      </div></div>""")
    github = (f'<a href="{GITHUB_URL}" target="_blank">{icon("code", INK, 16, 2)} View code on GitHub</a>'
              if GITHUB_URL else "")
    html(f"""<div class="footer"><div><b>Sources:</b> NHS England (ambulance response times), OHID (Index of Multiple
      Deprivation), ONS (population and rurality; boundaries contain OS data © Crown copyright and database right)
      &nbsp;|&nbsp; {fmt_month(FIRST_FULL_MONTH)} – {fmt_month(latest)} &nbsp;|&nbsp; Independent portfolio project
      by a data analyst. Not affiliated with or endorsed by the NHS.</div>{github}</div>""")


def overview():
    hero()
    kpi_row()
    st.write("")
    c1, c2, c3 = st.columns([1.0, 1.12, 0.98], gap="small")
    with c1:
        map_card()
    with c2:
        trend_card()
    with c3:
        ranking_card()
    c4, c5 = st.columns([2.6, 1.0], gap="small")
    with c4:
        factors_card()
    with c5:
        findings_card()
    why_and_footer()


# ---------------------------------------------------------------------------
# Page: Data & methodology
# ---------------------------------------------------------------------------
def methodology():
    html(f"""<div class="hero" id="top" style="min-height:auto"><div class="text" style="max-width:100%">
      <div class="eyebrow">Ambulance Response Analysis</div><h1>Data & methodology</h1>
      <p>Where the data comes from, how the numbers are calculated, and what they can't tell you.</p></div></div>""")

    with st.container(key="card_table"):
        card_header("The numbers behind the charts",
                    f"{category}, {period_label}. Change the filters in the sidebar to update this table.")
        # Name the column explicitly: some pandas versions drop the index name after a join
        table = combined.reset_index(names="Ambulance service").rename(columns={
            "mean_min": "Average response (min)", "calls": "Calls",
            "imd_score": "Deprivation score (IMD 2019)", "pct_65_plus": "% aged 65+",
            "pop_weighted_density": "Population-weighted density (per sq km)", "population": "Population",
        })[["Ambulance service", "Average response (min)", "Calls", "Population",
            "Deprivation score (IMD 2019)", "% aged 65+", "Population-weighted density (per sq km)"]]
        st.dataframe(table, hide_index=True, width="stretch", height=35 * (len(table) + 1) + 3,
                     column_config={
                         "Average response (min)": st.column_config.NumberColumn(format="%.1f"),
                         "Calls": st.column_config.NumberColumn(format="%d"),
                         "Population": st.column_config.NumberColumn(format="%d"),
                         "Deprivation score (IMD 2019)": st.column_config.NumberColumn(format="%.1f"),
                         "% aged 65+": st.column_config.NumberColumn(format="%.1f"),
                         "Population-weighted density (per sq km)": st.column_config.NumberColumn(format="%d"),
                     })
        st.download_button("Download this table (CSV)", table.to_csv(index=False),
                           file_name="ambulance_response_by_service.csv", mime="text/csv")

    st.write("")
    c1, c2 = st.columns(2, gap="small")
    with c1:
        with st.container(key="card_sources"):
            st.markdown("#### Data sources")
            st.markdown("""
| Data | Publisher |
|---|---|
| Ambulance Quality Indicators (AmbSYS): response times and call counts by ambulance trust | NHS England |
| Local Authority Health Profiles: deprivation (IMD 2019), % aged 65+ | Office for Health Improvement and Disparities |
| Mid-2025 population estimates (table MYE5): population and land area | Office for National Statistics |
| Counties and Unitary Authorities (Dec 2024) boundaries, BUC | Office for National Statistics |

All data is public and aggregated. No patient-level or identifiable information is used.

#### Response time categories
- **Category 1:** life-threatening calls, such as cardiac arrest. Target: 7 minutes on average.
- **Category 2:** emergencies, such as stroke or heart attack. Target: 18 minutes on average.
""")
    with c2:
        with st.container(key="card_methods"):
            st.markdown("""
#### How the numbers are calculated
- **Weighted averages:** an average over several months is total time waited ÷ total calls,
  so busy months count for more.
- **Linking areas to ambulance services:** 153 council areas were matched to the 11 services with a
  lookup table, then area measures were combined, weighted by population.
- **Rurality:** measured as population-weighted density, the density of the area where the average
  person lives. Fewer people per sq km means more rural.
- **Spearman correlation:** compares rankings, so one unusual service has less influence.
  Trend lines on the charts are simple straight-line fits, shown as a guide.
- **Map:** service outlines were made by merging council-area boundaries.

#### Limitations
- Only **11 ambulance services**, so correlations are clues, not proof.
- **Correlation is not causation.** Staffing and hospital handover delays aren't in this data.
- Service-level averages hide big differences between towns and countryside within a service.
- The council-area lookup is approximate at a few borders.
- Deprivation uses **IMD 2019**, the version in the source data.
- Data starts in **April 2018** in this dashboard, the first month every service reported.
""")
    why_and_footer()


if st.session_state["page"] == "overview":
    overview()
else:
    methodology()

# Scroll to the section picked in the sidebar menu
if st.session_state.get("scroll_to"):
    target_id = st.session_state["scroll_to"]
    st.session_state["scroll_to"] = None
    script = f"""<script>
      setTimeout(function() {{
        const el = window.parent.document.getElementById("{target_id}");
        if (el) el.scrollIntoView({{behavior: "smooth", block: "start"}});
      }}, 350);
    </script>"""
    # target_id only ever comes from our own menu, never from user input
    if hasattr(st, "iframe"):
        st.iframe(script, height=1)
    else:  # older Streamlit versions
        components.html(script, height=0)
